from aws_cdk import (
    aws_s3 as s3,
    RemovalPolicy,
    Stack
)

from constructs import Construct

class S3Construct(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket
        self.bucket = s3.Bucket(
            self,
            "ManagedByCDK",
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )