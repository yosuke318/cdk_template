from aws_cdk import (
    CfnOutput,
    Stack,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

from config import StageConfig
from construct.alb import AlbConstruct
from construct.ecs import EcsConstruct
from construct.logs import LogGroupConstruct


class ServiceStack(Stack):
    """ECS (Fargate) + ALB。

    ECR のイメージを引くので、初回 deploy の前に image_tag のイメージを
    push しておく必要がある。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: StageConfig,
        vpc: ec2.IVpc,
        alb_security_group: ec2.ISecurityGroup,
        service_security_group: ec2.ISecurityGroup,
        repository: ecr.IRepository,
        secret: secretsmanager.ISecret,
        image_tag: str = "latest",
        health_check_path: str = "/",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        service_logs = LogGroupConstruct(
            self,
            "ServiceLogs",
            retention=config.log_retention,
            removal_policy=config.removal_policy,
        ).log_group

        alb = AlbConstruct(self, "Alb", vpc=vpc, security_group=alb_security_group)

        ecs_service = EcsConstruct(
            self,
            "Ecs",
            vpc=vpc,
            security_group=service_security_group,
            repository=repository,
            log_group=service_logs,
            image_tag=image_tag,
            container_port=config.container_port,
            desired_count=config.desired_count,
            environment={"STAGE": config.stage},
            secrets={"APP_SECRET": secret},
        )

        alb.add_targets(
            [ecs_service.service],
            port=config.container_port,
            health_check_path=health_check_path,
        )

        self.load_balancer = alb.load_balancer

        CfnOutput(
            self,
            "AlbUrl",
            value=f"http://{alb.load_balancer.load_balancer_dns_name}",
            description="ALB endpoint of the ECS service",
        )
