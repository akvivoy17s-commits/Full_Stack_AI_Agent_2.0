# Docker Complete Guide for Full-Stack Development
## Dockerfile Syntax, Docker CLI Commands, Images, Containers, Compose, Networks, Volumes, Security, BuildKit, and Deployment

> **Purpose:** A practical, broad reference for learning Docker and using it to develop, test, package, and deploy full-stack applications.
>
> **Scope note:** Docker is a platform, not a single programming language with one fixed list of “functions.” Its ecosystem includes the Dockerfile instruction set, Docker CLI commands, Docker Compose Specification, Engine APIs, BuildKit/Buildx, registries, networking, storage drivers, orchestration, and platform-specific extensions. These APIs evolve. This guide covers the major Dockerfile instructions, commonly used CLI commands and options, Compose structures, and production concepts. It cannot guarantee every present and future command or option; use the official reference links at the end for exact syntax for your installed version.
>
> **Version note:** Examples use modern Docker CLI, BuildKit/Buildx, and Compose V2-style workflows. The Compose Specification is the recommended format; the old required `version:` field is obsolete in modern Compose files. Verify platform-specific flags and feature support before using them in production.

---

## Table of Contents

1. Docker Overview
2. Installation and Verification
3. Core Terminology
4. Docker Architecture
5. Docker CLI Syntax Rules
6. First Container
7. Image Commands
8. Container Commands
9. Logs, Inspect, Exec, and Debugging
10. Dockerfile Overview
11. All Main Dockerfile Instructions
12. Dockerfile Variables and Build Arguments
13. Shell Form vs Exec Form
14. Multi-Stage Builds
15. Build Context and `.dockerignore`
16. Build and Tag Images
17. Registry Login, Push, and Pull
18. Port Publishing
19. Environment Variables and Secrets
20. Volumes and Bind Mounts
21. Networks and DNS
22. Docker Compose Overview
23. Compose Services Syntax
24. Compose Volumes, Networks, Configs, and Secrets
25. Compose Commands
26. Full-Stack Compose Example
27. Dockerizing Python / Flask / FastAPI
28. Dockerizing Node.js / React
29. Dockerizing Spring Boot / Java
30. Dockerizing Databases
31. Health Checks and Startup Order
32. Resource Limits and Container Lifecycle
33. Docker Buildx and BuildKit
34. Image Size and Layer Caching
35. Docker Security Best Practices
36. Docker Debugging and Troubleshooting
37. Networking Deep Dive
38. Persistent Data and Backup Concepts
39. CI/CD and Deployment Patterns
40. Docker Swarm and Kubernetes Overview
41. Common Docker CLI Commands Quick Reference
42. Dockerfile Quick Reference
43. Compose Quick Reference
44. End-to-End Full-Stack Example
45. Practice Projects and Learning Roadmap
46. Official Documentation

---

# 1. Docker Overview

Docker is a platform for building, distributing, and running applications in containers.

A container packages an application and its dependencies while sharing the host operating system kernel. Containers are isolated processes, not full virtual machines.

Why developers use Docker:
- Consistent development/test environments.
- Package applications with runtime dependencies.
- Run databases, caches, and helper services locally.
- Reduce “works on my machine” differences.
- Build repeatable CI pipelines.
- Deploy versioned images to different environments.

Docker does not replace application code, database design, security, monitoring, or deployment planning. Containerizing a broken or insecure application does not fix it automatically.

Example architecture:

```text
Browser
   |
   v
Frontend container (React / Angular / static web server)
   |
   v
Backend API container (Flask / FastAPI / Spring Boot / Node.js)
   |
   +------> Database container or managed database
   |
   +------> Cache / message broker / object storage
```

In a Compose network, services can typically reach each other by service name, such as `api` connecting to `db:5432`. The hostname `localhost` inside a container means that container itself, not another service or the host.

---

# 2. Installation and Verification

Install Docker Desktop on supported Windows/macOS systems or Docker Engine on supported Linux systems using the official instructions for your OS. Windows container/WSL2 and Linux container behavior differs by platform.

Verify:

```bash
docker --version
docker version
docker info
docker compose version
docker buildx version
```

Check the daemon is reachable:

```bash
docker ps
```

Test with a small image:

```bash
docker run --rm hello-world
```

Common local requirements:
- Docker daemon/engine is running.
- The current account has permission to use Docker.
- Required ports are available.
- Enough disk, RAM, and CPU are available.
- Proxy, VPN, DNS, certificate, or registry credentials are configured where necessary.

A Docker CLI installation may exist even when the daemon is unavailable. In that case, `docker version` can show a client section but fail on the server section.

---

# 3. Core Terminology

| Term | Meaning |
|---|---|
| Image | Read-only template/layers used to create containers |
| Container | Running or stopped instance created from an image |
| Dockerfile | Text recipe describing how to build an image |
| Registry | Service that stores/distributes images |
| Docker Hub | A public/private image registry service |
| Volume | Docker-managed persistent storage |
| Bind mount | Mount a host path into a container |
| Network | Connectivity and service discovery between containers |
| Compose | Declarative configuration and lifecycle tool for multi-container apps |
| BuildKit | Modern image build engine |
| Buildx | Docker CLI plugin for advanced image builds |
| Layer | Cached/read-only filesystem change in an image |
| Container writable layer | Runtime write layer, normally ephemeral |
| Tag | Human-readable image reference such as `app:1.0` |
| Digest | Content-addressed image reference |
| Daemon / Engine | Service managing containers, images, networks, and volumes |
| Context | Build files and resources sent to the builder |
| Multi-stage build | Dockerfile using multiple `FROM` stages |
| Orchestrator | System scheduling/managing workloads across containers/nodes |

---

# 4. Docker Architecture

Typical components:
- Docker CLI: command-line client.
- Docker Engine/daemon: manages local container resources.
- BuildKit/buildx: builds images.
- Registry: stores images and manifests.
- Runtime components: execute isolated container processes.
- Compose: coordinates multiple local services from declarative YAML.

Commands often communicate with the Engine API through a local socket or configured context/endpoint. Remote contexts and daemon endpoints are powerful; secure access to them as administrative access.

Docker containers commonly use OS-level mechanisms such as namespaces and control groups on Linux. Isolation capabilities vary by host OS, platform, runtime, and configuration. A container should not be considered a perfect security boundary by default.

