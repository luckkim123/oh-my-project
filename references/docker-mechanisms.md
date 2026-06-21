# docker-mechanisms — how omp-env handles docker environment assets

Ported from docker-env (claudebase). Mechanisms only — personal values: zero.
omp-env references this card for scaffold gate, personal-value resolver,
canonical-view pattern, hybrid inventory, rule-id audit, pitfalls,
multi-user dev-server methodology, and remote-training knowledge.

---

## §1 Scaffold gate (omp-env writing to .omp/env/)

omp-env generates docker assets; it does **not** run `docker build`/`up`/`push`.
Every write goes through a four-step gate — no exceptions.

**Gate steps:**

1. **Dry-run diff** — if a target file already exists, compute and display the diff.
   Never silently overwrite.
2. **Human approval** — wait for explicit approval before writing. This reuses the
   same dry-run→approve pattern as omp-organize (references/safe-fileops.md).
3. **Write** — write the file to `.omp/env/` (canonical location) and the
   root view (§3). Single-pass, careful; never parallel writes to the same target.
4. **Disk verify** — after writing, confirm existence and non-emptiness on disk
   (`test -f`). For compose assets, additionally run `docker compose config` if the
   CLI is present. Never trust a tool's "Saved!" stdout — always verify the
   filesystem. (Inherited principle: the CLI lies.)

If the file is missing after step 3, or `compose config` errors: not done. Fix
and re-verify. Report the path only after disk verify passes.

---

## §2 Personal-value resolver (RIGID — never hardcode)

This card ships to every machine. No absolute path, registry namespace, username,
or host-specific value may appear in a file omp-env generates. Every such value
is resolved from `.env` (or asked once and written there), never embedded as a
literal.

| Value | Resolution method |
|:---|:---|
| Registry / namespace | `.env` `DOCKER_REGISTRY` / `DOCKER_NAMESPACE`; absent → ask once, write to `.env` |
| Image backup directory | `.env` `DOCKER_BACKUP_DIR`; absent → fall back to project-local `images/` |
| Data root / mounted host paths | `.env` `DATA_ROOT` or the project's existing variable names |
| `DISPLAY` / GPU count / `shm_size` | compose/env variables, templated as `${VAR:-default}` (e.g. `${DISPLAY:-:0}`) |

Generated Dockerfiles and compose files reference `${VAR}` — never a literal
home-directory path, a machine-specific absolute path, a concrete registry id,
or a machine hostname. When a value must be shown as an example in documentation,
use a placeholder (`<registry>/<image>:<version>`), not a real value.

> **Release gate** — before shipping any generated file or updating this card,
> grep for concrete IPs, home-directory paths, usernames, and machine names.
> Zero hits is the pass condition. A personal value in a distributed file breaks
> every other install.

---

## §3 Canonical-view pattern (.omp/env/ → project root)

The **canonical Dockerfile (and compose, .env, .dockerignore)** lives in
`.omp/env/`. The project root holds only a **build-tool view** — the file a
build tool needs to find at the conventional root path.

| Platform | Root view | Drift behaviour |
|:---|:---|:---|
| Unix / macOS (default) | Symlink pointing at `.omp/env/<file>` | Drift structurally impossible — single backing file |
| Windows (fallback) | Sync copy written in the **same pass** as the canonical | Drift detected by hash compare on next omp-env run |

**One-pass write rule for sync copies:** write canonical and root copy in the
same tool call, not sequentially across calls. Hash-compare (`sha256sum` or
`hashlib`) both on every subsequent omp-env invocation; if they differ, flag
drift and offer to reconcile (canonical wins unless the user says otherwise).

---

## §4 Hybrid inventory storage

Track image assets in two complementary stores — split by data type, not size.
(md reads ~34–38% more token-efficiently than JSON for grep-first access; JSON
wins for homogeneous keyed records. Verdict: hybrid, not wholesale conversion.)

**`.omp/manifest.json` — `docker_images[]` array** (keyed facts, closed schema)

```json
{
  "docker_images": [
    {
      "ref":        "${DOCKER_REGISTRY}/<purpose>-<base>",
      "tag":        "<semantic-version>",
      "dockerfile": ".omp/env/<name>.Dockerfile",
      "compose":    ".omp/env/<name>.compose.yml",
      "backup":     "$DOCKER_BACKUP_DIR or registry ref",
      "size":       null,
      "digest":     null
    }
  ]
}
```

Fields `size` and `digest` are **opt-in, nullable.** They require a live daemon
(`docker images`/`inspect`). Default: leave `null`; fill only when the user
opts into a read-only daemon query. Never guess or fabricate them.

**`.omp/wiki/docker-*.md` — narrative knowledge** (heterogeneous prose, grep-recalled)

Store here: *why* this base image was chosen, GUI/GPU domain rationale, build
pitfalls encountered, domain-specific setup notes. Use a small YAML frontmatter
(`tags`, `date`) and an INDEX line so grep can surface it. This is not queried
by key — it is recalled by topic search.

