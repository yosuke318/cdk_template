from aws_cdk import (
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_logs as logs,
)
from constructs import Construct


class ApiGatewayConstruct(Construct):
    """Lambda をプロキシ統合で公開する REST API。

    アクセスログを明示的に出す。デフォルトでは何も残らないため、
    404 や 5xx の切り分けができない。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        handler: lambda_.IFunction,
        access_log_group: logs.ILogGroup,
        stage_name: str = "api",
        allow_origins: list[str] | None = None,
    ) -> None:
        super().__init__(scope, construct_id)

        self.api = apigateway.LambdaRestApi(
            self,
            "RestApi",
            handler=handler,
            proxy=True,
            # アクセスログには API Gateway 用のアカウントレベル CloudWatch ロールが要る。
            # これは「リージョンごとに1つ」の設定なので、同じアカウントで複数の CDK アプリを
            # 動かす場合はどれか1つだけで作ること。
            cloud_watch_role=True,
            deploy_options=apigateway.StageOptions(
                stage_name=stage_name,
                access_log_destination=apigateway.LogGroupLogDestination(
                    access_log_group
                ),
                access_log_format=apigateway.AccessLogFormat.json_with_standard_fields(
                    caller=False,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=False,
                ),
                metrics_enabled=True,
                throttling_burst_limit=100,
                throttling_rate_limit=50,
            ),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=allow_origins or apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
            ),
        )