---

# 5. Docker CLI Syntax Rules

General command shape:

```bash
docker [OPTIONS] COMMAND [SUBCOMMAND] [ARGUMENTS]
```

Examples:

```bash
docker ps
docker image ls
docker container ls
docker logs my-container
docker compose up -d
```

CLI options may appear in locations permitted by the command parser. Use:

```bash
docker --help
docker COMMAND --help
docker compose --help
docker buildx --help
```

Quote paths/values that contain spaces. PowerShell, Command Prompt, Bash, and zsh have different quoting/environment syntax. The examples use cross-shell-friendly forms where practical, but some commands require shell-specific adaptation.

Inspect active context:

```bash
docker context ls
docker context show
docker context inspect
```

Switch context:

```bash
docker context use default
```

Only switch to a context you recognize. A remote context can change which machines or deployments your commands affect.

---

# 6. First Container

Run a temporary interactive Linux shell:

```bash
docker run --rm -it alpine:latest sh
```

- `run`: create and start a container.
- `--rm`: remove it when it exits.
- `-i`: keep standard input open.
- `-t`: allocate a terminal.
- `alpine:latest`: image reference.
- `sh`: command executed inside the container.

Print output and exit:

```bash
docker run --rm alpine:latest echo "Hello from Docker"
```

Run a web server and publish port 8080 on the host:

```bash
docker run -d --name demo-web -p 8080:80 nginx:alpine
```

Open `http://localhost:8080` in the browser.

Stop and remove the container:

```bash
docker stop demo-web
docker rm demo-web
```

Remove downloaded image only when no longer needed:

```bash
docker image rm nginx:alpine
```

Never remove a container/volume/image without understanding whether it contains data you need.

---

# 7. Image Commands

List local images:

```bash
docker image ls
docker images
```

Pull an image:

```bash
docker pull nginx:alpine
```

Inspect an image:

```bash
docker image inspect nginx:alpine
```

Show layer history:

```bash
docker image history nginx:alpine
```

Remove an image:

```bash
docker image rm IMAGE
```

Tag an image:

```bash
docker image tag my-app:local my-registry.example.com/team/my-app:1.0.0
```

Save/load image archives:

```bash
docker image save -o my-app.tar my-app:local
docker image load -i my-app.tar
```

`save` and `load` preserve image objects/layers better for image transfer than exporting a container filesystem. They are not database backups.

Prune unused image resources:

```bash
docker image prune
docker image prune -a
```

`-a` removes all unused images, not merely dangling images. Review space and impact before pruning shared development hosts.

---

# 8. Container Commands

List running containers:

```bash
docker ps
docker container ls
```

List all, including stopped:

```bash
docker ps -a
```

Run detached container:

```bash
docker run -d --name web nginx:alpine
```

Name, environment, port, and restart example:

```bash
docker run -d \
  --name api-demo \
  -p 8000:8000 \
  -e APP_ENV=development \
  --restart unless-stopped \
  my-api:local
```

Windows PowerShell supports backticks for multiline commands rather than Bash `\`. For fewer quoting issues, a command can be written on one line or moved into Compose YAML.

Stop/start/restart:

```bash
docker stop api-demo
docker start api-demo
docker restart api-demo
```

Pause/unpause:

```bash
docker pause api-demo
docker unpause api-demo
```

Remove container:

```bash
docker rm api-demo
docker rm -f api-demo
```

`-f` forcibly stops/removes a container; use carefully.

Rename:

```bash
docker rename old-name new-name
```

Container lifecycle operations may behave differently when the container belongs to a Compose project or orchestrator. Prefer the tool managing the workload (for example, Compose) when possible.

---

# 9. Logs, Inspect, Exec, and Debugging

Follow logs:

```bash
docker logs api-demo
docker logs --follow api-demo
docker logs --tail 100 api-demo
docker logs --since 10m api-demo
```

Execute a command in a running container:

```bash
docker exec -it api-demo sh
docker exec api-demo env
```

Use `bash` only if the image includes it; small images may include only `sh`.

Inspect configuration/state:

```bash
docker inspect api-demo
docker inspect --format '{{.State.Status}}' api-demo
docker container stats
docker top api-demo
docker diff api-demo
```

Copy files:

```bash
docker cp api-demo:/app/logs/app.log ./app.log
docker cp ./config.yml api-demo:/app/config.yml
```

Process signals:

```bash
docker kill api-demo
docker kill --signal=SIGTERM api-demo
```

`docker stop` normally requests graceful shutdown then eventually kills the process after the timeout; `docker kill` sends a signal immediately by default. Ensure applications handle termination signals and close resources cleanly.

---

# 10. Dockerfile Overview

A Dockerfile is a text file containing ordered build instructions.

Typical small Python API Dockerfile:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Important:
- `FROM` selects the base image.
- `WORKDIR` sets the working directory.
- `COPY` adds files from the build context.
- `RUN` executes build-time commands and creates image layers.
- `ENV` sets image environment defaults.
- `EXPOSE` documents the intended container port; it does not publish that port onto the host by itself.
- `CMD` supplies the default command/arguments when a container starts.
- `ENTRYPOINT` configures the main executable.
- `USER` selects the runtime user.
- `HEALTHCHECK` defines a container health test.
- `ARG` supplies build-time variables.

Dockerfile instructions are executed in order. Modern builds often use BuildKit.

---

# 11. All Main Dockerfile Instructions

The core Dockerfile instruction set includes `ADD`, `ARG`, `CMD`, `COPY`, `ENTRYPOINT`, `ENV`, `EXPOSE`, `FROM`, `HEALTHCHECK`, `LABEL`, `MAINTAINER` (deprecated/legacy), `ONBUILD`, `RUN`, `SHELL`, `STOPSIGNAL`, `USER`, `VOLUME`, and `WORKDIR`.

## `FROM`

```dockerfile
FROM python:3.12-slim
```

Use a pinned major/minor or digest as required by the reproducibility/security policy. `latest` is mutable and can change unexpectedly.

Multi-stage alias:

```dockerfile
FROM python:3.12-slim AS runtime-base
```

Platform selection:

```dockerfile
FROM --platform=$BUILDPLATFORM node:22-alpine AS build
```

Only use platform variables and cross-compilation patterns when supported by the chosen builder/base image.

## `RUN`

Shell form:

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

Exec form:

```dockerfile
RUN ["python", "-m", "compileall", "-q", "."]
```

Run commands at build time. Combine commands when it improves cache behavior and image cleanliness, but keep Dockerfiles maintainable.

## `CMD`

```dockerfile
CMD ["python", "app.py"]
```

A later command supplied to `docker run IMAGE ...` commonly overrides `CMD`.

## `ENTRYPOINT`

```dockerfile
ENTRYPOINT ["python", "-m", "myapp"]
```

Often combined with `CMD` for default arguments:

```dockerfile
ENTRYPOINT ["python", "-m", "myapp"]
CMD ["--port", "8000"]
```

Exec form is usually preferred for applications because it avoids unnecessary shell process behavior and makes signal handling clearer.

## `COPY`

```dockerfile
COPY requirements.txt /app/requirements.txt
COPY src/ /app/src/
```

Copy files/directories from the build context or supported build stages.

Copy from a stage:

```dockerfile
COPY --from=builder /app/dist /usr/share/nginx/html
```

Additional flags such as ownership/mode support depend on the Dockerfile frontend/platform.

## `ADD`

```dockerfile
ADD local-archive.tar.gz /app/
```

`ADD` has additional behavior for certain archives/remote sources. Prefer `COPY` unless that extra behavior is explicitly needed, because `COPY` is simpler and more predictable for ordinary local files.

## `WORKDIR`

```dockerfile
WORKDIR /app
```

Creates the directory if needed and changes the working directory for later relevant instructions.

## `ENV`

```dockerfile
ENV PYTHONUNBUFFERED=1
ENV APP_PORT=8000
```

Image environment defaults can be overridden at runtime. Do not bake secrets into `ENV`; values in image metadata/layers may be inspectable.

## `ARG`

```dockerfile
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim
```

Build arguments are mainly for build-time configuration; they are not secure secret storage. Use build secrets for credentials required during image builds.

## `EXPOSE`

```dockerfile
EXPOSE 8000
```

Documents the port the application intends to listen on. Publish it with `docker run -p` or Compose `ports`.

## `USER`

```dockerfile
RUN addgroup --system app && adduser --system --ingroup app app
USER app
```

The exact account-creation commands vary by base image/OS. Use a non-root user for applications where feasible, and ensure file/port permissions are correct.

## `VOLUME`

```dockerfile
VOLUME ["/data"]
```

Declares a mount point. Prefer explicit volume/bind mount configuration in Compose or runtime commands so persistence is clear.

## `LABEL`

```dockerfile
LABEL org.opencontainers.image.title="catalog-api"
LABEL org.opencontainers.image.description="Example backend API"
```

Labels add metadata. OCI label names/values should follow the convention your tooling expects.

## `HEALTHCHECK`

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
```

