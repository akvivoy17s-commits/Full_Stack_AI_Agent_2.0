"""Spring Boot (Java) generator, part A (phase 4.3): project skeleton, configuration, error envelope, security filters, validation core.
Static Java lives in templates/spring; built here: pom.xml, schema.json, .env.example, README. Same spec -> API contract as the other generators.

Registered in stage.GENERATORS (part C): core + data + JWT sign-in + seed are complete."""
import json
from pathlib import Path

from backend.gen import model as M
from backend.gen import openapi

TPL = Path(__file__).parent / "templates" / "spring"
BOOT = "3.3.5"                       # Spring Boot 3.3 = Spring Framework 6.1, Jakarta EE 10, Java 17+
JAVA = "17"
PARTS_DONE = {"core", "data", "security"}        # the README and pom follow this set


def schema_json(m: dict) -> str:
    body = {"db": m["db"], "auth": m["auth"], "refresh": m["auth"] and m["refresh"], "roles": m["roles"], "adminRole": m["adminRole"],
            "defaultRole": m["defaultRole"], "seed": m["seed"], "entities": {e["name"]: e for e in m["entities"]}}
    return json.dumps(body, indent=2) + "\n"


SQL_DEPS = {"sqlite": [("org.xerial", "sqlite-jdbc", "3.46.1.3")],
            "postgresql": [("org.postgresql", "postgresql", None), ("org.flywaydb", "flyway-database-postgresql", None)],
            "mysql": [("com.mysql", "mysql-connector-j", None), ("org.flywaydb", "flyway-mysql", None)],
            "mssql": [("com.microsoft.sqlserver", "mssql-jdbc", None), ("org.flywaydb", "flyway-sqlserver", None)]}


def _dep(g: str, a: str, v: str | None = None, scope: str | None = None) -> str:
    return (f"        <dependency>\n            <groupId>{g}</groupId>\n            <artifactId>{a}</artifactId>\n" + (f"            <version>{v}</version>\n" if v else "")
            + (f"            <scope>{scope}</scope>\n" if scope else "") + "        </dependency>\n")


