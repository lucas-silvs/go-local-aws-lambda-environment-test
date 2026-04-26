#!/bin/bash
set -e

echo "[init] Creating SQS queue: lambda-queue"

awslocal sqs create-queue \
    --queue-name lambda-queue \
    --attributes VisibilityTimeout=30,MessageRetentionPeriod=86400

echo "[init] Queue created. Listing queues:"
awslocal sqs list-queues
