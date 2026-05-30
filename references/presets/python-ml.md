# Preset Card — `python-ml`

> **What this is**: 데이터 파일이지 스킬이 아니다. `omp-init`과 `rule-architect` 에이전트가 이 카드를
> 읽고, `project-scanner`의 **귀납 스캔**(실제 폴더 트리·확장자·명명 패턴)과 **합성(synthesize)** 하여
> 초안 `rules.json`을 만든다. 이 카드는 **범용 시드(generic seed)** 다 — 모든 사용자에게 동일하게 배포된다.
> 특정 프로젝트의 고유 규칙은 여기 박지 말 것. 그건 `omp-learn`이 `<project>/.omp/rules.json`으로 승격한다.
>
> **합성 원칙**: 이 카드는 "이 타입의 프로젝트는 보통 이렇게 생겼다"는 **사전 확률(prior)** 일 뿐이다.
> 스캔된 실제 폴더가 카드와 어긋나면 **실제 폴더가 이긴다** (귀납 우선, 프리셋은 빈칸 채우기). 카드에 있으나
> 폴더에 없는 디렉토리는 강제 생성하지 않는다 — 제안만 하고 사람 게이트에 맡긴다.

## 0. 적용 대상 (matches)

Python ML / 연구(research) 프로젝트. 모델 학습·실험·데이터 파이프라인이 중심. 다음 신호 중 **2개 이상**이면
이 프리셋을 강한 후보로 매칭한다 (`rule-architect`가 점수화):

| 신호(signal) | 근거 |
|:---|:---|
| `requirements.txt` / `pyproject.toml` / `environment.yml` / `setup.py` 존재 | Python 프로젝트 |
| `torch` / `tensorflow` / `jax` / `sklearn` / `lightning` / `transformers` 의존성 | ML 스택 |
| `.ipynb` 노트북 다수 | 탐색적 연구 워크플로 |
| `data/` 디렉토리 + `.csv`/`.parquet`/`.npy`/`.pkl`/`.h5` 다수 | dataset-heavy |
| `models/` / `checkpoints/` / `*.pt`·`*.ckpt`·`*.onnx` | 모델 아티팩트 |
| `configs/` + `.yaml`/`.json` 하이퍼파라미터 | 실험 설정 관리 |

> **경계**: 웹 프레임워크(`fastapi`/`django`/`flask`) 신호가 더 강하면 `web-app` 프리셋, 여러 패키지가
> `packages/`·`apps/`로 쪼개져 있으면 `monorepo` 프리셋. ML + 서빙이 섞인 경우 `python-ml`을 base로 하되
> `rule-architect`가 서빙 디렉토리를 보강 규칙으로 추가.
>
> **`python-ml` vs `research-lab` tiebreaker** (둘은 신호가 겹친다 — 명시 규칙으로 하나를 고른다):
> `experiments/`(1실험 1디렉토리 재현 단위)가 있거나 `paper/`·`.tex`·`.bib`가 보이면 → **research-lab** 선호.
> `src/<pkg>` 패키징(설치 가능 라이브러리, `pyproject.toml`의 `[project]`/`packages`)이고 `experiments/`가
> 없으면 → **python-ml** 선호. 둘 다 강하면(설치형 패키지 + experiments 공존) `rule-architect`가 두 후보를
> 사람에게 제시하되, 위 신호 우선순위를 근거로 추천 1개를 박는다.

## 1. 표준 디렉토리 레이아웃 (canonical layout)

두 가지 실세계 관행이 공존한다. `project-scanner`가 import 루트를 보고 어느 쪽인지 판별한다.

- **src-layout** — import 가능한 패키지가 `src/<pkg>/`에 격리됨 (테스트가 설치본을 import, 권장 패키징 관행).
- **flat-layout** — 패키지가 repo 루트 바로 아래 `<pkg>/` 또는 모듈 산재 (연구 코드에서 흔함).

