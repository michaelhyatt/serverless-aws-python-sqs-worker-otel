import json
import logging
import os
import boto3
import time

from opentelemetry import trace
from opentelemetry.trace import SpanKind


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

QUEUE_URL = os.getenv('QUEUE_URL')
SQS = boto3.client('sqs')


def producer(event, context):
    status_code = 200
    message = ''

    # Get trace context if exists. If not, create the request with fresh context
    span_context = get_trace_context(event=event)

    tracer = trace.get_tracer(__name__)

    # Create the top-level transaction representing the lqmbda work
    with tracer.start_as_current_span(name="sqs-producer-function-top-level", context=span_context, kind=SpanKind.SERVER):    

        if not event.get('body'):
            return {'statusCode': 400, 'body': json.dumps({'message': 'No body was found'})}

        time.sleep(2)

        try:
            message_attrs = {
                'AttributeName': {'StringValue': 'AttributeValue', 'DataType': 'String'}
            }

            inject_context_into_request(message_attrs)

            SQS.send_message(
                QueueUrl=QUEUE_URL,
                MessageBody=event['body'],
                MessageAttributes=message_attrs,
            )
            message = 'Message accepted!'
        except Exception as e:
            logger.exception('Sending message to SQS queue failed!')
            message = str(e)
            status_code = 500

    return {'statusCode': status_code, 'body': json.dumps({'message': message})}


def consumer(event, context):

    tracer = trace.get_tracer(__name__)

    for record in event['Records']:

        # Get trace context sent from the other lambda
        span_context = get_trace_context_from_sqs_message(event=record)

        # Create top level transaction representing the lambda work for every message
        with tracer.start_as_current_span("sqs-consumer-function-top-level", context=span_context, kind=SpanKind.SERVER): 

            time.sleep(2)

            with tracer.start_as_current_span("sqs-consumer-function-some-internal-work", kind=SpanKind.INTERNAL):
                logger.info(f'Message: {record}')
                logger.info(f'Message body: {record["body"]}')
                logger.info(
                    f'Message attribute: {record["messageAttributes"]["AttributeName"]["stringValue"]}'
                )

                time.sleep(1)
       

# Utility functions
import typing
from opentelemetry import propagate

CarrierT = typing.TypeVar("CarrierT")

from opentelemetry.propagators.textmap import Getter, Setter

PROPAGATOR = propagate.get_global_textmap()

class get_header_from_event_request(Getter):
    def get(self, carrier: CarrierT, key: str) -> typing.Optional[typing.List[str]]:
        value = carrier['headers'].get(key)
        logger.debug(f'Getter requested {key}. Value returned {value}')
        return [value] if value is not None else []
        
    def keys(self, carrier: CarrierT) -> typing.List[str]:
        value = list(carrier['headers'].keys())
        logger.debug(f'Keys: {value}')
        return value

class set_header_into_sqs_message(Setter):
    def set(self, message: typing.Dict, key: str, value: str) -> None:
        logger.debug(f'Setter requested for {key} to value {value}')
        message[key] = {
            'StringValue': value,
            'DataType': 'String'
        }

class get_header_from_sqs_message(Getter):
    def get(self, carrier: CarrierT, key: str) -> typing.Optional[typing.List[str]]:
        value = carrier['messageAttributes'].get(key)
        logger.debug(f'Getter requested {key}. Value found {value}')
        
        if value is None:
            return []

        string_value = value.get('stringValue')
        logger.debug(f'Getter requested {key}. Value returned {string_value}')
        return [string_value] if string_value is not None else []
        
    def keys(self, carrier: CarrierT) -> typing.List[str]:
        value = list(carrier['messageAttributes'].keys())
        logger.debug(f'Keys: {value}')
        return value

# Retrieves trace context from lambda event
def get_trace_context(event):
    return PROPAGATOR.extract(getter=get_header_from_event_request(), carrier=event)

# Injects trace context into requests HTTP header
def inject_context_into_request(message_attrs):
    PROPAGATOR.inject(carrier=message_attrs, setter=set_header_into_sqs_message())

# Retrieves trace context from sqs message
def get_trace_context_from_sqs_message(event):
    return PROPAGATOR.extract(getter=get_header_from_sqs_message(), carrier=event)