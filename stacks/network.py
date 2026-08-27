from aws_cdk import Stack
from constructs import Construct

from config import StageConfig
from construct.security_group import SecurityGroupConstruct
from construct.vpc import VpcConstruct


class NetworkStack(Stack):
    """VPC とセキュリティグループ。他の全スタックの土台。"""

    def __init__(
        self, scope: Construct, construct_id: str, *, config: StageConfig, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        network = VpcConstruct(self, "Vpc", nat_gateways=config.nat_gateways)
        self.vpc = network.vpc

        security_groups = SecurityGroupConstruct(
            self, "SecurityGroup", vpc=self.vpc, container_port=config.container_port
        )
        self.alb_security_group = security_groups.alb
        self.service_security_group = security_groups.service