`rules.json`의 `structure.convention`에 `"src-layout"` 또는 `"flat"`을 기록한다.

```
<project>/
├── src/<pkg>/ 또는 <pkg>/   # import 가능한 라이브러리 코드 (재사용 로직)
├── data/
│   ├── raw/                 # 불변 원본 — 절대 직접 수정·덮어쓰기 금지 (read-only 취급)
│   ├── processed/           # 정제·feature 가공 결과 (스크립트로 재생성 가능)
│   └── external/            # 외부에서 받은 서드파티 dataset (출처 추적 대상)
├── notebooks/               # 탐색·분석 .ipynb (재현 코드는 src/로 졸업시킴)
├── models/                  # 학습 산출물: weights·checkpoints (대용량, 보통 .gitignore)
├── configs/                 # 하이퍼파라미터·실험 설정 .yaml/.json
├── scripts/                 # 실행 진입점 (train.py, evaluate.py, preprocess.py)
├── reports/figures/         # (선택) 생성된 그림·플롯
├── tests/                   # (선택) pytest 테스트
├── requirements.txt /       # 의존성 선언
│   pyproject.toml
└── README.md
```

### 디렉토리 역할표 (→ `rules.json`의 `structure.directories[]`로 1:1 매핑)

| path | role (한 문장, `role` 필드로) | enforced | 비고 |
|:---|:---|:---:|:---|
| `data/raw` | 불변 원본 데이터. 절대 in-place 수정 금지 — 새 산출물은 `processed/`로. | true | data 누수 방지의 1차선 |
| `data/processed` | 스크립트로 재생성 가능한 정제·feature 데이터. | true | `lineage`로 원본 추적 |
| `data/external` | 외부 출처 dataset (다운로드·서드파티). | true | manifest `source` 기록 |
| `notebooks` | 탐색·분석용 `.ipynb`. 재사용 로직은 `src/`로 졸업. | true | 노트북에 핵심 로직 잔류 = audit warn |
| `models` | 학습된 weights·checkpoint 아티팩트. | false | 대용량 — `ignore` 후보 |
| `configs` | 하이퍼파라미터·실험 설정 파일. | true | — |
| `scripts` | CLI 진입점 (train/eval/preprocess). | true | import 로직은 `src/`로 분리 |
| `src/<pkg>` 또는 `<pkg>` | import 가능한 라이브러리 코드. | true | `convention`에 따라 경로 결정 |

> **`enforced` 의미**: true면 `omp-audit`가 "이 디렉토리에 역할에 안 맞는 파일"을 위반으로 표시한다.
> `models/`는 아티팩트 덤프라 보통 `enforced:false` + `ignore` 등록. 스캔 결과 실제로 없는 디렉토리는
> `directories[]`에 넣지 않는다 (존재하지 않는 규칙을 강제하지 않음).

## 2. 명명 규칙 (naming conventions)

Python 생태계 관행. 각 항목은 `rules.json`의 `naming.patterns[]` 엔트리(`applies_to` glob + `regex` +
`description` + `severity`)로 매핑된다. 정규식은 **Python `re` 문법, basename에 대해 매칭**.

| applies_to (glob) | 규칙 | regex (시드) | severity | 예시 |
|:---|:---|:---|:---:|:---|
| `**/*.py` (소스 모듈) | snake_case 모듈명 | `^[a-z_][a-z0-9_]*\.py$` | warn | `data_loader.py` ✓ / `DataLoader.py` ✗ |
| `notebooks/*.ipynb` | 번호 접두 + snake_case (실행 순서 가시화) | `^(\d{2}[-_])?[a-z0-9_]+\.ipynb$` | info | `01_eda.ipynb`, `02_baseline.ipynb` |
| `configs/*.yaml` | snake_case 설정명 | `^[a-z0-9_]+\.(yaml\|yml\|json)$` | warn | `train_resnet.yaml` ✓ |
| `data/**/*` (데이터 파일) | 버전·날짜 태그 권장 (불변 데이터 추적) | `.*(_v\d+\|_\d{4}-\d{2}-\d{2})\.[^.]+$` | info | `train_v2.parquet`, `dump_2026-05-30.csv` |
| `models/*` (체크포인트) | 모델명 + 버전/에폭 | `.*(_v\d+\|_ep\d+\|_\d{4}-\d{2}-\d{2})\.[^.]+$` | info | `resnet_v3.pt`, `unet_ep050.ckpt` |
| `scripts/*.py` | 동사 시작 진입점 | `^(train\|eval\|evaluate\|predict\|preprocess\|run_\|make_).*\.py$` | info | `train.py`, `run_sweep.py` |

