import json
import logging
import os
import time
import urllib.error
import urllib.request

import boto3

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

SQS_ENDPOINT = os.environ.get("SQS_ENDPOINT", "http://localstack:4566")
SQS_QUEUE_URL = os.environ["SQS_QUEUE_URL"]
LAMBDA_ENDPOINT = os.environ["LAMBDA_ENDPOINT"]
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

sqs = boto3.client(
    "sqs",
    region_name=AWS_REGION,
    endpoint_url=SQS_ENDPOINT,
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
)


def wait_for_queue() -> None:
    logger.info("Waiting for SQS queue to be available...")
    while True:
        try:
            sqs.get_queue_attributes(QueueUrl=SQS_QUEUE_URL, AttributeNames=["All"])
            logger.info("SQS queue is ready")
            return
        except Exception as exc:
            logger.warning("Queue not ready: %s — retrying in 2s", exc)
            time.sleep(2)


def wait_for_lambda() -> None:
    logger.info("Waiting for Lambda RIE to be available...")
    while True:
        try:
            req = urllib.request.Request(
                LAMBDA_ENDPOINT,
                data=b"{}",
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
            logger.info("Lambda RIE is ready")
            return
        except Exception as exc:
            logger.warning("Lambda not ready: %s — retrying in 2s", exc)
            time.sleep(2)


def build_sqs_event(messages: list) -> dict:
    return {
        "Records": [
            {
                "messageId": msg["MessageId"],
                "receiptHandle": msg["ReceiptHandle"],
                "body": msg["Body"],
                "attributes": msg.get("Attributes", {}),
                "messageAttributes": msg.get("MessageAttributes", {}),
                "md5OfBody": msg.get("MD5OfBody", ""),
                "eventSource": "aws:sqs",
                "eventSourceARN": "arn:aws:sqs:us-east-1:000000000000:lambda-queue",
                "awsRegion": AWS_REGION,
            }
            for msg in messages
        ]
    }


def invoke_lambda(event: dict) -> bytes:
    payload = json.dumps(event).encode()
    req = urllib.request.Request(
        LAMBDA_ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def main() -> None:
    wait_for_queue()
    wait_for_lambda()
    logger.info("Poller started — polling %s", SQS_QUEUE_URL)

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
            )
            messages = response.get("Messages", [])
            if not messages:
                continue

            logger.info("Received %d message(s)", len(messages))
            event = build_sqs_event(messages)

            try:
                result = invoke_lambda(event)
                logger.info("Lambda response: %s", result.decode())

                for msg in messages:
                    sqs.delete_message(
                        QueueUrl=SQS_QUEUE_URL,
                        ReceiptHandle=msg["ReceiptHandle"],
                    )
                    logger.info("Deleted message %s", msg["MessageId"])

            except urllib.error.URLError as exc:
                logger.error("Lambda invocation failed: %s", exc)

        except Exception as exc:
            logger.error("Polling error: %s — retrying in 5s", exc)
            time.sleep(5)


if __name__ == "__main__":
    main()