**Rule:** when omp-env adds a new image entry, it writes to both stores in the
same pass, keeping them consistent without a reconciliation step later.

---

## §5 Rule-id-as-data audit

omp-env's audit mode checks Dockerfiles and compose files against best-practice
rules, mirroring the **upstream rule IDs as data** — not opaque internal codes.

| Rule (upstream id) | What is checked |
|:---|:---|
| `DL3007` (hadolint) | Base image pinned; not bare `:latest` |
| `DL3009` / layering | `apt-get` cleans `/var/lib/apt/lists`; deps installed before `COPY . .` |
| `DL3002` / `CIS-DI-0001` (dockle) | Runs as non-root (`USER` set) — **warn only** (see below) |
| `CKV_DOCKER_2` (checkov) | `HEALTHCHECK` present when the service exposes a readiness signal |
| `secret-in-ARG/ENV` | No secret material in `ARG`/`ENV` (leaks to `docker history`) |
| `compose-version` | No obsolete top-level `version:` key |
| `compose-name-clash` | No two services / containers share a name within the project |
| `sensitive-mount-ro` | Config mounts (e.g. project guidance files) are `:ro`, not `:rw` |

**Severity posture: warn, never block.** GUI/sim/ROS containers intentionally
break non-root, distroless, and privileged rules — that is correct for those
domains, not a violation. Audit **warns**; it does not fail the build.

A project may suppress a specific rule by adding a `rule_id → "off"` entry to
`.omp/env/audit.toml`. Rule ids are data: the suppress list is auditable and
reviewable, unlike a magic number override.

**Parse structure, not regex.** Handle line continuations, heredocs, multi-stage
builds, and JSON-vs-shell CMD form. A naive `grep latest` misses `FROM ${BASE}`
and false-flags comments.

---

## §6 Pitfall card

These are verified, mechanism-only pitfalls — no personal values, no
machine-specific examples.

**compose `version:` is obsolete.** The top-level `version:` key is ignored by
Compose Spec and emits a deprecation warning. Remove it entirely; the schema
version is inferred from the file structure.

**Secrets leak through `ARG`/`ENV`.** Anything passed as a build `ARG` or set as
`ENV` is recoverable from `docker history`. Use BuildKit
`RUN --mount=type=secret=…` for build-time secrets; use compose `secrets:` for
runtime injection. Never pass tokens, passwords, or API keys via `ARG`/`ENV`.

