# AWS Explore

AWS Explore is a Django dashboard that combines:

- AWS Cost Explorer data (cost + usage by service/region)
- Resource scanner output (currently EC2 running instances)

It helps you answer:

- Which AWS services were active in the last 30 days?
- How much did each service cost (MTD)?
- Is there usage even when cost is near zero?
- Which services have scanner coverage vs billing-only visibility?

## Current Feature Set

- Cost Explorer query for last 30 days (`UnblendedCost`, `UsageQuantity`)
- Service-level and region-level aggregation
- Dashboard KPIs:
  - Total MTD cost
  - Active services
  - Scanned services
  - Services with usage
  - Billing-only services
  - Resources found
- Filter/search/sort in UI
- Service details table with:
  - Cost (MTD)
  - Usage (MTD)
  - Coverage status
  - Regions
  - Resource links (for scanned services)

## Tech Stack

- Python 3.11+
- Django 6
- boto3
- django-tailwind
- SQLite (default local DB)
- PostgreSQL (Docker Compose sidecar)

## Project Structure

- `/Users/akash/vscodeprojects/aws-explore/web/` - dashboard views/templates
- `/Users/akash/vscodeprojects/aws-explore/scanner/` - AWS scanners and Cost Explorer integration
- `/Users/akash/vscodeprojects/aws-explore/theme/` - Tailwind setup and compiled CSS
- `/Users/akash/vscodeprojects/aws-explore/aws_explore/` - Django project config

## Prerequisites

1. AWS account with Cost Explorer enabled.
2. Valid AWS credentials (profile or static env keys).
3. Node.js + npm for Tailwind build.
4. Python virtual environment.

## Required AWS Permissions

Minimum read permissions used by current code:

- `ce:GetCostAndUsage`
- `sts:GetCallerIdentity`
- `ec2:DescribeInstances` (for EC2 scanner/resource listing)

## Environment Configuration

Copy `.env.example` to `.env.local` and fill values.

Example variables:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

# Database config
DB_ENGINE=sqlite
POSTGRES_DB=aws_explore
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5455

AWS_PROFILE=default
AWS_REGION=us-east-1

# Optional static credentials (if not using profile)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_SESSION_TOKEN=
```

Notes:

- If `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are set, they are preferred.
- Otherwise boto3 default credential chain/profile is used.
- Database mode:
  - `DB_ENGINE=sqlite` for local default
  - `DB_ENGINE=postgres` for PostgreSQL
- Never commit real credentials to git.

## Local Setup

1. Create and activate a virtual environment.
2. Install Python dependencies.
3. Install Tailwind dependencies.
4. Apply migrations.

```bash
cd /Users/akash/vscodeprojects/aws-explore

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd theme/static_src
npm install
cd ../..

python manage.py migrate
```

## Running the App

### Option A: Development with Tailwind watcher

Terminal 1:

```bash
cd /Users/akash/vscodeprojects/aws-explore
python manage.py tailwind start
```

Terminal 2:

```bash
cd /Users/akash/vscodeprojects/aws-explore
python manage.py runserver
```

Open: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Option B: Build CSS once + run server

```bash
cd /Users/akash/vscodeprojects/aws-explore/theme/static_src
npm run build

cd /Users/akash/vscodeprojects/aws-explore
python manage.py runserver
```

## Docker

This repository includes:

- `/Users/akash/vscodeprojects/aws-explore/Dockerfile`
- `/Users/akash/vscodeprojects/aws-explore/docker-compose.yml`

The Docker image:

- Builds Tailwind CSS in a Node build stage.
- Runs Django in a Python runtime stage.
- Applies migrations and `collectstatic` on startup.
- Starts Gunicorn (not Django dev server) on port `8000`.

The Docker Compose stack includes:

- `web` (Django app)
- `db` (PostgreSQL sidecar, `postgres:16-alpine`)

### Run with Docker Compose

1. Ensure `.env.local` exists (copy from `.env.example` if needed).
2. Build and start:

```bash
cd /Users/akash/vscodeprojects/aws-explore
docker compose up --build
```

Open: [http://127.0.0.1:8000](http://127.0.0.1:8000)

### Stop

```bash
cd /Users/akash/vscodeprojects/aws-explore
docker compose down
```

Note:

- Compose runs Django with `DB_ENGINE=postgres`.
- Postgres data is persisted in the named volume `postgres_data`.

## How to Read Dashboard Data

### Why cost can show `0.00`

- Service had usage but no billable amount (free tier/credits).
- Billable value is very small and rounds to 2 decimals.
- Control-plane/global service activity may not produce direct service spend.

### Why usage unit can show `N/A`

This comes from AWS Cost Explorer for `UsageQuantity` when usage cannot be represented by one clean unit at that grouping level (mixed usage types/units).

### Coverage Status

- `Scanned`: Service has a scanner implementation and resource metadata is fetched.
- `Billing Only`: Service appears in billing, but no scanner exists yet.

## Extending Scanner Coverage

Only EC2 scanner is implemented right now.

To add scanner support for another service:

1. Create a scanner under `/Users/akash/vscodeprojects/aws-explore/scanner/services/`.
2. Subclass `ServiceScanner`.
3. Register with `@ScannerFactory.register("<Exact Cost Explorer Service Name>")`.
4. Implement `list_resources(regions=...)`.
5. Import scanner so registration occurs (similar to EC2 import in view/app startup).

## Troubleshooting

### `Valid AWS credentials not found`

- Check `.env.local` values.
- Confirm `AWS_PROFILE` exists in `~/.aws/config` and credentials.
- Run `aws sts get-caller-identity` with same profile.

### Empty dashboard / no services

- Verify Cost Explorer is enabled in the account.
- Ensure selected account actually has activity in last 30 days.
- Confirm `ce:GetCostAndUsage` permission.

### UI looks unstyled

- Rebuild CSS:

```bash
cd /Users/akash/vscodeprojects/aws-explore/theme/static_src
npm run build
```

- For live updates, run `python manage.py tailwind start`.

## Useful Commands

```bash
cd /Users/akash/vscodeprojects/aws-explore
python manage.py check
python manage.py migrate
python manage.py runserver
```

## Future Development Notes

### Not Implemented Yet

- Scanner coverage for services beyond EC2 (for example S3, RDS, Lambda, ECS, EKS, ELB).
- Daily/weekly cost trend charts (currently focused on MTD aggregates).
- Budget/anomaly alerting and threshold notifications.
- Auth/RBAC for multi-user access and account-level permissions.
- Export/reporting (CSV/PDF or scheduled summaries).

### Planned Next

- Add scanner modules for top billed services first (S3, RDS, Lambda).
- Add time-series view with Cost Explorer daily granularity.
- Add service-level drilldown page with usage-by-unit breakdown.
- Improve error observability for scanner failures and AWS API permission gaps.
- Add tests for scanner aggregation and dashboard filtering/sorting logic.

### Good To Have

- Multi-account support (AWS Organizations / assume-role workflows).
- Cost optimization recommendations (idle resources, rightsizing hints).
- Tag-based cost slicing (team, environment, project).
- Caching layer for Cost Explorer responses to reduce API latency/cost.
- Background jobs for periodic scans instead of request-time scanning.
- CI pipeline with lint/test/build and container image publish.

## License

This project is licensed under the Apache License 2.0.
See `/Users/akash/vscodeprojects/aws-explore/LICENSE`.
