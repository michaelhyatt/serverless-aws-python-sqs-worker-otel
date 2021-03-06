#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from os import environ, system
import sys

# the path to the interpreter and all of the originally intended arguments
args = sys.argv[1:]

# enable OTel wrapper
environ["ORIG_HANDLER"] = environ.get("_HANDLER")
environ["_HANDLER"] = "otel_wrapper.lambda_handler"

# config OTel
environ["OTEL_TRACES_EXPORTER"] = "otlp_proto_grpc_span"

# Setting W3C context propagation - unable to receive them from lambda environment
environ["OTEL_PROPAGATORS"] = "tracecontext"

# set service name
if environ.get("OTEL_RESOURCE_ATTRIBUTES") is None:
    environ["OTEL_RESOURCE_ATTRIBUTES"] = "service.name=%s" % (
        environ.get("AWS_LAMBDA_FUNCTION_NAME")
    )
elif "service.name=" not in environ.get("OTEL_RESOURCE_ATTRIBUTES"):
    environ["OTEL_RESOURCE_ATTRIBUTES"] = "service.name=%s,%s" % (
        environ.get("AWS_LAMBDA_FUNCTION_NAME"),
        environ.get("OTEL_RESOURCE_ATTRIBUTES"),
    )

# TODO: Remove if sdk support resource detector env variable configuration.
lambda_resource_attributes = (
    "cloud.region=%s,cloud.provider=aws,faas.name=%s,faas.version=%s"
    % (
        environ.get("AWS_REGION"),
        environ.get("AWS_LAMBDA_FUNCTION_NAME"),
        environ.get("AWS_LAMBDA_FUNCTION_VERSION"),
    )
)
environ["OTEL_RESOURCE_ATTRIBUTES"] = "%s,%s" % (
    lambda_resource_attributes,
    environ.get("OTEL_RESOURCE_ATTRIBUTES"),
)

# start the runtime with the extra options
system(" ".join(args))