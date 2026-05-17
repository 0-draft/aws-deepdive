# aws-deepdive

Weekly AWS digests and topic deep-dives. GitHub Actions collects daily, builds a digest every Monday, and ships the result to GitHub Pages.

Primary focus is identity / auth (IAM Roles Anywhere, IAM Identity Center, STS, SCPs, workload identity). Security bulletins, cloud-wide What's New, and the AWS SDK / CLI release stream ride along.

Site: <https://0-draft.github.io/aws-deepdive/>

## Tracks

| Track       | Scope                                                                         |
| ----------- | ----------------------------------------------------------------------------- |
| `iam`       | IAM Roles Anywhere / Identity Center / STS / SCP / workload identity / SPIFFE |
| `security`  | Security Bulletins / GuardDuty / Inspector / Macie / KMS                      |
| `whats-new` | Cloud-wide What's New (filtered down once the other tracks have claimed)      |
| `releases`  | GitHub Releases for aws-cli / aws-cdk / aws-sdk-* / aws-sam-cli               |

## Pipeline

```text
collect (RSS + GitHub Releases) → normalize → score → report (daily | weekly)
```

Score = `freshness × keyword × source-weight × severity`. Items below the threshold stay in `normalized.json` but are not surfaced in the report.

## Layout

```text
Makefile                           # delegates to each track (matrix in CI)
scripts/
  awsdd/                           # shared Python package (collect/normalize/score/report)
  {new-track,new-deep-dive,prune}.sh
templates/                         # scaffolds for new tracks and deep-dives
tracks/<name>/
  Makefile                         # identical across tracks; derives name from CURDIR
  config/sources.yaml              # RSS feeds, GitHub repos, keywords, weights
  data/{raw/, normalized.json, scored.json}
  reports/{daily,weekly}/<date>.md
  deep-dives/<topic>.md
.github/workflows/
  daily-update.yml                 # 06:00 UTC, matrix.track
  weekly-digest.yml                # Mon 08:00 UTC
  deploy-pages.yml                 # push to main → Pages
  pr-checks.yml
web/                               # Astro 6 + Tailwind v4 + recharts (React island)
```

## Local

```bash
make dev-install                   # runtime + dev deps
make test                          # pytest + coverage
make lint                          # ruff check
make format                        # ruff format
make audit                         # pip-audit + npm audit (production deps)

make update                        # daily pipeline for all tracks (hits network)
make -C tracks/iam weekly          # single track, weekly mode
cd web && npm install && npm run build
```

Python 3.12 / Node 22+ (Astro 6 requirement).

## CI

| Workflow             | Trigger                                | Purpose                                                                  |
| -------------------- | -------------------------------------- | ------------------------------------------------------------------------ |
| `ci.yml`             | PR + push to `main` (code paths only)  | ruff, astro check, markdownlint, actionlint, pytest+coverage, builds     |
| `codeql.yml`         | PR + push to `main` + weekly cron      | CodeQL SAST for Python and TS/JS                                         |
| `audit.yml`          | weekly cron + manual + deps PR         | `pip-audit`, `npm audit --audit-level=high`, license report (copyleft gate) |
| `daily-update.yml`   | 06:00 UTC cron                         | per-track collect / score / report; commits artefacts to `main`          |
| `weekly-digest.yml`  | Mon 08:00 UTC cron                     | per-track weekly digest; commits artefact to `main`                      |
| `deploy-pages.yml`   | push to `main` (web/, tracks/ changes) | builds `web/dist` and publishes to GitHub Pages                          |

PRs into `main` should be gated by branch protection requiring `ci.yml` jobs to pass. Configure once in repo Settings → Branches.

`pre-commit` config at [`.pre-commit-config.yaml`](./.pre-commit-config.yaml) covers ruff, markdownlint, actionlint, and basic hygiene hooks. Opt-in for contributors (`pre-commit install`).

## Add a track or a deep-dive

```bash
make new-track NAME=eks
make new-deep-dive TRACK=iam TOPIC=roles-anywhere-spiffe
```

## License

MIT — see [LICENSE](./LICENSE).
