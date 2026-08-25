from aws_cdk import Stack, aws_dynamodb as dynamodb
from constructs import Construct

from construct.api_gateway import ApiGatewayConstruct
from construct.lambda_function import LambdaConstruct
from construct.logs import LogGroupConstruct


class ApiStack(Stack):
    """Lambda + API Gateway。DynamoDB テーブルを読み書きする。"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        table: dynamodb.ITableV2,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        function_logs = LogGroupConstruct(self, "FunctionLogs").log_group
        access_logs = LogGroupConstruct(self, "ApiAccessLogs").log_group

        api_function = LambdaConstruct(
            self,
            "ApiFunction",
            log_group=function_logs,
            environment={"TABLE_NAME": table.table_name},
        ).function

        table.grant_read_write_data(api_function)

        self.api = ApiGatewayConstruct(
            self,
            "ApiGateway",
            handler=api_function,
            access_log_group=access_logs,
        ).api
