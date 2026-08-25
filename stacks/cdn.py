from aws_cdk import CfnOutput, Stack, aws_s3 as s3
from constructs import Construct

from construct.cloudfront import CloudFrontConstruct


class CdnStack(Stack):
    """S3 を OAC で配信する CloudFront。"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        bucket: s3.IBucket,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # バケットを「インポート済み」として扱う。こうすると CDK は
        # バケットポリシーに触らなくなり、StorageStack への参照が
        # 一方向 (Cdn -> Storage) になって循環参照を避けられる。
        # 読み取り許可は StorageStack 側で付与済み。
        origin_bucket = s3.Bucket.from_bucket_name(
            self, "OriginBucket", bucket.bucket_name
        )

        self.distribution = CloudFrontConstruct(
            self, "CloudFront", bucket=origin_bucket
        ).distribution

        CfnOutput(
            self,
            "DistributionUrl",
            value=f"https://{self.distribution.distribution_domain_name}",
            description="CloudFront endpoint serving the S3 bucket",
        )
