# Preset — `research-lab`

> **omp preset card** — 프로젝트 타입 `research-lab` 의 범용 시드 규칙.
> `omp-init` / `rule-architect` 가 이 카드를 **실제 폴더 귀납 스캔과 합성**해서
> 초안 `rules.json` 을 만든다. 카드는 범용·portable (모든 사용자에게 배포), 합성 결과는 프로젝트별 발산.

| 필드 | 값 |
|:---|:---|
| `preset_origin` | `research-lab` |
| 적합 대상 | 학술·연구실 프로젝트 — 실험 반복, dataset, 결과·그림 산출, 논문 작성 동반 |
| 매칭 신호 (귀납 스캔이 이 중 2+ 발견 시 후보) | `experiments/`·`exp*/`·날짜/번호 디렉토리, `data/` + `results/` + `figures/` 공존, `paper/`·`.tex`·`.bib`, `*.ipynb` + `seed`·`config` 패턴, `references/`·`.bib` |
| 초기 `specificity` | `0` (순수 프리셋 — init 직후. learn 승격마다 상승) |
| `structure.convention` | `research-lab` |

---

## 1. Canonical directory layout (디렉토리 역할)

연구실 프로젝트의 표준 골격. 각 dir 의 `role` 은 `rules.json` 의 `structure.directories[].role` 로 그대로 들어간다.
`enforced: true` 면 `omp-audit` 가 그 dir 의 역할을 위반하는 파일을 flag 한다.

```
<project>/
├── experiments/    # 실험 단위 — 날짜 또는 번호로 1실험 1디렉토리 (재현 단위)
│   └── exp-2026-05-30_baseline/
│       ├── config.yaml      # 이 실험의 하이퍼파라미터·seed (재현 키)
│       ├── run.log
│       └── checkpoints/
├── data/           # 입력 데이터 — 절대 in-place 수정 금지, 원본은 raw 격리
│   ├── raw/        # 외부에서 받은 불변 원본 (read-only 취급, 절대 가공·덮어쓰기 X)
│   ├── interim/    # 중간 가공물 (선택)
│   └── processed/  # 학습/분석에 바로 쓰는 정제 데이터 (스크립트로 재생성 가능해야 함)
├── results/        # 실험 산출 수치·메트릭·표 (.csv/.json/.parquet) — 실험 ID로 추적
├── figures/        # 논문·발표용 그림 (.pdf/.png/.svg) — results 에서 파생, 재생성 가능
├── paper/          # 논문 원고 (oms 의 .tex/.bib 가 여기 살 수 있음) — omp 는 구조만, 내용은 oms
├── references/     # 외부 문헌·인용 자료 (.bib, 받은 PDF) — 읽기 자료, 산출물 아님
├── src/            # (선택) 공유 라이브러리 코드 — experiments 가 import
├── scripts/        # (선택) 일회성·재현 스크립트 (clean.py, make_figures.py 등 lineage 의 `by`)
├── notebooks/      # (선택) 탐색용 .ipynb — 정식 결과는 results/ 로 승격
└── README.md
```

**역할 경계 (audit 가 쓰는 핵심 분리):**
- `data/raw/` 는 **불변** — 어떤 스크립트도 여기에 쓰지 않는다. 가공물은 `data/processed/`.
- `results/` (수치) ≠ `figures/` (시각화). figure 는 result 의 파생 — 재생성 가능해야 한다.
- `paper/` 내부는 omp 가 **내용을 건드리지 않음** — 논문은 oms 도메인. omp 는 `paper/` 가 제자리에 있고 `references/.bib` 와 일관된지만 본다.
- `experiments/<id>/` 는 **재현 단위** — config + 산출 로그가 한 디렉토리에 모인다. 결과(`results/`)·그림(`figures/`)은 실험 ID 로 역추적 가능해야 한다.

**합성 규칙 (omp-init 에게):** 위 dir 중 **스캔에서 실제로 발견된 것만** `rules.json.structure.directories` 에 넣는다. 프리셋에 있다고 없는 dir 을 만들지 말 것 — 카드는 *역할 어휘 사전* 이지 강제 생성 목록이 아니다. 발견된 dir 의 이름이 다르면(예: `exp/` vs `experiments/`, `outputs/` vs `results/`) **실제 이름을 path 로 쓰고 role 만 이 카드에서 가져온다**.

---

## 2. Naming conventions (명명 규칙 + 예시)

`rules.json.naming.patterns[]` 로 들어가는 후보. regex 는 Python `re` 구문, basename 에 매칭. 초기 `severity` 는 보수적으로 `warn` (특화 전 false-positive 억제).

