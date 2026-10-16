"""Phase 4 part 3 (Spring Boot, part A: core). Pure Python plus, when a JDK is installed, a real javac + java run of the Spring-free classes.
Maven, Spring Boot and the generated JUnit suite are not run here (no network): run `mvn test` in a generated project."""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from backend.gen import spring_gen as S
from backend.gen import stage
from backend.stack import catalog as C
from gen_helpers import BRIEF, DBS, STORE, build

JAVA = shutil.which("java")
TPL = S.TPL / "src" / "main" / "java" / "app"


def sbuild(db, brief=BRIEF, **kw):
    return build(db, brief, backend="spring", **kw)


def test_spring_is_registered_and_ready_for_every_supported_stack():
    assert "spring" in stage.GENERATORS
    assert S.PARTS_DONE == {"core", "data", "security"}
    spec, st, m, files = sbuild("sqlite")
    assert stage.coverage(st)["ready"], stage.coverage(st)


@pytest.mark.parametrize("db", DBS + ["none"])
def test_files_per_database(db):
    spec, st, m, files = sbuild(db)
    for rel in ("pom.xml", ".env.example", ".gitignore", "README.md", "src/main/resources/schema.json", "src/main/resources/application.properties",
                "src/main/java/app/Application.java", "src/main/java/app/core/Validator.java", "src/main/java/app/web/ApiFilters.java",
                "src/test/java/app/ApiSmokeTest.java", "src/test/java/app/ValidatorTest.java"):
        assert f"backend/{rel}" in files, rel
    pom = files["backend/pom.xml"]
    assert "spring-boot-starter-web" in pom and "spring-boot-starter-parent" in pom and S.BOOT in pom
    for banned in ("jpa", "jjwt", "spring-boot-starter-security"):       # BCrypt only (spring-security-crypto); no Spring Security filter chain
        assert banned not in pom
    env = files["backend/.env.example"]
    assert "CORS_ORIGINS" in env and "<" in env or "CORS_ORIGINS" in env
    assert not re.search(r"(password|secret)=\S{12,}", env, re.I)
    assert "JWT sign-in" in files["backend/README.md"] and "not generated yet" in files["backend/README.md"].lower()


def test_schema_json_matches_the_spec_and_the_java_records():
    spec, st, m, files = sbuild("postgresql", STORE)
    sj = json.loads(files["backend/src/main/resources/schema.json"])
    assert sj["db"] == "postgresql" and sj["auth"] is True and set(sj["entities"]) == {e["name"] for e in m["entities"]}
    comp = lambda name: set(re.findall(r"(?:String|boolean|List<\w+>|Map<[^>]+>) (\w+)[,)]", (TPL / "core" / f"{name}.java").read_text().split("{", 1)[0]))
    ent, fld = comp("Entity"), comp("Field")
    for e in sj["entities"].values():
        assert set(e) <= ent, set(e) - ent
        for f in e["fields"]:
            assert set(f) <= fld, set(f) - fld


def test_generation_is_deterministic():
    a = sbuild("sqlite")[3]
    assert a == sbuild("sqlite")[3]


def test_error_envelope_and_security_defaults_are_present():
    h = (TPL / "web" / "ErrorHandler.java").read_text()
    for code in ("invalid_json", "not_found", "method_not_allowed", "internal_error", "unsupported_media_type"):
        assert code in h
    f = (TPL / "web" / "ApiFilters.java").read_text()
    for x in ("payload_too_large", "rate_limited", "X-Frame-Options", "Strict-Transport-Security", "Access-Control-Allow-Origin"):
        assert x in f
    assert "printStackTrace" not in h and "getStackTrace" not in h


@pytest.mark.skipif(not JAVA, reason="no JDK")
def test_core_classes_compile_and_pass_the_java_checks():
    probe = subprocess.run([JAVA, "--list-modules"], capture_output=True, text=True).stdout
    if "jdk.compiler" not in probe:
        pytest.skip("JDK without the compiler module")
    out = Path(tempfile.mkdtemp())
    srcs = [str(TPL / "core" / n) for n in ("ApiException", "Field", "Entity", "Schema", "SortSpec", "ListQuery", "Json", "Jwt", "RateLimiter", "ClientIp", "Validator")]
    srcs = [s + ".java" for s in srcs] + [str(Path(__file__).parent / "java" / "CoreCheck.java")]
    c = subprocess.run([JAVA, "-m", "jdk.compiler/com.sun.tools.javac.Main", "-Xlint:all", "-Werror", "-d", str(out)] + srcs, capture_output=True, text=True)
    assert c.returncode == 0, c.stderr
    r = subprocess.run([JAVA, "-cp", str(out), "CoreCheck"], capture_output=True, text=True)
    assert r.returncode == 0 and r.stdout.strip() == "OK", r.stdout
