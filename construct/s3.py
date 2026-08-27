from aws_cdk import RemovalPolicy, Stack, aws_iam as iam, aws_s3 as s3
from constructs import Construct


class S3Construct(Construct):
    """アプリの静的コンテンツ用バケット。

    CloudFront + OAC から読ませる前提なので、パブリックアクセスは全て遮断し、
    静的ウェブサイトホスティングは有効化しない。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        versioned: bool = True,
        removal_policy: RemovalPolicy = RemovalPolicy.DESTROY,
        auto_delete_objects: bool = True,
    ) -> None:
        super().__init__(scope, construct_id)

        self.bucket = s3.Bucket(
            self,
            "ManagedByCDK",
            versioned=versioned,
            removal_policy=removal_policy,
            auto_delete_objects=auto_delete_objects,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
        )

    def grant_cloudfront_read(self) -> None:
        """OAC 経由の CloudFront に GetObject を許可する。

        CloudFront を別スタックに置くと、Distribution が「バケット」を参照し
        バケットポリシーが「Distribution の ARN」を参照するため循環参照になる。
        そこで条件を SourceArn ではなく SourceAccount にして参照を断ち切り、
        許可はバケット側 (このスタック) で完結させる。自アカウントの
        Distribution からのみ読める状態で、パブリック公開にはならない。
        """
        self.bucket.add_to_resource_policy(
            iam.PolicyStatement(
                sid="AllowCloudFrontServicePrincipalReadOnly",
                actions=["s3:GetObject"],
                resources=[self.bucket.arn_for_objects("*")],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                conditions={
                    "StringEquals": {
                        "AWS:SourceAccount": Stack.of(self).account
                    }
                },
            )
        )
