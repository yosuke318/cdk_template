from aws_cdk import RemovalPolicy, aws_logs as logs
from constructs import Construct


class LogGroupConstruct(Construct):
    """ロググループを明示的に作るための薄いラッパー。

    Lambda や ECS に暗黙で作らせるとリテンションが「無期限」になり、
    スタックを消してもログが残り続けて課金される。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        log_group_name: str | None = None,
        retention: logs.RetentionDays = logs.RetentionDays.ONE_MONTH,
        removal_policy: RemovalPolicy = RemovalPolicy.DESTROY,
    ) -> None:
        super().__init__(scope, construct_id)

        self.log_group = logs.LogGroup(
            self,
            "LogGroup",
            log_group_name=log_group_name,
            retention=retention,
            removal_policy=removal_policy,
        )
