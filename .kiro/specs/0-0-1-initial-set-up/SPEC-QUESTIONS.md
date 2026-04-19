# Clarifying Questions & Recommendations

## Questions

### Q1: Schedule Expression
What schedule should the EventBridge Scheduler use? Should it be a parameter with a default (e.g., `rate(1 day)` or a cron expression), or should it be hardcoded? I'd recommend making it a template parameter with a default of `rate(1 day)` so each deployment can customize it.

**Answer**: Accept as a parameter as a cron expression. Use a separate parameter for Prod and Test. Allow user to leave it blank to disable.

### Q2: CodeBuild Compute & Image
The pipeline CodeBuild uses `BUILD_GENERAL1_SMALL` with `aws/codebuild/amazonlinux-x86_64-standard:5.0`. Should the scheduled CodeBuild project use the same compute type and image? I'd recommend matching the pipeline's configuration for consistency, but making the image a parameter so users can swap it if needed.

**Answer** Keep it the same, and hardcode. Add documentation for the admin-ops to increase on the scheduled codebuild environment if desired.

### Q3: CodeBuild Timeout
The pipeline CodeBuild doesn't set an explicit timeout (defaults to 60 minutes). Should the scheduled CodeBuild project have a configurable timeout parameter? I'd recommend a parameter defaulting to 30 minutes since scheduled jobs are typically shorter than build/deploy jobs.

**Answer** Yes, add a parameter for timeout. Default to 10 minutes. Add to admin-ops documentation

### Q4: S3 Mount Point Parameters
The `commands.yml` already references `S3_MOUNT_POINT` and `S3_BUCKET_NAME` environment variables for mounting S3. Should these be template parameters passed through to the CodeBuild environment, or should they come from `template-configuration.json`? I'd recommend template parameters with empty defaults (mount is optional), passed as CodeBuild environment variables.

**Answer** Yes, add them as environment variables but do not add them as parameters coming from template-configuration. They can be used as placeholders and updated as desired by the developer.

### Q5: S3StaticHostBucket Path Structure
The SPEC says `commands.yml` and `src/scripts/` should be copied to `S3_STATIC_HOST_BUCKET/<Prefix>-<ProjectId>-<StageId>/`. Should the path structure be:
- `s3://<bucket>/<Prefix>-<ProjectId>-<StageId>/commands.yml`
- `s3://<bucket>/<Prefix>-<ProjectId>-<StageId>/scripts/`

Is that correct? And should the scheduled CodeBuild reference the buildspec from S3 using this path?

**Answer**: Yes, use that path structure and the scheduled CodeBuild should reference the buildspec from S3 using that path

### Q6: Lambda & API Gateway Removal
The current `template.yml` has Lambda, API Gateway, and related resources (execution role, permissions, log groups, alarms, SNS). Confirming these should ALL be removed and replaced with:
- EventBridge Scheduler
- CodeBuild Project (scheduled)
- CodeBuild IAM Role
- CodeBuild Log Group
- CloudWatch Alarm on CodeBuild failures (PROD only)
- SNS Topic for alarm notifications (PROD only)

Should the existing Lambda-related parameters also be removed (FunctionTimeOutInSeconds, FunctionMaxMemoryInMB, FunctionArchitecture, FunctionGradualDeploymentType, ApiPathBase, ApiGatewayLoggingEnabled)?

**Answer** Yes, remove and replace as you listed here.

### Q7: CodeBuild Environment Variables
Looking at the pipeline's CodeBuild, it passes many environment variables (PREFIX, PROJECT_ID, STAGE_ID, PARAM_STORE_HIERARCHY, DEPLOY_ENVIRONMENT, etc.). Should the scheduled CodeBuild project receive the same set of environment variables for consistency? Plus the S3 mount-related ones?

**Answer**: Yes, it should receive the same environment variables as the Pipeline CodeBuild. We will need to add parameters in template.yml and template-configuration.json to pass some in, such as repository information. Be sure to use the placeholder convention in template-configuration as they are replaced during build time.

### Q8: Privileged Mode for S3 Mount
`mount-s3` in `commands.yml` uses `sudo`. CodeBuild needs `PrivilegedMode: true` for this to work. Should we enable privileged mode on the scheduled CodeBuild project? This is required for S3 file system mounting.

**Answer** Let's add PrivilegedMode and set it to false unless S3 mount env variable is not "". (this can also allow the developer to set PrivilagedMode if required for other scripts. Add that as a note to developer documentation)

## Recommendations

### R1: CloudFormation Service Role Permissions
The pipeline's `CloudFormationSvcRole` already has `EventBridgeSchedulerCRUDThisDeploymentOnly` and `CodeBuild` isn't explicitly listed. The CloudFormation service role will need permissions to create CodeBuild projects. I recommend noting in the deployment docs that the pipeline may need a managed policy added via `CloudFormationSvcRoleIncludeManagedPolicyArns` if the CloudFormation service role doesn't already have CodeBuild permissions.

**Answer**: Yes, recommend and require use of a codebuild managed policy. Mention this in the DEPLOYMENT.md doc and give a basic template sample in docs/admin-ops

### R2: Buildspec Copy During Pipeline Build
The `buildspec.yml` should be updated to copy `src/commands.yml` and `src/scripts/` to the S3 static host bucket during the build phase. This ensures the scheduled CodeBuild always has the latest commands and scripts available.

**Answer** yes, correct

### R3: Parameter Store Example in commands.yml
The SPEC asks for an example in `commands.yml` that reads the SSM parameter created by `buildspec.yml`. The parameter path would be `${PARAM_STORE_HIERARCHY}ExampleParameter`. I'll add an AWS CLI command to retrieve it.

**Answer** yes, correct

### R4: Keep DeployRole Parameter
Even though Lambda/CodeDeploy won't be used, the pipeline template passes `DeployRole` as a parameter override. I recommend keeping it as a parameter (with no usage) to avoid pipeline deployment errors, OR removing it from the pipeline's ParameterOverrides. Since we can't modify the pipeline template, we should keep the parameter but it can be unused.

**Answer** Keep since it is required in the pipeline, but don't use it. List it as being unused and why it is there. Utilize the parameter desciription. If cfn-lint is used, will this throw an unused parameter error? If so, is there a way to add a comment to override the cfn-lint check/error for that parameter?

### R5: New Parameters to Add
I recommend adding these parameters to `template.yml`:
- `ScheduleExpression` - cron/rate expression for the schedule
- `CodeBuildTimeoutInMinutes` - timeout for the scheduled CodeBuild
- `S3StaticHostBucket` - the S3 bucket where commands.yml and scripts are stored (passed from pipeline)
- `S3MountPoint` - optional mount point path
- `S3MountBucketName` - optional S3 bucket to mount

**Answer** yes, correct

### R6: template-configuration.json Updates
The `template-configuration.json` needs `S3_MOUNT_POINT` and `S3_BUCKET_NAME` parameters added (can default to empty). The `S3StaticHostBucket` should also be added as a parameter placeholder.

**Answer** yes, correct