# Follow-Up Questions & Clarifications (Round 2)

Based on your answers, a few follow-ups:

### Q9: Schedule Parameters — Separate PROD and TEST Cron
You said to use separate parameters for Prod and Test schedule expressions, and allow blank to disable. Should this follow the same pattern as `LogRetentionInDaysForPROD` / `LogRetentionInDaysForDEVTEST`? For example:
- `ScheduleExpressionPROD` (default: `cron(0 6 * * ? *)` — daily at 6 AM UTC)
- `ScheduleExpressionDEVTEST` (default: empty string — disabled)

Then use a condition to only create the EventBridge Scheduler rule when the resolved expression is non-empty?

**Answer** Yes, follow the same pattern and only create scheduler when non-empty.

### Q10: EventBridge Scheduler vs EventBridge Rule
AWS offers two scheduling mechanisms:
- **EventBridge Scheduler** (`AWS::Scheduler::Schedule`) — newer, supports one-time and recurring, built-in retry policies, dead-letter queues, flexible time windows
- **EventBridge Rules** (`AWS::Events::Rule` with `ScheduleExpression`) — older, simpler, well-established

The pipeline template already uses EventBridge Rules for pipeline event monitoring. For the scheduled CodeBuild trigger, I'd recommend **EventBridge Scheduler** since it's the newer AWS-recommended approach and the pipeline's CloudFormation service role already has `scheduler:*` permissions scoped to this deployment. Does that work, or would you prefer EventBridge Rules for simplicity/consistency?

**Answer** Use EventBridge Scheduler

### Q11: Scheduler IAM Role
EventBridge Scheduler needs its own IAM role to invoke CodeBuild (`codebuild:StartBuild`). This will be a separate role from the CodeBuild execution role. The naming would follow convention: `Prefix-ProjectId-StageId-SchedulerRole`. Confirming this is acceptable.

**Answer** Yes

### Q12: CodeBuild Execution Role — SSM Read Access
The scheduled CodeBuild needs to read SSM parameters (per the `commands.yml` example). The execution role should include `ssm:GetParameter` and `ssm:GetParametersByPath` scoped to `${ParameterStoreHierarchy}*`. Should it also have write access to SSM, or read-only is sufficient for the starter?

**Answer** It should be readonly

### Q13: CodeBuild Execution Role — S3 Static Host Bucket Read
The scheduled CodeBuild will pull its buildspec from the S3 static host bucket. The execution role needs `s3:GetObject` on that bucket. It also needs read access if scripts reference files from S3. Should the role also have write access to the static host bucket, or just read?

**Answer** It should only be read access.

### Q14: cfn-lint Suppression for DeployRole
Regarding your question about cfn-lint — yes, an unused parameter will trigger `W2001` (unused parameter). You can suppress it with a metadata annotation on the parameter:
```yaml
DeployRole:
  Type: String
  Description: "Unused - Required by pipeline template ParameterOverrides. IAM role passed by pipeline for CodeDeploy (not used in this stack)."
  Metadata:
    cfn-lint:
      ignore:
        checks:
          - W2001
```
I'll use this approach. Just confirming you're good with it.

**Answer** Yes, I'm good

### Q15: PrivilegedMode Condition
You said to set PrivilegedMode to `true` only when S3 mount env variables are non-empty. Since `S3MountPoint` and `S3MountBucketName` are template parameters, I can create a condition like:
```yaml
EnablePrivilegedMode: !And
  - !Not [!Equals [!Ref S3MountPoint, ""]]
  - !Not [!Equals [!Ref S3MountBucketName, ""]]
```
This means PrivilegedMode is automatically enabled when both mount parameters are provided. If a developer needs PrivilegedMode for other reasons but doesn't want S3 mount, they'd need to set a dummy mount value. Should I instead add a separate `PrivilegedMode` boolean parameter (default: false) that overrides, OR keep it tied to the S3 mount parameters?

**Answer** Good idea. Let's have a parameter. Set EnabledPrivlegedMode to true if the parameter is true OR meets the condition you described with mount point and mount bucket name

### Q16: Pipeline CodeBuild S3 Copy Permissions
The pipeline's CodeBuild service role needs `s3:PutObject` on the S3 static host bucket to copy `commands.yml` and `scripts/`. The pipeline template already passes `S3_STATIC_HOST_BUCKET` as an env var and the CodeBuild service role has S3 permissions scoped to the artifacts bucket. The static host bucket's bucket policy (from `template-storage-s3-devops.yml`) grants `s3:PutObject` to CodeBuild via `BuildSourceArn` condition. Should the deployment docs note that the `BuildSourceArn` on the S3 DevOps bucket should be set to the pipeline's CodeBuild project ARN?

**Answer** yes, deployment docs should note that the `BuildSourceArn` on the S3 DevOps bucket should be set to the pipeline's CodeBuild project ARN