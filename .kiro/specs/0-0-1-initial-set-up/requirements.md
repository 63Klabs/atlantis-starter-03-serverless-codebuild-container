# Requirements Document

## Introduction

This application provides a scheduled CodeBuild environment as a lightweight, managed alternative to containers or Lambda functions for running shell, Python, Node.js, or other commands on a recurring schedule. The project is scaffolded on the Atlantis Platform and currently contains API Gateway and Lambda resource definitions in `template.yml` that must be replaced with EventBridge Scheduler and CodeBuild Project resources. Two CodeBuild environments exist: the pipeline CodeBuild (buildspec.yml + build-scripts/) for CI/CD, and the scheduled CodeBuild (commands.yml + src/scripts/) for recurring workloads. Data and file persistence is achieved through S3 copy/sync, S3 file system mount, repo cloning, or CLI/API calls.

## Glossary

- **Application_Stack**: The CloudFormation stack defined in `template.yml` containing all application-specific resources deployed by the pipeline.
- **Pipeline_CodeBuild**: The CodeBuild project managed by the Atlantis pipeline template that executes `buildspec.yml` and `build-scripts/` for CI/CD build and deploy phases.
- **Scheduled_CodeBuild**: The CodeBuild project defined in the Application_Stack that runs `commands.yml` from S3 on a recurring schedule via EventBridge Scheduler.
- **EventBridge_Scheduler**: An `AWS::Scheduler::Schedule` resource that triggers the Scheduled_CodeBuild on a cron or rate expression.
- **Scheduler_Role**: An IAM role (`Prefix-ProjectId-StageId-SchedulerRole`) that grants EventBridge_Scheduler permission to start the Scheduled_CodeBuild.
- **CodeBuild_Execution_Role**: An IAM role (`Prefix-ProjectId-StageId-CodeBuildExecRole`) that grants the Scheduled_CodeBuild permissions to read SSM parameters, read from the S3 static host bucket, and write CloudWatch Logs.
- **S3_Static_Host_Bucket**: An S3 bucket deployed separately (via `template-storage-s3-devops.yml`) that stores the `commands.yml` buildspec and `scripts/` directory for the Scheduled_CodeBuild.
- **S3_Static_Host_Path**: The path `s3://<S3_Static_Host_Bucket>/<Prefix>-<ProjectId>-<StageId>/` where commands.yml and scripts/ are stored.
- **PrivilegedMode**: A CodeBuild setting that enables elevated permissions (e.g., `sudo`) required for S3 file system mounting via `mount-s3`.
- **Parameter_Store_Hierarchy**: The SSM Parameter Store path prefix used to organize application-specific parameters, structured as `/<hierarchy>/<DeployEnvironment>/<Prefix>-<ProjectId>-<StageId>/`.
- **Template_Configuration**: The `template-configuration.json` file containing parameter overrides and tags with placeholder values resolved during Pipeline_CodeBuild execution.
- **PROD_Environment**: A deployment environment (`DeployEnvironment=PROD`) used for beta and main/prod stages with alarms, longer log retention, and gradual deployments.
- **DEVTEST_Environment**: A deployment environment (`DeployEnvironment=DEV` or `DeployEnvironment=TEST`) used for test stages with shorter log retention and fewer cost-incurring resources.

## Requirements

### Requirement 1: Remove Lambda and API Gateway Resources

**User Story:** As a platform engineer, I want all Lambda and API Gateway resources removed from the Application_Stack, so that the template only contains resources relevant to the scheduled CodeBuild workload.

#### Acceptance Criteria

1. THE Application_Stack SHALL NOT contain any `AWS::Serverless::Function`, `AWS::Serverless::Api`, `AWS::Lambda::Permission`, or API Gateway log group resources.
2. THE Application_Stack SHALL NOT contain the following parameters: `FunctionTimeOutInSeconds`, `FunctionMaxMemoryInMB`, `FunctionArchitecture`, `FunctionGradualDeploymentType`, `ApiPathBase`, `ApiGatewayLoggingEnabled`.
3. THE Application_Stack SHALL NOT contain any Conditions, Globals, or Outputs that reference removed Lambda or API Gateway resources.

