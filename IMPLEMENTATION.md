# GroupMark Implementation Plan

This plan builds GroupMark in three stages:

1. **MVP backend**: prove the core product works.
2. **Resume-worthy production version**: add cloud, CI/CD, S3, observability, and deployment.
3. **Very impressive version**: add advanced product features after the foundation is stable.

The main goal is to finish a backend-first app that you can explain deeply in interviews. Build the core workflow yourself, then use AI mainly for review, debugging, tests, and infrastructure guidance.

## Stage 1: MVP Backend

**Goal:** build the useful product core.

MVP includes:

- FastAPI backend
- PostgreSQL
- dbmate raw SQL migrations
- JWT authentication
- project workspaces
- members and roles
- task workflow
- comments
- contribution events
- contribution reports
- Docker Compose
- tests
- README and demo flow

MVP excludes:

- frontend
- S3 uploads
- email invitations
- Celery/Redis
- notifications
- AI summaries
- GitHub integration
- PDF export
- AWS deployment

## Day 1: Project Structure

Set up the backend project structure.

Target structure:

```text
app/
  main.py
  core/
    config.py
    security.py
    database.py
    exceptions.py
  api/
    deps.py
    routes/
      health.py
      auth.py
      projects.py
      members.py
      tasks.py
      comments.py
      events.py
      reports.py
  models/
  schemas/
  repositories/
  services/
migrations/
tests/
docs/
infra/
scripts/
.github/workflows/
Dockerfile
docker-compose.yml
.env.example
README.md
```

Deliverables:

- FastAPI app starts
- `GET /health` returns `{"status": "ok"}`
- `.gitignore` ignores `.venv`, `__pycache__`, `.env`, and Python cache files
- empty project directories are either populated or kept with placeholder files

## Day 2: Config, Database, And Migrations

Implement:

- centralized settings in `app/core/config.py`
- PostgreSQL connection in `app/core/database.py`
- `GET /ready` endpoint that checks database connectivity
- dbmate migration setup

Use dbmate raw SQL migrations.

Do not use Alembic.

Deliverables:

- `migrations/001_create_users.sql`
- local PostgreSQL connection configured
- `dbmate up` works
- `/ready` passes when DB is available
- `/ready` fails cleanly when DB is unavailable

## Day 3: Authentication

Implement routes:

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

Build:

- password hashing
- JWT creation
- JWT validation dependency
- current user dependency
- user schema and repository

Tests:

- register user
- duplicate email fails
- login succeeds
- invalid login fails
- protected route rejects missing token

## Day 4: Project Workspaces

Create tables:

```text
projects
project_members
```

Implement routes:

```text
POST   /projects
GET    /projects
GET    /projects/{project_id}
PATCH  /projects/{project_id}
DELETE /projects/{project_id}
```

Rules:

- creating a project also creates owner membership
- users only list projects they belong to
- only owners can delete projects
- inaccessible projects return `404`

Tests:

- create project
- list own projects
- cannot view project outside membership
- non-owner cannot delete project

## Day 5: Member Management

Implement routes:

```text
POST   /projects/{project_id}/members
GET    /projects/{project_id}/members
PATCH  /projects/{project_id}/members/{member_id}
DELETE /projects/{project_id}/members/{member_id}
```

MVP behavior:

- owner adds existing users by email
- owner can change role
- owner can remove members
- no email invite flow yet

Tests:

- owner adds member
- non-owner cannot add member
- viewer cannot add member
- owner changes role
- owner removes member

## Day 6: Permission Layer

Create reusable permission helpers.

Implement checks for:

```text
is_project_member
is_project_owner
can_view_project
can_update_project
can_manage_members
can_create_task
can_comment
can_generate_report
```

Rules:

- owner can manage project and members
- member can create tasks and comments
- viewer can read only
- users outside project get `404`

Tests:

- owner permissions
- member permissions
- viewer permissions
- outsider access blocked

## Day 7: Task CRUD

Create `tasks` table.

Implement routes:

```text
POST   /projects/{project_id}/tasks
GET    /projects/{project_id}/tasks
GET    /projects/{project_id}/tasks/{task_id}
PATCH  /projects/{project_id}/tasks/{task_id}
DELETE /projects/{project_id}/tasks/{task_id}
```

Support:

```text
title
description
status
priority
size
assigned_to
due_date
```

Tests:

- member creates task
- viewer cannot create task
- assigned user must be project member
- filter tasks by assignee
- filter tasks by status

## Day 8: Task Workflow

Implement routes:

```text
POST /projects/{project_id}/tasks/{task_id}/submit
POST /projects/{project_id}/tasks/{task_id}/approve
POST /projects/{project_id}/tasks/{task_id}/dispute
```

Workflow:

```text
todo -> in_progress -> review -> done
```

Rules:

- assignee can submit task for review
- owner or another member can approve
- user cannot approve their own task
- disputed tasks do not count as verified work

Tests:

- assignee submits task
- another member approves task
- self-approval fails
- disputed task is excluded from verified contribution

## Day 9: Task Comments

Create `task_comments` table.

Implement routes:

```text
POST   /projects/{project_id}/tasks/{task_id}/comments
GET    /projects/{project_id}/tasks/{task_id}/comments
PATCH  /projects/{project_id}/tasks/{task_id}/comments/{comment_id}
DELETE /projects/{project_id}/tasks/{task_id}/comments/{comment_id}
```

Rules:

- members can comment
- viewers can read comments
- authors can edit/delete their own comments

Tests:

- member adds comment
- viewer cannot add comment
- author edits comment
- other user cannot edit comment

## Day 10: Contribution Events

Create `contribution_events` table.

Automatically log:

```text
project_created
member_added
member_removed
member_role_changed
task_created
task_assigned
task_status_changed
task_submitted
task_approved
task_disputed
comment_added
```

Implement:

```text
GET /projects/{project_id}/events
```

Tests:

- project creation logs event
- task creation logs event
- task approval logs event
- outsiders cannot view events

## Day 11: Report Table And Basic Report Endpoint

Create `reports` table with JSONB report data.

Implement:

```text
POST /projects/{project_id}/reports
GET  /projects/{project_id}/reports/latest
GET  /projects/{project_id}/reports/{report_id}
```

Report should include:

- project summary
- member summaries
- task counts
- comment counts
- approval counts
- dispute counts

Tests:

- generate report
- latest report returns newest report
- report is stored as snapshot

## Day 12: Contribution Scoring

Implement MVP scoring.

Formula:

```text
Final Score =
0.50 * TaskDelivery
+ 0.20 * Collaboration
+ 0.15 * Reliability
+ 0.15 * ReviewActivity
```

Include:

- task size weights
- approved task ratio
- on-time completion
- comments, capped
- reviews given, capped

Tests:

- score with no assigned tasks
- score with approved tasks
- late task affects reliability
- comment spam is capped
- disputed tasks do not count as approved

## Day 13: Evidence-Based Report Details

Improve reports so they show evidence behind scores.

Per member, include:

```text
assigned tasks
approved tasks
incomplete tasks
late tasks
disputed tasks
comments added
reviews given
timeline events
score breakdown
```

Tests:

- report includes evidence
- report includes timeline
- score breakdown is explainable

## Day 14: MVP Test Hardening

Focus on tests and edge cases.

Add tests for:

- auth
- project access
- role permissions
- task workflow
- comments
- events
- reports
- scoring

Goal:

```text
pytest passes reliably against local PostgreSQL
```

## Day 15: Docker Compose Local Development

Set up:

```text
api
postgres
```

Deliverables:

- `docker compose up --build` starts app and DB
- app connects to Postgres through environment variables
- migrations can be run against compose DB
- README includes local Docker workflow

## Day 16: Demo Seed Script

Create:

```text
scripts/demo_seed.py
```

It should create:

- owner user
- member users
- viewer user
- project
- tasks
- comments
- submitted tasks
- approved tasks
- disputed task
- generated report

Goal:

```text
fresh local app -> seed data -> generate useful report
```

## Day 17: MVP Documentation

Update README with:

- what GroupMark does
- local setup
- env vars
- dbmate migration commands
- test commands
- Docker Compose commands
- API route summary
- demo flow

Add docs:

```text
docs/architecture.md
docs/scoring.md
```

## Day 18: MVP Freeze

No new features.

Do:

- fix bugs
- clean naming
- remove dead code
- improve error responses
- verify fresh setup
- verify tests
- verify demo script

MVP complete when:

```text
user registers -> creates project -> adds members -> creates tasks -> submits/approves work -> comments -> generates contribution report
```

## Stage 2: Resume-Worthy Production Version

**Goal:** make the project production-style and cloud-deployable.

Adds:

- structured logging
- CI
- Docker build checks
- S3 file evidence uploads
- Terraform AWS infrastructure
- ECS Fargate deployment
- RDS PostgreSQL
- CloudWatch logs and alarms
- security scanning
- deployment docs

## Day 19: Structured Logging And Error Handling

Add:

- JSON logs
- request ID middleware
- consistent error responses
- safe logging for auth and permission failures

Do not log:

- passwords
- JWTs
- secrets
- full authorization headers

## Day 20: CI Basics

Create:

```text
.github/workflows/ci.yml
```

Run:

- install dependencies
- formatting check
- linting
- tests

Recommended tools:

```text
ruff
pytest
```

## Day 21: CI With PostgreSQL And Migrations

Improve CI:

- add PostgreSQL service container
- run `dbmate up`
- run tests against PostgreSQL
- verify migrations work from scratch

## Day 22: Docker Build And Security Scan In CI

Add:

- Docker build verification
- Trivy filesystem or image scan

Goal:

```text
PR checks prove the app installs, migrates, tests, builds, and scans
```

## Day 23: File Metadata Model

Create `files` table.

Fields:

```text
id
project_id
task_id
uploaded_by
filename
s3_key
content_type
file_size_bytes
created_at
```

Add repository and service layer.

## Day 24: Storage Abstraction

Create storage layer:

```text
app/storage/base.py
app/storage/local.py
app/storage/s3.py
```

Use local/mock storage in tests and development.

Do not require AWS credentials for local tests.

## Day 25: S3 Presigned Upload Flow

Implement routes:

```text
POST /projects/{project_id}/files/presign-upload
POST /projects/{project_id}/files/confirm-upload
GET  /projects/{project_id}/files
GET  /projects/{project_id}/files/{file_id}/download-url
DELETE /projects/{project_id}/files/{file_id}
```

Rules:

- users must be project members
- viewers cannot upload
- files may link to tasks
- uploaded files create `file_uploaded` contribution events

## Day 26: File Evidence In Reports

Add evidence score to reports.

Updated formula:

```text
Final Score =
0.45 * TaskDelivery
+ 0.20 * Evidence
+ 0.15 * Collaboration
+ 0.10 * Reliability
+ 0.10 * ReviewActivity
```

Tests:

- file uploads affect evidence score
- evidence score is capped
- linked task files appear in report

## Day 27: Production Dockerfile

Improve Dockerfile:

- slim Python base image
- no dev-only files in image where practical
- non-root user
- production uvicorn command
- environment-based config

## Day 28: Terraform Foundation

Create:

```text
infra/main.tf
infra/variables.tf
infra/outputs.tf
```

Add:

- AWS provider
- ECR repository
- S3 evidence bucket
- CloudWatch log group
- basic IAM roles

Keep Terraform flat.

## Day 29: RDS PostgreSQL

Add Terraform for:

- RDS PostgreSQL
- database subnet group if needed
- database security group
- generated or provided DB password
- Secrets Manager or SSM parameter storage

Document required variables.

## Day 30: ECS Fargate And ALB

Add Terraform for:

- ECS cluster
- ECS task definition
- ECS service
- Application Load Balancer
- target group
- app security group
- task execution role

Container config should include:

```text
DATABASE_URL
JWT_SECRET_KEY
S3_BUCKET_NAME
ENVIRONMENT=production
```

## Day 31: Deployment Workflow

Create:

```text
.github/workflows/deploy.yml
```

On merge to `main`:

1. Build Docker image.
2. Tag with commit SHA.
3. Push to ECR.
4. Update ECS task definition.
5. Deploy ECS service.
6. Verify `/health`.
7. Verify `/ready`.

## Day 32: CloudWatch Logs

Verify logs appear in CloudWatch.

Log fields:

```text
request_id
route
method
status_code
duration_ms
user_id where safe
project_id where safe
```

## Day 33: CloudWatch Alarms

Add basic alarms:

- unhealthy ECS tasks
- high ALB 5xx responses
- high target response time

Keep alarms simple.

## Day 34: Security Pass

Add or verify:

- no secrets committed
- `.env.example` is safe
- Trivy scan works
- auth errors do not leak information
- project-scoped resources return `404` for outsiders
- CORS config is environment-based

## Day 35: Production Documentation

Write:

```text
docs/architecture.md
docs/deployment.md
docs/security.md
docs/runbook.md
docs/scoring.md
```

Cover:

- architecture
- local setup
- AWS deployment
- secrets
- migrations
- report scoring
- operational runbook

## Day 36: End-To-End Local Validation

From a clean setup:

1. Start Docker Compose.
2. Run `dbmate up`.
3. Run tests.
4. Run seed script.
5. Generate report.
6. Upload or mock evidence file.
7. Confirm report includes evidence.

