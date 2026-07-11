---
name: omp-review
description: |
  Weekly (or on-demand) re-evaluation of the secretary axis — BuJo-style migration for every open
  todo.txt task (migrate/strike/done, human-judged per item, never auto-carried-over), a
  `scan_stale` sweep (stale task/blocker, BRIEF drift, sync-conflict copies), a `raid.md`
  reconfirmation pass (still valid? human closes only), a `scan_journal_tags` tally that *presents*
  repeated [LESSON:]/[BLOCKER:] tags as wiki-promotion candidates without promoting them, and a
  closing recommendation to run `omp-brief`.
  Triggers: 주간 리뷰, 정리하자, 리뷰 돌려, migration, weekly review, 재평가,
  이번 주 리뷰, todo 정리, stale 스캔, review todo, weekly cleanup
next-skill: omp-brief
---

# omp-review — weekly re-evaluation (BuJo migration, human-gated)

<Purpose>
A weekly (or on-demand) hygiene pass over the secretary axis, borrowing the Bullet Journal
"migration" discipline: every open `todo.txt` task is re-judged by a human, not silently carried
forward. This is re-evaluation, not carry-over — an item survives a review only because a human
decided it should, not because nobody looked at it. `omp-review` also surfaces what has gone stale
(`scan_stale`), asks whether each open `raid.md` item is still live, and tallies repeated journal
tags as **candidates** for wiki promotion — it never promotes anything itself (D9: closing/deleting
is always a human's call). This is the GTD "get current" moment for the secretary axis; without it,
`todo.txt`/`raid.md` are a stale-item graveyard (design §6 item 7).
</Purpose>

<Use_When>
- "주간 리뷰 돌리자" / "정리하자" / "migration 하자" — a scheduled or ad hoc weekly re-evaluation
- Deciding whether stale-looking tasks/blockers are still worth tracking
- Wanting a tally of recurring `[LESSON:]`/`[BLOCKER:]` journal tags as wiki-promotion candidates
- Moving accumulated `done` tasks out of `todo.txt` into `done.txt`
</Use_When>

<Do_Not_Use_When>
- Capturing a new event/todo/blocker/decision → `omp-log` (this skill re-evaluates existing entries,
  it does not create new ones).
- Regenerating `BRIEF.md` from current state → `omp-brief` (this skill recommends running it last,
  it does not regenerate BRIEF itself).
- `.omp/secretary/` doesn't exist yet → `omp-init` first; there is nothing to review.
- Actually promoting a wiki/learned.md candidate → `omp-learn`'s promotion gate; this skill only
  names candidates, it never writes `learned.md`/`wiki/`.
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **Migration = re-evaluation, not carry-over.** Every open `todo.txt` line gets one of three
  human-confirmed verdicts: **migrate** (still valid, keep open), **strike** (no longer worth doing,
  discard), or **done** (finished, move to `done.txt`). The skill proposes a verdict per item from
  context (stale age, journal mentions) but the human confirms every single one — **no batch
  auto-carry, no batch auto-strike**. Strike and done are both deletion-shaped decisions (D9): a
  human must say yes to each.
- ⚠️ **done → `done.txt` is a whole-file rewrite, not `atomic_write_json`.** `todo.txt`/`done.txt`
  are plain text (todo.txt schema), not JSON — the move is tempfile-write-then-`os.replace` over
  both files (secretary-protocol.md Lifecycle: "whole-file rewrite allowed — but only via atomic
  write"). `hooks/omp_atomic.py`'s `atomic_write_json` is JSON-shaped and does not apply here;
  chronicler performs the plain-text tempfile+`os.replace` swap itself.
- ⚠️ **`scan_stale(root, now)` output is the review agenda for hygiene findings** — stale
  task (>30d), stale blocker (>14d), `brief_drift` (hand-edited BRIEF.md), and `conflict_copy`
  (sync-duplicate files) all come from this one call. Do not hand-scan ages or grep for duplicates
  separately; `scan_stale` is the single source for what counts as stale.
- ⚠️ **`scan_journal_tags(root)` tallies are wiki-promotion *candidates* only — never auto-promoted.**
  Count repeated `[LESSON:...]`/`[BLOCKER:...]` slugs across `journal/*.md`; a tag appearing 2+ times
  is presented to the human as "recurring — consider promoting to wiki via `omp-learn`", nothing
  more. This skill never writes `wiki/` or `learned.md` itself (learning-protocol light channel
  boundary, same as `omp-log`'s handoff rule).
- ⚠️ **`raid.md` reconfirmation asks, never assumes.** For every open `raid.md` entry, ask "is this
  still valid?" — closing happens **only** after an explicit human yes, logged as a `blocker_closed`
  ledger event. A blocker that looks resolved from journal context still gets a `closeable?` flag,
  exactly like chronicler's own D9 discipline — never a silent close.
- ⚠️ **Single chronicler dispatch** for all writes this review produces (todo.txt rewrite,
  done.txt append, raid.md status updates, any `blocker_closed`/`task_done` ledger events) — D7,
  one narrative writer, no fan-out.
- ⚠️ **Close with an `omp-brief` recommendation**, not an automatic BRIEF regeneration — review and
  brief are separate skills; this one only recommends the next step.
</Execution_Policy>

<Steps>
1. **Load current state**: `todo.txt` (all open lines), `raid.md` (all `[open]` entries),
   `scan_stale(root, now)` findings, `scan_journal_tags(root)` tag tally.
2. **Per-task migration pass**: for each open `todo.txt` line, propose a verdict from context (age
   from `scan_stale`, any journal mentions) — **migrate** / **strike** / **done** — and ask the human
   to confirm or override each one individually. Do not batch-apply a default.
3. **Per-blocker reconfirmation pass**: for each open `raid.md` entry, ask "still valid?" — human
   answer decides keep-open vs. `closeable?` flag vs. explicit close (close only on explicit yes).
4. **Tally journal tags**: present `scan_journal_tags(root)` grouped by slug, highlighting any slug
   appearing 2+ times as a wiki-promotion candidate — hand off by name to `omp-learn`, do not write
   `wiki/`/`learned.md` here.
5. **Delegate the writes to chronicler (single dispatch)** — one `Task(subagent_type="oh-my-project:chronicler", ...)`
   call carrying every confirmed verdict:
   ```
   Task(
     subagent_type="oh-my-project:chronicler",
     description="omp-review: weekly migration",
     prompt="""
     Role: omp-review weekly migration. Apply exactly these human-confirmed verdicts — do not infer
     or add any verdict I did not list.
       Migrate (keep open, no change): <task ids/text>
       Strike (remove from todo.txt, human-confirmed discard): <task ids/text>
       Done (move to done.txt): <task ids/text>
       Blockers to close in raid.md (human-confirmed): <raid ids, or "none">
     Rewrite todo.txt/done.txt via tempfile + os.replace (plain-text whole-file rewrite, NOT
     atomic_write_json — that is JSON-only). Append a task_done ledger event per item moved to
     done.txt and a blocker_closed ledger event per raid.md item closed, via append_ledger. Never
     close or strike anything beyond this confirmed list.
     """
   )
   ```
6. **Recommend `omp-brief`** as the closing step — do not regenerate BRIEF.md within this skill.
7. **Report** — see Output.
</Steps>

<Output>
- Migration verdicts applied (migrate / strike / done counts, all human-confirmed — never a batch
  default)
- `scan_stale` findings surfaced (stale_task / stale_blocker / brief_drift / conflict_copy counts)
- `raid.md` reconfirmation outcome (kept-open / flagged-closeable / closed counts, all human-decided)
- Journal tag tally: any slug at 2+ occurrences, named as a wiki-promotion candidate for `omp-learn`
  (or "no recurring tags")
- Confirmation that `todo.txt`/`done.txt` were rewritten via tempfile+`os.replace`, not
  `atomic_write_json`
- Confirmation that no task/blocker was struck/closed without an explicit human verdict
- Recommendation to run `omp-brief` next
</Output>
