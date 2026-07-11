---
name: omp-log
description: |
  Universal capture router for the secretary axis — one entry point, five destinations. Routes an
  event/attempt/failure narrative to journal/, a to-do to todo.txt, a blocker/risk to raid.md, a
  recurring decision to decisions/ (ADR), and a structure/naming observation to the existing
  learned.md channel (this skill never intercepts that lane). Single chronicler dispatch, redact
  before write, ledger event per write via hooks/omp_secretary.py.
  Triggers: 기록해줘, 오늘 한 거, 막힌 거, 결정 기록, 블로커, journal, log this,
  todo 추가, 할 일 기록, 리스크 기록, 결정 남겨, 일지 써줘
---

# omp-log — Universal capture router (5 destinations)

<Purpose>
One capture entry point for anything worth recording during a session, routed to the correct
secretary-axis destination instead of dumped wherever is convenient. This is the omp translation of
OMC's `remember` router (design §2.1) — same "classify, don't dump" discipline, five destinations
instead of four because omp splits "risk/blocker" out from generic events. The router itself does no
writing; it classifies and delegates to `chronicler` (the sole narrative writer, D7) and to
`hooks/omp_secretary.py`'s `append_ledger` for the matching machine event.
</Purpose>

<Use_When>
- "오늘 한 거 기록해줘" / "이거 로그로 남겨" — a session narrative, an attempt, a failure worth remembering
- "할 일로 추가해" — a new task for `todo.txt`
- "이거 막혔어" / "리스크야" — a blocker, assumption, issue, or dependency for `raid.md`
- "이건 결정으로 남기자" — a decision worth a permanent, superseded-by-tracked record
- Any capture request where the destination isn't obvious from the words alone — this skill classifies it
</Use_When>

<Do_Not_Use_When>
- The observation is about **structure/naming conventions** (e.g. "이 폴더엔 항상 .pkl이 여기로 간다") →
  that is `omp-learn`'s heavy channel (`learned.md` → promotion gate). `omp-log` routes to it in name
  only — it never writes `learned.md` itself, so route the user to `omp-learn`'s capture surface, not
  through this skill's write path.
- Regenerating `BRIEF.md` from current state → `omp-brief` (a separate skill; `omp-log` only appends,
  never rebuilds the derived view).
- A weekly review, stale scan, or `todo.txt`→`done.txt` migration → `omp-review`.
- `.omp/` doesn't exist yet → `omp-init` first; there is no `.omp/secretary/` to write into.
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **5-destination router, no guess-dump**: classify every capture request into exactly one of
  journal / todo / raid / decisions / learned.md-handoff. If the destination is genuinely ambiguous,
  ask the user a one-line confirmation before writing — never dump into whichever file is closest.
- ⚠️ **learned.md is out of scope for this skill's writes** (learning-protocol boundary, design §2.1:
  "비서 축이 가로채지 않음"). A structure/naming observation gets named and handed to `omp-learn` in
  the Output — `omp-log` does not append to `learned.md` itself.
- ⚠️ **Single chronicler dispatch, never parallel**: exactly one `Task(subagent_type="oh-my-project:chronicler", ...)`
  call per capture request, regardless of how many destinations it touches (a session narrative that also
  spawns a todo item is still one chronicler call with multiple instructed writes) — chronicler is the
  sole LLM writer (D7); fanning it out risks two writers racing on the same file.
- ⚠️ **redact before write**: chronicler passes any journal/raid text through `redact_secrets` before it
  touches disk (secretary-protocol.md, already chronicler's own contract — this skill relies on it, does
  not re-implement it).
- ⚠️ **Ledger event per write**: every destination write pairs with an `append_ledger` event
  (`task_added`, `blocker_opened`, `decision_recorded`; journal narrative pairs with no dedicated ledger
  event beyond the existing `session_start`/`session_end` stubs — the narrative itself lives in the file,
  not the ledger). Cite `hooks/omp_secretary.py`'s `append_ledger` as the mechanism — `omp-log` does not
  hand-roll ledger JSON.
