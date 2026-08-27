import os

from aws_cdk import Duration, aws_lambda as lambda_, aws_logs as logs
from constructs import Construct

_ASSET_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "lambda"
)


class LambdaConstruct(Construct):
    """API のバックエンドになる Lambda 関数。

    ロググループは呼び出し側から渡す。渡さないと Lambda が暗黙で無期限の
    ロググループを作ってしまい、スタックを消しても残る。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        log_group: logs.ILogGroup,
        asset_dir: str = "api",
        handler: str = "index.handler",
        runtime: lambda_.Runtime = lambda_.Runtime.PYTHON_3_12,
        memory_size: int = 256,
        timeout: Duration = Duration.seconds(30),
        environment: dict[str, str] | None = None,
    ) -> None:
        super().__init__(scope, construct_id)

        self.function = lambda_.Function(
            self,
            "Function",
            runtime=runtime,
            handler=handler,
            code=lambda_.Code.from_asset(os.path.join(_ASSET_ROOT, asset_dir)),
            memory_size=memory_size,
            timeout=timeout,
            environment=environment or {},
            log_group=log_group,
            tracing=lambda_.Tracing.ACTIVE,
        )