### Requirement 2: Scheduled CodeBuild Project

**User Story:** As a developer, I want a CodeBuild project defined in the Application_Stack, so that scheduled commands and scripts execute in a managed build environment.

#### Acceptance Criteria

1. THE Application_Stack SHALL define an `AWS::CodeBuild::Project` resource named `<Prefix>-<ProjectId>-<StageId>-SchedContainer`.
2. THE Scheduled_CodeBuild SHALL use compute type `BUILD_GENERAL1_SMALL` and image `aws/codebuild/amazonlinux-x86_64-standard:5.0`.
3. THE Scheduled_CodeBuild SHALL reference the buildspec from S3 at `<S3_Static_Host_Bucket>/<Prefix>-<ProjectId>-<StageId>/commands.yml`.
4. THE Application_Stack SHALL define a `CodeBuildTimeoutInMinutes` parameter with a default value of 10.
5. THE Scheduled_CodeBuild SHALL use the value of `CodeBuildTimeoutInMinutes` as its build timeout.
6. THE Scheduled_CodeBuild SHALL receive the following environment variables: `PREFIX`, `PROJECT_ID`, `STAGE_ID`, `PARAM_STORE_HIERARCHY`, `DEPLOY_ENVIRONMENT`, `S3_MOUNT_POINT`, `S3_BUCKET_NAME`, and any additional variables matching those provided by the Pipeline_CodeBuild.
7. THE Application_Stack SHALL define `S3MountPoint` and `S3MountBucketName` as template parameters with empty string defaults, passed as CodeBuild environment variables `S3_MOUNT_POINT` and `S3_BUCKET_NAME`.
8. THE `S3MountPoint` and `S3MountBucketName` parameters SHALL NOT be sourced from Template_Configuration placeholder values.

### Requirement 3: PrivilegedMode Configuration

**User Story:** As a developer, I want PrivilegedMode to be configurable, so that I can mount S3 as a file system or run commands requiring elevated permissions.

#### Acceptance Criteria

1. THE Application_Stack SHALL define a `PrivilegedMode` boolean parameter with a default value of `false`.
2. WHEN the `PrivilegedMode` parameter is `true`, THE Scheduled_CodeBuild SHALL enable PrivilegedMode.
3. WHEN both `S3MountPoint` and `S3MountBucketName` parameters are non-empty, THE Scheduled_CodeBuild SHALL enable PrivilegedMode.
4. WHEN the `PrivilegedMode` parameter is `false` AND either `S3MountPoint` or `S3MountBucketName` is empty, THE Scheduled_CodeBuild SHALL disable PrivilegedMode.

### Requirement 4: EventBridge Scheduler

**User Story:** As an operator, I want the Scheduled_CodeBuild triggered on a configurable schedule, so that commands run automatically at defined intervals.

#### Acceptance Criteria

1. THE Application_Stack SHALL define a `ScheduleExpressionPROD` parameter with a default value of `cron(0 6 * * ? *)`.
2. THE Application_Stack SHALL define a `ScheduleExpressionDEVTEST` parameter with a default value of an empty string.
3. WHEN the resolved schedule expression for the current environment is non-empty, THE Application_Stack SHALL create an `AWS::Scheduler::Schedule` resource that triggers the Scheduled_CodeBuild.
4. WHEN the resolved schedule expression for the current environment is empty, THE Application_Stack SHALL NOT create the EventBridge_Scheduler resource.
5. THE EventBridge_Scheduler SHALL use the Scheduler_Role to invoke the Scheduled_CodeBuild.

### Requirement 5: Scheduler IAM Role

**User Story:** As a platform engineer, I want a dedicated IAM role for the EventBridge Scheduler, so that scheduler permissions are scoped to starting the Scheduled_CodeBuild only.

#### Acceptance Criteria