> **severity 기본값**: 코드 정합성(모듈명)은 `warn`, 데이터·모델 버전 태깅은 `info` (권장이지 강제 아님).
> 사람 게이트에서 사용자가 강제를 원하면 `omp-codify`가 `warn`→`error`로 승격. 노트북 번호 접두는
> 흔하지만 보편은 아니라 `info`로 시작, `omp-learn`이 실제 반복 관찰 시 승격.

## 3. Dataset 관행 (dataset-heavy — `omp-dataset`와 페어)

이 타입은 **dataset이 1급 시민**이다. `omp-init`은 `data/`·`models/`를 감지하면 `omp-dataset`을 후속
제안하고, `dataset-curator`가 `manifest.json`을 채운다. **메타데이터-only** — `dataset-curator`는 실제
데이터를 옮기거나 복사하지 않는다 (체크섬·split·lineage만 기록).

표준 데이터 흐름 (lineage 골격):

```
data/raw/<source>.csv  ──[scripts/preprocess.py]──▶  data/processed/<name>_v<N>.parquet
                                                              │
                                                    split: train / val / test (group 태그)
```

`manifest.json` 시드 규약 (`omp-dataset`가 채울 필드):

- **`split.group`** — train/val/test는 같은 `group`을 공유해야 한다. 그룹이 다르면 `omp-audit`가
  **data leakage 의심**을 경고 (같은 원본이 split 경계를 넘나드는지 점검).
- **`lineage.derived_from` + `lineage.by`** — `processed/` 파일은 어떤 raw에서 어떤 스크립트로 나왔는지
  추적. 재현성(reproducibility)의 핵심.
- **`sha256` + `size_bytes` + `rows`** — "데이터가 바뀌었나?" 감지. 같은 파일명에 내용이 바뀌면 경고.
- **`source`** — `data/external/`은 `"external"`, `data/raw/`는 보통 `"internal"`.

> **DVC / git-lfs 존중**: `.dvc/` 또는 `.gitattributes`에 lfs 필터가 있으면 데이터는 이미 외부 도구가
> 관리 중이다. `dataset-curator`는 **메타만 미러**하고 추적을 가로채지 않는다 (스캔 시 이 신호를
> `rule-architect`에게 보고 → `manifest.json`의 `managed_by_external.tool = "dvc"` 표기,
> `manifest.schema.json`의 객체-with-tool-enum 형태 준수).

## 4. `omp-init`이 스캔 결과를 이 프리셋에 매핑하는 법 (synthesis)

`omp-init` = 귀납 스캔(`project-scanner`) × 프리셋 매칭(`rule-architect`) → 초안 `rules.json` → 사람 게이트.
이 프리셋이 매칭됐을 때 합성 절차:

1. **레이아웃 판별** — `src/<pkg>/__init__.py`가 있으면 `convention:"src-layout"`, 루트 패키지면 `"flat"`.
   실제로 발견된 디렉토리만 `directories[]`에 추가. 카드에 있어도 폴더에 없으면 **넣지 않는다**.
