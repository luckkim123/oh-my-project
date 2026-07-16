---
name: omp-brief
description: |
  Pull-style briefing — regenerates `.omp/secretary/BRIEF.md` from current ledger/todo/raid/journal
  state: traffic light, state-of-play, top-5 tasks, open blockers, a next-session goal suggestion,
  and decision paths. Every number is `derive_status(root)` output quoted verbatim — never an
  LLM-authored count or percentage (D8). Gated by `brief_hash_check`: a hand-edited BRIEF.md STOPs
  regeneration instead of silently overwriting it.
  Triggers: 브리핑, 어디까지 했지, 현황, 다음 뭐하지, 상태 보고, brief, status,
  what's the status, where did I leave off, what's next, give me a briefing
---

# omp-brief — pull-style briefing (BRIEF.md regeneration)

<Purpose>
Regenerates `.omp/secretary/BRIEF.md`, the always-loaded index over the secretary axis (design §3:
"세션 핸드오프 필드" pattern — 2-minute scan, reference only, never paste-in-full). BRIEF is a
**derived view**, not a source: its content comes from `derive_status(root)` plus recent
`journal/`, `raid.md`, and `todo.txt`, never from the LLM's own judgment of "how much is done."
This skill only regenerates the file; it never appends new capture content (`omp-log`) and never
performs the weekly BuJo-style reevaluation (`omp-review`).
</Purpose>

<Use_When>
- "브리핑해줘" / "어디까지 했지" / "현황 보고" — a pull request for current project state
- "다음에 뭐 하지" — a next-session goal suggestion derived from `last_stage`
- Before ending a session, to leave a fresh BRIEF.md for the next one to pick up
</Use_When>

<Do_Not_Use_When>
- Capturing a new event/todo/blocker/decision → `omp-log` (this skill never appends new content,
  only regenerates the derived view from what's already recorded).
- A weekly review (BuJo migration, stale scan, `todo.txt`→`done.txt`, raid reconfirmation) →
  `omp-review`.
- `.omp/secretary/` doesn't exist yet → `omp-init` first; there is nothing to summarize.
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **`brief_hash_check` gates every regeneration**: before writing, call
  `hooks/omp_secretary.py`'s `brief_hash_check(path)` on the existing `BRIEF.md`. Result `"dirty"`
  (marker hash doesn't match on-disk content — a human hand-edited it since the last regeneration)
  → **STOP**, do not write, and ask the human whether to overwrite / merge their edit in / skip this
  regeneration. Only `"clean"` or `"missing"` (no file yet) proceeds straight to regeneration.
- ⚠️ **All numbers are `derive_status(root)` output, quoted verbatim** (D8): traffic-light color,
  its one-line reason, `open_tasks`, `open_blockers`, `done_7d`, `last_stage` all come from that one
  call. No paraphrasing, no re-deriving, no LLM-estimated percentage or count anywhere in the file.
- ⚠️ **Fixed section order** (never reordered): (1) omp-managed marker → (2) traffic light → (3)
  state-of-play → (4) goal → (5) top-5 tasks → (6) open blockers → (7) decisions (paths only).
- ⚠️ **Double cap: ≤30 lines AND ≤2000 characters** — both bounds apply simultaneously
  (secretary-protocol.md, BRIEF contract). Apply the fixed truncation order when over cap:
  top-5 tasks → top-3, then open-blocker list → count only, then decisions → path references only.
  The 3 inviolable lines (marker, traffic light, state-of-play) are never truncated regardless of
  cap pressure.
- ⚠️ **Handoff fields are references, never copies** (design §11.2 / secretary-protocol.md): the
  goal/decisions sections point at paths (`decisions/0004-slug.md`) or one-line summaries, never
  paste the full narrative — BRIEF stays a 2-minute scan, not a second journal.
- Single `chronicler` dispatch (D7) — chronicler generates and writes `BRIEF.md`; this skill does
  not hand-roll the write itself. `chronicler` is the generator here, not an auditor: this is
  synthesis, not a PASS/FAIL verdict.
- **read-map (Release 2)**: `derive_status` 결과의 `sources`가 비어 있지 않으면 State-of-play 아래에 `읽을 곳: <path> (<kind>, open N) — <convention>` 줄을 최대 4줄 추가한다. 수치는 `derive_status`가 계산한 `open` 값만 인용(D8) — 직접 세지 않는다. 캡 초과 시 이 줄들을 기존 truncation 우선순위보다 먼저 버린다.
</Execution_Policy>

<Steps>
1. **Compute status**: call `derive_status(root)` → `{light, reason, open_tasks, open_blockers,
   done_7d, last_stage}`. This is the only source of numbers for the whole file.
2. **Gather source material**:
   - Last 7 days of `journal/*.md` (for state-of-play / goal context)
   - Open items in `raid.md` (blockers)
   - `todo.txt`, sorted by priority letter, top 5
   - `decisions/` directory listing (paths only, no content read needed for the summary line)
   - **Actionable-knowledge reconcile (family wiki-status convention)**: enumerate the open
     actionable findings from `omp_content_audit.lint_wiki(root)` — `ready_to_promote` (a
     `learned.md` candidate at `evidence_count>=3` with `counter_examples==0` and
     `user_overridden` false per protocol §3, ripe for omp-learn), `stuck_candidate`, and
     `contradiction`. Any open one must be reflected in the next-session goal / top-5 tasks or
     consciously deferred — a recorded-but-actionable item must not silently vanish from the brief.
     This is enumeration-only (derived from existing fields, no schema change); the human gate still
     decides. Nothing open → nothing to add.
3. **Hash check**: run `brief_hash_check(<BRIEF.md path>)`.
   - `"dirty"` → STOP. Report the conflict to the human; ask overwrite / merge / skip. Do not
     proceed to step 4 without an explicit answer.
   - `"clean"` or `"missing"` → proceed.
4. **Delegate to chronicler (single dispatch)** — one `Task(subagent_type="oh-my-project:chronicler",
   ...)` call carrying the computed status and gathered material:
   ```
   Task(
     subagent_type="oh-my-project:chronicler",
     description="omp-brief: regenerate BRIEF.md",
     prompt="""
     Role: omp-brief regeneration. Rewrite .omp/secretary/BRIEF.md wholesale, following the fixed
     section order and double cap (<=30 lines AND <=2000 chars) in references/secretary-protocol.md.
     Use only these derive_status(root) values for every number — do not compute or estimate any
     count or percentage yourself:
       light=<light> reason=<reason> open_tasks=<open_tasks> open_blockers=<open_blockers>
       done_7d=<done_7d> last_stage=<last_stage>
     Source material (reference only, do not paste in full — summarize/point to paths):
       Recent journal (7d): <excerpt or "none">
       Open raid.md items: <list or "none">
       Top-5 todo.txt lines: <list>
       decisions/ paths: <list or "none">
     If over cap, truncate in this order only: top-5 tasks -> top-3, open blockers -> count only,
     decisions -> paths only. Never truncate the marker line, traffic-light line, or state-of-play
     line. Recompute the sha256 body hash and write the omp-managed marker as the first line.
     """
   )
   ```
5. **Report** — see Output.
</Steps>

<Output>
- Hash-check result (`clean`/`missing`/`dirty`) and, if `dirty`, the human's chosen resolution
- The regenerated traffic light + reason (quoted from `derive_status`, not paraphrased)
- Whether truncation was applied, and to which sections
- Confirmation that every number in the file traces to `derive_status(root)` and that BRIEF.md
  stays within both caps (≤30 lines, ≤2000 chars)
</Output>
