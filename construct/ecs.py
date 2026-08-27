from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct


class EcsConstruct(Construct):
    """Fargate で動かすアプリケーションサービス。

    イメージは ECR から引く。つまり初回 deploy の前にイメージを 1 つ push して
    おかないとサービスが安定せず、スタックがロールバックする。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        security_group: ec2.ISecurityGroup,
        repository: ecr.IRepository,
        log_group: logs.ILogGroup,
        image_tag: str = "latest",
        container_port: int = 80,
        cpu: int = 256,
        memory_limit_mib: int = 512,
        desired_count: int = 1,
        environment: dict[str, str] | None = None,
        secrets: dict[str, secretsmanager.ISecret] | None = None,
    ) -> None:
        super().__init__(scope, construct_id)

        self.cluster = ecs.Cluster(
            self,
            "Cluster",
            vpc=vpc,
            container_insights_v2=ecs.ContainerInsights.ENABLED,
        )

        self.task_definition = ecs.FargateTaskDefinition(
            self,
            "TaskDefinition",
            cpu=cpu,
            memory_limit_mib=memory_limit_mib,
        )

        self.container = self.task_definition.add_container(
            "AppContainer",
            image=ecs.ContainerImage.from_ecr_repository(repository, image_tag),
            environment=environment or {},
            secrets={
                name: ecs.Secret.from_secrets_manager(secret)
                for name, secret in (secrets or {}).items()
            },
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="app", log_group=log_group
            ),
            port_mappings=[
                ecs.PortMapping(
                    container_port=container_port, protocol=ecs.Protocol.TCP
                )
            ],
        )

        self.service = ecs.FargateService(
            self,
            "Service",
            cluster=self.cluster,
            task_definition=self.task_definition,
            desired_count=desired_count,
            # 明示しないと既定 50% になり、デプロイ中にタスクが desired を下回る。
            min_healthy_percent=100,
            max_healthy_percent=200,
            security_groups=[security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
        )
