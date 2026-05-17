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

## CI

- Daily at 06:00 UTC: `make update` for every track in parallel; raw / normalized / scored / daily.md get committed.
- Monday at 08:00 UTC: `make weekly` generates the weekly digest.
- Push to `main`: `web/` is rebuilt and deployed to Pages.

## Local

```bash
pip install -r requirements.txt
make update                        # daily pipeline for all tracks
make -C tracks/iam weekly          # single track, weekly mode
cd web && npm install && npm run build
```

Python 3.12 / Node 22+ (Astro 6 requirement).

## Add a track or a deep-dive

```bash
make new-track NAME=eks
make new-deep-dive TRACK=iam TOPIC=roles-anywhere-spiffe
```

## License

MIT — see [LICENSE](./LICENSE).
