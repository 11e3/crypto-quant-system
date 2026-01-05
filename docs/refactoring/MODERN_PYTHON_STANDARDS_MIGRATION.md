# Modern Python Development Standards Migration Plan

## 개요

이 문서는 `upbit-quant-system` 프로젝트를 Modern Python Development Standards에 맞춰 리팩토링하는 계획을 설명합니다.

## 현재 상태 분석

### ✅ 이미 준수 중인 항목

1. **Directory Structure**: `src/` 레이아웃 준수
2. **pyproject.toml**: 단일 소스로 프로젝트 메타데이터 관리
3. **Ruff**: 린터로 사용 중
4. **Mypy**: 타입 체크 설정 완료
5. **pytest**: 테스트 프레임워크 사용 중
6. **pre-commit**: 기본 설정 완료

### ❌ 개선 필요 항목

1. **uv 사용**: 아직 pip 기반 의존성 관리
2. **Ruff 포맷터**: Black을 포맷터로 사용 중, Ruff로 전환 필요
3. **Makefile**: pip 기반 명령어, uv 기반으로 업데이트 필요
4. **의존성 잠금**: `uv.lock` 파일 없음

---

## Phase 1: uv 마이그레이션

### 1.1 uv 설치 및 초기화

**목표**: pip 대신 uv를 사용하여 Python 버전, 가상환경, 의존성 관리

**작업 내용**:

1. **uv 설치 확인/설치**
   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Linux/macOS
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **프로젝트 초기화**
   ```bash
   # uv로 프로젝트 동기화 (의존성 설치 및 uv.lock 생성)
   uv sync
   ```

3. **가상환경 관리**
   ```bash
   # uv는 자동으로 가상환경을 관리
   # .venv 디렉토리가 자동 생성됨
   ```

**예상 결과**:
- `uv.lock` 파일 생성
- `.venv/` 디렉토리 생성 (uv 관리)
- 의존성이 uv를 통해 관리됨

**검증**:
```bash
# uv.lock 파일 확인
ls uv.lock

# 가상환경 활성화 (uv는 자동으로 관리)
uv run python --version
```

---

## Phase 2: Ruff 포맷터 전환

### 2.1 Black 제거 및 Ruff 포맷터 활성화

**목표**: Black을 제거하고 Ruff를 린터 + 포맷터로 통합 사용

**작업 내용**:

1. **pyproject.toml 업데이트**
   - `[tool.black]` 섹션 제거
   - `[tool.ruff]`에 포맷터 설정 추가
   - `dev` 의존성에서 `black` 제거

2. **Ruff 포맷터 설정 추가**
   ```toml
   [tool.ruff.format]
   quote-style = "double"
   indent-style = "space"
   skip-magic-trailing-comma = false
   line-ending = "auto"
   ```

3. **pre-commit 설정 업데이트**
   - Black hook 제거
   - Ruff hook에 `--format` 옵션 추가

4. **Makefile 업데이트**
   - `format` 타겟을 `ruff format`으로 변경
   - `format-check` 타겟 업데이트

**예상 결과**:
- Black 의존성 제거
- Ruff가 린터 + 포맷터로 통합 사용
- 코드 포맷팅이 Ruff로 통일됨

**검증**:
```bash
# 포맷팅 테스트
uv run ruff format --check src/ tests/

# 포맷팅 적용
uv run ruff format src/ tests/
```

---

## Phase 3: Makefile 업데이트

### 3.1 uv 기반 명령어로 전환

**목표**: 모든 Makefile 타겟을 uv 기반으로 업데이트

**작업 내용**:

1. **의존성 설치 타겟**
   ```makefile
   install:
       uv sync
   
   install-dev:
       uv sync --extra dev
   ```

2. **개발 도구 타겟**
   ```makefile
   lint:
       uv run ruff check src/ tests/
   
   format:
       uv run ruff format src/ tests/
   
   format-check:
       uv run ruff format --check src/ tests/
   
   type-check:
       uv run mypy src/
   
   test:
       uv run pytest
   ```

3. **통합 타겟 추가**
   ```makefile
   check: lint format-check type-check test
       @echo "All checks passed!"
   
   fix: format
       uv run ruff check --fix src/ tests/
   ```

**예상 결과**:
- 모든 명령어가 uv를 통해 실행
- 가상환경 관리가 자동화됨
- 일관된 개발 워크플로우

---

## Phase 4: pyproject.toml 최적화

### 4.1 설정 통합 및 최적화

**목표**: 모든 도구 설정을 pyproject.toml에 통합

**작업 내용**:

1. **Ruff 설정 강화**
   ```toml
   [tool.ruff]
   line-length = 100
   target-version = "py310"
   
   [tool.ruff.lint]
   select = [
       "E",   # pycodestyle errors
       "W",   # pycodestyle warnings
       "F",   # pyflakes
       "I",   # isort
       "B",   # flake8-bugbear
       "C4",  # flake8-comprehensions
       "UP",  # pyupgrade
       "N",   # pep8-naming
       "SIM", # flake8-simplify
   ]
   ignore = [
       "E501",  # line too long (handled by formatter)
       "B008",  # do not perform function calls in argument defaults
   ]
   
   [tool.ruff.format]
   quote-style = "double"
   indent-style = "space"
   ```

2. **Mypy 설정 강화**
   ```toml
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
   show_error_codes = true
   ```

3. **Pytest 설정 최적화**
   ```toml
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
   ```

**예상 결과**:
- 모든 도구 설정이 pyproject.toml에 통합
- 일관된 코드 스타일 및 품질 기준

