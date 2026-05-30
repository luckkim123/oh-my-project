---
name: omp-dataset
description: |
  dataset 등록·추적 — 데이터 파일의 SHA-256(hashlib)·size·rows·split·lineage를 `.omp/manifest.json`에
  기록하고 사람용 `.omp/DATASETS.md` 카탈로그를 갱신한다. 메타데이터-only: 실제 데이터는 절대 복사·이동·push
  하지 않고 "바뀌었나/어디서 왔나/누수 없나"만 추적한다. DVC/git-lfs 감지 시 소유권을 주장하지 않고 위임(메타만 미러).
  Triggers: dataset 등록, 데이터셋 추적, 체크섬, SHA256, manifest 갱신, split 추적, lineage,
  register dataset, track dataset, data inventory, train val leakage, 데이터 카탈로그
---

# omp-dataset — dataset 등록·추적 (메타데이터-only 인벤토리)

<Purpose>
프로젝트의 데이터 파일을 `.omp/manifest.json`에 **순수 메타데이터**로 등록한다 — SHA-256 체크섬·바이트 크기·행수·train/val/test split 멤버십·lineage(어디서 왔고 무엇이 만들었나)·source. 등록 후 페어인 사람용 `.omp/DATASETS.md` 카탈로그를 같은 패스에서 재생성한다. 코드의 "인벤토리 대장" — 실제 데이터는 한 바이트도 안 옮기고, 오직 *기술*만 해서 "이 파일 바뀌었나?", "train/val 누수 없나?", "이거 어디서 왔나?"를 답할 수 있게 만든다. dataset-curator agent에게 단일 위임한다.
</Purpose>

<Use_When>
- 데이터 파일(`.parquet`/`.csv`/`.npy`/`.pkl`/`.h5`/`.tfrecord` 등)을 `.omp/manifest.json`에 처음 등록할 때
- 데이터가 바뀌었는지(SHA-256 drift) 추적·갱신하고 싶을 때
- train/val/test split 그룹을 묶어 누수 점검 기반을 만들고 싶을 때
- lineage(원본 → 생성 스크립트 → 산출물)를 기록해 provenance를 남기고 싶을 때
- `.omp/DATASETS.md` 사람용 데이터 카탈로그를 manifest와 동기화하고 싶을 때
</Use_When>

<Do_Not_Use_When>
- 실제 데이터 파일을 **옮겨야** 하면 → 이건 dataset 레인이 전혀 아님. 파일 재배치는 `omp-organize`(organizer + `references/safe-fileops.md`)
- 폴더 구조·확장자 패턴을 **귀납·분류**하는 거라면 → `omp-init`/project-scanner (manifest는 dataset만 다룸)
- 구조·명명 **규칙**을 만들거나 바꾸는 거라면 → `omp-codify`/rule-architect (`rules.json`)
- 규칙 준수 PASS/FAIL **판정**이 필요하면 → `omp-audit`/auditor (dataset-curator는 self-audit 안 함)
- 데이터가 이미 **DVC/git-lfs로 관리**되고 그걸 omp가 인수해야 한다고 느낄 때 → 인수 금지. 감지 시 위임(메타만 미러)이 정책
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **메타데이터-only, 절대 원칙**: dataset-curator는 데이터 파일을 `mv`/`cp`/`rm`/symlink/`dvc push`/`git lfs push`/업로드 **절대 안 함**. 해시하려고 바이트를 *읽는* 것이 데이터 파일과의 유일한 접촉. 데이터 이동은 dataset 레인 밖(`omp-organize`의 organizer 소관). "등록하면서 옮기는" 것이 이 도메인의 1순위 실패 모드 — citation 날조의 dataset판.
- ⚠️ **SHA-256은 stdlib `hashlib`로 결정적**: raw 파일 바이트를 청크 스트리밍(예: 1 MiB)해서 lowercase 64-hex. OS별 CLI(`shasum`/`sha256sum`/`certutil`)를 진실의 출처로 쓰지 않음(hashlib은 macOS/Linux/Windows 동일). 해시가 비결정적이면 "바뀌었나?" 신호 자체가 무의미. 너무 큰 파일은 정직하게 `"sha256": "UNHASHED"`(스키마 허용) + size/mtime로 대체 — **가짜 해시 절대 날조 금지**.
- ⚠️ **메타데이터 발명 금지**: 안 센 `rows`, 그럴듯한 `lineage`, 지어낸 `source` 금지. 모르면 optional 필드 **생략**. 틀렸지만 그럴듯한 lineage가 없는 것보다 나쁨. 모호하면(split 배정/lineage/이게 정말 dataset인가) 추측 말고 사람에게 surface.
- ⚠️ **DVC/git-lfs는 경쟁이 아니라 위임**: `.dvc/`·`*.dvc`·`.gitattributes`의 `filter=lfs` 감지 시 `manifest.json.managed_by_external`(`tool: "dvc"` 또는 `"git-lfs"`) 설정 + 메타만 미러 + `DATASETS.md`에 "외부 관리 중" 명시. 재-해시로 "검증"하거나 push 금지.
- **페어 재생성은 강제·동일 패스**: `manifest.json.datasets[]`가 바뀌면 같은 런에서 `DATASETS.md` 재생성(`references/output-layout.md`: 사람 .md ↔ 기계 .json은 절대 drift 금지).
- **결정적 출력**: `datasets[]`를 안정 키(`id`)로 정렬 + 안정 JSON 포맷(정렬 키·고정 들여쓰기) → 안 바뀐 폴더는 byte-identical manifest. 경로는 `pathlib.Path`로, dataset `path`는 **프로젝트 루트 상대경로**(머신/OS 이식성).
- **self-approval 금지**: dataset-curator는 등록만 함. dataset 상태 "audited/compliant" 선언은 `omp-audit`(auditor) 별도 레인. 핸드오프는 "registered — ready for audit", 절대 "registered and verified-clean" 아님.
- 생성은 단일 신중(citation-safe 철학의 dataset판) — dataset-curator를 병렬로 여러 개 띄우지 않음.
</Execution_Policy>

