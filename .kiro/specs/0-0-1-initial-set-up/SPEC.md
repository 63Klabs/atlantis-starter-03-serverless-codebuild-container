# Initial Set-Up

The purpose of this application will be to provide a CodeBuild environment that runs on a schedule as an alternative to managing a container or using a Lambda function.

Lambda only provides a single runtime, and any "off the shelf" scripts require modification to run inside a function.

Containers require additional management, upgrades, installs.

CodeBuild provides a managed service, a clean slate, ability to run a variety of scripts and commands.

Data and file persistence can be maintained by:
- Cloning a repo (read only)
- S3 sync or copy
- S3 File System mount
- CLI or API calls

If system persitence is not required, then CodeBuild is a good, lightweight, low-maintenance option and this application is meant to fill that need.

This application will be deployed using the Atlantis Platform, specifically the pipeline template template-pipeline.yml

Deployment strategies do NOT need to be created. The method to deploy is already outlined in DEPLOYMENT.md. This does not need to be re-documented.

Review the project for an understanding of the architecture and structure. It is already scaffoled and ready for development. All documents have been updated EXCEPT the YAML definitions in template.yml.

template.yml still includes API Gateway and Lambda resource definitions. These need to be replaced by Event Scheduler and CodeBuild Project definitions.

This project MUST follow Atlantis Template and Script Platform patterns. Use the Atlantis mcp and AGENTS.md along with existing project documents to understand design patterns and structure.

Documentation for developers (docs/developer) should include options for mounting S3 as a file system, copying files from or to S3, syncing files to S3, cloning a repository, using AWS CLI or other commands.

Documentation for end-users (docs/end-user) can remain sparse as this project is a template for admins and developers. They will fill in their own scripts, use cases, and end-user documentation. 

Documentation for admins (docs/admin-ops) should be limited to setting runtime environments for both codebuild environments.

Note there are 2 CodeBuilds:
The one defined by the deployment pipeline and uses application-infrastructure/buildspec.yml and build-scripts, and the scheduled CodeBuild project defined in template.yml and uses src/commands.yml as the buildspec, and src/scripts

Be sure to examine what the deployment CodeBuild provides (template-pipeline.yml), and structure this applications' CodeBuild definition the same way.

S3_STATIC_HOST_BUCKET is an environment variable available in the Pipeline CodeBuild to copy files to.

The commands.yml file will need to be copied to S3_STATIC_HOST_BUCKET/<Prefix>-<ProjectId>-<StageId> so it can be referenced by the scheduled CodeBuild project as the BuildSpec file from S3. The scripts directory will also need to be copied to S3.

The S3_STATIC_HOST_BUCKET will be created prior to deployment and passed to the pipeline via S3StaticHostBucket parameter to the template. Instructions to deploy the static host bucket using storage template-storage-s3-devops.yml as well as passing the S3StaticHostBucket parameter to the pipeline should be included in the Deployment instructions.

In commands.yml, be sure to add an example script or command that gets the parameter from parameter store that was created during the buildspec.yml

Ask any clarifying questions, and make any recommendations for approval in SPEC-QUESTIONS.md and the user will answer them there before we move onto the spec driven workflow.