def pom_xml(m: dict, name: str) -> str:
    SB = "org.springframework.boot"
    deps = [(SB, "spring-boot-starter-web", None)]
    if m["sql"]:
        deps += [(SB, "spring-boot-starter-jdbc", None), ("org.flywaydb", "flyway-core", None)] + SQL_DEPS[m["db"]]
    elif m["db"] == "mongodb":
        deps.append((SB, "spring-boot-starter-data-mongodb", None))
    I = m["integrations"]
    if I["cache"] or I["ws"]:
        deps.append(("redis.clients", "jedis", None))            # version managed by the Spring Boot parent
    if I["ws"]:
        deps.append((SB, "spring-boot-starter-websocket", None))
    if I["uploads"] and m.get("storage") == "firebase-storage":
        deps.append(("com.google.firebase", "firebase-admin", "9.4.1"))
    if m["auth"]:
        deps.append(("org.springframework.security", "spring-security-crypto", None))      # BCrypt only; tokens are plain HS256 JWTs (core/Jwt.java)
    dep = "".join(_dep(*d) for d in deps)
    tst = _dep(SB, "spring-boot-starter-test", None, "test")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>{BOOT}</version>
        <relativePath/>
    </parent>
    <groupId>generated</groupId>
    <artifactId>{name}-api</artifactId>
    <version>1.0.0</version>
    <name>{name}-api</name>
    <description>Generated Spring Boot API</description>
    <properties>
        <java.version>{JAVA}</java.version>
    </properties>
    <dependencies>
{dep}{tst}    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
"""


# ---- SQL migration (Flyway V1__initial.sql), one dialect-specific script from the shared model -----------------------------------------
def _q(db: str, n: str) -> str:
    return f"`{n}`" if db == "mysql" else f"[{n}]" if db == "mssql" else f'"{n}"'


def _type(db: str, f: dict) -> str:
    t = f["type"]
    if t in ("int", "ref"):
        return "INT" if db in ("mysql", "mssql", "postgresql") else "INTEGER"
    if t == "bool":
        return {"postgresql": "BOOLEAN", "mysql": "TINYINT(1)", "mssql": "BIT"}.get(db, "INTEGER")
    if t == "float":
        return {"postgresql": "DOUBLE PRECISION", "mysql": "DOUBLE", "mssql": "FLOAT"}.get(db, "REAL")
    if t == "datetime":
        return {"postgresql": "TIMESTAMP", "mysql": "DATETIME", "mssql": "DATETIME2"}.get(db, "TEXT")
    if t == "text":
        return {"mysql": "MEDIUMTEXT", "mssql": "NVARCHAR(MAX)"}.get(db, "TEXT")
    n = 2048 if t == "url" else 255
    return f"NVARCHAR({n})" if db == "mssql" else f"VARCHAR({n})" if db != "sqlite" else "TEXT"


def migration_sql(m: dict) -> str:
    db = m["db"]
    q = lambda n: _q(db, n)   # noqa: E731
    table_of = {e["name"]: e["table"] for e in m["entities"]}
    pk = {"postgresql": "INT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY", "mysql": "INT AUTO_INCREMENT PRIMARY KEY", "mssql": "INT IDENTITY(1,1) PRIMARY KEY",
          "sqlite": "INTEGER PRIMARY KEY AUTOINCREMENT"}[db]
    out = ["-- Generated from the app spec. Do not edit by hand; regenerate instead (Flyway checksums applied scripts)."]
    for e in m["entities"]:
        t, cols, fks, extra = e["table"], [f"    {q('id')} {pk}"], [], []
        for f in e["fields"]:
            c = f"    {q(f['name'])} {_type(db, f)} {'NOT NULL' if f['required'] else 'NULL'}"
            if f["unique"] and (f["required"] or db != "mssql"):
                c += " UNIQUE"
            cols.append(c)
            if f["unique"] and not f["required"] and db == "mssql":     # SQL Server: UNIQUE allows one NULL only, a filtered index allows many
                extra.append(f"CREATE UNIQUE INDEX {q('uq_' + t + '_' + f['name'])} ON {q(t)} ({q(f['name'])}) WHERE {q(f['name'])} IS NOT NULL;")
            if f["type"] == "ref" and f.get("fk"):
                od = f["onDelete"].replace("RESTRICT", "NO ACTION") if db == "mssql" else f["onDelete"]
                fks.append(f"    CONSTRAINT {q('fk_' + t + '_' + f['name'])} FOREIGN KEY ({q(f['name'])}) REFERENCES {q(table_of[f['ref']])} ({q('id')}) ON DELETE {od}")
            if f.get("index"):
                extra.append(f"CREATE INDEX {q('ix_' + t + '_' + f['name'])} ON {q(t)} ({q(f['name'])});")
        tail = " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4" if db == "mysql" else ""
        out.append(f"CREATE TABLE {q(t)} (\n" + ",\n".join(cols + fks) + f"\n){tail};")
        out += extra
    return "\n".join(out) + "\n"


def env_lines(spec: dict, m: dict) -> list[str]:
    more = {"APP_ENV": ("Runtime mode: development or production", "development"),
            "HOST": ("Interface to listen on (use 0.0.0.0 in containers)", "127.0.0.1")}
    lines = M.env_lines(spec, m, {"SECRET": "<set>", "JWT_SECRET": "<set>", "APP_SECRET": "<set>"},
                        {"seed": "java -jar target/*.jar --seed=admin", "migrate": "start once with AUTO_MIGRATE=true"}, {**more, **M.integ_env(m)})
    # Environment templates contain instructions, never fake long secret values that look usable.
    import re
    for i, line in enumerate(lines):
        if "=" in line and re.match(r"(?i)^[A-Z0-9_]*(?:SECRET|PASSWORD|TOKEN)[A-Z0-9_]*=", line):
            key, value = line.split("=", 1)
            if len(value) >= 12:
                lines[i] = f"{key}=<set>"
    return lines


def readme(m: dict, spec: dict) -> str:
    routes = "\n".join(f"- `{r}`" for r in m["manifest"])
    db = {"sqlite": "SQLite", "postgresql": "PostgreSQL", "mysql": "MySQL", "mssql": "SQL Server", "mongodb": "MongoDB"}.get(m["db"], "no database")
    auth = ("## Sign-in\nPOST `/api/auth/register|login|refresh|logout`, GET `/api/auth/me`. HS256 JWT (`core/Jwt.java`, JDK only), BCrypt (`spring-security-crypto`, no Spring Security filter chain: "
            "access rules live in `EntityService`). Set `JWT_SECRET` (32+ chars).\n\n## Seed (then the process exits)\n```bash\n# ADMIN_EMAIL / ADMIN_PASSWORD in .env\njava -jar target/*.jar --seed=admin\njava -jar target/*.jar --seed=sample   # fake rows, idempotent, refused in production\n```\n"
            if m["auth"] else "## Sign-in\nThis project has no sign-in: only `public` routes work.\n")
    todo = "\n".join(f"- {n}" for n in m["not_generated"]) or "- Nothing from the spec."
    store = ("Spring JDBC (`app/data/SqlRepo.java`, every value a bound parameter) with Flyway migrations (`src/main/resources/db/migration/V1__initial.sql`). "
             "Set `AUTO_MIGRATE=true` (default) to apply them on start." if m["sql"] else
             "Spring Data MongoDB (`app/data/MongoRepo.java`); indexes are created on start from the spec." if m["db"] == "mongodb" else "No database in this project.")
    return f"""# {spec['purpose'][:80]} - API (Spring Boot)

