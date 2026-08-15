---
name: omp-garden
description: |
  Periodic documentation gardening — sweeps the project's prose for cited paths that no longer exist on disk,
  counts how many sweeps each finding has survived, and escalates the ones nobody acted on. Report-only: it
  never edits a document and never deletes anything. omp ships no scheduler; a human makes it periodic with
  Claude Code's own `/loop` or `/schedule`.
  Triggers: 문서 정원, 낡은 문서 찾아, 문서 드리프트, 경로 드리프트, 문서 청소, 죽은 경로,
  문서 관리 스윕, garden, doc drift, stale docs, dead paths in docs, documentation sweep, tend the docs
next-skill: omp-organize
---

# omp-garden — periodic doc-drift sweep (report-only, human-gated)

<Purpose>
Documents rot silently. A path moves, and every README, handoff note, and prompt that named it keeps
naming it — nothing errors, the sentence still reads fine, and the reader only finds out by opening
the path. This project has fixed that class by hand repeatedly. `omp-garden` is the sweep that finds
it instead: every backtick-quoted path in the project's prose is resolved against the actual tree,
and what does not resolve is reported with its line and its sentence.

The stage exists **beside** `omp-audit`, not inside it. `scan_structure_drift` already covers declared
paths — `rules.json structure.directories[]` and `.omp/STRUCTURE.md` / `.omp/DATASETS.md` — and this
sweep deliberately skips those two files so one drift is never reported under two stages. What was
uncovered is everything else: the README, `docs/`, handoff notes, a sibling harness's page.
</Purpose>

<Use_When>
- A periodic hygiene pass over project documentation ("문서 정원", "낡은 문서 찾아줘")
- After a rename or a folder move, to find the documents that still name the old path
- Before handing a project to someone (or to a sibling harness), so the prose they will trust resolves
- When a document has been suspected of describing a tree that no longer exists
</Use_When>

<Do_Not_Use_When>
- Checking rule compliance, checksums, or split leakage → `omp-audit` (this stage checks prose against
  the tree, not the tree against the rules).
- Moving or renaming files to satisfy a rule → `omp-organize` (this stage never moves anything).
- Regenerating `.omp/PROJECT.md`·`STRUCTURE.md`·`NAMING.md` from the scanner inventory → `omp-doc`.
- Re-triaging `todo.txt`/`raid.md` staleness → `omp-review` (a different axis: the secretary's time
  axis, not the documents).
- `.omp/` doesn't exist yet → `omp-init` first; there is no project knowledge to garden.
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **Report only. Never auto-fix.** The sweep does not edit a document, does not repoint a path, and
  does not delete anything (D9: closing a finding is a human's call). Repointing is often the *wrong*
  fix — a post-mortem that records where a bug used to live becomes false the moment its path is
  "corrected". Present the finding; the human decides between repoint, rewrite, and suppress.
- ⚠️ **Three verdicts per finding, and they are not interchangeable.** *Repoint* (the thing moved, the
  claim still holds), *rewrite* (the claim itself went stale with the path), *suppress* (the mention is
  historical and correct as written → mark the line `GARDEN_OK: <reason>`). A sweep that only ever
  repoints launders stale documents as checked ones.
- ⚠️ **The stop condition is "no new findings", and it is read from state, not judged.** Every sweep
  writes `.omp/garden-state.json`, which counts the sweeps each finding has survived. A finding at
  **3 sweeps** is marked `ESCALATE` — it has been shown twice and nobody acted, so it needs a decision
  rather than a fourth report. Do not silently carry it forward.
- ⚠️ **omp does not schedule anything.** Claude Code already provides the periodic substrate; making
  this stage recur is Claude Code's own `/loop <interval>` over this skill, or `/schedule` — and
  arming it is the human's call. Never arm it on the user's behalf.
- The report is the author; the human is the verifier. Do not accept your own sweep as a review of the
  documents — it proves a path does not resolve, never that a sentence is right.
</Execution_Policy>

<Steps>
1. Confirm `.omp/` exists. If not, say so and STOP (`omp-init` first).
2. Run the sweep — the deterministic core, never eyeballed:

   ```bash
   python3 hooks/omp_doc_garden.py --root <project>
   python3 hooks/omp_doc_garden.py --root <project> --json          # machine-readable
   python3 hooks/omp_doc_garden.py --root <project> --doc-glob 'notes/**/*.md'
   ```

   Default sweep set is `*.md`, `.omp/*.md`, `docs/*.md` — deliberately not `docs/**`, because a
   docs subtree is often a vendored analysis of *another* repo and every path it cites is
   correctly absent here. Add `--doc-glob` for prose that lives elsewhere (a vault's
   `0_Project/`, a repo's `notes/`). Repeatable.
3. Read the report. For each finding, quote the line to the user and propose one of the three verdicts
   with a reason — never a batch verdict over the whole list.
4. Apply only what the human confirms, one at a time. Repoint and rewrite are ordinary edits to the
   document. Suppress is appending `GARDEN_OK: <reason>` to that line, which the next sweep honors.
5. If any finding is marked `ESCALATE`, name it explicitly in the summary as needing a decision now,
   with how many sweeps it has survived and since when.
6. Report the state line: findings, how many are new this sweep, how many were resolved since the last
   one. `resolved` is the evidence the previous sweep's advice was acted on.
</Steps>

<Output>
- The findings table (file:line → cited path, sweeps survived, the sentence), the `ESCALATE` subset
  called out separately, and the resolved-since-last-sweep count.
- The per-finding verdict the human chose, and what was edited for it.
- If nothing drifted: say so plainly with the document count — a quiet sweep is the result, not a
  non-answer.
- `.omp/garden-state.json` is updated by the script itself. Never hand-edit it; it is the activity
  evidence that distinguishes a loop that runs from one that was only scaffolded.
</Output>