2. **역할 귀속** — 발견된 각 디렉토리를 §1 역할표와 매칭. 표에 없는 디렉토리(예: `serving/`, `airflow/`)는
   `role`을 스캔 증거(주요 확장자·파일명)에서 귀납하고 `enforced:false`로 보수적 시작.
3. **명명 패턴 검증** — §2 정규식을 실제 파일명 샘플에 돌려 **적합률(fit rate)** 측정. 적합률이 낮으면
   (예: 프로젝트가 CamelCase 모듈을 쓰면) 해당 패턴을 **빼거나 실제 관행에 맞게 정규식을 다시 귀납**한다.
   프리셋 규칙을 사용자 코드에 강요하지 않는다.
4. **ignore 시드** — `models/`, `data/raw/`(대용량), `.ipynb_checkpoints/`, `__pycache__/`, `*.egg-info/`,
   `.venv/`, `wandb/`, `mlruns/`, `.dvc/cache/`를 `ignore`에 제안 (audit 노이즈 차단).
5. **specificity 산정** — 숫자를 박지 말고 `learning-protocol.md` §4 공식으로 *계산*한다: 각 규칙의
   `origin` 가중(`preset`=0, `inductive`/`learned`=1) 비율. 귀납으로 발견해 넣은 `directories[]`·재귀납한
   naming은 `origin: inductive`, 프리셋 골격 그대로면 `origin: preset`. 순수 프리셋이면 0.0, 귀납 보정이
   섞인 만큼 >0. 이후 `omp-learn` 승격마다 1로 수렴. (전 프리셋이 이 규칙을 동일하게 따른다 — 숫자 하드코딩 금지.)
6. **`project.preset_origin`** = `"python-ml"` 기록 (provenance).

> **빈 채널 처리**: 스캔에서 `data/`가 없으면 dataset 관련 규칙·매니페스트를 **만들지 않는다** (없는 걸
> 강제하면 노이즈). 이 프리셋의 dataset 섹션은 `data/`가 실재할 때만 활성.

## 5. `omp-learn`이 이 타입에서 보통 특화하는 것 (specialization 예시)

운영하며 자주 관찰되는 → 승격 후보 패턴 (사람 승인 게이트 경유, `learned_refs`로 provenance 기록):

| 관찰(observation) | 승격 결과 (project-owned rule) |
|:---|:---|
| ".pkl은 항상 `data/processed/`에 떨어진다" 3회+ | `data/processed/*.pkl` 강제 규칙 추가, 다른 위치 = error |
| "체크포인트는 `models/<exp>/epoch=NN.ckpt` 패턴" | Lightning 명명 정규식을 프로젝트 규칙으로 고정 |
| "실험마다 `configs/<exp>.yaml` + `models/<exp>/` 1:1" | config↔model 짝 검증 규칙 (`omp-audit`가 고아 감지) |
| "raw는 `data/raw/YYYY-MM-DD_<source>/`로 날짜 폴더링" | 날짜 디렉토리 명명 강제, severity warn→error |
| "노트북 번호 접두가 실제로 일관됨" | §2의 `info` 노트북 규칙을 `warn`으로 승격 |
| "이 repo는 `experiments/` 디렉토리를 쓴다(프리셋엔 없음)" | 새 `directories[]` 엔트리 추가, specificity 상승 |

가벼운 채널(`.omp/wiki/`)에는 승인 없이 자동 누적되는 것들: "이 프로젝트는 parquet을 쓴다", "seed=42 관례",
"train 스크립트는 hydra 설정을 읽는다" 같은 **참고 메모**. 규칙(파일 이동 유발) 아닌 **맥락**은 wiki로.

---

**시드 출처**: Cookiecutter Data Science 레이아웃 + Python `src`-layout 패키징 관행 + 일반 ML 연구 repo
관행의 교집합. 특정 프레임워크(PyTorch/TF/Lightning/Hydra)에 종속되지 않도록 **범용 골격만** 담았다 —
프레임워크별 특화는 `omp-learn`이 실제 사용에서 귀납한다.
