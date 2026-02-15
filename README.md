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

## License

This project is licensed under the Apache License 2.0.
See `/Users/akash/vscodeprojects/aws-explore/LICENSE`.
