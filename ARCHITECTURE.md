# Architecture

## Directory Structure

```
├── application-infrastructure/    # AWS SAM application stack
│   ├── build-scripts/             # Scripts used during CodeBuild (Pipeline)
│   │   ├── generate-put-ssm.py
│   │   └── update_template_configuration.py
│   ├── src/                       # Commands and Scripts for Scheduled Container
│   │   ├── scripts/               # Scripts for CodeBuild Container
│.  │   └── commands.yml           # Commands for CodeBuild Container
│   ├── buildspec.yml              # AWS CodeBuild build specification
│   ├── template.yml               # AWS SAM/CloudFormation template
│   └── template-configuration.json # Stack parameter overrides
├── docs/                          # Documentation
│   ├── admin-ops/                 # For Admin, Operations
│   ├── developer/                 # For Developer maintaining application
│   └── end-user/                  # For consumer of this application's output (Exported reports)
├── scripts/                       # Utility scripts ran by developer (Not part of deployment)
│   └── generate-sidecar-metadata.py
├── AGENTS.md                      # AI and developer guidelines
├── CHANGELOG.md
├── DEPLOYMENT.md
├── ARCHITECTURE.md
└── README.md
```

## Application Stack

```mermaid
flowchart TB
    EventSchedule([Schedule]) -->|Event| CODEBUILD

        CODEBUILD["CodeBuild<br/>(Container)"]
        CODEBUILD -->|Execution Logs| CODEBUILDLogs["CloudWatch<br/>CodeBuild Logs"]
        CODEBUILDLogs --> CWAlarm
        CWAlarm -.->|Notify| SNS["SNS Topic"]
        SNS -.->|Email| Email([Admin Email])

```

## Deployment Pipeline

```mermaid
flowchart LR
    Repo["Source<br/>Repository"] --> CodeBuild["AWS<br/>CodeBuild"]
    CodeBuild -->|"npm install<br/>SAM package"| Artifacts["S3 Artifacts<br/>Bucket"]
    Artifacts --> CFN["CloudFormation<br/>Deploy"]
    CFN -->|"Create/Update Stack"| Stack["Application<br/>Stack"]
```

## Key Design Decisions

- **CloudWatch Alarms** and SNS notifications are created only in PROD to reduce cost.
- **CodeBuild logging** (execution)
- **Permissions Boundary** support is optional, controlled via a stack parameter.