The command must use a tool available in the image. A health check can report unhealthy but does not automatically fix an application bug. Define a meaningful health endpoint.

## `STOPSIGNAL`

```dockerfile
STOPSIGNAL SIGTERM
```

Configures the signal used by Docker to request container stop, subject to runtime behavior and support.

## `SHELL`

```dockerfile
SHELL ["/bin/sh", "-c"]
```

Changes the default shell used by shell-form `RUN`, `CMD`, and `ENTRYPOINT` in supported contexts. Syntax and availability depend on platform.

## `ONBUILD`

```dockerfile
ONBUILD COPY . /app
```

Adds a trigger to run when the image is used as a base for a later build. It is specialized and uncommon in straightforward app images; understand its delayed behavior before relying on it.

## `MAINTAINER`

`MAINTAINER` is a legacy instruction and deprecated in current Dockerfile documentation. Use labels to describe authorship/ownership metadata.

---

# 12. Dockerfile Variables and Build Arguments

```dockerfile
ARG NODE_VERSION=22
FROM node:${NODE_VERSION}-alpine

ARG BUILD_LABEL=local
LABEL org.example.build-label=$BUILD_LABEL
```

`ARG` before the first `FROM` is available for use in `FROM`; a build argument needed later in a stage may need a declaration inside that stage as well.

Build:

```bash
docker build --build-arg NODE_VERSION=22 --build-arg BUILD_LABEL=ci -t my-app:local .
```

Do not use `ARG` or ordinary build environment variables to pass passwords, private keys, or tokens. Build output/layers/caches can leak them. Use the builder's supported secret-mount mechanism for build-only credentials.

---

# 13. Shell Form vs Exec Form

Shell form:

```dockerfile
CMD python app.py
```

Exec form:

```dockerfile
CMD ["python", "app.py"]
```

Differences:
- Shell form typically runs through a shell.
- Exec form starts the executable directly.
- Environment-variable expansion and shell operators behave differently.
- Exec form generally offers cleaner signal delivery for the main application process.

For complex startup behavior, prefer a small, reviewed entrypoint script that properly forwards signals rather than burying fragile shell logic in a command string.

---

# 14. Multi-Stage Builds

Multi-stage builds separate build-time dependencies from the final runtime image.

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

Advantages:
- Smaller runtime image.
- Build toolchain does not need to be included in the final stage.
- More focused dependency surface.
- Build stages can be reused by name.

A Python wheel-building example varies depending on packages/native dependencies and should be adapted to the actual project. Confirm runtime shared libraries exist when native packages are copied from another stage.

---

# 15. Build Context and `.dockerignore`

The build context is the set of files made available to the builder. The trailing `.` usually means the current directory.

Example `.dockerignore`:

```dockerignore
.git
.venv
venv
__pycache__/
*.py[cod]
.pytest_cache/
.mypy_cache/
node_modules/
dist/
build/
.env
.env.*
!.env.example
coverage/
.DS_Store
```

Do not send secrets, local dependencies, large datasets, logs, or Git history into builds unless explicitly required. Use allow-list patterns carefully. The exact ignore pattern syntax follows Docker's documented rules.

Build with explicit context:

```bash
docker build -f Dockerfile -t catalog-api:local .
```

`-f` selects a Dockerfile. Build context and Dockerfile location are not necessarily identical; verify relative `COPY` paths.

---

# 16. Build and Tag Images

Build image:

```bash
docker build -t catalog-api:1.0 .
```

Multiple tags:

```bash
docker build \
  -t catalog-api:1.0 \
  -t catalog-api:latest \
  .
```

