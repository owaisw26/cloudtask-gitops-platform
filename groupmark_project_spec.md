# GroupMark Project Specification

## 1. Overview

**Project name:** GroupMark

**Full name:** GroupMark — Group Assignment Accountability Platform

**One-liner:**

GroupMark is a production-ready backend platform that helps university students manage group assignments, track contribution evidence, and generate structured peer-review contribution reports.

The app is not trying to replace Notion, Trello, Google Drive, Moodle, or a calendar. It solves a narrower problem:

> Who actually contributed to this group assignment, and what evidence supports that?

GroupMark gives each group project a structured workspace where members, tasks, comments, approvals, evidence, and contribution events are recorded. At the end of the assignment, the system generates a report based on recorded activity.

## 2. Core Problem

University group assignments often suffer from:

- unclear task ownership
- scattered files and comments
- members disappearing until the deadline
- weak evidence during peer review
- people claiming work without proof
- awkward and subjective contribution discussions

The app should not claim to perfectly prove who did the work. It should provide structured contribution indicators based on recorded project activity, approvals, and evidence.

## 3. Product Goal

GroupMark should allow students to:

1. Register and log in.
2. Create group assignment projects.
3. Add teammates.
4. Assign and track tasks.
5. Submit work for review.
6. Approve or dispute completed work.
7. Comment on tasks.
8. Automatically log contribution events.
9. Generate an evidence-based contribution report.

The hero feature is the contribution report. Task management exists to support fairer contribution evidence.

## 4. Target Users

### Student

A student can:

- create or join projects
- view assigned tasks
- create and update tasks
- submit tasks for review
- comment on tasks
- review teammate submissions
- view contribution events
- generate or view reports

### Project Owner

The project creator has extra permissions:

- add members
- remove members
- change roles
- archive the project
- resolve disputes
- lock or finalise reports later

### Viewer

A viewer can:

- view projects they belong to
- view tasks
- view contribution reports

A viewer cannot:

- create tasks
- edit tasks
- approve work
- upload evidence
- remove members

### Admin

Admin features are not part of the MVP. Later, an admin role may be used for operational visibility and audit logs.

## 5. MVP Scope

The MVP should stay backend-only and focus on the core contribution workflow.

MVP features:

- JWT authentication
- project creation and membership
- owner/member/viewer roles
- task creation and assignment
- task workflow: `todo -> in_progress -> review -> done`
- task disputes
- task comments
- automatic contribution event logging
- basic contribution report generation
- PostgreSQL persistence
- raw SQL migrations with dbmate
- Docker Compose local development
- pytest test suite

MVP does not include:

- frontend
- email invitations
- Celery or Redis
- AI summaries
- GitHub integration
- PDF export
- admin dashboard
- real-time notifications

## 6. Resume-Worthy Production Scope

After the MVP works, add production and cloud features:

- S3 file evidence uploads with presigned URLs
- file metadata stored in PostgreSQL
- evidence score included in reports
- structured JSON logging
- health and readiness endpoints
- GitHub Actions CI
- Docker build verification
- Trivy security scanning
- Terraform infrastructure
- AWS ECR
- AWS ECS Fargate
- AWS RDS PostgreSQL
- AWS S3
- AWS Secrets Manager or SSM Parameter Store
- CloudWatch logs and basic alarms
- deployment workflow on merge to `main`

This version is the resume-ready target.

## 7. Very Impressive Later Scope

Only add these after the production version is stable:

- invitation tokens
- email invitations
- in-app notifications
- scheduled reminders
- CSV report export
- PDF report export
- external evidence links
- GitHub PR/commit evidence integration
- peer review scoring
- advanced anti-gaming rules
- admin observability endpoints
- load testing

These features are useful but should not distract from the core app.

## 8. Core Domain Model

Core tables:

```text
users
projects
project_members
tasks
task_comments
contribution_events
reports
files
```

Later tables:

```text
invitations
notifications
audit_logs
external_evidence_links
peer_reviews
```

## 9. Authentication

Users can:

- register
- log in
- view current user

Routes:

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

Requirements:

- password hashing
- JWT access tokens
- protected routes
- no password hashes in API responses
- environment-based secret config

## 10. Projects

A project represents one group assignment.

Fields:

```text
id
owner_id
course_code
title
description
due_date
status
created_at
updated_at
```

Statuses:

```text
active
submitted
archived
```

Routes:

```text
POST   /projects
GET    /projects
GET    /projects/{project_id}
PATCH  /projects/{project_id}
DELETE /projects/{project_id}
```

Rules:

- creating a project also creates an owner membership
- users only see projects they belong to
- only owners can delete or archive projects

## 11. Members And Roles

MVP roles:

```text
owner
member
viewer
```

Routes:

```text
POST   /projects/{project_id}/members
GET    /projects/{project_id}/members
PATCH  /projects/{project_id}/members/{member_id}
DELETE /projects/{project_id}/members/{member_id}
```

MVP member flow:

- owner adds an existing user by email
- no email invite flow yet
- owner can change member roles
- owner can remove members

Permission rules:

- owners can manage project settings and members
- members can create tasks and comments
- viewers can read project data only
- users outside the project receive `404` for project-scoped resources

## 12. Tasks

Task statuses:

```text
todo
in_progress
review
done
blocked
disputed
```

Task priorities:

```text
low
medium
high
urgent
```

Task sizes:

```text
small
medium
large
```

Fields:

```text
id
project_id
title
description
status
priority
size
assigned_to
created_by
due_date
submitted_at
completed_at
approved_by
created_at
updated_at
```

Routes:

```text
POST   /projects/{project_id}/tasks
GET    /projects/{project_id}/tasks
GET    /projects/{project_id}/tasks/{task_id}
PATCH  /projects/{project_id}/tasks/{task_id}
DELETE /projects/{project_id}/tasks/{task_id}
POST   /projects/{project_id}/tasks/{task_id}/submit
POST   /projects/{project_id}/tasks/{task_id}/approve
POST   /projects/{project_id}/tasks/{task_id}/dispute
```

Rules:

- tasks belong to projects
- assigned users must be project members
- viewers cannot create or update tasks
- assignees can submit tasks for review
- users cannot approve their own tasks
- disputed tasks do not count as verified contribution

## 13. Comments

Routes:

```text
POST   /projects/{project_id}/tasks/{task_id}/comments
GET    /projects/{project_id}/tasks/{task_id}/comments
PATCH  /projects/{project_id}/tasks/{task_id}/comments/{comment_id}
DELETE /projects/{project_id}/tasks/{task_id}/comments/{comment_id}
```

Rules:

- project members can comment
- viewers can read comments
- comment authors can edit or delete their own comments
- owners may delete inappropriate comments later

## 14. Contribution Events

Contribution events are the audit trail for project activity.

Events are created internally by services, not directly by users.

MVP event types:

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
report_generated
```

Later event types:

```text
file_uploaded
evidence_link_added
invite_sent
invite_accepted
peer_review_submitted
report_locked
```

Route:

```text
GET /projects/{project_id}/events
```

Event fields:

```text
id
project_id
user_id
event_type
entity_type
entity_id
metadata
created_at
```

## 15. Reports

Reports are the main product output.

Routes:

```text
POST /projects/{project_id}/reports
GET  /projects/{project_id}/reports/latest
GET  /projects/{project_id}/reports/{report_id}
```

Reports should include per member:

- assigned task count
- approved task count
- incomplete task count
- disputed task count
- late task count
- comments added
- reviews given
- contribution events
- contribution score

Reports should include project-level summary:

- total tasks
- completed tasks
- disputed tasks
- most active member
- least active member
- generated timestamp

Reports should be stored as JSONB snapshots so historical reports do not change when project data changes later.

## 16. Scoring Model

The scoring model should be simple and defensible.

MVP formula:

```text
Final Score =
0.50 * TaskDelivery
+ 0.20 * Collaboration
+ 0.15 * Reliability
+ 0.15 * ReviewActivity
```

TaskDelivery:

```text
approved_completed_task_weight / assigned_task_weight * 100
```

Task sizes:

```text
small = 1
medium = 2
large = 3
```

Collaboration:

```text
comments and helpful project activity, capped at 100
```

Reliability:

```text
on_time_approved_tasks / approved_tasks * 100
```

ReviewActivity:

```text
reviews_given / expected_reviews * 100, capped at 100
```

Important rules:

- cap comment contribution to avoid spam
- users cannot approve their own tasks
- disputed tasks do not count as approved work
- reports should show evidence behind the score
- scoring should be described as contribution indicators, not absolute truth

Production version adds an Evidence score from file uploads and linked evidence.

## 17. File Evidence Uploads

File uploads are not part of MVP, but they are important for the resume-worthy production version.

Use S3 presigned URLs.

Routes:

```text
POST   /projects/{project_id}/files/presign-upload
POST   /projects/{project_id}/files/confirm-upload
GET    /projects/{project_id}/files
GET    /projects/{project_id}/files/{file_id}/download-url
DELETE /projects/{project_id}/files/{file_id}
```

Rules:

- files are stored in S3
- metadata is stored in PostgreSQL
- uploads can optionally be linked to tasks
- file uploads create contribution events
- uploaded evidence can affect report scoring

Do not upload large files directly through FastAPI.

## 18. Backend Architecture

Use FastAPI with a layered architecture.

Recommended structure:

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
      auth.py
      projects.py
      members.py
      tasks.py
      comments.py
      events.py
      reports.py
      files.py
      health.py
  models/
    user.py
    project.py
    member.py
    task.py
    comment.py
    contribution_event.py
    report.py
    file.py
  schemas/
    auth.py
    user.py
    project.py
    member.py
    task.py
    comment.py
    event.py
    report.py
    file.py
  repositories/
    users.py
    projects.py
    members.py
    tasks.py
    comments.py
    events.py
    reports.py
    files.py
  services/
    auth_service.py
    project_service.py
    member_service.py
    task_service.py
    comment_service.py
    contribution_service.py
    report_service.py
    file_service.py
migrations/
tests/
infra/
docs/
scripts/
```

