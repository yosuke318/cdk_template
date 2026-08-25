from aws_cdk import (
    Duration,
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
)
from constructs import Construct


class AlbConstruct(Construct):
    """ECS サービスの前段に置く Application Load Balancer。

    証明書を用意していないため今は HTTP:80 リスナーのみ。ACM 証明書を
    取得したら add_listener(443, certificates=[...]) を足し、80 は
    redirect に変更する。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        security_group: ec2.ISecurityGroup,
        internet_facing: bool = True,
    ) -> None:
        super().__init__(scope, construct_id)

        self.load_balancer = elbv2.ApplicationLoadBalancer(
            self,
            "Alb",
            vpc=vpc,
            internet_facing=internet_facing,
            security_group=security_group,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=(
                    ec2.SubnetType.PUBLIC
                    if internet_facing
                    else ec2.SubnetType.PRIVATE_WITH_EGRESS
                )
            ),
        )

        self.listener = self.load_balancer.add_listener(
            "HttpListener",
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            open=False,  # インバウンドは SecurityGroupConstruct 側で管理する
        )

    def add_targets(
        self,
        targets: list[elbv2.IApplicationLoadBalancerTarget],
        *,
        port: int = 80,
        health_check_path: str = "/",
    ) -> elbv2.ApplicationTargetGroup:
        return self.listener.add_targets(
            "Targets",
            port=port,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=targets,
            health_check=elbv2.HealthCheck(
                path=health_check_path,
                healthy_threshold_count=2,
                unhealthy_threshold_count=3,
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5),
            ),
            deregistration_delay=Duration.seconds(30),
        )