Build without using cache:

```bash
docker build --no-cache -t catalog-api:debug .
```

Pull base image before a build:

```bash
docker build --pull -t catalog-api:local .
```

Choose a build target:

```bash
docker build --target build -t catalog-api:build-stage .
```

Build progress, cache export/import, SSH forwarding, secret mounts, target platform, and other advanced flags are builder-dependent. See the current Buildx reference.

---

# 17. Registry Login, Push, and Pull

Tag an image for a registry:

```bash
docker tag catalog-api:1.0 registry.example.com/team/catalog-api:1.0
```

Login:

```bash
docker login registry.example.com
```

Push/pull:

```bash
docker push registry.example.com/team/catalog-api:1.0
docker pull registry.example.com/team/catalog-api:1.0
```

Logout:

```bash
docker logout registry.example.com
```

Use secure credential helpers where available. Avoid embedding registry passwords directly in a shell command because they may enter shell history or process metadata. CI should use its secrets mechanism and short-lived/least-privilege credentials when supported.

Use version tags and ideally digest pinning for release reproducibility. A tag like `latest` can point to different image content over time.

---

# 18. Port Publishing

Syntax:

```bash
docker run -p HOST_PORT:CONTAINER_PORT IMAGE
```

Example:

```bash
docker run -d --name web -p 8080:80 nginx:alpine
```

Bind only to the local host for a development-only service when appropriate:

```bash
docker run -d -p 127.0.0.1:8080:80 nginx:alpine
```

`EXPOSE` in a Dockerfile does not publish a host port. `-p` creates a published port mapping; `-P` publishes exposed ports using dynamically chosen host ports.

Check ports:

```bash
docker port web
docker ps
```

Do not publish databases or admin endpoints to all host interfaces unless the network/security design requires it. Firewall and host networking behavior can vary.

---

# 19. Environment Variables and Secrets

Set a runtime environment variable:

```bash
docker run --rm -e APP_ENV=development my-app:local
```

Load from an environment file:

```bash
docker run --rm --env-file .env my-app:local
```

The file format and quoting rules are documented by Docker; do not assume it is identical to every shell's `.env` parser.

Dockerfile default:

```dockerfile
ENV APP_PORT=8000
```

Runtime override:

```bash
docker run -e APP_PORT=9000 my-app:local
```

Secrets principles:
- Do not commit real `.env` files.
- Do not bake secrets into image layers.
- Do not print secrets in build logs.
- Use orchestrator secret support or a secret manager.
- Rotate any credential that was accidentally published.
- Keep application logs redacted.

Docker BuildKit supports build secrets in documented builder configurations. Swarm secrets and Compose secret mounts have distinct support/behavior; ensure they match the deployment you use. A Compose file referring to a host environment variable is not automatically a secure secret-management system.

---

# 20. Volumes and Bind Mounts

Container writable layers are normally ephemeral. Use volumes or bind mounts when data must survive container recreation.

## Named volume

```bash
docker volume create db-data
docker run -d --name some-db -v db-data:/var/lib/example-data example/db
```

List/inspect/remove:

```bash
docker volume ls
docker volume inspect db-data
docker volume rm db-data
```

## Bind mount

```bash
docker run --rm -it \
  --mount type=bind,source="$(pwd)",target=/app \
  -w /app python:3.12-slim python -V
```

The source syntax above is shell-dependent. On Windows, use the current shell's correct path syntax.

Mount a read-only directory:

```bash
docker run --rm \
  --mount type=bind,source=/host/config,target=/app/config,readonly \
  my-app:local
```

Common options:
- Named volumes: managed by Docker; useful for database persistence.
- Bind mounts: expose a host filesystem path.
- `tmpfs`: temporary memory-backed mount on supported platforms.
- Read-only mounts where write access is unnecessary.

Mounting over a container directory hides the image's files at that path while the mount is active. This frequently explains why a mounted host directory appears empty or why built files disappear in development.

Removing a container does not normally remove its named volume. Pruning volumes can delete persistent data; review before running destructive cleanup commands.

---

# 21. Networks and DNS

List networks:

```bash
docker network ls
docker network inspect bridge
```

Create a network:

```bash
docker network create app-network
```

Run containers on it:

```bash
docker run -d --name app --network app-network my-app:local
docker run -d --name cache --network app-network redis:alpine
```

Connect/disconnect:

```bash
docker network connect app-network existing-container
docker network disconnect app-network existing-container
```

On a user-defined Docker network, containers can generally resolve other container/service names by Docker DNS. The default legacy bridge network has different service-name DNS behavior.

Inside the `app` container, `localhost` refers to `app`; to reach the cache container, use its network name/alias as appropriate (e.g., `cache`). Host access patterns vary by OS and runtime.

Network drivers include bridge and others for supported environments; overlay is used with compatible multi-host/swarm networking. Use segmentation so frontend, backend, and database services have only the connectivity they require.

---

# 22. Docker Compose Overview

Compose describes a multi-container application using YAML, usually `compose.yaml` or `docker-compose.yml`.

Modern Compose uses the Compose Specification. The old top-level `version:` property is no longer required and is considered obsolete by modern Compose implementations.

Basic example:

```yaml
services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"
```

Run:

```bash
docker compose up -d
docker compose ps
docker compose logs -f
docker compose down
```

Compose manages services, networks, volumes, configs/secrets where supported, and build settings. Its configuration is not identical to every Kubernetes/Swarm deployment format.

---

# 23. Compose Services Syntax

A service can use a prebuilt image or build from a Dockerfile.

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    image: example/api:local
    command: ["python", "-m", "app"]
    working_dir: /app
    environment:
      APP_ENV: development
    ports:
      - "8000:8000"
    restart: unless-stopped
