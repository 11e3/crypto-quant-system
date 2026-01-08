# Type Checking Status

## Current Status

프로젝트는 Python 타입 힌트를 점진적으로 적용하고 있습니다.

### Type Checking Configuration

- **Tool**: mypy
- **Config**: `mypy.ini`
- **Policy**: Gradual typing (실용적 접근)

### Quick Start

```bash
# 핵심 모듈만 체크
mypy src/monitoring src/backtester/trade_cost_calculator.py scripts/real_time_monitor.py

# 전체 프로젝트 체크 (경고 많음)
mypy . --config-file mypy.ini
```

### Current Type Coverage

#### ✅ Well-Typed Modules
- `src/monitoring/` - 모니터링 시스템
- `scripts/real_time_monitor.py` - 실시간 모니터링
- `scripts/setup_task_scheduler.py` - Task Scheduler 설정

#### ⚠️ Partially Typed
- `src/backtester/` - 일부 Optional 타입 이슈
- `src/strategies/` - 일부 Generic 타입 미지정

#### ❌ Untyped (Legacy)
- `examples/` - 예제 코드
- `legacy/` - 레거시 코드
- `scripts/tools/` - 유틸리티 스크립트

### Known Issues

1. **Optional Type Parameters**
   - 일부 함수에서 `None` 기본값과 타입 불일치
   - 해결: `| None` 명시 또는 mypy.ini에서 `no_implicit_optional = False`

2. **Generic Types**
   - `dict`, `list`, `tuple` 등에 타입 파라미터 누락
   - 점진적으로 `dict[str, float]` 형태로 수정 중

3. **External Libraries**
   - pandas, numpy 등은 stub 패키지 설치 필요
   - 현재는 `ignore_missing_imports = True`로 우회

### Roadmap

- [ ] Phase 1: 핵심 모듈 타입 완성도 향상 (src/monitoring, src/backtester)
- [ ] Phase 2: 전략 모듈 타입 추가 (src/strategies)
- [ ] Phase 3: 스크립트 타입 정리 (scripts/)
- [ ] Phase 4: 예제 코드 타입 추가 (examples/)

### Development Guidelines

**새 코드 작성 시:**
- 함수 시그니처에 타입 힌트 추가
- Generic 타입은 타입 파라미터 명시 (`dict[str, float]`)
- Optional 타입은 `| None` 명시

**기존 코드 수정 시:**
- 타입 에러 발견 시 점진적으로 수정
- 대규모 리팩토링은 피하고 작은 단위로 개선
- 레거시 코드는 무리하게 타입 추가 않음

### CI/CD Integration

현재 CI/CD 파이프라인에서는 mypy 체크를 optional로 설정:

```yaml
# .github/workflows/ci.yml
- name: Type check (optional)
  run: mypy src/monitoring src/backtester/trade_cost_calculator.py
  continue-on-error: true
```

프로젝트 성숙도가 높아지면 strict 모드로 전환 예정.
