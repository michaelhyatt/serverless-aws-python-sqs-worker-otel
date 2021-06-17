<!--
title: 'Serverless Framework Python SQS Producer-Consumer on AWS'
description: 'This template demonstrates how to develop and deploy a simple SQS-based producer-consumer service running on AWS Lambda using the traditional Serverless Framework.'
layout: Doc
framework: v2
platform: AWS
language: Python
authorLink: 'https://github.com/serverless'
authorName: 'Serverless, inc.'
authorAvatar: 'https://avatars1.githubusercontent.com/u/13742415?s=200&v=4'
-->

# Serverless Framework Python SQS Producer-Consumer on AWS

This template demonstrates how to develop and deploy a simple SQS-based producer-consumer service running on AWS Lambda using the traditional Serverless Framework. It allows to accept messages, for which computation might be time or resource intensive, and offload their processing to an asynchronous background process for a faster and more resilient system.

## Support for AWS Distro for OpenTelemetry for Lambdas
This project was changed to work with ADOT4L and currently supports specifying Elastic APM server as the OTel intake point (collector.yaml).

## Anatomy of the template

This template defines two functions, `producer` and `consumer`. First of them, `producer`, is triggered by `http` event type, accepts JSON payload and sends it to a corresponding SQS queue for further processing. To learn more about `http` event configuration options, please refer to [http event docs](https://www.serverless.com/framework/docs/providers/aws/events/apigateway/). Second function, `consumer`, is responsible for processing messages from SQS queue thanks to its `sqs` trigger definition. To learn more about `sqs` event configuration options, please refer to [sqs event docs](https://www.serverless.com/framework/docs/providers/aws/events/sqs/). Additionally, the template takes care of provisioning underlying SQS queue along with corresponding SQS dead-letter queue, which are defined in `resources` section. The dead-letter queue is defined in order to prevent processing invalid messages over and over. In our case, if message is delivered to the source queue more than 5 times, it will be moved to dead-letter queue. For more details, please refer to official [AWS documentation](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html). To learn more about `resources`, please refer to [our docs](https://www.serverless.com/framework/docs/providers/aws/guide/resources/).

## Usage

### Deployment

This example requires `git`, `serverless` framework and `npm` to be installed.

Clone the repo, install npm dependencies
```
git clone https://github.com/michaelhyatt/serverless-aws-python-sqs-worker-otel
cd serverless-aws-python-sqs-worker-otel
npm install
npm install --save-dev serverless-plugin-lambda-insights
```

Copy `env.json.template` into `env.json` and update the right region and APM server credentials:
```json
{
    "aws-region": "ap-southeast-1",
    "apm-server-url": "YOURCLUSTER.apm.australia-southeast1.gcp.elastic-cloud.com:443",
    "apm-server-token": "YOURTOKEN"
}

```

Deploy the lambdas
```
serverless deploy
```

To remove lambdas
```
serverless remove
```


After running deploy, you should see output similar to:

```bash
Serverless: Packaging service...
Serverless: Excluding development dependencies...
Serverless: Creating Stack...
Serverless: Checking Stack create progress...
........
Serverless: Stack create finished...
Serverless: Uploading CloudFormation file to S3...
Serverless: Uploading artifacts...
Serverless: Uploading service aws-python-sqs-worker.zip file to S3 (1.04 KB)...
Serverless: Validating template...
Serverless: Updating Stack...
Serverless: Checking Stack update progress...
................................................
Serverless: Stack update finished...
Service Information
service: aws-python-sqs-worker
stage: dev
region: us-east-1
stack: aws-python-sqs-worker-dev
resources: 17
api keys:
  None
endpoints:
  POST - https://xxxxxxx.execute-api.us-east-1.amazonaws.com/dev/produce
functions:
  producer: aws-python-sqs-worker-dev-producer
  consumer: aws-python-sqs-worker-dev-consumer
layers:
  None
```

_Note_: In current form, after deployment, your API is public and can be invoked by anyone. For production deployments, you might want to configure an authorizer. For details on how to do that, refer to [http event docs](https://www.serverless.com/framework/docs/providers/aws/events/apigateway/).

### Invocation

After successful deployment, you can now call the created API endpoint with `POST` request to invoke `producer` function:

```bash
curl --request POST 'https://xxxxxx.execute-api.us-east-1.amazonaws.com/dev/produce' --header 'Content-Type: application/json' --data-raw '{"name": "John"}'
```

In response, you should see output similar to:

```bash
{"message": "Message accepted!"}
```

### Bundling dependencies

In case you would like to include 3rd party dependencies, you will need to use a plugin called `serverless-python-requirements`. You can set it up by running the following command:

```bash
serverless plugin install -n serverless-python-requirements
```

Running the above will automatically add `serverless-python-requirements` to `plugins` section in your `serverless.yml` file and add it as a `devDependency` to `package.json` file. The `package.json` file will be automatically created if it doesn't exist beforehand. Now you will be able to add your dependencies to `requirements.txt` file (`Pipfile` and `pyproject.toml` is also supported but requires additional configuration) and they will be automatically injected to Lambda package during build process. For more details about the plugin's configuration, please refer to [official documentation](https://github.com/UnitedIncome/serverless-python-requirements).
