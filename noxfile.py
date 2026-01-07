import nox


@nox.session(python="3.14", reuse_venv=True)
def lint(session):
    # 1. 개발 의존성 설치
    session.install(".[dev]")
    # 2. 린팅 및 타입 검사 실행
    session.run("ruff", "check", ".", "--fix", "--unsafe-fixes")
    # Incremental 캐시로 인한 mypy 크래시 회피
    session.run("mypy", "src", "tests")


@nox.session(python=["3.14"], reuse_venv=True)
def tests(session):
    # 1. 패키지 및 테스트 의존성 설치
    session.install(".[test]")
    # 2. 테스트 실행
    session.run("pytest")
