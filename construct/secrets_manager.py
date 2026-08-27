from aws_cdk import RemovalPolicy, aws_secretsmanager as secretsmanager
from constructs import Construct


class SecretConstruct(Construct):
    """アプリが実行時に読む機密値。

    値そのものは CDK に書かない。ここでは空の入れ物 (とパスワードの自動生成) だけ
    作り、中身は AWS 側で後から埋める。テンプレートに平文で書くと
    CloudFormation の履歴に残る。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        secret_name: str | None = None,
        username: str = "app",
        removal_policy: RemovalPolicy = RemovalPolicy.DESTROY,
    ) -> None:
        super().__init__(scope, construct_id)

        self.secret = secretsmanager.Secret(
            self,
            "Secret",
            secret_name=secret_name,
            description="Runtime secrets for the application",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=f'{{"username":"{username}"}}',
                generate_string_key="password",
                exclude_punctuation=True,
                password_length=32,
            ),
            removal_policy=removal_policy,
        )
