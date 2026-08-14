"""Ambient kill-switch 격리 — 스위트가 명시하지 않은 환경변수는 훅에 닿지 않는다.

훅들은 셸 환경에서 두 개의 앰비언트 킬스위치를 읽는다: `OMP_ROUTE_GATE`
(off/observe/on, `omp_route_emit._gate_mode`) 와 `OMP_SKIP_HOOKS` (4훅 공통).
테스트는 훅을 subprocess 로 띄우면서 `env=None` 이거나 `dict(os.environ, ...)` 로
env 를 만들기 때문에, 개발자 셸이 이 둘 중 하나를 export 하고 있으면 그 값이 그대로
서브프로세스로 흘러들어간다.

실측(2026-08-14): claudebase 가 `config/settings.json` 에 `OMP_ROUTE_GATE=on` 을 넣고
있는 머신에서 `python3 -m pytest -q` 가 8건 실패했다 — 게이트와 무관한 테스트들이
억제 경로(`main()` 의 `if not relevant: return 0`)를 타서 stdout 이 빈 문자열이 되고,
`context_of("")` 가 `""` 를 돌려주며 "STAGE(project) → 가 없다" 로 터진다. 코드 결함이
아니라 환경 누수인데 실패 메시지는 그걸 말해주지 않는다. `OMP_ROUTE_GATE=off` 를 앞에
붙이면 206 passed 로 바뀌는 것이 그 진단이었다.

그래서 세션 시작 시 한 번 벗겨낸다. 게이트를 *일부러* 시험하는 테스트들은 영향받지
않는다 — 그쪽은 `_env(OMP_ROUTE_GATE="on")` 처럼 값을 명시적으로 넣어서 만든다.
"""
import os

for _ambient in ("OMP_ROUTE_GATE", "OMP_SKIP_HOOKS"):
    os.environ.pop(_ambient, None)