1. WHEN the EventBridge_Scheduler is created, THE Application_Stack SHALL define an IAM role named `<Prefix>-<ProjectId>-<StageId>-SchedulerRole`.
2. THE Scheduler_Role SHALL grant `codebuild:StartBuild` permission scoped to the Scheduled_CodeBuild project ARN.
3. THE Scheduler_Role SHALL have a trust policy allowing `scheduler.amazonaws.com` to assume the role.
4. WHEN a PermissionsBoundaryArn is provided, THE Scheduler_Role SHALL attach the specified permissions boundary.

### Requirement 6: CodeBuild Execution Role

**User Story:** As a platform engineer, I want a least-privilege IAM role for the Scheduled_CodeBuild, so that it can read SSM parameters, read from S3, and write logs without excess permissions.

#### Acceptance Criteria

1. THE Application_Stack SHALL define an IAM role named `<Prefix>-<ProjectId>-<StageId>-CodeBuildExecRole`.
2. THE CodeBuild_Execution_Role SHALL grant `ssm:GetParameter` and `ssm:GetParametersByPath` scoped to the Parameter_Store_Hierarchy path.
3. THE CodeBuild_Execution_Role SHALL grant `s3:GetObject` scoped to the S3_Static_Host_Bucket and the application's S3_Static_Host_Path.
4. THE CodeBuild_Execution_Role SHALL grant CloudWatch Logs write permissions (`logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`) scoped to the Scheduled_CodeBuild log group.
5. THE CodeBuild_Execution_Role SHALL have a trust policy allowing `codebuild.amazonaws.com` to assume the role.
6. WHEN a PermissionsBoundaryArn is provided, THE CodeBuild_Execution_Role SHALL attach the specified permissions boundary.

### Requirement 7: CodeBuild Log Group

**User Story:** As an operator, I want a dedicated CloudWatch log group for the Scheduled_CodeBuild, so that execution logs are retained according to environment policy.

#### Acceptance Criteria

1. THE Application_Stack SHALL define an `AWS::Logs::LogGroup` for the Scheduled_CodeBuild.
2. WHILE the DeployEnvironment is PROD, THE log group SHALL use the `LogRetentionInDaysForPROD` parameter for retention.
3. WHILE the DeployEnvironment is not PROD, THE log group SHALL use the `LogRetentionInDaysForDEVTEST` parameter for retention.

### Requirement 8: CloudWatch Alarm and SNS Notification (PROD Only)

**User Story:** As an operator, I want to be alerted when the Scheduled_CodeBuild fails in production, so that I can investigate and remediate issues promptly.

#### Acceptance Criteria

1. WHILE the DeployEnvironment is PROD, THE Application_Stack SHALL create a CloudWatch Alarm that triggers when the Scheduled_CodeBuild has failed builds.
2. WHILE the DeployEnvironment is PROD, THE Application_Stack SHALL create an SNS Topic named `AWS-Alarm-<Prefix>-<ProjectId>-<StageId>` subscribed to the `AlarmNotificationEmail` parameter.
3. WHEN the CloudWatch Alarm transitions to ALARM state, THE alarm SHALL publish a notification to the SNS Topic.
4. WHILE the DeployEnvironment is not PROD, THE Application_Stack SHALL NOT create the CloudWatch Alarm or SNS Topic.

### Requirement 9: DeployRole Parameter Retention

**User Story:** As a platform engineer, I want the `DeployRole` parameter retained in the template even though it is unused, so that pipeline parameter overrides do not fail.

#### Acceptance Criteria

1. THE Application_Stack SHALL define a `DeployRole` parameter with a description stating it is unused and required by the pipeline template ParameterOverrides.
2. THE `DeployRole` parameter SHALL include a `cfn-lint` metadata annotation suppressing the `W2001` unused parameter warning.

### Requirement 10: Pipeline Buildspec S3 Copy

**User Story:** As a developer, I want the pipeline build phase to copy `commands.yml` and `scripts/` to the S3_Static_Host_Bucket, so that the Scheduled_CodeBuild always uses the latest commands and scripts.

#### Acceptance Criteria