- ⚠️ **git commit messages are optional narrative material only**: if `.git` exists, recent commit
  messages may be offered to chronicler as narrative *reference*, never required — the skill works
  identically with no git repo present.
- D9 unaffected: `omp-log` only ever **opens** a task/blocker/decision, never closes one — closing is
  D9-gated to a human, unchanged from chronicler's own contract.
</Execution_Policy>

<Steps>
1. **Classify the capture request** against the 5 destinations:
   - Event/attempt/failure narrative → `journal/YYYY-MM-DD.md`
   - Actionable to-do → `todo.txt` (todo.txt grammar, `references/secretary-protocol.md`)
   - Blocker/risk/assumption/issue/dependency → `raid.md`, `[open]` status
   - A decision meant to persist and guide future choices → `decisions/NNNN-slug.md` (ADR, 5 fields)
   - A structure/naming rule observation → **not written here**; name it and point to `omp-learn`
   If more than one destination applies (e.g. "실패했고, 다음에 이거 해야 해" → journal + todo), note all
   that apply. If none is a confident fit, ask the user a one-line disambiguation before proceeding.
2. **Gather optional git context**: if `<project>/.git` exists, recent commit messages (`git log
   --oneline -10`) may be surfaced to chronicler as narrative reference material only — skip entirely if
   absent or irrelevant.
3. **Delegate to chronicler (single dispatch)** — one `Task(subagent_type="oh-my-project:chronicler", ...)`
   call carrying the classified destination(s), the raw capture text, and any git reference gathered:
   ```
   Task(
     subagent_type="oh-my-project:chronicler",
     description="omp-log: capture to <destination(s)>",
     prompt="""
     Role: omp-log capture. Record the following into the secretary axis at the destination(s)
     below. Follow references/secretary-protocol.md grammar exactly. Redact secrets before write.
     Append the matching hooks/omp_secretary.py ledger event for each write. Never close an
     existing task/blocker/decision — only open new ones (D9). Never author a progress percentage
     (D8) — if a status figure is needed, call derive_status(root) and quote it verbatim.

     Destination(s): <journal | todo | raid | decisions — one or more>
     Raw capture text: <verbatim user content>
     Optional git reference: <recent commit log, or "none">
     """
   )
   ```
4. **Handle the learned.md case separately (no chronicler dispatch for this part)**: if step 1 identified
   a structure/naming observation, do not fold it into the chronicler call — name the observation in the
   Output and tell the user to run `omp-learn` (or that the next `omp-learn` pass will need it fed in
   manually, since `omp-log` does not write `learned.md`).
5. **Report what was written** — see Output.
</Steps>

<Output>
- Classified destination(s) for this capture (journal / todo / raid / decisions / learned.md-handoff)
- Chronicler's write summary (file(s) touched, ledger event(s) appended) — quoted from its own
  `## Recorded` output, not re-derived
- If a learned.md-shaped observation was present: the observation text, explicitly separated, with
  "hand this to omp-learn — not written by omp-log"
- Any disambiguation question asked to the user before writing (or "destination was unambiguous")
- Confirmation that no task/blocker/decision was closed (only opened) and no progress percentage was authored
</Output>

## handoff 반환 흡수 (Release 2)

`omp-handoff` 로 형제 하네스에 맡긴 일이 돌아오면, 그 결과는 **새 목적지가 아니라 기존
5목적지로** 흡수한다: 압축 요지(1–2천 토큰 수준)를 journal 서사로, 후속 할 일은
todo.txt 로, 새 막힘은 raid.md 로, 내려진 결정은 decisions/ ADR 로. 신규 ledger
이벤트·파일은 만들지 않는다(위임 사실 자체는 `handoff_prepared` 가 이미 기록).
강제 아님 — 위임 결과를 기록할 가치가 있을 때의 권장 경로다.