| `applies_to` (glob) | 규칙 | 예시 (good) | 예시 (bad) | regex 시드 | severity |
|:---|:---|:---|:---|:---|:---|
| `experiments/*` | 실험 디렉토리 = 날짜 또는 번호 + 짧은 슬러그 | `exp-2026-05-30_baseline`, `exp-007_ablation` | `final`, `test2`, `김승민_실험` | `^exp[-_](\d{4}-\d{2}-\d{2}|\d{3,})[-_].+$` | `warn` |
| `experiments/*/config.*` | 각 실험에 재현용 config 1개 | `config.yaml` | (config 없는 실험 디렉토리) | `^config\.(ya?ml|json|toml)$` | `warn` |
| `data/raw/*` | 원본은 출처·날짜 식별 가능하게 | `census_2026-01.csv` | `data.csv`, `final_v2.csv` | (프로젝트별 — 시드는 비강제, learn 이 채움) | `info` |
| `data/processed/*` | 정제 데이터는 split·버전 식별 | `train-v2.parquet`, `val.parquet` | `output.pkl`, `temp.parquet` | `^[a-z0-9-]+(-(v\d+))?\.(parquet|csv|npz|pkl)$` | `warn` |
| `results/*` | 결과는 실험 ID 로 추적 | `exp-007_metrics.json`, `2026-05-30_eval.csv` | `results.csv`, `new.json` | `^(exp[-_][\w-]+|\d{4}-\d{2}-\d{2})[_-].+\.(csv|json|parquet|tsv)$` | `warn` |
| `figures/*` | 그림은 논문 figure 번호 또는 설명적 이름 | `fig3_loss_curve.pdf`, `arch_diagram.svg` | `Untitled.png`, `image (1).png` | `^[\w-]+\.(pdf|png|svg|eps)$` | `info` |

**날짜·ID 컨벤션:**
- 날짜 = `YYYY-MM-DD` (ISO, lexicographic 정렬 = 시간 정렬). `MM-DD-YY` 같은 모호 포맷 금지.
- 실험 번호 = zero-pad (`exp-007`, not `exp-7`) — 정렬·tab-completion 안정.
- 두 스타일(날짜 vs 번호)은 보통 **한 프로젝트 안에서 하나로 통일** — 스캔이 둘 다 발견하면 omp-init 은 다수파를 채택하고 소수파를 `omp-organize` 위반 후보로 남긴다.

**합성 규칙:** 위 regex 는 **시드**다. omp-init 은 실제 basename 들을 보고 (a) 시드가 다수 파일과 맞으면 그대로 채택, (b) 안 맞으면 실측 패턴으로 regex 를 좁힌다(귀납). 어떤 패턴도 init 단계에서 `error` 로 올리지 말 것 — `error` 승격은 learn 게이트(사람 승인)의 몫.

---

## 3. Dataset conventions (manifest 시드 — research-lab 특이사항)

연구실 프로젝트는 dataset 추적이 1급 관심사다. `omp-dataset` / `dataset-curator` 가 `manifest.json` 을 쓸 때 이 프리셋이 주는 기대값:

- **추적 대상 default 경로**: `data/raw/`, `data/processed/`, `results/*.{parquet,csv,npz}`. (figure·log 는 manifest 비대상 — 재생성 가능 산출물)
- **split 추적이 핵심**: `data/processed/` 안의 `train`/`val`/`test` 파일은 같은 `split.group` 으로 묶어 **leakage 감지**(같은 행이 train·test 양쪽에 있나)를 가능케 한다. research-lab 에서 가장 흔한 사고가 split 누수.
- **lineage 필수 권장**: `data/processed/*` 와 `results/*` 는 `lineage.derived_from`(원본 경로/dataset id) + `lineage.by`(`scripts/clean.py` 등) 를 채운다. "이 결과 어느 데이터·어느 코드에서 나왔나" 가 재현성의 핵심.
- **`source` 어휘**: 외부 dataset 은 `kaggle:<slug>`, `vendor-X`, 내부 수집은 `internal`.
- **DVC/git-lfs 존중**: `.dvc/` 또는 `.gitattributes` 의 lfs 필터 감지 시 `manifest.managed_by_external.tool` 을 채우고 **메타데이터만 미러**. omp 는 실제 데이터를 절대 복사·이동·push 하지 않는다 (메타데이터-only 철학).
- **대용량**: hash 비용이 큰 파일은 `sha256: "UNHASHED"` 허용(size+mtime 으로 변경 감지). iCloud/exFAT 이동 함정 회피 — 데이터를 옮기지 않는다.

---

## 4. omp-init mapping (스캔 → 이 프리셋 합성)

`omp-init` 이 폴더를 이 프리셋에 얹는 절차. **rule-architect 는 프리셋을 강제하지 않고 실측에 양보한다.**

