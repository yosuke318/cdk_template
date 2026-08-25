from aws_cdk import Stack
from constructs import Construct

from construct.dynamodb import DynamoDbConstruct
from construct.ecr import EcrConstruct
from construct.s3 import S3Construct
from construct.secrets_manager import SecretConstruct


class StorageStack(Stack):
    """状態を持つリソース。作り直したくないものをここにまとめる。

    RemovalPolicy は Construct 側の既定で DESTROY。本番に載せる時は
    S3 と DynamoDB を RETAIN に変える。
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        s3_construct = S3Construct(self, "S3")
        # CloudFront (CdnStack) からの読み取り許可はここで付ける。
        # 詳細は S3Construct.grant_cloudfront_read の docstring を参照。
        s3_construct.grant_cloudfront_read()
        self.bucket = s3_construct.bucket
        self.table = DynamoDbConstruct(self, "DynamoDb").table
        self.repository = EcrConstruct(self, "Ecr").repository
        self.secret = SecretConstruct(self, "Secret").secret
