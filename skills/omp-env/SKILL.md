---
name: omp-env
description: |
  The environment asset stage that generates and manages Dockerfile/compose canonical files
  into .omp/env/ — enforcing a generation gate (dry-run diff → human approval → write → disk verify),
  personal-value resolver (.env/${VAR} substitution, never hardcode), and a strict not-a-build-runner
  boundary (omp proposes commands, the user executes them). docker_naming rules are delegated to
  omp-codify; docker_images inventory to omp-dataset. Generation observations auto-accumulate to
  .omp/wiki/docker-*.md; rule promotion goes through omp-learn's human gate.
  Triggers: docker 환경 만들어, dockerfile 생성, compose 생성, 환경 자산, omp env,
  provision env, docker scaffold, 도커 환경, 도커파일, compose 파일 생성, env stage,
  generate dockerfile, generate compose, docker asset, 환경 파일 만들어
---

# omp-env — Environment Asset Generation & Management (Stage: env)

<Purpose>
Generates and manages Dockerfile/docker-compose canonical files into `.omp/env/` — the single
authoritative location for environment assets within this project's `.omp/` store
(`references/output-layout.md`). Enforces a creation gate (dry-run diff → human approval →
write → disk verify) so no file is silently overwritten (`references/docker-mechanisms.md` §1).
Resolves personal values via `.env`/`${VAR:-default}` substitution — no IPs, home paths, or
usernames are ever hardcoded (`references/docker-mechanisms.md` §2). Seeds generation from
`references/presets/docker.md`. This is a not-a-build-runner stage: omp proposes `docker build`/
`up`/`push` commands and verifies their preconditions; the user runs them.
</Purpose>

<Use_When>
- `.omp/` exists (omp-init done) and you need to create or update a Dockerfile or
  docker-compose file for this project.
- You want environment assets governed by omp rules (naming, layout, resolver) rather than
  hand-edited ad hoc files.
- You are setting up a GPU/GUI-capable container and need pitfall-aware scaffolding
  (base image selection, DISPLAY/NVIDIA flags, user UID matching).
- You want to record *why* this base image or compose topology was chosen in
  `.omp/wiki/docker-*.md` for future sessions.
</Use_When>

<Do_Not_Use_When>
- `.omp/` does not exist yet → **omp-init first**.
- You only want to define docker_naming rules (what images/containers should be called) →
  **omp-codify** (writes docker_naming block into `.omp/rules.json` + NAMING.md).
- You only want to register image metadata (SHA digest, registry, pull date, lineage) →
  **omp-dataset** (writes docker_images block into `.omp/manifest.json` + DATASETS.md).
- You want to actually run `docker build`, `docker compose up`, or push an image →
  **not this stage**. omp-env is a not-a-build-runner: it proposes the command and verifies
  preconditions; execution is always the user's action.
- The project already has Dockerfiles that are working and need no change — read-only audit
  of existing environment assets belongs to omp-audit.
</Do_Not_Use_When>

<Execution_Policy>
- ⚠️ **Canonical files live in `.omp/env/` ONLY.** Never write Dockerfile or compose files
  outside `.omp/env/`. The project root (or any other location) receives only a symlink or a
  sync view — the in-place invariant of `.omp/` is preserved (`references/output-layout.md`).
  Writing directly to the root violates the single-source-of-truth contract.
- ⚠️ **Generation gate is mandatory — no silent overwrite.** Every write is preceded by a
  dry-run diff shown to the human, followed by an explicit approval step. No file is written
  before approval. After writing, disk presence is verified with `test -f` and the compose
  file (if any) is validated with `docker compose config` (`references/docker-mechanisms.md` §1).
- ⚠️ **Personal values 0 — resolver only.** IP addresses, home directory paths, usernames,
  and machine-specific tokens must never appear as literals in generated files. All such values
  are expressed as `${VAR:-default}` placeholders resolved from a `.env` file
  (`references/docker-mechanisms.md` §2). Generated files must be portable across machines.
