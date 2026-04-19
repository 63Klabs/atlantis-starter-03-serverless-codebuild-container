# Admin-Ops Documentation

Operational guidance for administrators managing the Scheduled CodeBuild environment and pipeline.

## Scheduled CodeBuild Compute Type and Image

The Scheduled CodeBuild (`SchedContainer`) defaults to:

- **Compute Type:** `BUILD_GENERAL1_SMALL`
- **Image:** `aws/codebuild/amazonlinux-x86_64-standard:5.0`

These values are hardcoded in `application-infrastructure/template.yml` under the `SchedContainer` resource's `Environment` section.

To change them, edit the `ComputeType` and `Image` properties in the `SchedContainer` Environment block:

```yaml
Environment:
  ComputeType: BUILD_GENERAL1_MEDIUM   # change here
  Image: aws/codebuild/amazonlinux-x86_64-standard:5.0  # change here
  Type: LINUX_CONTAINER
```

Available compute types (each step up increases cost):

| Compute Type | vCPUs | Memory |
|---|---|---|
| `BUILD_GENERAL1_SMALL` | 3 | 3 GB |
| `BUILD_GENERAL1_MEDIUM` | 7 | 15 GB |
| `BUILD_GENERAL1_LARGE` | 15 | 145 GB |
| `BUILD_GENERAL1_2XLARGE` | 72 | 145 GB |

Larger compute types cost more per build minute. Choose the smallest size that meets your workload requirements.

## CodeBuild Timeout

The `CodeBuildTimeoutInMinutes` parameter controls how long the Scheduled CodeBuild can run before it times out.

- **Default:** 10 minutes
- **Range:** 5–480 minutes

This is set during deployment via the `CodeBuildTimeoutInMinutes` CloudFormation parameter. You can override it in the pipeline's parameter overrides or in `template-configuration.json`.

## Runtime Environment Settings

### Pipeline CodeBuild

The Pipeline CodeBuild handles CI/CD build and deploy phases:

- **Buildspec:** `application-infrastructure/buildspec.yml`
- **Scripts:** `application-infrastructure/build-scripts/`
- **Purpose:** SAM package, S3 copy of `commands.yml` and `scripts/`, and CloudFormation deployment
- **Available runtimes:** Python, Node.js, AWS CLI (pre-installed in the CodeBuild image)
- **Configuration:** Compute type and image for the Pipeline CodeBuild are configured in the pipeline template (`template-pipeline.yml`), not in this repository. Contact your platform engineer to adjust pipeline CodeBuild settings.

### Scheduled CodeBuild

The Scheduled CodeBuild runs recurring workloads on a schedule:

- **Buildspec:** `commands.yml` (copied to S3 by the pipeline, read from `S3StaticHostBucket` at runtime)
- **Scripts:** `src/scripts/` (copied to S3 by the pipeline)
- **Trigger:** EventBridge Scheduler (cron or rate expression)
- **Compute Type:** `BUILD_GENERAL1_SMALL` (hardcoded in `template.yml`)
- **Image:** `aws/codebuild/amazonlinux-x86_64-standard:5.0` (hardcoded in `template.yml`)
- **Available runtimes:** Python, Node.js, AWS CLI (pre-installed in the CodeBuild image)
- **Configuration:** Compute type and image are configured directly in `application-infrastructure/template.yml` under the `SchedContainer` resource (see above).