1. **타입 판정**: project-scanner 의 귀납 결과(트리·확장자·명명)에서 §0 매칭 신호 2+ 발견 → `research-lab` 후보. 신호가 약하거나 다른 프리셋(python-ml 등)과 경합하면 사람에게 후보 2개를 제시.
2. **dir 매핑**: 스캔이 찾은 실제 dir → 이 카드의 역할 어휘에 매핑. 이름이 다르면 **실제 이름 유지 + 역할만 채택**(`outputs/`→role="결과 수치", `exp/`→role="실험 단위"). 카드에 있으나 스캔에 없는 dir 은 `rules.json` 에 **넣지 않는다**.
3. **naming 귀납**: §2 시드 regex 를 실측 basename 다수파에 맞춰 검증·축소. 맞으면 채택, 안 맞으면 실측에서 패턴 재추출. init 단계 severity 는 `warn`/`info` 만.
4. **dataset 시드**: `data/`·`results/` 존재 시 `omp-dataset` 호출을 STRUCTURE.md 에 권유 메모로 남긴다(자동 등록 X — 등록은 사람 확인 게이트). DVC 감지 결과도 기록.
5. **specificity = 0** 으로 초안 작성 + `project.preset_origin = "research-lab"`. 사람 게이트(초안 rules.json 승인) 통과 후 `.omp/rules.json` 확정.
6. **STRUCTURE.md / NAMING.md** 사람용 문서에 이 카드의 역할 경계(§1)·날짜 컨벤션(§2)을 산문으로 옮긴다 — 사람이 읽고 어긋난 규칙을 교정할 수 있게.

**합성 vs 강제 한 줄**: 이 카드는 *무엇을 기대하는지* 의 사전이지 *무엇을 만들지* 의 명령이 아니다. 충돌 시 **실측이 이긴다** — 프리셋은 어휘·기본값만 제공.

---

## 5. omp-learn 특화 경로 (research-lab 에서 흔히 일어나는 진화)

운영 중 `omp-learn` 이 이 프리셋을 프로젝트 규칙으로 발산시키는 전형 패턴 (관찰 누적 → 승급 게이트 → `rules.json` + `specificity` 상승):

- **확장자→폴더 고정 규칙**: "이 프로젝트에서 `.pkl` 은 항상 `data/processed/`", "`.pth` 체크포인트는 항상 `experiments/<id>/checkpoints/`" — 관찰 3회 반복 → learned.md 후보 → 승인 → `structure.directories` 의 enforced 규칙으로.
- **실험 ID 스킴 확정**: 프로젝트가 날짜식인지 번호식인지 운영 중 굳어짐 → §2 의 두 후보 중 하나를 `error` severity 로 승격(다른 쪽은 위반).
- **results↔experiments 연결 강제**: "`results/` 파일명은 반드시 대응하는 `experiments/<id>/` 가 존재" 같은 cross-dir 무결성 규칙이 learn 으로 추가될 수 있음.
- **split 그룹 명명 표준**: `split.group` 명명(`exp-2026-05` 식)이 manifest 운영 중 표준화 → DATASETS.md 에 고정.
- **paper 디렉토리 oms 핸드오프 경계**: `paper/` 안을 omp 가 audit 대상에서 빼고 oms 에 위임한다는 `ignore` 항목이 굳어짐 (`paper/**` ignore).
- **figure 재생성 계약**: "모든 `figures/*` 는 `scripts/` 의 생성 스크립트 lineage 보유" 규칙 — 재현성 강화 시 승격.

learn 이 한 항목을 승격할 때마다 `specificity` 가 0 에서 1 쪽으로 이동하고, 해당 규칙의 `learned_refs` 에 출처 관찰 ID 가 기록된다.

---

## 6. wiki 자동 누적 예시 (가벼운 채널, 승인 불필요)

`research-lab` 운영 중 `.omp/wiki/` 에 자동 append 되는 가벼운 패턴·결정 (다음 세션 grep 회수):
- "exp-013 이후 seed 를 config.yaml 에 명시하기 시작 — 이전 실험은 seed 불명"
- "data/raw/ 는 NAS 미러본, 로컬은 processed 만 — 원본 hash 는 manifest 에 UNHASHED"
- "figure 폰트는 발표용 16pt 고정 (make_figures.py 의 rcParams)"

이런 항목은 규칙이 아니라 *맥락 메모* 이므로 게이트 없이 누적, audit 에 영향 없음.

---

**카드 버전**: omp v0.1.0 시드 · 프리셋 패밀리: `python-ml` / `web-app` / `research-lab` / `monorepo` / `johnny-decimal` / `generic` 중 하나.
**참조 스키마**: `references/schemas/rules.schema.json` (structure/naming) · `references/schemas/manifest.schema.json` (dataset).
