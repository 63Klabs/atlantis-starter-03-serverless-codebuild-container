# Deployment Guide

This application is **Ready-to-Deploy-and-Run** with the [63Klabs Atlantis DevOps Platform for Serverless Deployments on AWS](https://atlantis.63klabs.net)

- Use the Atlantis scripts from your organization's central SAM Config infrastructure repository to manage your application's repository and deployment.
- Add a pipeline to each branch in your repository you want to deploy from (`test`, `beta`, `main`)
- Make all code changes in the `dev` branch (or configure the approval/promotion option in the pipeline).
- To initiate a deployment, just merge your code from the `dev` branch to the `test` branch and push. This will kick-off the test deployment pipeline.
- You can subsequently deploy your code to the next branch/instance (`beta` and `main`/`prod`) by merging and pushing to each (or by configuring an approval/promotion option in the pipeline).

Follow your organization's guidelines for repository and pipeline management.

## Prerequisites

Before deploying this application, ensure the following are in place:

- The pipeline's CloudFormation service role must include a CodeBuild managed policy. Add it via the `CloudFormationSvcRoleIncludeManagedPolicyArns` pipeline parameter — this allows the CloudFormation service role to create and manage CodeBuild, EventBridge Scheduler, and related resources in the application stack.
- An S3 DevOps bucket (using `template-storage-s3-devops.yml`) must be deployed with the same `Prefix` and `ProjectId` to grant the pipeline's CodeBuild project permission to copy `commands.yml` and `scripts/` to the S3 Static Host Bucket.
- The `S3StaticHostBucket` parameter of the DevOps bucket must be passed to the pipeline — this is the S3 bucket name where `commands.yml` and `scripts/` are stored for the Scheduled CodeBuild.

## Why Use Atlantis for Deployment?

Like any other project, you can skip the Atlantis platform and go at it on your own using `sam deploy` from the CLI within the application-infrastructure directory.

However, the [Atlantis DevOps Platform](https://atlantis.63klabs.net) is highly recommended for individual developers and small teams as it implements Platform Engineering, AWS best practices, and deployment automation. It utilizes AWS native resources including SAM deployments and CloudFormation without the need of proprietary DevOps tools. Everything is API, CloudFormation template, and SAM CLI based as well as AI-ready.

## Create Repository and Initialize with this Code

Using the Atlantis SAM Config scripts in your organization's central infrastructure repository, deploy the S3 bucket and pipeline. They must use the same `Prefix` and `ProjectId`.

First, deploy the S3 DevOps Bucket to save your scheduled buildspec file and scripts:

```bash
./cli/config.py storage PREFIX YOUR_PROJECT_ID --profile default
# Choose template-storage-s3-devops.yml

# Deploy the pipeline (if you didn't choose to deploy right away from the config script)
./cli/deploy.py storage PREFIX YOUR_PROJECT_ID --profile default
```

Next, create the repository and pipeline:

```bash
./cli/create_repo.py YOUR_REPO_NAME --profile default
# Choose 03-serverless-codebuild-container.zip

# Create a pipeline for the test branch
./cli/config.py pipeline PREFIX YOUR_PROJECT_ID test --profile default
# Choose template-pipeline.yml (CodeCommit source) or template-pipeline-github.yml

# Deploy the pipeline (if you didn't choose to deploy right away from the config script)
./cli/deploy.py pipeline PREFIX YOUR_PROJECT_ID test --profile default
```

Once the pipeline is created the first deployment will automatically kick off. You can follow it in the web console using the link provided in the Output.

Make sure it deploys without errors before going to the `dev` branch and making changes.

Clone the repository to your local machine:

```bash
git clone HTTPS_CLONE_URL

cd YOUR_CLONED_REPO

git switch dev
```

## Development and Deploy Process

Always make and commit your changes in `dev`

Perform merges to advance code to the next branch. `dev` -> `test` -> `beta` -> `main`

```bash
git switch test
git merge dev
git push
# Always return to dev for new changes
git switch dev
```

When you are ready to move code to the next stage, merge:

```bash
git switch test
git pull # always a good idea
git switch beta
git pull # always a good idea
git merge test
git push
# Always return to dev for new changes
git switch dev
```

### Setting Up Pipelines

For each branch/stage you wish to deploy from, set up a pipeline using your organization's central Atlantis SAM Config repository.

There are several pipeline configurations to choose from. If you prefer to not use the branch merge strategy (`dev` -> `test` -> `beta` -> `main`) you can configure the pipeline to use an approval and promotion strategy instead. Cross account configuration is also available.

All Atlantis pipeline templates support approval with promotion and cross-account deployment.

#### Standard Branch-Merge-Based

This will set up deployments for each branch and you will merge changes between them to deploy (`dev` -> `test` -> `beta` -> `main`).

- This is the least complex as it is all Git-based (no logging into the console for approvals.)
- **HOWEVER**: It requires discipline, only forward merges, and squash merges may produce unpredictable results.

Choose template-pipeline.yml (CodeCommit source) or template-pipeline-github.yml and do not enable the approval and promotion configuration. 

```bash
# Create a pipeline for the beta branch
./cli/config.py pipeline PREFIX YOUR_PROJECT_ID beta --profile default
# Choose template-pipeline.yml (CodeCommit source) or template-pipeline-github.yml

# Deploy the pipeline (if you didn't choose to deploy right away from the config script)
./cli/deploy.py pipeline PREFIX YOUR_PROJECT_ID beta --profile default
```

#### Approve/Promote and/or Cross-Account

> Cross-account deployments must use the approve/promote configuration.

This will set up an automatic Git-based deployment for the `test` branch but to deploy your application to subsequent stages you will need to:

1. Configure the `test` pipeline to promote to the next stage
2. All subsequent deployment stages use `template-pipeline-s3-source.yml`

Automated deployment process using approve/promote:

1. The test pipeline will still run automatically when changes are merged to the `test` branch.
2. Then, to promote to the next stage, go into the console for the test pipeline and choose approve promotion.
3. The pipeline will then drop the deployment artifact in an S3 bucket, triggering the next pipeline (which can either be in the same account, or in a separate PROD account depending on your organization's policies).
4. The receiving pipeline will then pick up the new artifact from S3 and await an approval to deploy.
5. The end of this pipeline can also have an approval/promote option. (In case you deploy from test to beta to prod).

You will still need to create one pipeline per stage and only the test branch will have a corresponding stage. (However, you _can_ set up the main branch, or any branch, to deploy to the initial "test" pipeline, it doesn't need to be the `test` branch. Just be sure to set the `StageId` to `test`). You can always create temporary pipelines using `template-pipeline.yml`/`template-pipeline-github.yml` for feature and bug fix test branches.

> By default approval is required to promote and deploy both at the end of the pipeline (promote) and at the start of the next stage (approve). This provides optimal protection against run-away deployments. If you want to disable either the promote or deploy approval, it is recommended you disable the deploy approval at the start of the receiving stage to avoid creating too many deploy artifact versions.
