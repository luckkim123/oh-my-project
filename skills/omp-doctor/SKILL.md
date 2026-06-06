---
name: omp-doctor
description: |
  omp installation/prerequisite self-diagnosis — checks hook registration, python3 availability,
  and the presence of reference cards to report "is omp ready to work in this environment" as
  PASS/WARN/FAIL. Unlike omp-audit, which *assumes .omp already exists* and inspects rule
  compliance, doctor looks at the installation layer that comes before that (it does NOT perform
  the rules.json schema validation that overlaps with audit). read-only, no auto-fix.
  Triggers: omp 진단, doctor, 설치 점검, omp 작동 확인, 왜 안 되지, hooks 확인,
  omp-doctor, 설정 점검, 환경 점검, omp 안 돼,
  omp diagnose, install check, verify omp works, why isn't it working, check hooks,
  settings check, environment check, omp broken
---

# omp-doctor — installation/prerequisite self-diagnosis (read-only)

<Purpose>
Checks whether omp is *ready to work*. `omp-audit` assumes `.omp/` already exists and judges
whether the project folder follows the rules (structure/naming/dataset), but doctor inspects the
**layer before that** — is the hook installed, is python3 present, are omp's own reference cards
intact. The goal is to catch *installation* problems like "I installed omp but the STAGE line
doesn't appear / a skill can't find its card."
</Purpose>

<When_To_Use>
- When you just installed omp and want to confirm it attached correctly.
- When omp skills/hooks aren't behaving as expected and you want to distinguish whether the cause
  is *installation/environment* or *rules*.
- When doing a cross-platform check of whether omp works for the first time on another machine
  (especially Windows/Linux).
</When_To_Use>

<When_Not_To_Use>
- If you want to check whether the project folder follows the `.omp/rules.json` rules → `omp-audit`
  (that's the rule-compliance gate). doctor **does not perform rules.json schema validation** — it's
  deliberately excluded as overlap (audit's domain).
- If you want to create `.omp/` for the first time → `omp-init`. doctor only diagnoses; it does not
  create `.omp/`.
- If you want to change the rules → `omp-codify`.
</When_Not_To_Use>

<Execution_Policy>
- **read-only**: doctor does not write or fix any file. It only reports the diagnostic result
  (PASS/WARN/FAIL + evidence + a one-line fix). No auto-fix (installation fixes are made
  deliberately by the user).
- **stdlib/cross-platform**: checks use only python3 stdlib + standard CLI (`python3 --version`,
  checking for `pathlib` existence). OS branching uses `platform`/`os.name`. No hardcoding of
  absolute paths or `~`.
- **fail-soft**: if one item's check fails, the other items still run (one FAIL does not stop the
  whole diagnosis).
- **audit-overlap excluded**: doctor does NOT inspect rules.json/manifest.json *schema validity or
  specificity consistency* (that's the domain of omp-audit Step 1·2). doctor's .omp-related checks
  go only as far as "does the file exist."
</Execution_Policy>

<Steps>
1. **hook installation check**:
   - Do the `hooks/omp_route_emit.py`·`hooks/omp_verify_emit.py` files exist?
   - Are the two hooks registered in `.claude-plugin/plugin.json` (or the installation environment's
     hook registration) as UserPromptSubmit / PostToolUse? (If not registered, the STAGE line and
     integrity reminder won't appear → WARN.)
   - Live behavior check (optional): does `echo '{"prompt":"x"}' | python3 hooks/omp_route_emit.py`
     exit 0 and emit JSON containing `STAGE(project)`?
2. **python3 availability check**:
   - Does `python3 --version` succeed (the runtime prerequisite for hooks/helpers)? Is it 3.x?
   - Does the atomic write in `hooks/omp_atomic.py` work (the safety prerequisite for SSOT writes,
     T20) — is it importable?
3. **reference card integrity check**:
   - Do all 4 cards in `references/` (`safe-fileops.md`·`output-layout.md`·`omc-backport-analysis.md`·
     `learning-protocol.md`) exist?
   - Do the 6 presets in `references/presets/` and the 2 schemas in `references/schemas/`
     (`rules.schema.json`·`manifest.schema.json`) exist? (Schema *content validation* is not done —
     existence only, audit-overlap excluded.)
4. **summary judgment report**: report each item as PASS / WARN / FAIL + evidence (what is missing or
   failed) + a one-line fix. End with a single-line overall summary ("omp install OK" / "hook not
   registered — reinstall needed", etc.).
   ⚠️ No item is fixed automatically — doctor's role is to *tell* the user so they can fix it.
</Steps>

<Output>
- For each of the 3 axes (hooks / python3 / reference cards): PASS|WARN|FAIL + evidence + 1-line fix.
- A single-line overall summary (is it ready to work / what needs fixing).
- ⚠️ rules.json rule compliance is not in this report — that goes through `omp-audit` (role
  separation stated explicitly).
</Output>
