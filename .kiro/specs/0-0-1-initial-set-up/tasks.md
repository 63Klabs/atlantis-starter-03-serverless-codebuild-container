# Implementation Plan: Initial Set-Up

## Overview

Transform the application stack from Lambda/API Gateway to a scheduled CodeBuild container workload. The largest task is rewriting `template.yml`, broken into logical sub-tasks. Supporting changes include `buildspec.yml` S3 copy commands, `commands.yml` SSM example, `template-configuration.json` updates, and documentation across `DEPLOYMENT.md`, `docs/developer/`, `docs/admin-ops/`, and `docs/end-user/`.

## Tasks

- [x] 1. Remove Lambda and API Gateway resources from template.yml
  - [x] 1.1 Remove Lambda/API Gateway parameters, conditions, globals, and metadata references
    - Remove parameters: `FunctionTimeOutInSeconds`, `FunctionMaxMemoryInMB`, `FunctionArchitecture`, `FunctionGradualDeploymentType`, `ApiPathBase`, `ApiGatewayLoggingEnabled`
    - Remove conditions: `ApiGatewayLoggingIsEnabled` and any Lambda/API Gateway-specific conditions
    - Remove the entire `Globals` section (only contained API Gateway `OpenApiVersion`)
    - Remove Lambda/API Gateway parameter groups from `Metadata` `ParameterGroups`
    - _Requirements: 1.1, 1.2, 1.3_
  - [x] 1.2 Remove Lambda/API Gateway resources and outputs
    - Remove resources: `WebApi`, `ApiGatewayAccessLogGroup`, `ApiGatewayExecutionLogGroup`, `AppFunction`, `LambdaExecutionRole`, `ConfigLambdaPermission`, `ConfigLambdaPermissionLive`, `AppFunctionErrorsAlarm`, `AppFunctionErrorAlarmNotification`, `AppLogGroup`
    - Remove outputs: `ApiEndpoint`, `CloudWatchLambdaExecutionLogGroup`, `CloudWatchApiGatewayExecutionLogGroup`, `CloudWatchApiGatewayAccessLogGroup`, `LambdaWebConsole`
    - _Requirements: 1.1, 1.3_

- [x] 2. Add new parameters and conditions to template.yml
  - [x] 2.1 Add new template parameters
    - Add `ScheduleExpressionPROD` (String, default: `cron(0 6 * * ? *)`)
    - Add `ScheduleExpressionDEVTEST` (String, default: `""`)
    - Add `CodeBuildTimeoutInMinutes` (Number, default: 10, min: 5, max: 480)
    - Add `S3StaticHostBucket` (String) for the S3 bucket storing commands.yml and scripts
    - Add `S3MountPoint` (String, default: `""`) — optional S3 mount path
    - Add `S3MountBucketName` (String, default: `""`) — optional S3 bucket to mount
    - Add `PrivilegedMode` (String, default: `"false"`, AllowedValues: `["true", "false"]`)
    - _Requirements: 2.4, 2.7, 2.8, 3.1, 4.1, 4.2_
  - [x] 2.2 Update DeployRole parameter with cfn-lint suppression
    - Update `DeployRole` description to state it is unused and required by pipeline template ParameterOverrides
    - Add `Metadata` annotation suppressing cfn-lint `W2001` unused parameter warning
    - Remove `FunctionGradualDeploymentType` parameter (already removed in 1.1, but `DeployRole` stays)
    - _Requirements: 9.1, 9.2_
  - [x] 2.3 Add new conditions
    - Add `HasScheduleExpression` — true when the resolved schedule expression (PROD or DEVTEST based on `DeployEnvironment`) is non-empty
    - Add `EnablePrivilegedMode` — true when `PrivilegedMode` is `"true"` OR both `S3MountPoint` and `S3MountBucketName` are non-empty
    - Retain `IsProduction`, `HasPermissionsBoundaryArn`, `CreateAlarms`
    - _Requirements: 3.2, 3.3, 3.4, 4.3, 4.4_