```

Common Compose service attributes (availability/details vary by Compose implementation/platform):
- `image`
- `build`
- `command`
- `entrypoint`
- `container_name` (avoid when you want easy scaling)
- `ports`
- `expose`
- `environment`
- `env_file`
- `volumes`
- `networks`
- `depends_on`
- `healthcheck`
- `restart`
- `working_dir`
- `user`
- `read_only`
- `tmpfs`
- `stdin_open`
- `tty`
- `labels`
- `logging`
- `deploy` (some keys depend on deployment target and are not applied identically by every runtime)
- `profiles`
- `secrets`
- `configs`
- `init`
- `stop_grace_period`
- `extra_hosts`
- `dns`
- `cap_add` / `cap_drop`
- `security_opt`
- `ulimits`
- `mem_limit`/CPU-related controls and related platform-dependent settings
- `platform`
- `pull_policy`
- `develop` (support depends on Compose version/features)
- `extends`
- `include` / merge-related features, according to the installed Compose implementation

Not all options work the same way across local Compose, Swarm, Windows containers, and other deployment targets. Check the Compose reference for exact support.

---

# 24. Compose Volumes, Networks, Configs, and Secrets

## Named volume

```yaml
services:
  db:
    image: postgres:17
    volumes:
      - pg-data:/var/lib/postgresql/data

volumes:
  pg-data:
```

Choose the database image/version and data directory based on current vendor documentation.

## Bind mount

```yaml
services:
  api:
    build: .
    volumes:
      - ./src:/app/src:ro
```

Use read-write only when the application genuinely needs to change host files. Be aware of permissions, performance, and platform-specific file-sharing behavior.

## Networks

```yaml
services:
  frontend:
    image: example/frontend:local
    networks: [frontend-net]

  api:
    image: example/api:local
    networks: [frontend-net, backend-net]

  db:
    image: postgres:17
    networks: [backend-net]

networks:
  frontend-net:
  backend-net:
    internal: true
```

`internal: true` can constrain external connectivity for the network; review deployment behavior before relying on it as the only security control.

## Secrets

```yaml
services:
  api:
    image: example/api:local
    secrets:
      - database_password

secrets:
  database_password:
    file: ./secrets/database_password.txt
```

Compose secret implementation and guarantees depend on the runtime/platform. A local file referenced as a secret still requires secure file permissions and safe lifecycle handling; do not check real secret files into version control.

## Configs

Compose configs are designed to provide non-secret configuration files to services in supported environments. Don't use configs as a substitute for secret storage.

---

# 25. Compose Commands

Validate/inspect merged configuration:

```bash
docker compose config
docker compose config --services
docker compose config --images
```

Start services:

```bash
docker compose up
docker compose up -d
docker compose up --build
docker compose up -d --build
```

List:

```bash
docker compose ps
docker compose ps -a
```

Logs:

```bash
docker compose logs
docker compose logs -f api
docker compose logs --tail 100
```

Run command inside a service container:

```bash
docker compose exec api sh
docker compose exec api python --version
```

Run a one-off container for a service:

```bash
docker compose run --rm api python -m pytest
```

Stop/remove project containers and network:

```bash
docker compose stop
docker compose down
```

Remove named volumes too (DANGEROUS when they contain database data):

```bash
docker compose down --volumes
```

Other common commands:
- `docker compose start`, `stop`, `restart`
- `docker compose pull`
- `docker compose build`
- `docker compose push`
- `docker compose rm`
- `docker compose top`
- `docker compose port`
- `docker compose events`
- `docker compose kill`
- `docker compose pause`, `unpause`
- `docker compose cp`
- `docker compose exec`
- `docker compose run`
- `docker compose watch` when supported
- `docker compose images`/`ps` availability and exact output can differ with Compose version

Use `docker compose COMMAND --help` for the complete options in your installed version.

---

# 26. Full-Stack Compose Example

Example `compose.yaml` for an API, database, and frontend. Adapt each image, database version, credentials, network, and health-check command to your project and current image documentation.

```yaml
services:
  api:
    build:
      context: ./backend
    environment:
      APP_ENV: development
      DATABASE_HOST: db
      DATABASE_PORT: "5432"
      DATABASE_NAME: appdb
      DATABASE_USER: appuser
      DATABASE_PASSWORD: ${DATABASE_PASSWORD:?Set DATABASE_PASSWORD}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    networks:
      - backend
      - frontend
    restart: unless-stopped

  db:
    image: postgres:17
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD:?Set DATABASE_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d appdb"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
    ports:
      - "8080:80"
    depends_on:
      - api
    networks:
      - frontend
    restart: unless-stopped

volumes:
  postgres-data:

networks:
  frontend:
  backend:
    internal: true
```

Important notes:
- Set `DATABASE_PASSWORD` through the environment/secrets mechanism before starting Compose.
- The backend should build its database URL using these values safely.
- `depends_on` with a health condition waits for the configured health check in supported Compose contexts, but does not replace reconnect logic in the application.
- Frontend browser code typically calls the backend via a browser-accessible URL; a Compose service name such as `api` generally resolves inside the Docker network, not in the end user's browser.
- In production, do not use example credentials, and review whether the API should be directly exposed or fronted by a reverse proxy.
- Keep secrets out of Git. Add local secret/env files to `.gitignore`.

---

# 27. Dockerizing Python / Flask / FastAPI

Example FastAPI project files:

```text
backend/
├── app/
│   └── main.py
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

`requirements.txt` might include compatible pinned versions for FastAPI and the chosen ASGI server.

`Dockerfile`:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN useradd --create-home --shell /usr/sbin/nologin appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The `useradd` command is available in many Debian-based Python slim images; verify the selected base image and adjust for its OS. Use a non-root user where practical and ensure all needed files are readable.

For Flask, the production command typically uses a supported WSGI server. Do not use `flask run --debug` in production.

`.dockerignore`:

```dockerignore
.git
.venv
__pycache__
*.pyc
.env
.env.*
.pytest_cache
.mypy_cache
dist
build
```

Build/run:

```bash
docker build -t python-api:local ./backend
docker run --rm -p 8000:8000 --env-file .env python-api:local
```

Adapt the path and environment settings to the app. Avoid copying local virtual environments or secrets into the image.

---

# 28. Dockerizing Node.js / React

For a static React frontend, a multi-stage build can compile assets in Node.js and serve them with a web server.

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

The build output directory may be `dist`, `build`, or something else depending on the frontend tool. Check your actual build configuration.

Build/run:

```bash
docker build -t frontend:local ./frontend
docker run --rm -p 8080:80 frontend:local
```

Single-page applications with client-side routes may need a web-server fallback to `index.html`. Configure Nginx or your chosen static server accordingly.

Browser environment variables are usually embedded at build time by frontend tooling; they are not secret after they reach browser code. Never include private API credentials in a frontend bundle.

---

# 29. Dockerizing Spring Boot / Java