- ⚠️ **not-a-build-runner.** omp-env never executes `docker build`, `docker compose up`,
  `docker push`, or any container runtime command. It generates the asset files, proposes the
  commands the user should run, and verifies file-level preconditions. The user runs the
  commands. Executing build/run commands inside this skill is forbidden.
- ⚠️ **Stage boundaries are hard.** docker_naming rules (image/container naming patterns,
  tag conventions) are written by omp-codify into `.omp/rules.json`. docker_images inventory
  (SHA digest, registry, lineage) is written by omp-dataset into `.omp/manifest.json`. omp-env
  creates only the canonical asset files and points to those two stages for their concerns.
  Do not conflate the three stages in a single pass.
- **Wiki learning is automatic, rule promotion is gated.** Generation observations — why this
  base image was chosen, which GUI/GPU pitfalls were avoided, which compose topology was selected
  — are auto-appended to `.omp/wiki/docker-*.md` after each generation (no approval needed,
  recoverable via grep). Promotion of an observation into a formal rule goes through omp-learn's
  human gate.
- **Preset seeds generation.** Start from `references/presets/docker.md` for base image
  recommendations, GPU/GUI flag patterns, and compose topology templates. Never invent values
  that the preset already specifies.
</Execution_Policy>

<Steps>
1. **Load references.** Read `references/presets/docker.md` (base image seeds, GPU/GUI
   patterns, compose templates) and `references/docker-mechanisms.md` (§1 generation gate,
   §2 personal-value resolver). If either is absent, halt and report missing reference.
2. **Check docker_naming rules.** Read `.omp/rules.json` for any existing `docker_naming`
   block. If absent, note it — generation can proceed with preset defaults, but remind the
   user that naming rules should be codified via omp-codify afterward.
3. **Draft assets (dry-run).** Generate the Dockerfile and/or docker-compose draft in memory,
   substituting all personal values with `${VAR:-default}` resolver patterns. Show the full
   diff against any existing `.omp/env/` files (or "(new file)" if none). This is the dry-run
   — nothing is written to disk yet.
4. **━━━ GATE — Human approval. ━━━** Present the dry-run diff. Ask: proceed / revise /
   abort. No file is written before explicit approval. If "revise", loop back to Step 3 with
   the requested changes.
5. **Write to `.omp/env/`.** Once approved, write the canonical files to `.omp/env/`
   (e.g., `.omp/env/Dockerfile`, `.omp/env/docker-compose.yml`). If a root-level symlink or
   sync view is needed, create it pointing to `.omp/env/<file>` — never copy the content
   outside `.omp/env/`.
6. **Disk verify.** Confirm presence with `test -f .omp/env/<file>` for each written file.
   If a compose file was written, run `docker compose -f .omp/env/docker-compose.yml config`
   to validate syntax. Report pass or fail explicitly; do not silently skip verification.
7. **Delegate and accumulate.** Propose the follow-up commands the user should run
   (e.g., `docker build -f .omp/env/Dockerfile -t ${IMAGE_NAME} .`). Remind the user to
   register image metadata via omp-dataset (docker_images block in manifest.json). Append a
   one-line generation observation (base image rationale, pitfalls avoided, topology chosen)
   to `.omp/wiki/docker-<YYYY-MM-DD>.md`. If the observation suggests a reusable rule,
   mention it as a candidate for omp-learn promotion — do not promote it automatically.
</Steps>

<Output>
Canonical Dockerfile/docker-compose files written to `.omp/env/` (single authoritative location,
in-place invariant preserved) + dry-run diff shown and human approval recorded + disk verification
evidence (`test -f` pass + `docker compose config` pass if applicable) + proposed build/run
commands for the user to execute (not-a-build-runner: omp proposes, user runs) + delegation
reminders (omp-codify for docker_naming, omp-dataset for docker_images inventory) + one-line
observation appended to `.omp/wiki/docker-*.md` (auto-accumulated, no gate). Rule promotion
candidates flagged for omp-learn but not auto-promoted.
</Output>