- [x] 3. Add CodeBuild execution role to template.yml
  - Define `CodeBuildExecRole` (`AWS::IAM::Role`) named `Prefix-ProjectId-StageId-CodeBuildExecRole`
  - Trust policy: `codebuild.amazonaws.com`
  - Policy: `ssm:GetParameter`, `ssm:GetParametersByPath` scoped to `ParameterStoreHierarchy` path
  - Policy: `s3:GetObject` scoped to `S3StaticHostBucket` and `Prefix-ProjectId-StageId/*` path
  - Policy: `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` scoped to the CodeBuild log group ARN
  - Attach `PermissionsBoundaryArn` when provided (use `HasPermissionsBoundaryArn` condition)
  - Use `RolePath` for the role path
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 4. Add CodeBuild project to template.yml
  - Define `SchedContainer` (`AWS::CodeBuild::Project`) named `Prefix-ProjectId-StageId-SchedContainer`
  - Source type: `NO_SOURCE`, buildspec from S3 at `S3StaticHostBucket/Prefix-ProjectId-StageId/commands.yml`
  - Environment: `BUILD_GENERAL1_SMALL`, `LINUX_CONTAINER`, `aws/codebuild/amazonlinux-x86_64-standard:5.0`
  - PrivilegedMode: reference `EnablePrivilegedMode` condition via `!If`
  - TimeoutInMinutes: `!Ref CodeBuildTimeoutInMinutes`
  - ServiceRole: `!GetAtt CodeBuildExecRole.Arn`
  - Environment variables: `PREFIX`, `PROJECT_ID`, `STAGE_ID`, `PARAM_STORE_HIERARCHY` (full Sub path), `DEPLOY_ENVIRONMENT`, `S3_MOUNT_POINT`, `S3_BUCKET_NAME`
  - LogsConfig: point to the dedicated `SchedContainerLogGroup`
  - _Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 2.7, 3.2, 3.3, 3.4_

- [x] 5. Checkpoint - Validate template core resources
  - Ensure template.yml is valid YAML with no syntax errors
  - Ensure all `!Ref` and `!Sub` references resolve to defined parameters/resources
  - Ask the user if questions arise.

- [x] 6. Add EventBridge Scheduler and Scheduler role to template.yml
  - [x] 6.1 Add SchedulerRole (conditional on HasScheduleExpression)
    - Define `SchedulerRole` (`AWS::IAM::Role`) named `Prefix-ProjectId-StageId-SchedulerRole`
    - Trust policy: `scheduler.amazonaws.com`
    - Policy: `codebuild:StartBuild` scoped to `SchedContainer` project ARN
    - Attach `PermissionsBoundaryArn` when provided
    - Use `RolePath` for the role path
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [x] 6.2 Add Schedule resource (conditional on HasScheduleExpression)
    - Define `Schedule` (`AWS::Scheduler::Schedule`) named `Prefix-ProjectId-StageId-Schedule`
    - ScheduleExpression: resolved from PROD or DEVTEST parameter based on `DeployEnvironment`
    - Target: `StartBuild` on `SchedContainer`
    - RoleArn: `SchedulerRole`
    - _Requirements: 4.3, 4.4, 4.5_

- [x] 7. Add log group, CloudWatch alarm, and SNS topic to template.yml
  - [x] 7.1 Add SchedContainerLogGroup
    - Define `SchedContainerLogGroup` (`AWS::Logs::LogGroup`)
    - LogGroupName: `/aws/codebuild/Prefix-ProjectId-StageId-SchedContainer`
    - RetentionInDays: conditional on `IsProduction` (PROD vs DEVTEST retention params)
    - _Requirements: 7.1, 7.2, 7.3_
  - [x] 7.2 Add CloudWatch Alarm and SNS Topic (PROD only)
    - Define `SchedContainerAlarm` (`AWS::CloudWatch::Alarm`) with condition `CreateAlarms`
    - Metric: `FailedBuilds` on `AWS/CodeBuild` namespace, dimension: ProjectName = SchedContainer
    - AlarmActions: SNS topic
    - Define `AlarmNotification` (`AWS::SNS::Topic`) with condition `CreateAlarms`
    - DisplayName: `AWS-Alarm-Prefix-ProjectId-StageId`
    - Subscription: email to `AlarmNotificationEmail`
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 8. Add outputs and update metadata parameter groups in template.yml
  - [x] 8.1 Add new outputs
    - Add `CloudWatchSchedContainerLogGroup` — console link to the CodeBuild log group
    - Retain `ParameterStore` output
    - _Requirements: 2.1 (resource visibility)_
  - [x] 8.2 Update Metadata ParameterGroups
    - Replace Lambda/API Gateway parameter groups with groups for: Application Resource Naming, Deployment Environment, External Resources and Alarm Notifications, CodeBuild Settings, Schedule Settings, S3 and PrivilegedMode Settings
    - Update template description if needed
    - _Requirements: 2.4, 3.1, 4.1, 4.2_

