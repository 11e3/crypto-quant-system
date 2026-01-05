# 전략 실험 결과 (Strategy Experiments)

이 디렉토리는 전략 실험 노트북(`02_strategy_experiments.ipynb`)에서 생성된 실험 결과를 저장합니다.

## 파일 구조

- `experiment_XXX_Name.json`: 개별 실험 결과 (JSON 형식)
  - 실험 ID, 타임스탬프
  - 전략 파라미터
  - 백테스트 결과 메트릭
  - 비고 및 인사이트

- `experiment_comparison.csv`: 모든 실험 결과 비교 테이블
- `experiment_comparison.png`: 실험 결과 비교 시각화
- `metrics_correlation.png`: 메트릭 간 상관관계 히트맵
- `best_strategy_report_*.png`: 최적 전략 상세 리포트

## 실험 결과 분석

각 실험 JSON 파일에는 다음 정보가 포함됩니다:

```json
{
  "id": 1,
  "name": "Exp1_Default",
  "timestamp": "2025-01-05T...",
  "strategy_params": {
    "sma_period": 4,
    "trend_sma_period": 8,
    ...
  },
  "config_params": {
    "initial_capital": 1.0,
    "fee_rate": 0.0005,
    ...
  },
  "results": {
    "cagr": 65.14,
    "mdd": 24.85,
    "sharpe_ratio": 1.66,
    ...
  },
  "notes": "Parameter experiment: Default"
}
```

## 사용 방법

1. `notebooks/02_strategy_experiments.ipynb` 노트북을 실행
2. 실험 결과가 자동으로 이 디렉토리에 저장됨
3. `experiment_comparison.csv`를 열어 모든 실험 결과 비교
4. 시각화 이미지로 성능 메트릭 비교

## 실험 추적

각 실험은 고유한 ID와 타임스탬프를 가지므로, 시간에 따른 실험 진행 상황을 추적할 수 있습니다.