Spring Boot {BOOT} + Java {JAVA}+ and Maven. Generated from the app spec. Core, data + CRUD, JWT sign-in and seed commands are all generated.

## Run
```bash
cd backend
cp .env.example .env     # then edit the values (DATABASE_URL: {db})
mvn spring-boot:run      # http://127.0.0.1:8000/api/health  /api/docs  /api/openapi.json
mvn test
```
Production: `mvn -DskipTests package && java -jar target/*.jar`.

## Data
{store}

## Layout
`app/core` has no Spring dependency (error type, validation, rate limiter, schema records); `app/data` is the storage port and its adapter; `app/service/EntityService.java` holds the
access rules (public / user / owner / admin; other users' records answer 404); `app/web` is the HTTP layer; `schema.json` and `openapi.json` are the generated contracts.

## Behaviour (same contract as the other generated backends)
- List: `{{data, page, limit, total}}`; `?page`, `?limit` (max 100), `?q`, exact filters on ref / enum / bool fields, `?sort=field` or `?sort=-field` (id or any non-text, non-sensitive field; default `-id`).
- Errors: `{{error: {{code, message, details?}}}}`; unique violation 409, foreign-key violation 409, unknown field / bad type 400.

## Routes
{routes}

{auth}
{M.integ_readme(m)}## Not generated yet
{todo}
"""


def _skip(rel: str, m: dict) -> bool:
    """Only the files this project needs: SQL gets JDBC + Flyway, MongoDB gets Spring Data MongoDB, no database gets neither; sign-in files only with auth."""
    name = rel.rsplit("/", 1)[-1]
    I = m["integrations"]
    if rel.startswith(("src/main/java/app/integrations/", "src/test/java/app/")):
        if name in ("Cache.java", "Events.java", "LiveFilter.java", "CacheTest.java"):
            return not (I["cache"] or I["ws"])
        if name in ("UploadController.java", "UploadKinds.java", "UploadKindsTest.java"):
            return not I["uploads"]
        if name in ("ObjectStore.java", "UploadControllerRemote.java", "S3Store.java", "FirebaseStore.java"):
            st = m.get("storage") if I["uploads"] else None
            return name == "UploadControllerRemote.java" or {"ObjectStore.java": st not in ("s3", "firebase-storage"), "S3Store.java": st != "s3", "FirebaseStore.java": st != "firebase-storage"}[name]
        if name in ("WsConfig.java", "WsHandler.java", "WsTokens.java"):
            return not I["ws"]
    if rel.startswith("src/main/java/app/checkout/") or name == "CheckoutMathTest.java":
        return not m.get("checkout")
    if rel.startswith("src/main/java/app/payments/"):
        prov = {"StripePay.java": "stripe", "RazorpayPay.java": "razorpay", "PaypalPay.java": "paypal"}
        return not I["payments"] or (name in prov and prov[name] != m.get("paymentProvider"))
    if name in ("AnonymousAuth.java",) and m["auth"]:
        return True
    if name in ("Jwt.java", "JwtAuth.java", "AuthController.java", "AuthSettings.java", "JwtTest.java", "AuthFlowTest.java") and not m["auth"]:
        return True
    if not m["db"]:
        return rel.startswith(("src/main/java/app/data/", "src/main/java/app/service/", "src/main/java/app/seed/")) or name in ("CrudController.java", "AnonymousAuth.java")
    if m["sql"]:
        return name == "MongoRepo.java"
    return name in ("SqlRepo.java", "DbConfig.java")


def properties(m: dict, base: str) -> str:
    base += f"app.cache={'true' if m['integrations']['cache'] else 'false'}\n"
    if m["sql"]:
        return base + "spring.flyway.enabled=${AUTO_MIGRATE:true}\nspring.flyway.locations=classpath:db/migration\n"
    if m["db"] == "mongodb":
        return base + "spring.data.mongodb.uri=${DATABASE_URL:}\n"
    return base


TEST_SECRET = "test-secret-test-secret-test-secret-0123"


def smoke_test(m: dict, text: str) -> str:
    """The HTTP smoke test must not need a database server: mock the connection pool / Mongo template."""
    if m["auth"]:
        text = text.replace('"app.cors-origins=http://localhost:5173"', f'"app.cors-origins=http://localhost:5173", "JWT_SECRET={TEST_SECRET}", "BCRYPT_ROUNDS=4"', 1)
    if m["sql"]:
        text = text.replace('"app.cors-origins=http://localhost:5173"}', '"app.cors-origins=http://localhost:5173", "spring.flyway.enabled=false"}')
        return text.replace("    @Autowired MockMvc mvc;", "    @Autowired MockMvc mvc;\n    @org.springframework.boot.test.mock.mockito.MockBean javax.sql.DataSource dataSource;")
    if m["db"] == "mongodb":
        return text.replace("    @Autowired MockMvc mvc;", "    @Autowired MockMvc mvc;\n    @org.springframework.boot.test.mock.mockito.MockBean(answer = org.mockito.Answers.RETURNS_DEEP_STUBS)\n    org.springframework.data.mongodb.core.MongoTemplate mongo;")
    return text


def _java(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return f"{v}L"
    return json.dumps(v) if isinstance(v, str) else repr(v)


def repo_test(m: dict) -> str | None:
    """Real SQLite round trip (create, list with sort, delete) through SqlRepo. Only for SQLite: other databases need a server."""
    if m["db"] != "sqlite":
        return None
    e = next((x for x in m["entities"] if not x["internal"] and not x["isUser"] and all(f["type"] != "ref" or not f["required"] for f in x["fields"])), None)
    if not e:
        return None
    puts = "\n".join(f"        data.put({json.dumps(f['name'])}, {_java(M._sample(e, f, 0))});" for f in e["fields"] if f["type"] != "ref" and (f["required"] or f["unique"]))
    return f"""package app;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import app.core.Entity;
import app.core.Schema;
import app.core.Validator;
import app.data.Repo;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(properties = {{"app.env=test", "app.cors-origins=http://localhost:5173", "DATABASE_URL=sqlite:///:memory:", "JWT_SECRET={TEST_SECRET}", "BCRYPT_ROUNDS=4"}})
class SqlRepoTest {{
    @Autowired Repo repo;
    @Autowired Schema schema;
    @Autowired Validator validator;

    @Test void createListSortDelete() {{
        Entity e = schema.entities().get({json.dumps(e['name'])});
        Map<String, Object> data = new LinkedHashMap<>();
{puts}
        Map<String, Object> made = repo.create(e, data);
        assertNotNull(made.get("id"));
        Repo.Page page = repo.list(e, Map.of(), validator.parseList(e, Map.of("sort", List.of("-id"))));
        assertEquals(1, page.total());
        assertTrue(repo.remove(e, made.get("id")));
        assertNull(repo.get(e, made.get("id"), false));
    }}
}}
"""


def auth_test(m: dict) -> str | None:
    """Real SQLite + MockMvc: register, me, login, wrong password, refresh once, role is never client-set. SQLite only (no server needed)."""
    if m["db"] != "sqlite" or not m["auth"]:
        return None
    refresh = m["refresh"]
    rf = """
        String rt = body(r2).get("refreshToken").toString();
        String again = "{\\"refreshToken\\":\\"" + rt + "\\"}";
        mvc.perform(post("/api/auth/refresh").contentType("application/json").content(again)).andExpect(status().isOk());
        mvc.perform(post("/api/auth/refresh").contentType("application/json").content(again)).andExpect(status().isUnauthorized());""" if refresh else ""
    return f"""package app;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

@SpringBootTest(properties = {{"app.env=test", "app.cors-origins=http://localhost:5173", "DATABASE_URL=sqlite:///:memory:", "JWT_SECRET={TEST_SECRET}", "BCRYPT_ROUNDS=4"}})
@AutoConfigureMockMvc
class AuthFlowTest {{
    @Autowired MockMvc mvc;

    @SuppressWarnings("unchecked")
    static Map<String, Object> body(MvcResult r) throws Exception {{ return new ObjectMapper().readValue(r.getResponse().getContentAsString(), Map.class); }}

    @Test void registerLoginMeRefresh() throws Exception {{
        String creds = "{{\\"email\\":\\"A@Example.com\\",\\"name\\":\\"Ann\\",\\"password\\":\\"correct horse\\"}}";
        MvcResult r1 = mvc.perform(post("/api/auth/register").contentType("application/json").content(creds)).andExpect(status().isCreated())
                .andExpect(jsonPath("$.user.email").value("a@example.com")).andExpect(jsonPath("$.user.password_hash").doesNotExist()).andReturn();
        mvc.perform(post("/api/auth/register").contentType("application/json").content(creds)).andExpect(status().isConflict());
        mvc.perform(post("/api/auth/register").contentType("application/json").content("{{\\"email\\":\\"b@example.com\\",\\"name\\":\\"B\\",\\"password\\":\\"correct horse\\",\\"role\\":\\"admin\\"}}"))
                .andExpect(status().isBadRequest()).andExpect(jsonPath("$.error.details.role").exists());
        mvc.perform(post("/api/auth/login").contentType("application/json").content("{{\\"email\\":\\"a@example.com\\",\\"password\\":\\"nope nope nope\\"}}"))
                .andExpect(status().isUnauthorized()).andExpect(jsonPath("$.error.code").value("invalid_credentials"));
        MvcResult r2 = mvc.perform(post("/api/auth/login").contentType("application/json").content("{{\\"email\\":\\"a@example.com\\",\\"password\\":\\"correct horse\\"}}"))
                .andExpect(status().isOk()).andReturn();
        String token = body(r2).get("accessToken").toString();
        mvc.perform(get("/api/auth/me").header("Authorization", "Bearer " + token)).andExpect(status().isOk()).andExpect(jsonPath("$.user.role").value("{m['defaultRole']}"));
        mvc.perform(get("/api/auth/me")).andExpect(status().isUnauthorized());
        mvc.perform(get("/api/auth/me").header("Authorization", "Bearer " + token + "x")).andExpect(status().isUnauthorized()).andExpect(jsonPath("$.error.code").value("invalid_token"));
        assertEquals("Bearer", body(r1).get("tokenType"));{rf}
    }}
}}
"""


def jwt_test() -> str:
    return f"""package app;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;

import app.core.Jwt;
import org.junit.jupiter.api.Test;

class JwtTest {{
    static final String S = "{TEST_SECRET}";

    @Test void roundTripTamperExpiryAndAlg() {{
        String t = Jwt.sign(S, "7", "user", 60, 1000);
        assertEquals("7", Jwt.verify(S, t, 1010).sub());
        assertNull(Jwt.verify(S, t, 1060), "expired");
        assertNull(Jwt.verify("another-secret-another-secret-123456", t, 1010), "wrong key");
        String[] p = t.split("\\\\.");
        assertNull(Jwt.verify(S, p[0] + "." + p[1] + "A." + p[2], 1010), "tampered body");
        String none = java.util.Base64.getUrlEncoder().withoutPadding().encodeToString("{{\\"alg\\":\\"none\\"}}".getBytes());
        assertNull(Jwt.verify(S, none + "." + p[1] + ".", 1010), "alg none");
    }}
}}
"""


def generate(spec: dict, stack: dict, m: dict) -> dict[str, str]:
    files = {}
    for p in sorted(TPL.rglob("*")):
        if p.is_file():
            rel = p.relative_to(TPL).as_posix()
            if not _skip(rel, m):
                files[f"backend/{rel}"] = p.read_text(encoding="utf-8")
    I = m["integrations"]
    if I["ws"] and not m["auth"]:       # no sign-in: every socket is allowed, and the JWT classes are not generated
        files["backend/src/main/java/app/integrations/WsTokens.java"] = ("package app.integrations;\n\nimport org.springframework.stereotype.Component;\n\n"
            "/** This project has no sign-in, so there is no token to check (WsHandler never asks). */\n@Component\npublic class WsTokens {\n    public boolean valid(String token) { return false; }\n}\n")
    if m.get("checkout") and not (I["cache"] or I["ws"]):      # Cache / Events are not generated: Notify has nothing to call
        files["backend/src/main/java/app/checkout/Notify.java"] = ("package app.checkout;\n\nimport org.springframework.stereotype.Component;\n\n"
            "/** This app has no cache and no WebSocket, so a write outside the CRUD routes has nothing to announce. */\n@Component\npublic class Notify {\n    public void changed(String... pairs) { /* nothing to invalidate or announce */ }\n}\n")
    if I["uploads"] and m.get("storage") in ("s3", "firebase-storage"):
        files["backend/src/main/java/app/integrations/UploadController.java"] = (TPL / "src/main/java/app/integrations/UploadControllerRemote.java").read_text(encoding="utf-8")
    if I["uploads"]:
        bl = "backend/src/main/java/app/web/ApiFilters.java"
        files[bl] = files[bl].replace("/*UPLOAD_EXEMPT*/", '&& !"/api/uploads".equals(req.getRequestURI())')    # UploadController enforces UPLOAD_MAX_BYTES itself
    files["backend/src/main/resources/application.properties"] = properties(m, files["backend/src/main/resources/application.properties"])
    files["backend/src/test/java/app/ApiSmokeTest.java"] = smoke_test(m, files["backend/src/test/java/app/ApiSmokeTest.java"])
    if m["sql"]:
        files["backend/src/main/resources/db/migration/V1__initial.sql"] = migration_sql(m)
    t = repo_test(m)
    if t:
        files["backend/src/test/java/app/SqlRepoTest.java"] = t
    if m["auth"]:
        files["backend/src/test/java/app/JwtTest.java"] = jwt_test()
        t2 = auth_test(m)
        if t2:
            files["backend/src/test/java/app/AuthFlowTest.java"] = t2
    files["backend/src/main/resources/openapi.json"] = openapi.dumps(m, spec)
    files["backend/src/main/resources/schema.json"] = schema_json(m)
    files["backend/pom.xml"] = pom_xml(m, M.slug(spec.get("purpose", "app").split(".")[0])[:40])
    files["backend/.env.example"] = "\n".join(env_lines(spec, m)) + "\n"
    files["backend/.gitignore"] = "target/\n.env\n*.db\n.idea/\n.vscode/\n"
    files["backend/README.md"] = readme(m, spec)
    files["backend/.agent-manifest.json"] = json.dumps({"generator": "spring", "parts": sorted(PARTS_DONE), "db": m["db"], "routes": m["manifest"]}, indent=1) + "\n"
    return files


def commands(m: dict) -> dict:
    c = {"run": "cd backend && cp .env.example .env && mvn spring-boot:run", "test": "cd backend && mvn test"}
    if m["auth"]:
        c["seed"] = "cd backend && mvn spring-boot:run -Dspring-boot.run.arguments=--seed=admin"
    return c
