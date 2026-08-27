from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class VpcConstruct(Construct):
    """ECS / ALB を載せるための VPC。

    nat_gateways は 1 つでも常時課金される。ただし 0 にしても
    PRIVATE_WITH_EGRESS サブネット自体は残り、そこへの default route だけが
    消える (エラーにはならない)。結果としてサブネットの型は
    「egress あり」のままなのに実際には外に出られない状態になり、
    ECS が ECR からイメージを引けず原因の分かりにくい失敗をする。

    NAT を無くしたい場合は、代わりに ECR / CloudWatch Logs / Secrets Manager
    への VPC エンドポイントを張るか、subnet_configuration ごと
    PRIVATE_ISOLATED に組み替えること。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        cidr: str = "10.0.0.0/16",
        max_azs: int = 2,
        nat_gateways: int = 1,
    ) -> None:
        super().__init__(scope, construct_id)

        self.vpc = ec2.Vpc(
            self,
            "Vpc",
            ip_addresses=ec2.IpAddresses.cidr(cidr),
            max_azs=max_azs,
            nat_gateways=nat_gateways,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )
