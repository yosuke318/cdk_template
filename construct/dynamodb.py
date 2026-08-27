from aws_cdk import RemovalPolicy, aws_dynamodb as dynamodb
from constructs import Construct


class DynamoDbConstruct(Construct):
    """アプリのメインテーブル。

    トラフィックが読めないうちはオンデマンド課金 (PAY_PER_REQUEST) が無難。
    定常負荷が見えてから PROVISIONED に切り替える。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        partition_key_name: str = "pk",
        sort_key_name: str | None = "sk",
        removal_policy: RemovalPolicy = RemovalPolicy.DESTROY,
        point_in_time_recovery: bool = False,
    ) -> None:
        super().__init__(scope, construct_id)

        self.table = dynamodb.TableV2(
            self,
            "Table",
            partition_key=dynamodb.Attribute(
                name=partition_key_name, type=dynamodb.AttributeType.STRING
            ),
            sort_key=(
                dynamodb.Attribute(
                    name=sort_key_name, type=dynamodb.AttributeType.STRING
                )
                if sort_key_name
                else None
            ),
            billing=dynamodb.Billing.on_demand(),
            point_in_time_recovery=point_in_time_recovery,
            removal_policy=removal_policy,
        )