1. WHEN the Pipeline_CodeBuild executes the build phase, THE `buildspec.yml` SHALL copy `src/commands.yml` to `s3://<S3_STATIC_HOST_BUCKET>/<Prefix>-<ProjectId>-<StageId>/commands.yml`.
2. WHEN the Pipeline_CodeBuild executes the build phase, THE `buildspec.yml` SHALL copy `src/scripts/` to `s3://<S3_STATIC_HOST_BUCKET>/<Prefix>-<ProjectId>-<StageId>/scripts/`.

### Requirement 11: Example SSM Parameter Read in commands.yml

**User Story:** As a developer, I want an example command in `commands.yml` that reads an SSM parameter, so that I have a working reference for accessing Parameter Store from the Scheduled_CodeBuild.

#### Acceptance Criteria

1. THE `commands.yml` SHALL include a command that retrieves the SSM parameter at path `${PARAM_STORE_HIERARCHY}ExampleParameter` using the AWS CLI.

### Requirement 12: Template Configuration Updates

**User Story:** As a platform engineer, I want `template-configuration.json` updated with the new parameters and placeholder conventions, so that pipeline deployments pass the correct values to the Application_Stack.

#### Acceptance Criteria

1. THE Template_Configuration SHALL include parameter entries for values that require pipeline environment variable resolution using the `$PLACEHOLDER$` convention.
2. THE Template_Configuration SHALL NOT include entries for `S3MountPoint` or `S3MountBucketName` parameters.

### Requirement 13: CloudFormation Service Role Permissions

**User Story:** As a platform engineer, I want deployment documentation to specify the required CloudFormation service role managed policy, so that the pipeline can create and manage CodeBuild resources.

#### Acceptance Criteria

1. THE `DEPLOYMENT.md` SHALL document that the pipeline requires a CodeBuild managed policy added via `CloudFormationSvcRoleIncludeManagedPolicyArns`.
2. THE `DEPLOYMENT.md` SHALL document that the S3 DevOps bucket (`template-storage-s3-devops.yml`) must be deployed with `BuildSourceArn` set to the pipeline's CodeBuild project ARN.
3. THE `DEPLOYMENT.md` SHALL document that the `S3StaticHostBucket` parameter must be passed to the pipeline.

### Requirement 14: Developer Documentation

**User Story:** As a developer, I want documentation covering S3 mounting, S3 copy/sync, repo cloning, AWS CLI usage, and PrivilegedMode, so that I can extend the scheduled CodeBuild with additional capabilities.

#### Acceptance Criteria

1. THE `docs/developer/` documentation SHALL describe how to mount S3 as a file system using `mount-s3` in the Scheduled_CodeBuild.
2. THE `docs/developer/` documentation SHALL describe how to copy or sync files to and from S3.
3. THE `docs/developer/` documentation SHALL describe how to clone a repository within the Scheduled_CodeBuild.
4. THE `docs/developer/` documentation SHALL describe how to use the AWS CLI within the Scheduled_CodeBuild.
5. THE `docs/developer/` documentation SHALL note that PrivilegedMode is required for S3 file system mounting and can be enabled via the `PrivilegedMode` parameter for other use cases.

### Requirement 15: Admin-Ops Documentation

**User Story:** As an administrator, I want documentation covering runtime environment settings for both CodeBuild environments, so that I can adjust compute, image, and timeout settings as needed.

#### Acceptance Criteria

1. THE `docs/admin-ops/` documentation SHALL describe how to change the compute type and image for the Scheduled_CodeBuild.
2. THE `docs/admin-ops/` documentation SHALL describe how to adjust the `CodeBuildTimeoutInMinutes` parameter.
3. THE `docs/admin-ops/` documentation SHALL describe runtime environment settings for both the Pipeline_CodeBuild and the Scheduled_CodeBuild.

### Requirement 16: End-User Documentation

**User Story:** As a template consumer, I want sparse end-user documentation with a template structure, so that I can fill in my own use-case-specific content.

#### Acceptance Criteria

1. THE `docs/end-user/` documentation SHALL provide a template structure for admins and developers to fill in with application-specific end-user content.
