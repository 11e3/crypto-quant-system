# pyproject.toml 마이그레이션 가이드

## 개요

이 문서는 `requirements.txt` 기반 프로젝트를 `pyproject.toml` 기반 최신 Python 프로젝트 구조로 전환하는 상세 가이드를 제공합니다.

## PEP 표준 준수

- **PEP 518**: 빌드 시스템 요구사항
- **PEP 621**: 프로젝트 메타데이터 표준
- **PEP 517**: 빌드 백엔드 표준

## pyproject.toml 구조

### 기본 구조 예시

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "upbit-quant-system"
version = "0.1.0"
description = "Automated trading system for Upbit using volatility breakout strategy"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["trading", "cryptocurrency", "upbit", "quantitative", "backtesting"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Financial and Insurance Industry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Office/Business :: Financial :: Investment",
]

dependencies = [
    "pyupbit>=0.2.34",
    "requests>=2.31.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "matplotlib>=3.7.0",
    "seaborn>=0.12.0",
    "pyarrow>=12.0.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.7.0",
    "mypy>=1.5.0",
    "ruff>=0.0.287",
    "pre-commit>=3.4.0",
]
test = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
]
docs = [
    "sphinx>=7.1.0",
    "sphinx-rtd-theme>=1.3.0",
]

[project.scripts]
upbit-quant = "src.cli.main:main"
upbit-backtest = "src.cli.commands.backtest:main"
upbit-collect = "src.cli.commands.collect:main"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

# 개발 도구 설정
[tool.black]
line-length = 100
target-version = ['py310', 'py311', 'py312']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
disallow_incomplete_defs = false
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
strict_optional = true

[[tool.mypy.overrides]]
module = [
    "pyupbit.*",
    "pyarrow.*",
]
ignore_missing_imports = true

[tool.ruff]
line-length = 100
target-version = "py310"
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = [
    "E501",  # line too long (handled by black)
    "B008",  # do not perform function calls in argument defaults
]

[tool.ruff.per-file-ignores]
"__init__.py" = ["F401"]  # unused imports allowed in __init__.py

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow running tests",
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__init__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
```

## 마이그레이션 단계

### 1단계: pyproject.toml 생성

```bash
# 프로젝트 루트에 pyproject.toml 생성
touch pyproject.toml
```

### 2단계: 기본 메타데이터 작성

프로젝트 정보, 버전, 설명 등을 작성합니다.

### 3단계: 의존성 마이그레이션

`requirements.txt`의 의존성을 `pyproject.toml`의 `[project]` 섹션으로 이동:

```toml
dependencies = [
    "pyupbit>=0.2.34",
    "requests>=2.31.0",
    # ... 기타 의존성
]
```

### 4단계: 개발 의존성 분리

개발/테스트/문서화 도구를 `[project.optional-dependencies]`로 분리:

```toml
[project.optional-dependencies]
dev = ["pytest", "black", "mypy", "ruff"]
test = ["pytest", "pytest-cov"]
docs = ["sphinx"]
```

### 5단계: 개발 도구 설정

각 도구의 설정을 `[tool.*]` 섹션에 추가합니다.

### 6단계: 패키지 구조 확인

`src/` 레이아웃이 올바른지 확인하고 `[tool.setuptools]` 설정합니다.

### 7단계: 설치 테스트

```bash
# 개발 모드 설치
pip install -e .

# 개발 의존성 포함 설치
pip install -e ".[dev]"

# 특정 그룹만 설치
pip install -e ".[test]"
```

### 8단계: requirements.txt 제거 (선택사항)

`pyproject.toml`로 완전히 전환 후 `requirements.txt`는 제거하거나,
하위 호환성을 위해 최소한의 내용만 유지할 수 있습니다:

```txt
# This file is kept for backward compatibility.
# Use: pip install -e .
-e .
```

## 빌드 시스템 선택

### 옵션 1: setuptools (권장 - 안정적)

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"
```

**장점:**
- 가장 널리 사용됨
- 안정적이고 검증됨
- 대부분의 도구와 호환

### 옵션 2: hatchling (최신, 빠름)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**장점:**
- 빠른 빌드
- 간단한 설정
- PEP 621 완전 지원

### 옵션 3: Poetry (의존성 관리 강화)

```toml
[tool.poetry]
name = "upbit-quant-system"
version = "0.1.0"
# ...

[tool.poetry.dependencies]
python = "^3.10"
# ...

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**장점:**
- 강력한 의존성 해결
- lock 파일 지원
- 통합된 도구

## 버전 관리 전략

### __version__.py 사용

```python
# src/__version__.py
__version__ = "0.1.0"
```

```toml
# pyproject.toml
[project]
dynamic = ["version"]

[tool.setuptools.dynamic]
version = {attr = "upbit_quant.__version__.__version__"}
```

또는 단일 소스로 관리:

```toml
[project]
version = "0.1.0"
```

## CLI 진입점 정의

```toml
[project.scripts]
upbit-quant = "src.cli.main:main"
upbit-backtest = "src.cli.commands.backtest:main"
upbit-collect = "src.cli.commands.collect:main"
```

설치 후 명령어로 사용 가능:
```bash
upbit-quant --help
upbit-backtest --config config.yaml
```

## 개발 워크플로우

### 설치

```bash
# 프로젝트 클론
git clone <repo>
cd upbit-quant-system

# 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 개발 모드 설치 (의존성 포함)
pip install -e ".[dev]"
```

### 개발 도구 사용

```bash
# 코드 포맷팅
black src/ tests/

# 타입 체크
mypy src/

# 린팅
ruff check src/

# 테스트 실행
pytest

# 커버리지 포함 테스트
pytest --cov=src --cov-report=html
```

### Pre-commit Hooks (선택사항)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.287
    hooks:
      - id: ruff
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
```

설치:
```bash
pip install pre-commit
pre-commit install
```

## 마이그레이션 체크리스트

- [ ] `pyproject.toml` 생성
- [ ] 프로젝트 메타데이터 작성
- [ ] 의존성 마이그레이션 (requirements.txt → pyproject.toml)
- [ ] 개발 의존성 분리
- [ ] 빌드 시스템 설정
- [ ] 개발 도구 설정 (black, mypy, ruff, pytest)
- [ ] 패키지 구조 확인
- [ ] 설치 테스트 (`pip install -e .`)
- [ ] CLI 진입점 테스트
- [ ] 기존 스크립트 동작 확인
- [ ] 문서 업데이트
- [ ] CI/CD 파이프라인 업데이트 (있는 경우)

## 문제 해결

### 패키지를 찾을 수 없음

```bash
# src 레이아웃 확인
[tool.setuptools.packages.find]
where = ["src"]
```

### 의존성 충돌

```bash
# 의존성 트리 확인
pipdeptree

# 충돌 해결
pip install --upgrade <package>
```

### 타입 체크 오류

```toml
# 외부 라이브러리는 타입 체크 제외
[[tool.mypy.overrides]]
module = ["pyupbit.*"]
ignore_missing_imports = true
```

## 참고 자료

- [PEP 621 - Project metadata](https://peps.python.org/pep-0621/)
- [PEP 518 - Specifying Build System](https://peps.python.org/pep-0518/)
- [setuptools 문서](https://setuptools.pypa.io/)
- [hatchling 문서](https://hatch.pypa.io/)
- [Poetry 문서](https://python-poetry.org/)
