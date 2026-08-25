from aws_cdk import (
    Duration,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
)
from constructs import Construct


class CloudFrontConstruct(Construct):
    """S3 を OAC で配信する CloudFront ディストリビューション。

    OAC ではバケットをパブリックにしない。S3BucketOrigin.with_origin_access_control
    がバケットポリシーに「この Distribution だけ読める」条件を自動で追加する。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        bucket: s3.IBucket,
        default_root_object: str = "index.html",
        price_class: cloudfront.PriceClass = cloudfront.PriceClass.PRICE_CLASS_200,
        spa_fallback: bool = True,
    ) -> None:
        super().__init__(scope, construct_id)

        error_responses = []
        if spa_fallback:
            # SPA のクライアントサイドルーティング用。S3 が返す 403/404 を
            # index.html にフォールバックさせる。
            error_responses = [
                cloudfront.ErrorResponse(
                    http_status=status,
                    response_http_status=200,
                    response_page_path=f"/{default_root_object}",
                    ttl=Duration.seconds(0),
                )
                for status in (403, 404)
            ]

        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress=True,
            ),
            default_root_object=default_root_object,
            error_responses=error_responses,
            price_class=price_class,
            http_version=cloudfront.HttpVersion.HTTP2_AND_3,
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
        )
