# GitHub 포트폴리오 공개 체크리스트

## ✅ 완료된 작업

- [x] LICENSE 파일 생성 (MIT)
- [x] CONTRIBUTING.md 생성
- [x] SECURITY.md 생성
- [x] 포트폴리오용 README 작성 (README_PORTFOLIO.md)
- [x] .gitignore 최종 확인 및 개선
- [x] 포트폴리오 공개 계획 문서 작성

## 🔄 진행 중인 작업

- [ ] README.md를 포트폴리오 버전으로 교체
- [ ] .env.example 파일 생성 (globalignore로 차단됨 - 수동 생성 필요)
- [ ] config/settings.yaml.example 생성
- [ ] Git 히스토리에서 민감 정보 확인

## 📋 남은 작업

### 1. 보안 최종 확인 (30분)

```bash
# Git 히스토리에서 API 키 검색
git log --all --full-history --source -S "ACCESS_KEY" -- "*.py"
git log --all --full-history --source -S "SECRET_KEY" -- "*.py"
git log --all --full-history --source -S "your-access-key" -- "*.py"

# 민감 정보가 발견되면 BFG Repo-Cleaner 사용
# https://rtyley.github.io/bfg-repo-cleaner/
```

### 2. 파일 생성 (15분)

```bash
# .env.example 수동 생성 (프로젝트 루트에)
# deploy/.env.example을 참고하여 생성

# config/settings.yaml.example 생성
# config/settings.yaml의 템플릿 버전 생성
```

### 3. README 교체 (5분)

```bash
# README_PORTFOLIO.md를 README.md로 교체
mv README.md README_OLD.md
mv README_PORTFOLIO.md README.md
```

### 4. 최종 검증 (30분)

- [ ] 모든 링크 작동 확인
- [ ] 코드 예시가 올바른지 확인
- [ ] 이미지/스크린샷 경로 확인 (추가 시)
- [ ] 문서 일관성 확인

### 5. GitHub 설정 (10분)

- [ ] Repository description 작성
- [ ] Topics 추가:
  - `python`
  - `trading-bot`
  - `quantitative-finance`
  - `backtesting`
  - `cryptocurrency`
  - `upbit`
  - `volatility-breakout`
  - `docker`
  - `pydantic`
  - `pytest`
- [ ] Repository를 Public으로 설정

## 🎯 공개 전 최종 체크

### 보안
- [ ] 모든 API 키 제거 확인
- [ ] .env 파일이 .gitignore에 있는지 확인
- [ ] config/settings.yaml이 .gitignore에 있는지 확인
- [ ] Git 히스토리 스캔 완료

### 문서
- [ ] README가 명확하고 매력적인지 확인
- [ ] LICENSE 파일 존재 확인
- [ ] CONTRIBUTING.md 존재 확인
- [ ] SECURITY.md 존재 확인
- [ ] 모든 링크 작동 확인

### 코드
- [ ] 모든 테스트 통과
- [ ] Linter 오류 없음
- [ ] Type checker 오류 없음
- [ ] 불필요한 파일 제거 (egg-info, __pycache__ 등)

### 프로젝트
- [ ] 프로젝트 설명이 명확한지 확인
- [ ] 기술 스택 명시
- [ ] 성과/결과 강조
- [ ] 사용 예시 제공

## 📝 공개 후 작업

### 즉시
- [ ] GitHub Pages 설정 (선택)
- [ ] 첫 번째 Release 생성
- [ ] Issues 템플릿 활성화
- [ ] Pull Request 템플릿 활성화

### 1주일 내
- [ ] 프로젝트 소개 블로그 포스트 (선택)
- [ ] 소셜 미디어 공유 (선택)
- [ ] 피드백 수집 및 개선

## 🚀 빠른 실행 명령어

```bash
# 1. 보안 검증
git log --all --full-history --source -S "ACCESS_KEY" -- "*.py"

# 2. 테스트 실행
make test

# 3. 코드 품질 확인
make check

# 4. README 교체
mv README.md README_OLD.md && mv README_PORTFOLIO.md README.md

# 5. 최종 커밋
git add .
git commit -m "docs: prepare for portfolio publication"
git push origin main
```

## 📊 예상 소요 시간

- **보안 검증**: 30분
- **파일 생성**: 15분
- **README 교체**: 5분
- **최종 검증**: 30분
- **GitHub 설정**: 10분

**총 예상 시간**: 약 1.5시간