- [x] 9. Checkpoint - Full template.yml validation
  - Ensure template.yml is valid YAML and all cross-references are correct
  - Run `aws cloudformation validate-template` or `cfn-lint` if available
  - Ensure all 16 requirements related to template.yml are addressed
  - Ask the user if questions arise.

- [x] 10. Update buildspec.yml with S3 copy commands
  - Add S3 copy commands in the build phase (after `cd application-infrastructure`):
    - `aws s3 cp src/commands.yml s3://$S3_STATIC_HOST_BUCKET/$PREFIX-$PROJECT_ID-$STAGE_ID/commands.yml`
    - `aws s3 cp src/scripts/ s3://$S3_STATIC_HOST_BUCKET/$PREFIX-$PROJECT_ID-$STAGE_ID/scripts/ --recursive`
  - _Requirements: 10.1, 10.2_

- [x] 11. Update commands.yml with SSM parameter read example
  - Add an AWS CLI command in the build phase to retrieve the SSM parameter at `${PARAM_STORE_HIERARCHY}ExampleParameter`
  - _Requirements: 11.1_

- [x] 12. Update template-configuration.json
  - Add parameter entry for `S3StaticHostBucket` using `$S3_STATIC_HOST_BUCKET$` placeholder convention
  - Do NOT add entries for `S3MountPoint` or `S3MountBucketName`
  - Remove `S3_MOUNT_POINT` and `S3_BUCKET_NAME` from Parameters if present (these are not template-configuration params)
  - _Requirements: 12.1, 12.2_

- [x] 13. Update DEPLOYMENT.md with prerequisites
  - Document that the pipeline requires a CodeBuild managed policy added via `CloudFormationSvcRoleIncludeManagedPolicyArns`
  - Document that the S3 DevOps bucket (`template-storage-s3-devops.yml`) must be deployed with `BuildSourceArn` set to the pipeline's CodeBuild project ARN
  - Document that the `S3StaticHostBucket` parameter must be passed to the pipeline
  - _Requirements: 13.1, 13.2, 13.3_

- [x] 14. Update developer documentation
  - Write `docs/developer/README.md` covering:
    - How to mount S3 as a file system using `mount-s3` in the Scheduled CodeBuild
    - How to copy or sync files to and from S3
    - How to clone a repository within the Scheduled CodeBuild
    - How to use the AWS CLI within the Scheduled CodeBuild
    - Note that PrivilegedMode is required for S3 file system mounting and can be enabled via the `PrivilegedMode` parameter for other use cases
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5_

- [x] 15. Update admin-ops and end-user documentation
  - [x] 15.1 Write docs/admin-ops/README.md
    - Describe how to change compute type and image for the Scheduled CodeBuild
    - Describe how to adjust `CodeBuildTimeoutInMinutes`
    - Describe runtime environment settings for both Pipeline CodeBuild and Scheduled CodeBuild
    - _Requirements: 15.1, 15.2, 15.3_
  - [x] 15.2 Write docs/end-user/README.md
    - Provide a sparse template structure for admins and developers to fill in with application-specific end-user content
    - _Requirements: 16.1_

- [x] 16. Update ARCHITECTURE.md and CHANGELOG.md
  - Update ARCHITECTURE.md if the architecture diagram or description needs changes to reflect the new CodeBuild/Scheduler resources (review current content — it may already be correct)
  - Update CHANGELOG.md with v0.0.1 changes summarizing the Lambda-to-CodeBuild transformation
  - _Requirements: (documentation completeness per AGENTS.md section 9)_

- [x] 17. Final checkpoint - Full review
  - Ensure all 16 requirements are covered by the implementation
  - Ensure all files are consistent and cross-references are correct
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- No property-based tests are included — this feature is entirely Infrastructure as Code, build specs, configuration, and documentation with no pure functions or business logic
- The template.yml rewrite (tasks 1–8) is the largest body of work and is broken into logical sub-tasks for incremental progress
- Each task references specific requirements for traceability
- Checkpoints at tasks 5, 9, and 17 ensure incremental validation
- All CloudFormation resources follow Atlantis naming convention: `Prefix-ProjectId-StageId-ResourceId`
- The Atlantis MCP tools and pipeline template should be referenced during implementation for CodeBuild configuration patterns
