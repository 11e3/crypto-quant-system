# 설정 관리 표준화 완료

## 변경 사항

### 1. 12-Factor App 원칙 준수

설정 관리가 **12-Factor App 원칙**을 따르도록 개선되었습니다:

**우선순위**:
1. 환경 변수 (최우선) - 프로덕션 표준
2. `.env` 파일 - 로컬 개발용 (python-dotenv)
3. `config/settings.yaml` - 선택적 기본값
4. 하드코딩 기본값 - 최종 fallback

### 2. ConfigLoader 개선

**변경 전**:
- YAML 파일 우선
- 환경 변수는 오버라이드로만 사용

**변경 후**:
- 환경 변수 최우선
- `.env` 파일 자동 로드 (python-dotenv)
- YAML 파일은 선택적 기본값만
- 타입 안전한 파싱

### 3. 파일 구조

```
config/
├── settings.yaml.example  # 템플릿 (git에 포함)
└── settings.yaml          # 실제 설정 (git에서 제외)

.env.example               # 환경 변수 템플릿 (git에 포함)
.env                       # 실제 환경 변수 (git에서 제외)
```

### 4. 보안 강화

- ✅ `config/settings.yaml`은 `.gitignore`에 포함
- ✅ `.env` 파일은 `.gitignore`에 포함
- ✅ 템플릿 파일만 git에 포함
- ✅ 민감한 정보는 환경 변수만 사용 권장

## 사용 방법

### 프로덕션 (권장)

```bash
# 환경 변수 직접 설정
export UPBIT_ACCESS_KEY=prod_key
export UPBIT_SECRET_KEY=prod_secret
```

### 로컬 개발

```bash
# .env 파일 사용
cp .env.example .env
# .env 편집
```

또는

```bash
# YAML 파일 사용 (선택적)
cp config/settings.yaml.example config/settings.yaml
# settings.yaml 편집 (기본값만)
```

## 주요 개선 사항

1. ✅ **환경 변수 우선순위**: 12-Factor App 준수
2. ✅ **python-dotenv 통합**: `.env` 파일 표준 지원
3. ✅ **타입 안전 파싱**: 환경 변수 자동 타입 변환
4. ✅ **에러 메시지 개선**: 필수 설정 누락 시 명확한 안내
5. ✅ **문서화**: 설정 가이드 문서 작성

## 테스트 결과

- ✅ 모든 테스트 통과 (52개)
- ✅ 코드 커버리지: 27%
- ✅ 린터 오류 없음

## 참고

- [설정 관리 가이드](guides/configuration.md)
- [시작 가이드](guides/getting_started.md)
