from aws_cdk import RemovalPolicy, Stack
from construct.S3 import S3Construct
from constructs import Construct

class S3Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        S3Construct(self, "S3Construct")
