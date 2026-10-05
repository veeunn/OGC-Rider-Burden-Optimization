# 11. One-page Results Summary for Discussion

## 연구 질문

비용 최소화 중심의 음식배달 배차가 라이더 간 부담 불균형을 만들 수 있는지, 그리고 동일한 라이더 수를 유지한 상태에서 배차를 재구성하면 어느 정도의 추가 비용으로 부담 형평성을 개선할 수 있는지를 확인함.

## 분석 설계

- OGC Stage 1의 **16개 primary instance** 사용
- BIKE rider만 분석하여 운송수단 이질성 통제
- 모든 형평성 시나리오에서 S0의 active rider 수 **R0를 고정**
- S1 = Order Count
- S2 = Active Route Duration
- S3 = Waiting Time
- 각 scenario는 cost와 Gini를 동시에 최소화하는 NSGA-II로 분석
- population 80, generations 100, seeds 0–4
- 핵심 비교점은 5개 seed를 pooled한 Pareto frontier의 knee solution

## 핵심 결과

| Burden definition | Mean equity improvement | Mean Price of Fairness |
|---|---:|---:|
| S1 Order Count | **12.45%** | **1.19%** |
| S2 Route Duration | **27.58%** | **2.62%** |
| S3 Waiting Time | **26.70%** | **3.28%** |

가장 중요한 결과는 **같은 수의 라이더를 유지해도 배차 구조를 바꾸는 것만으로 burden inequality를 줄일 수 있었다는 점**임. 특히 Route Duration과 Waiting Time은 평균적으로 약 27% 수준의 형평성 개선이 가능했고, pooled knee에서의 평균 추가 비용은 약 2.6–3.3% 수준이었음.

Order Count는 평균 형평성 개선 폭이 12.45%로 상대적으로 작았으나, 평균 Price of Fairness 역시 1.19%로 가장 낮았음. 따라서 “주문 건수를 비슷하게 나누는 것”과 “실제 시간 부담을 비슷하게 만드는 것”은 동일하지 않으며, burden을 어떤 차원으로 정의하는지가 결과에 직접적인 영향을 미침.

## 눈에 띄는 instance

**STAGE1_10-S1**에서는 pooled-knee 기준 Order Count 불평등이 **62.46% 개선**되었고, 이에 필요한 PoF는 **9.54%**였음. S0 baseline 보정 이후에도 효과가 크게 유지되어 단순 baseline 오류가 아닌 instance 자체의 구조적 특성으로 판단됨.

반대로 **STAGE1_5-S1**에서는 pooled-knee 개선이 사실상 0%였음. 따라서 본 최적화가 모든 instance에서 자동으로 형평성을 개선하는 구조는 아니며, 실제 feasible assignment structure에 따라 trade-off의 크기가 달라짐.

## S0 검증 및 해석상 주의

16개 중 12개 S0는 MILP solver에서 최적성이 확인됨. STAGE1_5, 10, 11, 18은 time limit 내 feasible incumbent를 확보한 경우이므로 논문에서는 전부를 “cost-optimal S0”라고 표현하지 않고, 해당 instance는 **best-known feasible baseline**으로 구분함.

QA 과정에서 STAGE1_5, 10, 18의 기존 S0보다 더 저렴한 feasible solution이 발견되어 baseline을 보정했으며, 이후 PoF와 Pareto frontier, knee를 다시 계산함. 최종 frozen 결과에서는 음수 PoF가 남아 있지 않음.

## 현재 해석

이 결과는 “형평성을 고려하면 비용이 크게 희생된다”기보다, **비교적 작은 추가 비용으로 상당한 burden redistribution이 가능할 수 있다**는 방향을 보여줌. 또한 형평성 목표를 단일 composite burden으로 합치기보다 Order Count, Route Duration, Waiting Time을 별도로 분석해야 한다는 설계 선택을 지지함.

## 현재 상태

- 240/240 seed-level scenario result 확보
- QA critical checks PASS
- 16-instance 숫자 freeze 완료
- 이후 표, 그림, Results 문장은 `05_results/frozen_stage1_16/`만 source of truth로 사용
