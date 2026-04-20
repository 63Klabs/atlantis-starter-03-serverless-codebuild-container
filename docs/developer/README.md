# Developer Guide

This guide covers common tasks for extending the Scheduled CodeBuild environment.

The Scheduled CodeBuild runs `commands.yml` (and scripts in `src/scripts/`) on a recurring schedule via EventBridge Scheduler. Commands execute in an Amazon Linux CodeBuild container with Python, Node.js, and the AWS CLI pre-installed.

## Manually Starting the Scheduled CodeBuild

In DEV/TEST environments the EventBridge schedule is often left empty, meaning the Scheduled CodeBuild won't run on its own. You can trigger it manually using the AWS CLI or the AWS Console.

### AWS CLI

```bash
aws codebuild start-build \
  --project-name <Prefix>-<ProjectId>-<StageId>-SchedContainer
```

For example, if your Prefix is `acme`, ProjectId is `cron-job`, and StageId is `test`:

```bash
aws codebuild start-build \
  --project-name acme-cron-job-test-SchedContainer
```

You can optionally override environment variables for a single run:

```bash
aws codebuild start-build \
  --project-name acme-cron-job-test-SchedContainer \
  --environment-variables-override "name=MY_VAR,value=my-value,type=PLAINTEXT"
```

To watch the build progress:

```bash
# Get the build ID from the start-build output, then:
aws codebuild batch-get-builds \
  --ids <build-id> \
  --query "builds[0].buildStatus" \
  --output text
```

### AWS Console

1. Open the [CodeBuild console](https://console.aws.amazon.com/codesuite/codebuild/projects)
2. Find the project named `<Prefix>-<ProjectId>-<StageId>-SchedContainer`
3. Click **Start build** (or **Start build with overrides** to customize environment variables)
4. Monitor progress in the **Build history** tab

### When to Use

- Testing changes to `commands.yml` or scripts after a pipeline deployment to a TEST stage
- Debugging build failures without waiting for a schedule
- One-off executions in environments where no schedule is configured

> **Note:** The CodeBuild project must already be deployed by the pipeline before you can start a manual build. Make sure your latest code has been merged and deployed to the target stage first.

## Mounting S3 as a File System

You can mount an S3 bucket as a local file system using `mount-s3`. This is useful when your scripts need to read or write files on S3 as if they were local.

### Setup

Set the following parameters in your CloudFormation deployment:

- `S3MountPoint` — the local path where the bucket will be mounted (e.g., `/mnt/s3data`)
- `S3MountBucketName` — the name of the S3 bucket to mount

When both `S3MountPoint` and `S3MountBucketName` are provided, PrivilegedMode is automatically enabled on the CodeBuild project (required for `mount-s3`).

### How It Works

The mount happens automatically in the `pre_build` phase of `commands.yml`:

```yaml
pre_build:
  commands:
    - |
      if [ "${S3_MOUNT_POINT}" != "" ] && [ "${S3_BUCKET_NAME}" != "" ]; then
        echo "Mounting S3 bucket ${S3_BUCKET_NAME} to ${S3_MOUNT_POINT}"
        mkdir -p ${S3_MOUNT_POINT}
        sudo mount-s3 ${S3_BUCKET_NAME} ${S3_MOUNT_POINT}
      else
        echo "S3_MOUNT_POINT or S3_BUCKET_NAME not set, skipping S3 mount"
      fi
```

Once mounted, access files normally:

```bash
ls ${S3_MOUNT_POINT}/
cat ${S3_MOUNT_POINT}/data/input.csv
```

> **Note:** The CodeBuild execution role needs appropriate S3 permissions on the mounted bucket. By default, `CodeBuildExecRole` only has `s3:GetObject` on the static host bucket. You will need to add S3 permissions for the mounted bucket to `CodeBuildExecRole` in `template.yml`.

## Copying or Syncing Files to and from S3

Use the AWS CLI `s3 cp` and `s3 sync` commands to transfer files between the CodeBuild environment and S3.

### Examples

Copy a single file from S3:

```bash
aws s3 cp s3://my-bucket/data/input.csv /tmp/input.csv
```

Copy a file to S3:

```bash
aws s3 cp /tmp/output.csv s3://my-bucket/data/output.csv
```

Sync a directory from S3:

```bash
aws s3 sync s3://my-bucket/data/ /tmp/data/
```

Sync a local directory to S3:

```bash
aws s3 sync /tmp/results/ s3://my-bucket/results/
```

### Permissions

By default, `CodeBuildExecRole` only has `s3:GetObject` on the static host bucket (`S3StaticHostBucket`). To read from or write to other S3 buckets, add the necessary permissions to `CodeBuildExecRole` in `template.yml`. For example:

```yaml
- Sid: AdditionalS3Access
  Effect: Allow
  Action:
    - s3:GetObject
    - s3:PutObject
  Resource:
    - !Sub 'arn:aws:s3:::${MyBucketName}/*'
```

## Cloning a Repository

You can clone a Git repository within the Scheduled CodeBuild to pull in code, configuration, or data.

### Example

```bash
git clone https://${GIT_TOKEN}@github.com/my-org/my-repo.git /tmp/my-repo
```

### Credential Management

Store credentials (personal access tokens, SSH keys, etc.) in AWS Systems Manager Parameter Store or AWS Secrets Manager. Retrieve them at runtime:

```bash
GIT_TOKEN=$(aws ssm get-parameter --name "${PARAM_STORE_HIERARCHY}GitToken" --with-decryption --query "Parameter.Value" --output text)
git clone https://${GIT_TOKEN}@github.com/my-org/my-repo.git /tmp/my-repo
```

> **Note:** You will need to add permissions to `CodeBuildExecRole` for any additional SSM parameters or Secrets Manager secrets beyond the default `ParameterStoreHierarchy` path. The default role already has `ssm:GetParameter` and `ssm:GetParametersByPath` scoped to the application's parameter hierarchy.

## Using the AWS CLI

The AWS CLI is pre-installed in the CodeBuild environment. Any commands you run will use the credentials from `CodeBuildExecRole`.

### Example: Reading an SSM Parameter

The `commands.yml` build phase includes a working example:

```bash
aws ssm get-parameter --name "${PARAM_STORE_HIERARCHY}ExampleParameter" --query "Parameter.Value" --output text
```

### Other AWS Services

You can call any AWS service using the CLI. For example:

```bash
# Invoke a Lambda function
aws lambda invoke --function-name my-function /tmp/response.json

# Publish to an SNS topic
aws sns publish --topic-arn arn:aws:sns:us-east-1:123456789012:my-topic --message "Hello"
```

> **Note:** Permissions must be added to `CodeBuildExecRole` in `template.yml` for any AWS service you want to access. The default role only has permissions for SSM Parameter Store (scoped to the application hierarchy), S3 (read-only on the static host bucket), and CloudWatch Logs.

## PrivilegedMode

PrivilegedMode enables elevated permissions (`sudo`) in the CodeBuild container. It is controlled by the `PrivilegedMode` template parameter (default: `false`).

PrivilegedMode is **automatically enabled** when both `S3MountPoint` and `S3MountBucketName` are provided, since `mount-s3` requires it.

You can also enable it manually by setting the `PrivilegedMode` parameter to `true` for other use cases such as running Docker commands:

```bash
# Requires PrivilegedMode: true
docker build -t my-image .
```
