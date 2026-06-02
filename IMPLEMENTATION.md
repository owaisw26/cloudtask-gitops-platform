# CloudOps Event Platform Implementation Timeline

CloudOps Event Platform is a backend-only cloud and data engineering platform for ingesting, storing, archiving, and analysing operational events from software services.

The final project should prove that you can build a production-style backend and data platform, deploy it on AWS, automate infrastructure with Terraform, run CI/CD with GitHub Actions, manage secrets securely, store and process event data, generate analytics, and monitor the system with CloudWatch.

This timeline is designed for 28 days. The goal is not to build every possible feature, but to finish a resume-ready vertical slice with strong backend, data engineering, cloud, and DevOps signals.

## Project Scope

Core event types:

```text
deployment_started
deployment_succeeded
deployment_failed
incident_created
incident_resolved
health_check_failed
health_check_recovered
```

Core resources:

```text
User
Service
Event
DeadLetterEvent
DailyServiceMetrics
```

Core API features:

- JWT authentication
- service management
- operational event ingestion
- event validation
- idempotency keys to prevent duplicate event processing
- event querying and filtering
- invalid event handling through a dead-letter table
- health and readiness endpoints
- analytics endpoints for deployment failure rate, incident trends, service health, and daily service metrics

Data engineering layer:

- valid events are stored in PostgreSQL for normal application queries
- raw event payloads are archived to S3 using partitioned paths
- invalid events are recorded in a dead-letter table
- a scheduled aggregation job calculates daily metrics per service
- a backfill command can recompute metrics for a historical date range
- aggregated metrics are stored in `daily_service_metrics` and exposed through analytics endpoints

Cloud infrastructure:

- FastAPI app containerised with Docker
- PostgreSQL deployed using AWS RDS
- raw event archive stored in Amazon S3
- app deployed to AWS ECS Fargate
- Docker images stored in Amazon ECR
- infrastructure provisioned with Terraform
- secrets stored in AWS Secrets Manager or SSM Parameter Store
- logs sent to CloudWatch
- scheduled aggregation job triggered using EventBridge Scheduler
- application exposed through an Application Load Balancer

CI/CD:

- pull requests run tests, linting, formatting checks, Docker build verification, and security scans
- merges to `main` build and push Docker images to ECR, then deploy to ECS
- deployments update ECS and verify health checks

## Recommended Repository Structure

```text
cloudtask-gitops-platform/
  app/
    main.py
    config.py
    database.py
    auth/
    service_catalog/
    events/
    analytics/
    jobs/
    storage/
  migrations/
  tests/
  infra/
    main.tf
    variables.tf
    outputs.tf
  scripts/
    demo_seed_events.py
  docs/
    architecture.md
    deployment.md
    data-pipeline.md
    runbook.md
    security.md
  .github/
    workflows/
      ci.yml
      deploy.yml
  Dockerfile
  docker-compose.yml
  README.md
```

## Week 1: Backend Foundation

### Day 1: Project Setup

Set up the repository structure.

Deliverables:

- Python environment
- FastAPI installed
- initial app package
- `tests/` directory
- `migrations/` directory
- `infra/` directory
- `docs/` directory
- `.github/workflows/` directory
- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- initial `README.md`

End the day with this endpoint working locally:

```text
GET /health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Day 2: Configuration, Database, Migrations

Build the backend foundation.

Implement:

- environment-based config
- PostgreSQL database connection
- database session handling
- dbmate raw SQL migration setup
- initial `users` table
- readiness endpoint that checks database connectivity

Endpoints:

```text
GET /health
GET /ready
```

Deliverables:

- local PostgreSQL works through Docker Compose
- migrations can be applied from scratch
- readiness fails when the database is unavailable
- tests for health and readiness

Migration guidance:

- keep migrations as raw SQL files in `migrations/`
- use `dbmate` for migrations
- do not use Alembic
- make the same migration command work locally, in CI, and before deployment

Example migration file shape:

```sql
-- migrate:up
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- migrate:down
DROP TABLE users;
```

Expected migration command:

```bash
dbmate up
```

### Day 3: Authentication

Implement JWT authentication.

Endpoints:

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

Build:

- password hashing
- JWT creation
- JWT validation dependency
- user creation
- current user lookup
- auth tests

Rules:

- never store plaintext passwords
- never return password hashes in API responses
- protected routes must reject missing or invalid tokens

### Day 4: Service Management

Implement service CRUD.

Resource:

```text
Service
```

Endpoints:

```text
POST   /services
GET    /services
GET    /services/{service_id}
PATCH  /services/{service_id}
DELETE /services/{service_id}
```

Rules:

- services belong to users
- users can only access their own services
- service names should be unique per user
- return `404` when a service does not exist or does not belong to the current user

Add tests for ownership isolation.

### Day 5: Event Model and Ingestion Skeleton

Create event tables.

Tables:

```text
events
dead_letter_events
```

Implement the first ingestion endpoint:

```text
POST /services/{service_id}/events
```

Validation requirements:

- valid event type
- valid timestamp
- valid payload shape
- service exists and belongs to the authenticated user

Dead-letter guidance:

- malformed event payloads from authorized requests should be stored in `dead_letter_events`
- unauthorized requests should return `401` or `404` and should not be stored as dead-letter events

Do not add S3 yet. Make database ingestion reliable first.

### Day 6: Idempotency and Dead-Letter Handling

Add idempotency and invalid event handling.

Implement:

- `Idempotency-Key` header
- unique constraint per service and idempotency key
- duplicate submissions do not create duplicate events
- invalid event payloads are recorded in `dead_letter_events`

Expected behavior:

```text
valid authorized event -> events table
invalid authorized event payload -> dead_letter_events table
unauthorized request -> rejected, not dead-lettered
duplicate event -> no duplicate processing
```

Add tests for:

- duplicate idempotency keys
- invalid event type
- invalid payload
- inaccessible service

### Day 7: Event Querying

Implement event history APIs.

Endpoints:

```text
GET /services/{service_id}/events
GET /events
```

Filters:

```text
event_type
service_id
start_date
end_date
limit
offset
```

Deliverables:

- pagination
- date filtering
- event type filtering
- ownership-safe queries
- tests for event filtering

By the end of Week 1, the project should have a strong backend core.

## Week 2: Data Engineering and Analytics

### Day 8: S3 Storage Abstraction

Create a storage layer.

Files:

```text
app/storage/s3.py
app/storage/local.py
```

Use an interface-like boundary so local development can write archived payloads to disk while production writes to S3. Build local storage first, then wire in real S3 once the AWS infrastructure exists.

Archive path format:

```text
raw/year=2026/month=06/day=02/service=payments-api/event-id.json
```

Deliverables:

- raw event archive path generator
- local storage implementation
- S3 client wrapper stub or interface
- tests can mock storage

### Day 9: Integrate Archival With Ingestion

Wire storage into event ingestion.

Ingestion flow:

1. Validate event.
2. Store valid event in PostgreSQL.
3. Archive raw payload.
4. Store archive path and archive status.
5. Return event response.

Recommended event fields:

```text
archive_status = pending | archived | failed
archive_path
```

Failure behavior:

- if the database write fails, the request fails
- if archival fails, mark the event `archive_status` as `failed` and log the failure

For resume quality, preserve the event even if S3 archival fails.

### Day 10: Daily Metrics Table

Create:

```text
daily_service_metrics
```

Suggested fields:

```text
id
service_id
metric_date
deployment_count
deployment_success_count
deployment_failure_count
incident_count
incident_resolved_count
health_check_failure_count
health_check_recovery_count
created_at
updated_at
```

Add a unique constraint:

```text
service_id + metric_date
```

### Day 11: Aggregation Job

Implement scheduled aggregation logic.

File:

```text
app/jobs/aggregate_daily_metrics.py
```

Command:

```bash
python -m app.jobs.aggregate_daily_metrics --date 2026-06-02
```

Requirements:

- calculate daily metrics from the `events` table
- upsert into `daily_service_metrics`
- be safe to re-run
- log the date and number of services processed
- include tests with sample events

### Day 12: Backfill Command

Implement historical recomputation.

Command:

```bash
python -m app.jobs.backfill_metrics --start-date 2026-06-01 --end-date 2026-06-30
```

Rules:

- loop by date
- call the same aggregation logic used by the daily job
- overwrite or recompute existing metrics safely
- log progress clearly

### Day 13: Analytics Endpoints

Build analytics APIs.

Endpoints:

```text
GET /analytics/services/{service_id}/daily-metrics
GET /analytics/services/{service_id}/deployment-failure-rate
GET /analytics/services/{service_id}/incident-trends
GET /analytics/services/{service_id}/health
```

Support date ranges:

```text
?start_date=2026-06-01&end_date=2026-06-30
```

Where possible, analytics should use `daily_service_metrics` rather than scanning raw events.

### Day 14: Test Hardening

Focus on test coverage.

Add or improve tests for:

- auth
- service ownership
- valid event ingestion
- invalid event dead-lettering
- idempotency
- event filtering
- archive path generation
- archive failure handling
- daily aggregation
- backfill
- analytics endpoints

By the end of Week 2, the app should be locally impressive and data-focused.

## Week 3: Docker, CI/CD, Terraform

### Day 15: Dockerize the App

Create a production-oriented Dockerfile.

Requirements:

- slim Python base image
- dependencies installed cleanly
- app runs with Uvicorn or Gunicorn/Uvicorn workers
- exposes port `8000`
- avoids committing secrets

Update Docker Compose:

```text
api
postgres
```

Add README commands:

```bash
docker compose up --build
```

### Day 16: Linting, Formatting, CI

Create:

```text
.github/workflows/ci.yml
```

Run on pull requests:

- install dependencies
- run formatting check
- run linting
- run tests
- build Docker image

Suggested tools:

```text
ruff
pytest
trivy
```

Keep CI simple and reliable before making it advanced.

### Day 17: Security Scan and Test Database in CI

Improve CI with a real database.

Add:

- PostgreSQL service container
- migration step
- test execution against PostgreSQL
- Trivy filesystem or image scan

Deliverable:

- PR checks prove the app can install, migrate, test, and build

### Day 18: Terraform Foundation

Start AWS infrastructure in `infra/`.

Define:

- AWS provider
- variables
- outputs
- ECR repository
- S3 bucket for raw events
- S3 bucket name output for application config
- IAM basics
- VPC setup, or default VPC if you want to keep the scope smaller

Keep Terraform flat at first with `main.tf`, `variables.tf`, and `outputs.tf`. Add modules only if the infrastructure becomes hard to maintain.

At this point, replace the local-only archive implementation with the real S3 storage implementation for production config.

### Day 19: RDS and Secrets

Add:

- RDS PostgreSQL
- database security group
- app security group
- Secrets Manager or SSM parameters
- database credentials
- application environment variables

Deliverables:

- Terraform can provision database resources
- secrets are not committed to git
- documentation explains required variables

### Day 20: ECS Fargate and ALB

Add:

- ECS cluster
- task definition
- ECS service
- Application Load Balancer
- target group
- CloudWatch log group

Container environment should include:

```text
DATABASE_URL
JWT_SECRET_KEY
S3_BUCKET_NAME
ENVIRONMENT=production
```

Deliverable:

- Terraform can create the deployable runtime environment

### Day 21: Deploy Workflow

Create:

```text
.github/workflows/deploy.yml
```

On merge to `main`:

1. Build Docker image.
2. Tag it with the commit SHA.
3. Push it to ECR.
4. Update the ECS task definition.
5. Deploy the ECS service.
6. Verify `/health`.
7. Verify `/ready`.

By the end of Week 3, the project should be deployable.

## Week 4: Production Polish and Resume Readiness

### Day 22: EventBridge Scheduled Job

Add scheduled aggregation.

Recommended approach:

- use the same Docker image
- run a different command for the aggregation job
- trigger it with EventBridge Scheduler

Command:

```bash
python -m app.jobs.aggregate_daily_metrics --date yesterday
```

Terraform should define:

- scheduler
- IAM role
- ECS task invocation permissions

### Day 23: CloudWatch Logs and Alarms

Add basic observability.

Implement:

- structured JSON logs
- request id or correlation id
- useful ingestion logs
- aggregation job logs
- clear error logs without secrets

Terraform alarms:

- unhealthy ECS tasks
- high ALB 5xx responses
- optional high target response time

### Day 24: Documentation Pass 1

Write project documentation.

Files:

```text
docs/architecture.md
docs/data-pipeline.md
docs/deployment.md
docs/security.md
docs/runbook.md
```

Cover:

- system architecture
- request flow
- event ingestion pipeline
- S3 archive layout
- metric aggregation
- deployment process
- secrets handling
- operational runbook

### Day 25: Demo Data and API Examples

Create:

```text
scripts/demo_seed_events.py
```

It should:

- create demo services
- submit deployment events
- submit incident events
- submit health check events
- generate enough data for analytics

Add README examples using `curl`.

Demo flow:

```text
register user
login
create service
submit events
run aggregation
query analytics
```

### Day 26: End-to-End Local Validation

Run the full system locally from scratch.

Checklist:

- clone fresh or clean local setup
- copy `.env.example`
- start Docker Compose
- run migrations
- run tests
- seed demo data
- run aggregation
- query analytics

Fix any setup friction immediately. A resume project is much stronger when someone else can run it without guessing.

### Day 27: Cloud Deployment Validation

Deploy to AWS and verify.

Checklist:

- Terraform apply succeeds
- GitHub Actions deploy succeeds
- ECS task becomes healthy
- ALB responds
- `/health` works
- `/ready` works
- events can be ingested
- raw event appears in S3
- metrics job runs
- analytics endpoint returns data
- logs appear in CloudWatch
- alarms exist

Save useful screenshots or command outputs for portfolio notes.

### Day 28: Resume and Portfolio Polish

Make the project presentable.

Finalize:

- README
- architecture diagram
- endpoint list
- local setup instructions
- deployment setup instructions
- CI/CD explanation
- security notes
- runbook
- known tradeoffs

Resume bullet examples:

```text
Built a production-style FastAPI event platform for ingesting, archiving, and analysing operational service events using PostgreSQL, S3, ECS Fargate, Terraform, and GitHub Actions.
```

```text
Implemented JWT authentication, idempotent event ingestion, dead-letter handling, scheduled metric aggregation, analytics endpoints, Dockerized local development, CI checks, ECR/ECS deployment automation, and CloudWatch monitoring.
```

## Must-Have Scope If You Fall Behind

Prioritize these features:

```text
FastAPI backend
JWT auth
service CRUD
event ingestion
idempotency
dead-letter table
PostgreSQL
daily metrics aggregation
analytics endpoints
Docker Compose
tests
README
```

These features make the project resume-ready even before AWS deployment is perfect.

## Strong Resume Additions

Add these after the must-have scope is stable:

```text
S3 archival
Terraform
ECS Fargate
GitHub Actions deploy
CloudWatch logs and alarms
EventBridge scheduled aggregation
Trivy security scanning
```

## Features You Can Simplify

If time gets tight, simplify:

```text
advanced Terraform modules
multiple AWS environments
complex IAM boundaries
full alerting suite
very high test coverage everywhere
advanced analytics beyond daily metrics
```

## Final Success Criteria

By the end, the project should demonstrate this complete flow:

1. A user registers and logs in.
2. The user creates a service.
3. The user submits operational events.
4. Valid events are stored in PostgreSQL.
5. Raw payloads are archived to S3 or local storage in development.
6. Invalid events are saved to the dead-letter table.
7. Duplicate submissions are prevented with idempotency keys.
8. A daily aggregation job calculates reliability metrics.
9. Analytics endpoints expose deployment, incident, and health metrics.
10. The app runs locally with Docker Compose.
11. Tests and scans run in GitHub Actions.
12. Terraform provisions the AWS infrastructure.
13. The app deploys to ECS Fargate.
14. Logs and basic alarms are visible in CloudWatch.