A runtime-only Dockerfile:

```dockerfile
FROM eclipse-temurin:21-jre
WORKDIR /app

COPY target/catalog-api.jar app.jar

RUN useradd --system --create-home appuser
USER appuser

EXPOSE 8080
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

Adapt `target/catalog-api.jar` to the actual artifact filename. Base-image OS and user-creation commands can differ.

Build Java before building the runtime image:

```bash
mvn clean package
docker build -t catalog-api:local .
docker run --rm -p 8080:8080 catalog-api:local
```

A multi-stage build can compile in a JDK image and copy only the runtime artifact into a JRE image. For production, configure memory/container awareness and JVM flags based on the chosen Java version and observed workload.

---

# 30. Dockerizing Databases

Database containers are useful for development and automated tests. Follow the official image documentation for current environment variables, startup behavior, data paths, and version upgrades.

General pattern:

```yaml
services:
  database:
    image: postgres:17
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${DATABASE_PASSWORD:?Set DATABASE_PASSWORD}
    volumes:
      - database-data:/var/lib/postgresql/data
    ports:
      - "127.0.0.1:5432:5432"

volumes:
  database-data:
```

Use port publishing only if a host client needs direct access. The example binds to loopback so it is not intentionally published on every host interface; verify platform behavior and firewall rules.

Database container safety:
- Persist data in a volume or supported managed storage.
- Keep database credentials out of the image.
- Use a supported image tag and follow vendor upgrade instructions.
- Understand initialization variables often apply only when the data directory is empty.
- Back up data and test restore.
- Avoid destructive commands such as `docker compose down --volumes` unless data loss is intended.
- A container restart is not a database backup.
- A local development database and a production database need different hardening and recovery plans.

---

# 31. Health Checks and Startup Order

A container being “running” does not guarantee that the application is ready to accept requests.

Dockerfile health-check example:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
```

This works only if Python and the endpoint are available inside the image. Some slim images do not include curl/wget, so choose a probe command that actually exists.

Compose health check:

```yaml
services:
  api:
    build: .
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
```

`depends_on` without a health condition generally describes dependency/start ordering, not proof that the dependency is ready. For robust startup, apps should handle a temporarily unavailable database with safe retries/backoff.

Do not expose a detailed health endpoint containing credentials or internal system data.

---

# 32. Resource Limits and Container Lifecycle

Common runtime flags:
- `--memory` / `-m`: memory limit
- `--cpus`: CPU quota
- `--pids-limit`: process count limit
- `--restart`: restart policy
- `--read-only`: read-only container filesystem
- `--tmpfs`: temporary in-memory filesystem
- `--user`: runtime UID/GID
- `--cap-drop`: drop Linux capabilities on supported environments
- `--security-opt`: security-related runtime options
- `--init`: use an init process where supported

Example:

```bash
docker run -d \
  --name limited-api \
  --memory=512m \
  --cpus=1.5 \
  --pids-limit=200 \
  --read-only \
  --tmpfs /tmp \
  my-api:local
```

Only use read-only root filesystems if the app writes only to explicitly writable mounts/paths. CPU/memory enforcement and flag support vary by platform/runtime. Measure the app's requirements and test graceful behavior when limits are reached.

Restart policies commonly include:
- `no`
- `on-failure`
- `always`
- `unless-stopped`

Restart policies are not a substitute for health monitoring, orchestration, and proper error handling.

---

# 33. Docker Buildx and BuildKit

Buildx is a Docker CLI plugin providing advanced build functionality using BuildKit.

Check builders:

```bash
docker buildx version
docker buildx ls
docker buildx inspect
```

Create/use a builder:

```bash
docker buildx create --name mybuilder --use
docker buildx inspect --bootstrap
```

Build image:

```bash
docker buildx build -t my-app:local --load .
```

Multi-platform example:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t registry.example.com/team/my-app:1.0 \
  --push \
  .
```

A multi-platform build may need emulation, native builders, cross-compilation support, and correct base images. `--load` and `--push` have different image-export behavior; a multi-platform manifest may be pushed to a registry rather than loaded as a single local image.

Other common areas:
- Cache export/import
- Build secrets
- SSH forwarding
- Provenance and metadata attestations
- SBOM generation
- Build targets and named contexts
- Cache mounts
- Platform selection

Use exact flags from the current Buildx reference; builder capabilities depend on version and configuration.

---

# 34. Image Size and Layer Caching

Image optimization strategies:
- Choose an appropriate maintained base image.
- Copy dependency manifests before frequently changing source files to improve cache reuse.
- Use multi-stage builds.
- Exclude `.git`, local virtual environments, node_modules, local datasets, logs, caches, and secrets with `.dockerignore`.
- Avoid package manager caches in the final image.
- Avoid installing build toolchains at runtime if not needed.
- Keep only required runtime files.
- Pin dependency versions and assess base-image updates.
- Use BuildKit cache mounts when appropriate.
- Inspect the resulting layers and image size.

Example layer-friendly Python pattern:

```dockerfile
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
```

Changing `app/` can preserve the dependency-install layer if `requirements.txt` has not changed. Cache behavior can change with build args, base image, file metadata, builder version, and other inputs.

Smaller is not automatically safer or better if it requires an unmaintained base image or strips necessary debugging/security components. Optimize for maintainability, patchability, and verified runtime requirements.

---

# 35. Docker Security Best Practices

## Image and build security
- Use trusted, maintained base images.
- Pin image tags thoughtfully and consider immutable digests for releases.
- Scan image/package vulnerabilities.
- Avoid copying secrets into build contexts or image layers.
- Use BuildKit secret mounts for build-time credentials.
- Use multi-stage builds to keep build tools out of runtime images.
- Rebuild images regularly to incorporate base-image security updates.
- Generate and retain SBOM/provenance where useful.

## Runtime security
- Run as a non-root user when feasible.
- Drop unnecessary Linux capabilities.
- Avoid `--privileged` unless an exceptional, reviewed requirement exists.
- Avoid mounting the Docker socket into application containers; it can grant extensive control over the host daemon.
- Use read-only filesystems where practical.
- Restrict published ports.
- Apply resource limits and network segmentation.
- Keep secrets out of environment dumps/logs when feasible.
- Apply least privilege to users and mounted files.
- Patch Docker Engine, Compose, base images, dependencies, and the host OS.

## Supply chain
- Prefer official or verified publisher images where appropriate.
- Verify image source and digest when the threat model requires it.
- Review licenses and dependency provenance.
- Use CI scanning and access-controlled registries.
- Have an incident/credential rotation process.

Containers do not remove the need for host security, application security, database backups, or monitoring.

---

# 36. Docker Debugging and Troubleshooting

Useful commands:

```bash
docker ps -a
docker logs --tail 200 my-container
docker inspect my-container
docker stats
docker top my-container
docker network ls
docker volume ls
docker system df
docker events
```

Common problems:

| Symptom | What to check |
|---|---|
| Cannot connect to daemon | Docker Desktop/Engine status, context, socket/permissions |
| Port already allocated | Another process/container owns host port; choose another port |
| Container exits immediately | `docker logs`, entrypoint/CMD, missing dependencies, bad config |
| `exec` says container is not running | Inspect state and exit code first |
| `COPY` file not found | Build context, `.dockerignore`, relative path, Dockerfile location |
| App works locally but not in container | Bind address, environment, missing file/dependency, OS differences |
| API unreachable | Published port, app listening address, firewall, service/network name |
| Container cannot reach DB | Wrong host: `localhost` may refer to the same container; verify network/service name |
| Data disappears | No volume, wrong mount path, or destructive cleanup |
| Permission denied | Container user, host file permissions, mount mode, SELinux/platform rules |
| Image is large | Base image, build tools, cache, context, layers |
| Build cache never hits | Copy order, changed dependency files, args, context metadata |
| Health check fails | Wrong endpoint/port or probe tool missing from image |
| Compose startup race | Add appropriate readiness checks and application retry behavior |
| Out-of-memory termination | Container/host memory, model size, concurrency, batch settings |
| Wrong architecture | Platform/image build support, native dependencies, builder target |

Avoid sharing full `docker inspect`, environment output, or logs publicly if they may include credentials or private configuration.

---

# 37. Networking Deep Dive

## Container-to-container

Use a user-defined network or Compose. Each service can usually resolve other services by name inside the same network.

## Host-to-container

Publish a port:

```bash
docker run -p 127.0.0.1:9000:8000 my-api:local
```

Then a host client may use `http://127.0.0.1:9000`.

