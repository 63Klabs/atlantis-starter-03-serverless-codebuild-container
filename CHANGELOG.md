# Changelog

All notable changes to this project will be documented in this file.

## v0.0.1 (2026-04-18)

- Replaced Lambda/API Gateway resources with Scheduled CodeBuild project
- Added EventBridge Scheduler with configurable cron/rate expressions (PROD and DEVTEST)
- Added CodeBuild execution role with least-privilege SSM, S3, and CloudWatch Logs permissions
- Added Scheduler role with scoped codebuild:StartBuild permission
- Added CloudWatch Alarm and SNS notification for failed builds (PROD only)
- Added S3 copy commands in buildspec.yml for commands.yml and scripts/
- Added SSM parameter read example in commands.yml
- Added PrivilegedMode with auto-enable for S3 file system mounting
- Updated template-configuration.json with S3StaticHostBucket parameter
- Added deployment prerequisites documentation
- Added developer, admin-ops, and end-user documentation
