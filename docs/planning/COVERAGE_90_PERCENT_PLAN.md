# 90% 테스트 커버리지 달성 계획

## 현재 상태 (2026-01-05 업데이트)
- **현재 커버리지**: 87.20%
- **목표 커버리지**: 90%
- **필요한 커버리지 증가**: 2.80%
- **예상 누락 라인 수**: 약 80 lines

### 최근 완료 (2026-01-05)
- ✅ `backtester/report.py`: 100% 달성
- ✅ `config/settings.py`: 100% 달성
- ✅ `utils/logger.py`: 100% 달성
- ✅ `backtester/engine.py`: 84.48% → 99.64%

## 우선순위별 작업 계획

### Phase 1: 빠른 효과 (예상 +2.0~2.5%)

#### 1.1 CLI 모듈 완성
- `cli/commands/backtest.py`: 현재 32.00% (34 lines missing)
- `cli/commands/run_bot.py`: 현재 40.91% (13 lines missing)
- **예상 개선**: +1.5~2.0%
- **작업량**: 낮음 (간단한 CLI 테스트)

#### 1.2 Config 모듈 마무리
- `config/loader.py`: 현재 64.65% (35 lines missing)
- **예상 개선**: +0.5~1.0%
- **작업량**: 중간

### Phase 2: 중간 효과 (예상 +1.5~2.0%)

#### 2.1 Backtester 모듈 개선
- `backtester/engine.py`: 현재 76.90% (64 lines missing)
- `backtester/report.py`: 현재 78.38% (48 lines missing)
- **예상 개선**: +1.5~2.0%
- **작업량**: 중간-높음

### Phase 3: 장기 효과 (예상 +1.0~1.5%)

#### 3.1 Execution 모듈 개선
- `execution/bot.py`: 현재 52.97% (103 lines missing)
- `execution/bot_facade.py`: 현재 16.74% (194 lines missing)
- **예상 개선**: +1.0~1.5%
- **작업량**: 높음 (WebSocket 의존, 통합 테스트 권장)

## 권장 진행 순서

### 즉시 시작 (Phase 1)
1. **CLI 모듈 테스트 작성** (2-3시간)
   - `cli/commands/backtest.py` 테스트
   - `cli/commands/run_bot.py` 테스트
   - 예상: +1.5~2.0%

2. **Config 모듈 테스트 보완** (1-2시간)
   - `config/loader.py` 남은 경로 테스트
   - 예상: +0.5~1.0%

**Phase 1 합계 예상**: +2.0~3.0% → **87.27~88.27%**

### 다음 단계 (Phase 2)
3. **Backtester 모듈 개선** (3-4시간)
   - `engine.py` 남은 경로 테스트
   - `report.py` 남은 경로 테스트
   - 예상: +1.5~2.0%

**Phase 2 합계 예상**: +1.5~2.0% → **88.77~90.27%** ✅ **90% 달성!**

## 작업 상세

### CLI 모듈 테스트 (`cli/commands/backtest.py`)

**누락된 경로**:
- 에러 처리 경로
- 다양한 옵션 조합
- 출력 파일 생성

**테스트 케이스**:
```python
def test_backtest_with_custom_options():
    """Test backtest with various option combinations"""
    
def test_backtest_error_handling():
    """Test error handling for invalid inputs"""
    
def test_backtest_output_generation():
    """Test report generation"""
```

### Config 모듈 (`config/loader.py`)

**누락된 경로**:
- YAML 파일 로딩 에러 처리
- 환경 변수 파싱 에러
- 복잡한 설정 경로

### Backtester 모듈

**engine.py 누락 경로**:
- 캐시 히트 경로
- 예외 처리 경로
- 엣지 케이스 (빈 데이터, 단일 데이터 포인트)

**report.py 누락 경로**:
- 리포트 생성 에러 처리
- 시각화 에러 처리
- 다양한 데이터 형태 처리

## 예상 작업 시간

- **Phase 1**: 3-5시간 → 87~88%
- **Phase 2**: 3-4시간 → 90%+ ✅

**총 예상 시간**: 6-9시간

## 체크리스트

- [ ] CLI 모듈 테스트 작성
- [ ] Config 모듈 테스트 보완
- [ ] Backtester 모듈 테스트 개선
- [ ] 커버리지 리포트 확인
- [ ] 90% 달성 확인
- [ ] README 업데이트 (실제 커버리지 반영)

## 참고

- 현재 커버리지: `uv run pytest --cov=src --cov-report=term-missing`
- HTML 리포트: `uv run pytest --cov=src --cov-report=html`
- 목표: `pyproject.toml`의 `fail_under = 90` 설정
