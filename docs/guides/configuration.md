# 설정 관리 가이드

## 구현 방식 (12-Factor App 준수)

프로젝트는 **12-Factor App 원칙**을 따릅니다:
- **환경 변수** (최우선): 프로덕션 및 민감한 정보
- **.env 파일**: 로컬 개발용 (python-dotenv)
- **YAML 파일** (`config/settings.yaml`): 선택적 기본값
- **하드코딩 기본값**: 최종 fallback

## 설정 우선순위

1. **환경 변수** (최우선) - 시스템/셸에서 설정
2. **.env 파일** - 프로젝트 루트의 `.env` 파일
3. **YAML 파일** (`config/settings.yaml`) - 선택적 기본값
4. **하드코딩 기본값** - 코드 내 기본값

## 표준적인 설정 관리 방법

### 1. 12-Factor App 방식 (권장)

**원칙**: 설정은 환경 변수로 관리

```bash
# .env 파일 (로컬 개발용)
UPBIT_ACCESS_KEY=your_key
UPBIT_SECRET_KEY=your_secret
TELEGRAM_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# 프로덕션은 환경 변수 직접 설정
export UPBIT_ACCESS_KEY=prod_key
export UPBIT_SECRET_KEY=prod_secret
```

**장점**:
- ✅ 환경별 설정 분리 용이
- ✅ 민감 정보 노출 방지
- ✅ 컨테이너/클라우드 배포에 적합
- ✅ 12-Factor App 원칙 준수

### 2. python-dotenv 사용 (구현 완료)

프로젝트는 `python-dotenv`를 사용하여 `.env` 파일을 자동으로 로드합니다:

```python
# src/config/loader.py
try:
    from dotenv import load_dotenv
    
    # .env 파일 자동 로드
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv is optional, but recommended
    logger.warning("python-dotenv not installed. Install it for .env file support")
```

**구현 상태**:
- ✅ `python-dotenv` 의존성 추가됨 (`pyproject.toml`)
- ✅ `.env` 파일 자동 로드 구현
- ✅ 환경 변수 우선순위 유지
- ✅ `.env.example` 템플릿 제공

**장점**:
- ✅ `.env` 파일 자동 로드
- ✅ 환경별 `.env` 파일 관리 용이
- ✅ 표준 라이브러리 사용
- ✅ 선택적 의존성 (없어도 동작)

### 3. 현재 구현 방식

#### 구현 완료 사항
- ✅ 12-Factor App 원칙 준수 (환경 변수 우선)
- ✅ `.env` 파일 지원 (python-dotenv)
- ✅ YAML 파일 선택적 기본값 제공
- ✅ 타입 안전한 설정 접근 메서드
- ✅ 설정 파일 템플릿 제공 (`settings.yaml.example`, `.env.example`)
- ✅ 보안 강화 (실제 설정 파일은 `.gitignore`에 포함)
- ✅ 에러 메시지 개선 (필수 설정 누락 시 명확한 안내)

#### 설정 우선순위
1. **환경 변수** (최우선) - 시스템/셸에서 설정
2. **.env 파일** - 프로젝트 루트의 `.env` 파일
3. **YAML 파일** - `config/settings.yaml` (선택적 기본값)
4. **하드코딩 기본값** - 코드 내 기본값

## 향후 개선 가능 사항

### Option 1: Pydantic Settings (고급, 선택사항)

타입 검증과 설정 스키마 정의를 더 강화하려면 Pydantic Settings를 고려할 수 있습니다:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    upbit_access_key: str
    upbit_secret_key: str
    trading_tickers: list[str]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

**장점**:
- ✅ 타입 검증 자동
- ✅ 설정 스키마 정의
- ✅ 환경 변수 자동 매핑

**단점**:
- ⚠️ 추가 의존성 (`pydantic-settings`)
- ⚠️ 현재 구현으로도 충분히 동작함

### Option 2: 환경별 설정 파일 (선택사항)

개발/프로덕션 환경별로 다른 설정 파일을 사용하려면:

- `config/settings.dev.yaml`
- `config/settings.prod.yaml`
- 환경 변수로 선택: `CONFIG_ENV=dev`

**현재 권장 방식**:
- 환경 변수와 `.env` 파일로 환경별 설정 분리 (더 간단하고 표준적)

## 현재 방식 사용법

### 로컬 개발

```bash
# 1. settings.yaml.example 복사
cp config/settings.yaml.example config/settings.yaml

# 2. 환경 변수 설정 (선택)
export UPBIT_ACCESS_KEY=your_key
export UPBIT_SECRET_KEY=your_secret
```

### 프로덕션

```bash
# 환경 변수만 사용 (권장)
export UPBIT_ACCESS_KEY=prod_key
export UPBIT_SECRET_KEY=prod_secret
export TELEGRAM_TOKEN=prod_token
export TELEGRAM_CHAT_ID=prod_chat_id

# 또는 Docker/Kubernetes secrets 사용
```

## 결론

프로젝트는 **12-Factor App 원칙**을 준수하는 표준적인 설정 관리 방식을 구현했습니다:

1. ✅ **환경 변수 우선순위**: 프로덕션 표준 방식
2. ✅ **python-dotenv 통합**: `.env` 파일 자동 로드
3. ✅ **설정 템플릿 제공**: `settings.yaml.example`, `.env.example` 제공
4. ✅ **민감 정보 보호**: 실제 설정 파일은 `.gitignore`에 포함
5. ✅ **타입 안전 파싱**: 환경 변수 자동 타입 변환
6. ✅ **에러 메시지 개선**: 필수 설정 누락 시 명확한 안내

이 방식은 **표준적이고 안전하며 유연한** 설정 관리입니다.
