# Serverless CodeBuild Container

An example to demonstrate Atlantis provisioning a container service utilizing a CodeBuild Project triggered by an Event Schedule to run jobs.

| | Build/Deploy | Application Stack |
|---|---|---|
| **Languages** | Python, Shell | Shell, Python, Node.js |
| **Frameworks** | Atlantis | Atlantis |
| **Features** | SSM Parameters | CodeBuild Project, Event Scheduler, CloudWatch Logs, CloudWatch Alarms |

> **Ready-to-Deploy-and-Run** with the [63Klabs Atlantis Templates and Scripts Platform for Serverless Deployments on AWS](https://github.com/63Klabs/atlantis)

## Why Use Over a Self-Managed Container?

First, you may not need a container when the AWS managed Linux environment provided by CodeBuild will do.

If you just need to run scripts on a periodic basis, and you don't need persistence between runs, CodeBuild provides a lightweight option on an environment managed by AWS. However, you should use your own self-managed container when you need to install applications or require installs, data, and advanced configurations to persist between runs.

With the ability to mount S3 as an NFS you can extend persistence within CodeBuild.

## Why Use Over Lambda?

Scheduled Lambda functions serve their purpose, but if you are running a combination of shell, Python, and/or Node.js scripts, or you just need to run scripts "off the shelf" without modifying to run inside Lambda, CodeBuild is a good option.

What about Lambda containers? We'll return to the fact that you may not need a container when the AWS managed Linux environment provided by CodeBuild will do.

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
