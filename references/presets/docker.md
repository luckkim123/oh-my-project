# Preset Card — `docker`

> **What this is**: This is a data file, not a skill. The `omp-init` and `rule-architect` agents read
> this card, then **synthesize** a draft `rules.json` by combining it with `project-scanner`'s
> **inductive scan** (the actual folder tree, extensions, and naming patterns). This card is a
> **generic seed** — it is distributed identically to every user.
> Do not bake a specific project's unique rules in here. Those are promoted by `omp-learn` into
> `<project>/.omp/rules.json`.
>
> **Synthesis principle**: This card is only a **prior** stating "a project of this type usually looks
> like this." When the actual scanned folders disagree with the card, **the actual folders win**
> (induction first, the preset just fills in the blanks). Directories that the card lists but the folder
> lacks are not force-created — only proposed, leaving the decision to the human gate.

## 0. What it matches

Docker / container projects that define image build specifications and deployment configurations. This preset activates when **two or more** of the following signals are present:

| signal | rationale |
|:---|:---|
| `Dockerfile` or `Dockerfile.*` present | Container build definition |
| `docker-compose.yml` / `docker-compose.yaml` or `compose.yaml` | Multi-container orchestration |
| `.dockerignore` present | Container build optimizations |
| `docker/` or `containers/` directory | Container/build management folder |
| build scripts referencing `docker build` / `docker push` | Build pipeline signals |

> **Boundaries**: if Kubernetes manifests (`k8s/`, `*.yaml` with `apiVersion: ...`) dominate, use the
> `kubernetes` preset (future). If the project is pure infrastructure-as-code (Terraform/Ansible),
> use `infra-iac`. When both Docker and orchestration are present, use `docker` as the base and let
> `rule-architect` add supplementary rules.

## 1. Docker image & container naming conventions

Container assets follow OCI Distribution and Image specifications. Each naming rule traces to a verified
standard in `references/standards-registry.seed.json`.

### docker_naming (codify seed)

The following conventions are seeded into `rules.json` as **provenance rules**. Each traces to an external standard:

| rule | template | notes | traces_to | normative |
|:---|:---|:---|:---|:---|
| `image_ref_template` | `${REGISTRY}/${NAMESPACE}/<purpose>-<base>:<semver>` | Fully-qualified reference (no bare names, no `:latest`). Registry and namespace are template vars — a project must bind them at deployment time. | OCI-DIST-1.1.1 | MUST (error) |
| `container_name_template` | `<purpose>-<base>` | Container names follow the same purpose+base pattern for traceability. | OCI-IMAGE-1.1.1 | SHOULD (warn) |
| `service_name_template` | `<purpose>-<platform>` | Compose/orchestration service names include platform signal (e.g. `api-prod`, `worker-staging`). | COMPOSE-SPEC | SHOULD (warn) |
| `version_scheme` | `semver-2.0.0` | All image tags use semantic versioning (major.minor.patch). | SEMVER-2.0.0 | SHOULD (warn) |

> **Binding placeholders at runtime**: `${REGISTRY}` (e.g., `ghcr.io`, `docker.io`, private registry) and
> `${NAMESPACE}` (e.g., user/org) are **never hardcoded** in preset rules. They are bound in the project's
> `rules.json` at initialization, allowing the same rule set to work across dev/staging/prod without duplication.

## 2. Audit rules (Dockerfile & Compose lint seed)

When `omp-codify` processes this preset, it generates audit rules that `omp-env` uses to validate
container builds and configs. Each rule is data-driven: a **`rule_id`** entry in `rules.json`, with
`traces_to` pointing to a standards-registry entry, and `severity` derived from the normative word
(MUST→error, SHOULD→warn, MAY→info).

The **enforced** column marks whether `hooks/omp_docker_audit.py` mechanically checks the rule today.
Enforced rules emit violations during `omp-audit`/`omp-env`; advisory rules are documented best-practice
seeds that a project may codify but the harness does not yet check automatically. The **severity** column
is the rule's *normative-word-derived recommendation* (MUST→error, SHOULD→warn, MAY→info) — note that the
docker audit **axis ships warn-default** for every rule (so it never auto-blocks an overall PASS); a project
escalates a rule to its recommended severity via `rules.json` `docker_severity_overrides` (see §3).

| rule_id | check | rationale | traces_to | severity (recommended) | enforced |
|:---|:---|:---|:---|:---|:---|
| `DL3007` | Base image must be pinned to a digest (not `:latest` or floating tags) | Ensures reproducible, auditable builds. Digest pinning (SHA-256) is the strongest guarantee. | DL3007 | warn | ✅ yes |
| `secret-in-env` | No secrets/credentials in `ENV` or `ARG` Dockerfile directives (history visibility) | BuildKit secrets or runtime-mounted secrets prevent secrets from leaking into image history. | BUILDKIT-SECRETS | error (recommended; axis ships warn — escalate via `docker_severity_overrides`) | ✅ yes |
| `compose-version` | Remove deprecated `version:` top-level key in Compose files | Modern Compose spec discourages the version field; reliance on compose CLI version is the standard. | COMPOSE-SPEC | warn | ✅ yes |
| `oci-annotations` | Container labels include recommended OCI image annotations (`org.opencontainers.image.*`) | Standardized metadata (authors, source, description, licenses) improves container discoverability and compliance. | OCI-IMAGE-1.1.1 | warn | ⚠️ advisory (not yet checked by `omp_docker_audit.py`) |

> **Severity assignment**: `warn` is the default for audit rules (suggests best practice but does not block
> build). `error` is reserved for security-critical violations (e.g., secrets in history). `info` is rarely
> used (informational only, no action required). Projects can override severity in their own `rules.json`
> if domain-specific exceptions apply (see §3).

## 3. Domain exemptions (GUI, GPU, ROS, Simulation)

Strict security rules (e.g., `--privileged`, `--network host`, large shared memory, running as root) are
**justified in specific contexts**:

- **GUI containers** (X11, display forwarding) require host access to graphics devices.
- **GPU compute** (CUDA, ML training) often requires privileged access for device mapping.
- **ROS middleware** sometimes requires host networking for real-time performance or DDS discovery.
- **Simulation** (Gazebo, physics engines) may need large `--shm-size` allocations.

**Implementation**: Audit rules remain `warn`-only in the preset (do not block builds). Projects with these
requirements declare domain-specific `severity-override` entries in their own `rules.json`, suppressing or
escalating specific rule-ids on a project basis. The rule itself stays data-driven and auditable.

---

**Seed sources**: OCI Distribution & Image Specification standards, Docker BuildKit and Compose best practices,
and industry container security standards (NIST, CIS). This preset is **generic** — it does not assume a
specific registry, orchestrator, or deployment target. Framework-specific rules (Kubernetes CRDs, Helm,
Terraform) are added by supplementary presets and induced by `omp-learn` from actual usage.