## Container-to-host

The host address varies by OS, Docker Desktop, network mode, and host configuration. `host.docker.internal` is provided in many Docker Desktop environments but is not universal for every runtime. On supported platforms it may be explicitly added using documented host-gateway behavior.

## DNS and aliases

Compose service names can act as DNS names on shared Compose networks. Do not hard-code container IP addresses; they can change after recreation.

## Network drivers

Common Docker Engine network driver types include:
- `bridge`
- `host`
- `none`
- `overlay` (multi-host/Swarm contexts)
- `macvlan`
- `ipvlan`

Availability/semantics depend on platform and configuration. Host networking behaves differently across Linux and Docker Desktop. Use the official network docs for exact behavior.

---

# 38. Persistent Data and Backup Concepts

Persistence options:
- Docker named volumes
- Bind mounts
- External object storage
- Managed databases/volumes
- Application-level backup/export

For databases, use the storage layout recommended by the official image/vendor. Do not assume copying live database files while it is writing produces a valid backup. Use native backup tools or documented volume/database snapshots.

Important concepts:
- Volume backup and restore
- Consistent snapshots
- Data retention
- Encryption and access control
- Restore testing
- Migration/upgrade paths
- Storage capacity and monitoring
- Recovery point/time objectives

Never use `docker compose down --volumes` as a routine reset on an environment with data that must be retained; it can delete named volumes associated with the Compose project.

---

# 39. CI/CD and Deployment Patterns

A typical release pipeline:

```text
Commit
  ↓
Lint and unit tests
  ↓
Build container image
  ↓
Scan dependencies/image
  ↓
Run integration tests
  ↓
Tag and push image
  ↓
Deploy immutable image reference
  ↓
Health checks and smoke tests
  ↓
Monitor / rollback if necessary
```

Best practices:
- Use a unique immutable release tag and retain the image digest.
- Keep registry credentials in CI secrets.
- Do not build production secrets into the image.
- Promote the same tested image between environments where practical.
- Run database migrations in a controlled step.
- Configure health checks and graceful shutdown.
- Define rollout/rollback procedures.
- Verify that the database schema is compatible during rolling deployments.
- Scan base images/dependencies and update them regularly.
- Review provenance/SBOM options in the CI environment.

Deployment mechanism depends on whether you use a VM, Compose on a single host, Swarm, Kubernetes, a managed container platform, or another orchestrator. Docker alone is not a complete high-availability deployment strategy.

---

# 40. Docker Swarm and Kubernetes Overview

Docker Swarm is Docker's native clustering/orchestration feature. Kubernetes is a separate container orchestration platform.

Typical Swarm concepts:
- Swarm initialization/joining
- Manager and worker nodes
- Services and replicas
- Overlay networks
- Secrets and configs
- Rolling updates
- Placement constraints

Typical Kubernetes concepts:
- Pods
- Deployments
- Services
- ConfigMaps and Secrets
- Ingress/Gateway
- Probes
- Resource requests/limits
- Persistent volumes
- Namespaces and RBAC

Commands such as `docker service`, `docker stack`, and `docker swarm` pertain to Swarm-related management; Compose files do not map perfectly to every Swarm feature. Kubernetes uses its own API objects and command-line tools. Select the orchestrator that fits the team and workload; avoid choosing based only on popularity.

---

# 41. Common Docker CLI Commands Quick Reference

## General
```bash
docker --help
docker version
docker info
docker context ls
docker system df
```

## Images
```bash
docker pull IMAGE
docker image ls
docker image inspect IMAGE
docker image history IMAGE
docker image tag SOURCE TARGET
docker image rm IMAGE
docker image prune
docker image save -o image.tar IMAGE
docker image load -i image.tar
```

## Containers
```bash
docker run IMAGE
docker run -d --name NAME -p HOST:CONTAINER IMAGE
docker ps
docker ps -a
docker stop CONTAINER
docker start CONTAINER
docker restart CONTAINER
docker rm CONTAINER
docker rm -f CONTAINER
docker exec -it CONTAINER sh
docker logs -f CONTAINER
docker inspect CONTAINER
docker stats
docker top CONTAINER
docker cp CONTAINER:/path ./path
docker port CONTAINER
```

