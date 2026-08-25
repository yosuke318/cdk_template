from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class SecurityGroupConstruct(Construct):
    """ALB と ECS サービス用のセキュリティグループ。

    ALB は 80/443 をインターネットに開き、ECS サービスは ALB からの
    container_port のみを受ける。ECS 側にインバウンドの直接開放は無い。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        container_port: int = 80,
    ) -> None:
        super().__init__(scope, construct_id)

        self.alb = ec2.SecurityGroup(
            self,
            "AlbSg",
            vpc=vpc,
            description="Allow HTTP/HTTPS from the internet to the ALB",
            allow_all_outbound=True,
        )
        self.alb.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "HTTP from anywhere"
        )
        self.alb.add_ingress_rule(
            ec2.Peer.any_ipv4(), ec2.Port.tcp(443), "HTTPS from anywhere"
        )

        self.service = ec2.SecurityGroup(
            self,
            "ServiceSg",
            vpc=vpc,
            description="Allow traffic from the ALB to the ECS service",
            allow_all_outbound=True,
        )
        self.service.add_ingress_rule(
            self.alb,
            ec2.Port.tcp(container_port),
            f"Container port {container_port} from the ALB",
        )
