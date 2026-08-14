# 재부상 층(층위 2) — 제안된 검출기가 자기 사례에서 실패한다 (실측, 2026-08-14)

> 이 문서는 `2026-08-14-drift-detection-gap-prompt.md` 의 **후보 B 에 대한 반증 실측**이다.
> 설계 결과가 아니라 설계 입력이며, B 를 구현하려던 세션이 착수 직전에 멈춘 이유를 담는다.
> **B 를 그대로 구현하지 마라. 아래 두 실측이 그 메커니즘을 기각한다.**

## 제안된 것 (원문)

형제 문서 §후보 B:

> wiki 산문의 "미결"·"TODO"·"별도 세션 대상" 패턴을 `lint_wiki` 의 8번째 종류로 추가하고,
> **30일 이상 방치 시** BRIEF 의 "다음 세션" 에 싣는다.
> 이게 층위 2 의 직접 해법이고 **비용 대비 효과가 가장 크다**.

진단은 옳다. **메커니즘이 틀렸다.** 둘 다 이 제안의 동기가 된 바로 그 파일에서 깨진다.

## 기각 1 — mtime 은 방치 기간의 신호가 아니다

동기 사례는 `.omp/wiki/paper-work-split.md` 의 2026-05-31 자 "미결" 이 3개월 방치된 것이다.
그 파일의 mtime 을 사건 당일 재면:

```
paper-work-split.md    mtime 0.0d   마커 6건
```

**0.0 일이다.** 같은 날 다른 세션이 그 파일에 새 절을 덧붙였기 때문이다. 파일 단위 mtime 은
"이 파일이 최근 편집됐나" 를 답하지 파일 *안의 한 항목*이 얼마나 묵었는지는 답하지 못한다.
살아 있는 wiki 페이지일수록 mtime 은 계속 갱신되고, 그 안의 낡은 미결은 계속 숨는다.
**30일 게이트를 걸면 동기 사례 자체가 안 잡힌다.**

기존 `stale` kind 가 mtime 을 쓰는 건 맞다 — 그건 "페이지 전체가 방치됐나" 라는 다른 질문이라
유효하다. 항목 단위에 같은 신호를 재사용할 수 없다.

## 기각 2 — 산문 마커는 해소 상태를 못 가진다 (오탐 3/7)

`.omp/wiki/*.md` 4개에 `미결|별도 세션|TODO|미실행|보류` 를 걸면 7줄이 걸린다. 구조 위치까지
붙여 전수 분류하면:

| 파일:줄 | 위치 | 내용 | 판정 |
|:---|:---|:---|:---|
| paper-work-split:20 | 제목 | `### 미결 (omp-organize 별도 세션 대상)` | 진짜 — 동기 사례 |
| paper-work-split:22 | 산문 | "init 범위 밖이라 **미실행**. 이동 대상 후보:" | 진짜 (위 항목의 본문) |
| paper-work-split:51 | 제목 | `## 2026-08-14 — 이주 2차 실행, 1차 미결 전부 해소` | **오탐 — 해소 선언인데 걸린다** |
| paper-work-split:46 | 항목 | ``RL-ALBC - TODO.md:242`` dead link | **오탐 — 파일명이다** |
| paper-work-split:82 | 항목 | ``RL-ALBC - TODO.md:242`` dead link | **오탐 — 같은 파일명** |
| paper-work-split:207 | 항목 | "1·2차의 마지막 미해결 **해소**" | 경계 — 해소 선언 |
| schedule-system:120 | 항목 | `- **보류: krit/Kanban.md** — 병렬 세션이 재편 중` | 진짜 |

**오탐 3건 / 7건.** 게다가 20행(열림)과 51행(해소)이 같은 파일에 공존한다 — 산문에는 열림·닫힘을
잇는 기계 판독 가능한 연결이 없어서, 검출기가 "이건 이미 해소됐다" 를 알 방법이 원리적으로 없다.
제목·항목 위치로 제한해도 51행과 46/82행이 그대로 남는다(위 표의 위치 열이 그 시험이다).

형제 문서 자신의 회귀 관문이 이걸 기각한다: *"규칙이 현행 관행을 위반이라 부르면 그 규칙은
쓰이지 않고 꺼진다."* 7건 중 3건이 오탐인 검사는 첫 주에 꺼진다.

## 그래서 무엇이 남나 — 결정은 사람 몫

진단(층위 2 가 병목)은 유지된다. 바뀌는 건 **상태를 어디에 두느냐**다.

omp 에서 이미 작동하는 유일한 재부상 장치는 `ready_to_promote` 인데, 그게 되는 이유는 산문을
읽어서가 아니라 `learned.md` OBS 블록이 **명시적 `status:` 필드**를 갖기 때문이다. 산문 미결에는
그 필드가 없다. 그래서 선택지는 검출기 튜닝이 아니라 **규약을 줄 것인가**다:

1. **체크박스 규약** — wiki 미결을 `- [ ] …` 로 쓴다. 열림·닫힘이 한 글자로 표현되고,
   `hooks/omp_secretary.py` 가 이미 마크다운 체크박스를 파싱한다(`secretary.sources[]` 의
   `todo` kind). `lint_wiki` 는 미체크만 세면 되고 오탐이 0 이다. 비용: 기존 산문 미결의 수동 전환.
2. **frontmatter 상태** — wiki 페이지에 `open_items:` 목록. 더 무겁고, wiki 는 의도적으로
   schema-less 라는 0.6.0 의 결정(CHANGELOG)과 충돌한다.
3. **안 만든다** — 미결을 `learned.md` 에 OBS 로 쓰게 하고 wiki 는 산문으로 둔다. 그러면
   `stuck_candidate`/`ready_to_promote` 가 이미 재부상을 담당한다. 비용: OBS 는 *규칙 후보*
   전용이라 "이 폴더 옮기기" 같은 일회성 액션과 의미가 안 맞는다.

**1번이 유력하나 규약 변경이라 사람 결정이다.** 형제 문서의 "결정하지 말고 검토할 것" 과 같은
취급을 받아야 한다.

## 이 문서가 확정한 것 / 안 한 것

- 확정: mtime 게이트 기각(실측), 산문 마커 검출 기각(오탐 3/7 전수).
- 미확정: 대체 규약 1·2·3 중 무엇인가 — 사람 결정.
- 착수 안 함: `lint_wiki` 8번째 kind, BRIEF 열거 확장(`skills/omp-brief/SKILL.md:74` 가 현재
  `ready_to_promote`/`stuck_candidate`/`contradiction` 3종만 싣는다 — kind 를 늘리면 여기도 같이
  늘려야 한다).

## 재현

```bash
cd <프로젝트>
python3 - <<'EOF'
import re, pathlib, time
for p in sorted(pathlib.Path('.omp/wiki').glob('*.md')):
    age = (time.time() - p.stat().st_mtime)/86400
    for i, line in enumerate(p.read_text().splitlines(), 1):
        if re.search(r'미결|별도 세션|TODO|미실행|보류', line):
            pos = 'HEAD' if line.lstrip().startswith('#') else ('ITEM' if line.lstrip().startswith(('-','*')) else 'PROSE')
            print(f"{p.name}:{i} [{pos}] mtime={age:.1f}d  {line.strip()[:90]}")
EOF
```
