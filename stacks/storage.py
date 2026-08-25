from aws_cdk import Stack
from constructs import Construct

from config import StageConfig
from construct.dynamodb import DynamoDbConstruct
from construct.ecr import EcrConstruct
from construct.s3 import S3Construct
from construct.secrets_manager import SecretConstruct


class StorageStack(Stack):
    """状態を持つリソース。作り直したくないものをここにまとめる。

    RemovalPolicy はステージ設定に従う (prod は RETAIN)。
    """

    def __init__(
        self, scope: Construct, construct_id: str, *, config: StageConfig, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        s3_construct = S3Construct(
            self,
            "S3",
            removal_policy=config.removal_policy,
            auto_delete_objects=config.auto_delete_objects,
        )
        # CloudFront (CdnStack) からの読み取り許可はここで付ける。
        # 詳細は S3Construct.grant_cloudfront_read の docstring を参照。
        s3_construct.grant_cloudfront_read()
        self.bucket = s3_construct.bucket

        self.table = DynamoDbConstruct(
            self,
            "DynamoDb",
            removal_policy=config.removal_policy,
            point_in_time_recovery=config.point_in_time_recovery,
        ).table

        self.repository = EcrConstruct(
            self, "Ecr", removal_policy=config.removal_policy
        ).repository

        self.secret = SecretConstruct(
            self, "Secret", removal_policy=config.removal_policy
        ).secret