Routes should stay thin. Business rules belong in services. SQL/database access belongs in repositories.

## 19. Database And Migrations

Use PostgreSQL and raw SQL migrations with dbmate.

Do not use Alembic.

Migration files should live in:

```text
migrations/
```

Expected command:

```bash
dbmate up
```

Initial migrations:

```text
001_create_users.sql
002_create_projects.sql
003_create_project_members.sql
004_create_tasks.sql
005_create_task_comments.sql
006_create_contribution_events.sql
007_create_reports.sql
008_create_files.sql
```

Important constraints:

- unique user emails
- unique project membership: `(project_id, user_id)`
- task assignee must reference a user
- project members should reference users and projects
- report data stored as JSONB
- contribution event metadata stored as JSONB

## 20. Local Development

Use Docker Compose.

MVP services:

```text
api
postgres
```

Production-version local services may add:

```text
localstack or mocked S3
redis, only if background workers are added
worker, only if background workers are added
```

Do not add Redis/Celery until there is a real need.

## 21. AWS Production Architecture

Production architecture:

```text
GitHub Actions
  -> build Docker image
  -> push to ECR
  -> deploy ECS Fargate service

FastAPI app
  -> RDS PostgreSQL
  -> S3 file evidence bucket
  -> Secrets Manager or SSM Parameter Store
  -> CloudWatch Logs
```

AWS resources:

- ECR repository
- ECS cluster
- ECS Fargate service
- Application Load Balancer
- RDS PostgreSQL
- S3 bucket for file evidence
- Secrets Manager or SSM parameters
- CloudWatch log group
- basic CloudWatch alarms
- IAM roles and policies

Use Terraform in:

```text
infra/
```

Keep Terraform flat at first:

```text
infra/main.tf
infra/variables.tf
infra/outputs.tf
```

Add modules only if the infrastructure becomes hard to maintain.

## 22. CI/CD

Pull request CI should run:

- formatting check
- linting
- tests
- database migrations against PostgreSQL
- Docker build verification
- Trivy security scan

Deployment workflow on merge to `main` should:

1. Build Docker image.
2. Tag with commit SHA.
3. Push to ECR.
4. Update ECS task definition.
5. Deploy ECS service.
6. Verify `/health`.
7. Verify `/ready`.

## 23. Testing Strategy

Test areas:

- authentication
- project ownership
- member roles
- permission checks
- task CRUD
- task submit/approve/dispute workflow
- comments
- contribution event logging
- report generation
- scoring algorithm
- file metadata and S3 URL generation later

For every feature, write at least:

- one success test
- one failure test
- one permission test where relevant

## 24. Features That Are Intentionally Deferred

Deferred from MVP:

- frontend
- Celery and Redis
- email notifications
- in-app notifications
- reminders
- PDF export
- GitHub integration
- AI summaries
- admin dashboard

Reason:

The first version should prove the core product: project membership, verified task contribution, contribution events, and reports.

## 25. Final Success Criteria

The finished resume-worthy version should demonstrate:

1. User registration and login.
2. Project creation.
3. Member and role management.
4. Task assignment and workflow.
5. Submit, approve, and dispute logic.
6. Comments.
7. Automatic contribution event logging.
8. Evidence-based contribution report generation.
9. PostgreSQL persistence with dbmate migrations.
10. Docker Compose local development.
11. Tests running in CI.
12. File evidence stored in S3.
13. App deployed to ECS Fargate.
14. Database deployed on RDS.
15. Infrastructure provisioned with Terraform.
16. Logs visible in CloudWatch.
17. Clear documentation and demo data.

## 26. Resume Description

Use this as a project description:

> Built GroupMark, a production-ready group assignment accountability platform for university students. Implemented JWT authentication, project workspaces, role-based membership, task assignment, task review and approval workflows, automatic contribution event logging, evidence-based contribution reports, PostgreSQL persistence, Dockerized local development, and automated tests. Extended the platform with S3 file evidence uploads, Terraform-managed AWS infrastructure, ECS Fargate deployment, RDS PostgreSQL, CloudWatch logging, and GitHub Actions CI/CD.

