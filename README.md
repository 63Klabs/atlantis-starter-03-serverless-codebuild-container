# Serverless CodeBuild Container

An example to demonstrate Atlantis provisioning a container service utilizing a CodeBuild Project triggered by an Event Schedule to run jobs.

| | Build/Deploy | Application Stack |
|---|---|---|
| **Languages** | Python, Shell | Shell, Python, Node.js |
| **Frameworks** | Atlantis | Atlantis |
| **Features** | SSM Parameters | CodeBuild Project, Event Scheduler, CloudWatch Logs, CloudWatch Alarms |

> **Ready-to-Deploy-and-Run** with the [63Klabs Atlantis Templates and Scripts Platform for Serverless Deployments on AWS](https://github.com/63Klabs/atlantis)

## Why Use Over a Self-Managed Container or Lambda?

Lambda only provides a single runtime, and any "off the shelf" scripts require modification to run inside a function.

Containers require additional management, upgrades, installs.

CodeBuild provides a managed service, a clean slate, ability to run a variety of scripts and commands.

Data and file persistence can be maintained by:
- Cloning a repo (read only)
- S3 sync or copy
- S3 File System mount
- CLI or API calls

If system persistence is not required, then CodeBuild is a good, lightweight, low-maintenance option and this application is meant to fill that need.

> **NOTE:** If you require system persistence with installed applications and configurations then you may be better off managing a container. 

## Tutorial

1. Read the [Atlantis Tutorials introductory page](https://github.com/63Klabs/atlantis-tutorials)
2. Then perform the steps outlined in the [Run CodeBuild on a Schedule for Operations tutorial](https://github.com/63Klabs/atlantis-tutorials/blob/main/tutorials/05-run-codebuild-on-a-schedule-for-operations/).

## Architecture

See [Architecture](./ARCHITECTURE.md)

## Deployment Guide

See [Deployment Guide](./DEPLOYMENT.md)

## Advanced Documentation

See [Docs Directory](./docs/README.md)

## AI Context

See [AGENTS.md](./AGENTS.md) for important context and guidelines for AI-generated code in this repository.

The agents file is also helpful (and perhaps essential) for HUMANS developing within the application's structured platform as well.

## Changelog

See [Change Log](./CHANGELOG.md)

## Security

See [SECURITY.md](./SECURITY.md)

## Contributors

- [63Klabs](https://github.com/63klabs)
- [Chad Kluck](https://github.com/chadkluck)