## Builds and registries
```bash
docker build -t NAME:TAG .
docker build --no-cache -t NAME:TAG .
docker buildx ls
docker buildx build -t NAME:TAG --load .
docker login REGISTRY
docker push IMAGE
docker pull IMAGE
docker logout REGISTRY
```

## Networks and volumes
```bash
docker network ls
docker network create NAME
docker network inspect NAME
docker network rm NAME
docker volume ls
docker volume create NAME
docker volume inspect NAME
docker volume rm NAME
docker volume prune
```

## Compose
```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose logs -f
docker compose exec SERVICE sh
docker compose run --rm SERVICE COMMAND
docker compose stop
docker compose down
docker compose down --volumes  # Destructive to project volumes: review first
```

The command surface is larger than this shortlist. Use `docker COMMAND --help` for the exact subcommands/options supported by your installation.

---

# 42. Dockerfile Quick Reference

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS runtime

ARG APP_VERSION=dev
LABEL org.opencontainers.image.version=$APP_VERSION

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser app/ ./app/

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]

ENTRYPOINT ["uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

This example assumes:
- The base image contains `uvicorn` from installed dependencies.
- `appuser` exists (it would need to be created earlier in the image).
- `/health` exists.
- The Dockerfile frontend supports the syntax shown.
- File permissions are correct.

It is a syntax illustration rather than a directly runnable standalone Dockerfile. A valid production Dockerfile must create the runtime user before assigning file ownership or switching users.

Core instructions: `ADD`, `ARG`, `CMD`, `COPY`, `ENTRYPOINT`, `ENV`, `EXPOSE`, `FROM`, `HEALTHCHECK`, `LABEL`, `MAINTAINER` (legacy/deprecated), `ONBUILD`, `RUN`, `SHELL`, `STOPSIGNAL`, `USER`, `VOLUME`, `WORKDIR`.

---

# 43. Compose Quick Reference

Modern Compose Specification example:

```yaml
name: demo-app

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        APP_VERSION: local
    image: demo-api:local
    command: ["python", "-m", "app"]
    environment:
      APP_ENV: development
    env_file:
      - .env
    ports:
      - "8000:8000"
    volumes:
      - type: bind
        source: ./app
        target: /app/app
    networks:
      - app-net
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "print('health command placeholder')"]
      interval: 30s
      timeout: 3s
      retries: 3

networks:
  app-net:

volumes:
  app-data:
```

Common top-level elements:
- `name`
- `services`
- `networks`
- `volumes`
- `configs`
- `secrets`
- `include` and other Compose features depending on version

Common service keys include:
- `image`, `build`
- `command`, `entrypoint`
- `ports`, `expose`
- `environment`, `env_file`
- `volumes`, `networks`
- `depends_on`
- `healthcheck`
- `restart`
- `working_dir`, `user`
- `read_only`, `tmpfs`
- `logging`, `labels`
- `profiles`
- `secrets`, `configs`
- `platform`, `pull_policy`
- `init`, `stop_grace_period`
- `extra_hosts`, `dns`
- `cap_add`, `cap_drop`, `security_opt`
- resource limits and deploy-related settings, depending on runtime/version

The Compose Specification is broad. Check the official file reference for the complete schema and runtime-specific behavior.

---

# 44. End-to-End Full-Stack Example

A minimal local stack may include:
- Frontend container
- Backend API container
- Database service
- Named persistent database volume
- Private network between backend and database
- Published frontend/API ports appropriate for the environment
- Health checks and restart policy

Development and production configuration should be separated. Development bind mounts are useful for hot reload but can obscure files built into the image. Production should use immutable images, pinned dependencies/base images, secret management, TLS, backups, health checks, logging, monitoring, and rollout/rollback planning.

Never publish a database port publicly just because the API needs database access. Containers on a shared internal network can communicate via service names without publishing the database port on the host.

---

# 45. Practice Projects and Learning Roadmap

Learn in this order:
1. Images vs containers.
2. `docker run`, `ps`, `logs`, `exec`, `inspect`, `stop`, `rm`.
3. Dockerfile instructions and image layers.
4. Build context and `.dockerignore`.
5. Port mapping and environment variables.
6. Volumes and data persistence.
7. Networking and container DNS.
8. Compose services, health checks, and dependencies.
9. Multi-stage builds and BuildKit.
10. Registries, tags, immutable digests.
11. Security, non-root containers, secrets, and scanning.
12. CI/CD and deployment orchestration.

Practice projects:
- Run Nginx locally
- Containerize a Flask/FastAPI API
- Containerize a Spring Boot API
- Containerize a static React build
- Run API + PostgreSQL/MongoDB through Compose
- Persist database data in a volume
- Add health checks and readiness handling
- Build a multi-stage frontend/backend image
- Build and test in CI
- Deploy using a documented hosting/orchestration approach

---

# 46. Official Documentation

- [Docker Documentation](https://docs.docker.com/)
- [Docker Reference](https://docs.docker.com/reference/)
- [Docker CLI Reference](https://docs.docker.com/reference/cli/docker/)
- [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/)
- [Buildx Reference](https://docs.docker.com/reference/cli/docker/buildx/)
- [Docker Compose Reference](https://docs.docker.com/reference/compose-file/)
- [Compose Services Reference](https://docs.docker.com/reference/compose-file/services/)
- [Compose Volumes Reference](https://docs.docker.com/reference/compose-file/volumes/)
- [Compose Networks Reference](https://docs.docker.com/reference/compose-file/networks/)
- [Networking Overview](https://docs.docker.com/engine/network/)
- [Storage Overview](https://docs.docker.com/engine/storage/)
- [Docker Security](https://docs.docker.com/engine/security/)
- [Docker Engine API](https://docs.docker.com/reference/api/engine/)
- [Docker Hub](https://docs.docker.com/docker-hub/)

---

## Final Note

Docker's full surface consists of CLI subcommands/options, Dockerfile instructions, Compose schema, Engine APIs, BuildKit/Buildx features, registry APIs, runtime/security settings, and platform-specific behavior. No single file can guarantee a literal 100% listing of every current and future command. Use this guide as a comprehensive learning reference and consult the exact official reference for your installed version before applying commands to production or deleting data.
