# Phase 0: 프로젝트 구조 현대화 체크리스트

## 진행 상황 추적

### 0.1 pyproject.toml 기반 프로젝트 구조

- [x] `pyproject.toml` 생성 (PEP 621)
- [x] 프로젝트 메타데이터 정의
- [x] 의존성 관리 (requirements.txt → pyproject.toml)
- [x] 빌드 시스템 설정 (setuptools)
- [ ] 패키지 구조 정의 확인
- [ ] `setup.py` 제거 (없으면 스킵)

### 0.2 개발 도구 통합

- [x] Black 설정 (코드 포맷팅)
- [x] MyPy 설정 (타입 체크)
- [x] Ruff 설정 (린팅, import 정렬)
- [x] Pytest 설정 (테스트 프레임워크)
- [x] Coverage 설정 (커버리지 측정)
- [x] Pre-commit hooks 설정

### 0.3 패키지 구조 개선

- [x] `__version__.py` 추가
- [ ] `__init__.py`에서 주요 API export 확인
- [ ] 패키지명 결정 (현재: src 구조 유지)

### 0.4 설치 및 테스트

- [ ] 개발 모드 설치 테스트: `pip install -e .`
- [ ] 개발 의존성 포함 설치: `pip install -e ".[dev]"`
- [ ] Black 실행 테스트
- [ ] MyPy 실행 테스트
- [ ] Ruff 실행 테스트
- [ ] Pytest 실행 테스트

## 다음 단계

Phase 0 완료 후:
1. Phase 1: 인터페이스 정의 및 추상화 시작
2. 또는 Phase 0의 추가 개선사항 적용
