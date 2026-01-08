# MyPy Type Checking Guide

## Quick Start

프로젝트의 타입 체크를 실행하려면 다음 명령어를 사용하세요:

```powershell
# 권장: 명시적 경로 지정 (examples, legacy, tests 제외)
mypy src scripts\real_time_monitor.py scripts\setup_task_scheduler.py scripts\convert_csv_to_parquet.py scripts\generate_sample_data.py scripts\performance_profiling.py
```

또는 가상 환경에서:

```powershell
.\.venv\Scripts\mypy.exe src scripts\real_time_monitor.py scripts\setup_task_scheduler.py scripts\convert_csv_to_parquet.py scripts\generate_sample_data.py scripts\performance_profiling.py
```

## ⚠️ 주의사항

**다음 명령어를 사용하지 마세요:**

```powershell
# ❌ 잘못된 방법 - 모든 파일(examples, legacy, tests 포함)을 검사함
mypy .

# ❌ 잘못된 방법 - pyproject.toml의 files 설정이 무시됨
mypy . --config-file pyproject.toml
```

## 이유

- **mypy의 동작 방식**: `mypy .` 명령은 현재 디렉토리의 모든 Python 파일을 재귀적으로 검사합니다.
- **pyproject.toml의 files 설정**: `mypy .`를 실행하면 명령행 인자가 우선순위를 가져서 `pyproject.toml`의 `files` 설정이 무시됩니다.
- **exclude 패턴 문제**: TOML 형식의 `exclude` 패턴은 정규식이 아닌 glob 패턴을 사용해야 하지만, mypy는 일관성 없는 동작을 보입니다.

## 설정 파일

프로젝트는 `pyproject.toml`에 mypy 설정이 있습니다:

```toml
[tool.mypy]
python_version = "3.14"
files = [
    "src/",
    "scripts/real_time_monitor.py",
    ...
]
```

이 설정은 **명시적 경로 없이 mypy를 실행할 때만** 적용됩니다:

```powershell
# 이 명령은 pyproject.toml의 files 설정을 사용합니다
mypy

# 하지만 이 명령은 files 설정을 무시합니다
mypy .  # ❌
```

## PowerShell Alias (선택사항)

편의를 위해 PowerShell 프로필에 alias를 추가할 수 있습니다:

```powershell
# $PROFILE 파일 편집
notepad $PROFILE

# 다음 내용 추가:
function Run-MyPy {
    mypy src scripts\real_time_monitor.py scripts\setup_task_scheduler.py scripts\convert_csv_to_parquet.py scripts\generate_sample_data.py scripts\performance_profiling.py
}
Set-Alias -Name check-types -Value Run-MyPy
```

그러면 간단히 실행할 수 있습니다:

```powershell
check-types
```

## CI/CD 설정

GitHub Actions나 다른 CI 도구에서는 명시적 경로를 사용하세요:

```yaml
- name: Type check with mypy
  run: |
    mypy src scripts/real_time_monitor.py scripts/setup_task_scheduler.py ...
```

## 문제 해결

### 캐시 문제

mypy 캐시 때문에 문제가 발생하면:

```powershell
# 캐시 삭제
Remove-Item -Path .mypy_cache -Recurse -Force

# incremental 모드 비활성화
mypy --no-incremental src scripts\...
```

### 인코딩 문제

`.mypy.ini` 파일은 cp949 인코딩 문제가 있을 수 있으므로 `pyproject.toml`을 사용하세요.

## 현재 상태

✅ **시스템 Python**: 에러 없음
✅ **.venv 환경**: 에러 없음 (올바른 명령 사용 시)

```powershell
# 모두 성공해야 함:
mypy src scripts\real_time_monitor.py scripts\setup_task_scheduler.py scripts\convert_csv_to_parquet.py scripts\generate_sample_data.py scripts\performance_profiling.py
Success: no issues found in XX source files
```