---

## Phase 5: pre-commit 설정 업데이트

### 5.1 Ruff 포맷터 통합

**목표**: pre-commit hooks에서 Ruff 포맷터 사용

**작업 내용**:

1. **.pre-commit-config.yaml 업데이트**
   ```yaml
   repos:
     - repo: https://github.com/astral-sh/ruff-pre-commit
       rev: v0.1.0  # 최신 버전 사용
       hooks:
         - id: ruff
           args: [--fix, --exit-non-zero-on-fix]
         - id: ruff-format
   
     - repo: https://github.com/pre-commit/mirrors-mypy
       rev: v1.7.0  # 최신 버전 사용
       hooks:
         - id: mypy
           additional_dependencies: [types-requests, types-PyYAML]
           args: [--ignore-missing-imports]
   
     - repo: https://github.com/pre-commit/pre-commit-hooks
       rev: v4.5.0  # 최신 버전 사용
       hooks:
         - id: trailing-whitespace
         - id: end-of-file-fixer
         - id: check-yaml
         - id: check-added-large-files
         - id: check-json
         - id: check-toml
   ```

2. **Black hook 제거**
   - Black 관련 설정 완전 제거

**예상 결과**:
- pre-commit에서 Ruff 포맷터 자동 실행
- Black 의존성 완전 제거

---

## Phase 6: 문서 업데이트

### 6.1 README 및 개발 가이드 업데이트

**목표**: 모든 문서를 새로운 워크플로우에 맞게 업데이트

**작업 내용**:

1. **README.md 업데이트**
   - 설치 방법을 uv 기반으로 변경
   - 개발 워크플로우 업데이트

2. **개발 가이드 업데이트**
   - uv 사용법 추가
   - Ruff 포맷터 사용법 추가
   - Makefile 명령어 업데이트

**예상 결과**:
- 문서가 최신 워크플로우를 반영
- 새로운 개발자가 쉽게 시작 가능

---

## 구현 순서

### 우선순위 1 (필수)
1. ✅ Phase 1: uv 마이그레이션
2. ✅ Phase 2: Ruff 포맷터 전환
3. ✅ Phase 3: Makefile 업데이트

### 우선순위 2 (권장)
4. ✅ Phase 4: pyproject.toml 최적화
5. ✅ Phase 5: pre-commit 설정 업데이트

### 우선순위 3 (문서)
6. ✅ Phase 6: 문서 업데이트

---

## 마이그레이션 체크리스트

### Phase 1: uv 마이그레이션
- [ ] uv 설치 확인
- [ ] `uv sync` 실행하여 uv.lock 생성
- [ ] 기존 .venv 제거 (선택사항)
- [ ] `uv run` 명령어 테스트

### Phase 2: Ruff 포맷터 전환
- [ ] pyproject.toml에서 `[tool.black]` 제거
- [ ] `[tool.ruff.format]` 설정 추가
- [ ] dev 의존성에서 `black` 제거
- [ ] 코드 포맷팅 테스트 (`ruff format`)

### Phase 3: Makefile 업데이트
- [ ] 모든 타겟을 `uv run` 기반으로 변경
- [ ] `check` 타겟 추가
- [ ] `fix` 타겟 추가
- [ ] 각 타겟 테스트

### Phase 4: pyproject.toml 최적화
- [ ] Ruff 설정 강화
- [ ] Mypy 설정 강화
- [ ] Pytest 설정 검토

### Phase 5: pre-commit 설정 업데이트
- [ ] Black hook 제거
- [ ] Ruff 포맷터 hook 추가
- [ ] `pre-commit run --all-files` 테스트

### Phase 6: 문서 업데이트
- [ ] README.md 설치 방법 업데이트
- [ ] 개발 가이드 업데이트
- [ ] CONTRIBUTING.md 생성 (선택사항)

---

## 예상 소요 시간

- **Phase 1**: 30분
- **Phase 2**: 1시간 (코드 포맷팅 변경사항 검토 포함)
- **Phase 3**: 30분
- **Phase 4**: 1시간
- **Phase 5**: 30분
- **Phase 6**: 1시간

**총 예상 시간**: 약 4-5시간

---

## 주의사항

1. **코드 포맷팅 변경**: Black → Ruff 포맷터 전환 시 일부 포맷팅 스타일이 달라질 수 있음
   - 전체 코드베이스에 `ruff format` 적용 필요
   - 변경사항을 별도 커밋으로 분리 권장

2. **의존성 버전**: uv.lock 파일이 생성되면 의존성 버전이 고정됨
   - `uv lock` 명령어로 업데이트 가능

3. **CI/CD**: CI/CD 파이프라인도 uv 기반으로 업데이트 필요

4. **팀 협업**: 모든 팀원이 uv를 설치하고 사용해야 함

---

## 참고 자료

- [uv 공식 문서](https://github.com/astral-sh/uv)
- [Ruff 포맷터 문서](https://docs.astral.sh/ruff/formatter/)
- [Modern Python Packaging 가이드](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)

---

## 롤백 계획

만약 문제가 발생할 경우:

1. **uv 롤백**: `uv.lock` 파일 삭제 후 기존 pip 워크플로우로 복귀
2. **Ruff 포맷터 롤백**: Black 설정 복원 및 Ruff 포맷터 비활성화
3. **Makefile 롤백**: Git 히스토리에서 이전 버전 복원

모든 변경사항은 Git으로 관리되므로 언제든지 롤백 가능합니다.