**GPU passthrough requires `deploy.resources.reservations.devices`.** The old
`runtime: nvidia` form is deprecated. The correct form:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities: [compute, utility, graphics]
```

Add `graphics` to `capabilities` for OpenGL / GUI workloads. The NVIDIA
Container Toolkit must be installed on the host.

**X11 GUI from a container needs three parts.** Mount
`/tmp/.X11-unix:/tmp/.X11-unix:rw`, pass `DISPLAY=${DISPLAY:-:0}` and
`QT_X11_NO_MITSHM=1` as environment variables, and run
`xhost +SI:localuser:root` on the host before `docker compose up`. Missing any
one of the three → "cannot connect to X server". Host-side `xhost` goes in a
comment or a project README — never baked into the image.

**`shm_size` / `ipc: host` for DDS and large shared memory.** ROS2 DDS and some
GPU compute stacks need shared memory well above the 64 MB default. Set
`shm_size: ${SHM_SIZE:-16g}` and/or `ipc: host` in the compose service.

**CMD shell-form swallows signals.** `CMD foo` runs under `/bin/sh -c` and will
not forward `SIGTERM` to the process, preventing clean shutdown. Use exec-form
`CMD ["foo"]` or an `ENTRYPOINT` that `exec`s the command.

**`COPY . .` before installing deps busts layer cache.** Copy only the
dependency manifest first (e.g. `requirements.txt`, `package.json`), install,
then `COPY . .`. Every source-file edit invalidates the install layer if `COPY`
comes first.

**Opaque build patches must be commented.** When a build quirk requires a
one-line workaround (e.g. a `RUN sed -i …` to patch a generated config), add an
inline comment explaining why — the next person (or CI) should not have to
reverse-engineer it.

---

## §7 Multi-user dev-server methodology (generic — personal values: zero)

When a shared GPU or CPU server hosts multiple users, the safe pattern is
**one container per user** generated from a single parameterised template.

**Template variables (all resolved from per-user `.env.<user>` files):**

| Variable | Purpose |
|:---|:---|
| `${USER}` / `${UID}` / `${GID}` | User identity inside the container |
| `${BASE_PORT}` | Host-side port base (e.g. SSH, Jupyter, VNC) offset per user |
| `${GPU_IDS}` | `NVIDIA_VISIBLE_DEVICES` value for this user's GPU allocation |
| `${DATA_DIR}` | Per-user data mount path |

omp-env generates the template and per-user `.env.<user>` stubs. It does **not**
loop over N users and `docker compose up` each — that is a build-runner action
outside omp's scope.

**Known pitfalls:**

- **UID/GID collision** — two users mapped to the same UID inside containers
  causes file-permission conflicts on shared volumes. Assign UIDs explicitly and
  verify uniqueness before first launch.
- **Host-port clash** — each user needs a distinct `BASE_PORT` offset. A port
  conflict silently routes traffic to the wrong container. Document the
  allocation in `.omp/wiki/docker-multiuser-ports.md`.
- **SSHFS UID mapping and stale mounts** — SSHFS mounts survive container
  restarts but not daemon restarts. Stale mounts show `Transport endpoint is not
  connected`; unmount and remount. UID remapping (`-o uid=…`) must match the
  container's expected UID or bind-mount writes fail silently.
- **VNC display conflicts** — each container needs a unique `DISPLAY` number (or
  VNC port). Collisions produce black screens or attach to the wrong session.
- **Entrypoint user-sync** — if the entrypoint creates the user from `${UID}`/
  `${GID}` at startup, it must handle the case where the UID already exists in
  `/etc/passwd` (idempotent `useradd -o` or a pre-check).

**Reference standards:** Compose variable interpolation (Compose Spec §3),
12-Factor App Factor III (config in env), JupyterHub DockerSpawner (per-user
container pattern), Dev Container Spec (`.devcontainer/devcontainer.json`),
Docker `userns-remap` (daemon-level UID isolation).

**What stays per-project only** (never in a distributed card): concrete
usernames, actual UIDs/GIDs, assigned GPU IDs, host port numbers, data-directory
paths. These belong in `.omp/wiki/docker-multiuser-*.md` in the specific project.

---

## §8 Remote training — knowledge only (omp never executes)

> **Disclaimer.** `ssh <host> docker exec <container> train.py` is workload
> execution — the same category as `docker build`/`up`/`push`. omp generates and
> proposes configurations; the **user runs all remote commands**. This section is
> a knowledge card, not an action plan. omp never issues `docker build`, `docker
> up`, `docker push`, or `ssh host docker exec` on the user's behalf.

**Ad-hoc pattern (ssh + docker exec) — knowledge only:**

```bash
# User runs this — omp does not
ssh <training-host> "docker exec <container> python train.py --config /workspace/cfg.yaml"
```

Prerequisites for this pattern to work reliably:
- The container is already running (`docker run -d …`) before the `exec` call.
- The entrypoint and working directory are aligned with the training script path.
- The image on the remote host is current (stale image = silently wrong
  experiment). Verify with `docker images` before executing.
- SSHFS data mounts (if any) must be live — stale mounts silently produce empty
  reads or permission errors.

**Safer ad-hoc variant:** `docker run -d --rm …` (detached, auto-remove on exit)
rather than `exec` into a pre-existing container. Detached runs survive SSH
disconnection; foreground `exec` does not.

**Enterprise answer — recommended upgrade path:**

The ad-hoc ssh-docker-exec pattern is a convenience, not a production workflow.
For shared GPU infrastructure the standard tools are:

| Scheduler | Mechanism |
|:---|:---|
| **Slurm + Pyxis/Enroot** | `sbatch` submits a job; Pyxis/Enroot pulls and runs the container image under Slurm's resource accounting. Multi-GPU, multi-node, fair-share queuing. |
| **Kubernetes + GPU operator** | `kubectl apply` deploys a `Job` or `Pod` with `resources.limits.nvidia.com/gpu`. The NVIDIA GPU Operator manages driver and device-plugin lifecycle. |

Both give: queue management, resource accounting, reproducible environments, log
collection, and failure recovery — none of which ad-hoc ssh-docker-exec provides.

omp-env can generate a Slurm batch script stub or a Kubernetes `Job` manifest
(as a proposed template the user submits), following the same scaffold gate (§1)
and personal-value resolver (§2) as any other docker asset.

---

## Sources

Mechanisms verified against:

- **hadolint** rule reference (`DL3007`, `DL3009`, `DL3002`) — Dockerfile lint rule IDs, canonical namespace.
- **checkov** (`CKV_DOCKER_*`) and **dockle** (`CIS-DI-*`) — IaC/CIS docker rule IDs.
- **Compose Specification** — `version:` obsolescence; named volumes; `secrets:`; variable interpolation.
- **Docker BuildKit secrets** docs — `RUN --mount=type=secret`; `ARG`/`ENV` history leak.
- **NVIDIA Container Toolkit** + Compose `deploy.resources.reservations.devices` — GPU passthrough.
- **Slurm + Pyxis/Enroot** and **Kubernetes GPU operator** — enterprise GPU scheduler references.
- **JupyterHub DockerSpawner**, **Dev Container Spec** — per-user container prior art.
- Storage split rationale (md vs JSON hybrid): md ~34–38% fewer read tokens, grep-first; JSON for homogeneous keyed records — hybrid by data type, not size.

Origin: ported from docker-env skill (claudebase, designed 2026-06-02). Mechanisms kept; every personal value stripped for distribution.