Fix friction immediately.

## Day 37: End-To-End AWS Validation

Verify:

- Terraform apply succeeds
- ECS service starts
- RDS connection works
- S3 presigned upload flow works
- `/health` works
- `/ready` works
- logs appear in CloudWatch
- deployment workflow works

## Day 38: README And Portfolio Polish

Update README with:

- project overview
- architecture diagram
- endpoint examples
- local setup
- Docker setup
- testing
- AWS deployment
- demo user journey
- sample report JSON
- known tradeoffs

## Day 39: Production Bug Fix Day

Fix:

- failing tests
- flaky CI
- unclear docs
- rough error responses
- deployment gaps

No new features.

## Day 40: Resume-Worthy Freeze

Final checks:

- app works locally
- tests pass
- CI passes
- Docker works
- AWS deploy works
- S3 file flow works
- reports are useful
- docs explain the project clearly

This is the resume-ready version.

## Stage 3: Very Impressive Version

**Goal:** add standout features after the production version is stable.

## Day 41: Invitation Tokens

Add:

```text
POST /projects/{project_id}/invitations
POST /invitations/{token}/accept
POST /invitations/{token}/decline
```

Rules:

- tokens expire
- owners create invites
- accepted invites create membership

## Day 42: Email Invitations

Add email sending for invitations.

Local behavior:

- log email contents
- do not require real provider

Production later:

- AWS SES or another provider

## Day 43: In-App Notifications

Create `notifications` table.

Routes:

```text
GET   /notifications
PATCH /notifications/{notification_id}/read
```

Generate notifications for:

- added to project
- task assigned
- task commented
- task approved
- report generated

## Day 44: Reminder Jobs

Add scheduled reminders for:

- overdue tasks
- tasks due soon
- project due soon

Use a simple scheduled command first. Deploy as ECS scheduled task with EventBridge later.

## Day 45: CSV Report Export

Add:

```text
GET /projects/{project_id}/reports/{report_id}/export.csv
```

CSV is practical and easier than PDF.

## Day 46: PDF Report Export

Add PDF export only after CSV works.

Keep formatting simple:

- project summary
- member score table
- evidence details
- generated timestamp

## Day 47: External Evidence Links

Add generic evidence links:

```text
GitHub PR
Google Doc
Figma
Moodle submission
meeting notes
```

Generic links are more useful than GitHub-only support.

## Day 48: GitHub Evidence Integration

Optional integration:

- link commit or PR to a task
- store metadata
- count linked PRs as evidence

Do this only after generic evidence links work.

## Day 49: Peer Review

Add private peer ratings.

Rating categories:

- reliability
- communication
- quality of work

Keep peer review weight low because it can be biased.

## Day 50: Anti-Gaming Rules

Add safeguards:

- comment score cap
- evidence score cap
- large task requires evidence
- late activity warning
- disputed work excluded
- self-approval blocked

## Day 51: Report Locking

Add:

```text
POST /projects/{project_id}/reports/{report_id}/lock
```

Rules:

- only owner can lock
- locked report cannot be regenerated in place
- new report version can be created if needed

## Day 52: Audit Logs

Create `audit_logs` table for security-sensitive actions:

- login failed
- member removed
- role changed
- project archived
- report locked
- invite accepted

Keep contribution events for product activity. Use audit logs for security and administration.

## Day 53: Admin Observability API

Add admin-only endpoints:

```text
GET /admin/stats
GET /admin/recent-audit-logs
GET /admin/recent-errors
```

Do not build a full admin dashboard unless you also build a frontend.

## Day 54: Load Testing

Add a small load test script for:

- login
- list projects
- list tasks
- generate report

Document rough results and bottlenecks.

## Day 55: Performance Pass

Review:

- indexes
- slow report queries
- N+1 query patterns
- pagination
- event timeline queries

Add indexes where needed.

## Day 56: Final Portfolio Polish

Finalize:

- README
- architecture diagram
- API examples
- demo script
- sample report
- deployment guide
- runbook
- resume bullets

## Final Recommended Scope

If time is limited, stop at Stage 2. That is already a strong resume project.

Do not start Stage 3 until:

- MVP is complete
- tests are passing
- Docker works
- CI works
- AWS deployment works
- reports are actually useful

The project is impressive because it combines:

- real user pain
- multi-user permissions
- backend-heavy product logic
- contribution scoring
- evidence tracking
- PostgreSQL
- raw SQL migrations
- tests
- Docker
- AWS deployment
- Terraform
- CI/CD
- observability