<Steps>
1. **`.omp/` 존재 확인**: `<project>/.omp/`가 없으면 dataset 등록 불가 — 먼저 `omp-init`을 돌려 부트스트랩해야 함을 알리고 중단. 있으면 기존 `manifest.json`(갱신 대상, clobber 금지)과 계약(`references/schemas/manifest.schema.json`)을 로드.
2. **등록 범위 확인**: 사용자가 명시한 경로 또는 데이터 위치(`data/`/`datasets/`/`raw/`/`processed/` + `.parquet`/`.csv`/`.npy`/`.pkl`/`.h5`/`.tfrecord` 확장자). split 멤버십·lineage·source를 사용자가 알면 받아두되, 모르는 건 비워두고 dataset-curator가 증거 기반으로만 채우게 함.
3. **외부 버저닝 먼저 감지**(해시 전): `.dvc/`·`*.dvc`·`.gitattributes`의 `filter=lfs`. 발견 시 위임 정책 — `managed_by_external` 설정 + 메타만 미러, 인수·push 금지를 진행 방침으로 확정.
4. **dataset-curator에게 단일 위임** — `Task(subagent_type="oh-my-project:dataset-curator", ...)`:
   - **입력**: (a) 등록 범위 데이터 파일 경로(있으면), (b) 알려진 split/lineage/source 힌트(있으면 — 없으면 생략), (c) 프로젝트 루트, (d) 계약 카드 `references/schemas/manifest.schema.json`, (e) 출력 경로 규약 `references/output-layout.md`, (f) 데이터-이동 경계 참조 `references/safe-fileops.md`(이동은 organizer 소관임을 명시), (g) 자가학습 채널 `references/learning-protocol.md`(반복 관찰은 `.omp/learned.md`/`.omp/wiki/`로 — 규칙 승격은 `omp-learn`).
   - **지시**: `.omp/manifest.json`과 `.omp/DATASETS.md` **두 파일만** 쓴다. SHA-256은 stdlib `hashlib`로 raw 바이트 스트리밍(결정적, lowercase 64-hex), 너무 크면 정직한 `UNHASHED`. `rows`는 실제로 셌을 때만, `lineage`는 실재하는 스크립트·원본 증거가 있을 때만, `split.group`으로 형제 split 묶기. 데이터 파일 `mv`/`cp`/`rm`/push **절대 금지**. DVC/git-lfs 감지 시 `managed_by_external` + 메타만 미러. 스키마 검증 후 쓰기 — `manifest.json` 쓰기는 부분쓰기로 기존 인벤토리가 손상되지 않도록 `hooks/omp_atomic.py`의 atomic write를 경유한다(T20). `datasets[]`는 `id`로 정렬, 모호하면 발명 말고 surface, self-approve 금지("registered — ready for audit" 핸드오프).
5. dataset-curator 산출 받아 정리: 등록된 dataset 목록(id·경로·sha256·size·rows·split·source) + 외부 버저닝 감지/조치 + 쓴 파일 2개 + 증거 기반 lineage/split 노트 + 사람 결정 필요한 모호 항목(발명 안 함) + "메타데이터-only 확인(데이터 0개 이동) + ready for omp-audit" 핸드오프.
6. 사람 결정 필요 항목(모호한 split/lineage, `UNHASHED` 처리)이 있으면 사용자에게 확인 요청 후 dataset-curator 재위임으로 manifest 갱신. 규칙으로 굳힐 가치가 있는 반복 패턴(예: "이 폴더의 .pkl은 항상 processed split")은 `omp-learn`으로 승격(사람 게이트) — dataset-curator가 직접 규칙화하지 않음.
</Steps>

<Output>
등록된 dataset 목록(id → 상대경로 · sha256(64hex 또는 UNHASHED) · size_bytes · rows · split role/ratio/group · source) + 외부 버저닝 감지 결과 및 조치(DVC/git-lfs → `managed_by_external` 미러 / none) + 쓴 파일 2개(`<project>/.omp/manifest.json`·`<project>/.omp/DATASETS.md`, 같은 패스 재생성으로 drift 0) + 증거 기반 lineage/split 노트 + 사람 확인 필요 잔여(모호한 split·lineage·`UNHASHED` — 발명 안 함) + "메타데이터-only: 데이터 파일 0개 이동/복사/push, 결정적 재실행 = byte-identical manifest, self-approve 안 함 → ready for omp-audit(별도 패스)". 경로·페어링 규약은 `references/output-layout.md`, 스키마는 `references/schemas/manifest.schema.json`가 SSOT.
</Output>
