"""ステージ (dev / stg / prod) ごとの設定。

スタック名の接頭辞だけ変えても「環境を分けた」ことにはならない。消えて困る
リソースの扱い、冗長度、ログ保持期間といった実際に差が出る値をここに集約する。
"""

from dataclasses import dataclass

from aws_cdk import RemovalPolicy, aws_logs as logs


@dataclass(frozen=True)
class StageConfig:
    """1 ステージ分の設定。"""

    stage: str

    # マルチアカウント構成にする場合はここにアカウント ID を書く。
    # None なら -c account=... か CDK_DEFAULT_ACCOUNT にフォールバックする。
    account: str | None
    region: str | None

    # 消えて困るリソース (S3 / DynamoDB / ECR / Secret) の扱い
    removal_policy: RemovalPolicy
    auto_delete_objects: bool
    point_in_time_recovery: bool

    # 冗長度とコスト
    nat_gateways: int
    desired_count: int

    log_retention: logs.RetentionDays
    container_port: int = 80

    @property
    def prefix(self) -> str:
        """スタック名の接頭辞。dev -> Dev, prod -> Prod"""
        return self.stage.capitalize()

    @property
    def is_production(self) -> bool:
        return self.stage == "prod"


STAGES: dict[str, StageConfig] = {
    "dev": StageConfig(
        stage="dev",
        account=None,
        region=None,
        # 作っては壊す環境。cdk destroy で綺麗に消えることを優先する
        removal_policy=RemovalPolicy.DESTROY,
        auto_delete_objects=True,
        point_in_time_recovery=False,
        nat_gateways=1,
        desired_count=1,
        log_retention=logs.RetentionDays.ONE_WEEK,
    ),
    "stg": StageConfig(
        stage="stg",
        account=None,
        region=None,
        # 本番前の確認用。データは消えてよいが、構成は本番に寄せる
        removal_policy=RemovalPolicy.DESTROY,
        auto_delete_objects=True,
        point_in_time_recovery=True,
        nat_gateways=1,
        desired_count=2,
        log_retention=logs.RetentionDays.ONE_MONTH,
    ),
    "prod": StageConfig(
        stage="prod",
        account=None,
        region=None,
        # cdk destroy やスタック削除でデータが飛ばないようにする
        removal_policy=RemovalPolicy.RETAIN,
        auto_delete_objects=False,
        point_in_time_recovery=True,
        # AZ ごとに NAT を置く。1 台だとその AZ の障害で外向き通信が全滅する
        nat_gateways=2,
        desired_count=2,
        log_retention=logs.RetentionDays.SIX_MONTHS,
    ),
}


def resolve(node) -> StageConfig:
    """context の stage / account / region を解決して StageConfig を返す。

    未知のステージ名は黙って通さない。通すと typo がそのまま
    「まだ存在しない環境」として deploy されてしまう。
    """
    stage = node.try_get_context("stage") or "dev"

    if stage not in STAGES:
        valid = ", ".join(STAGES)
        raise ValueError(
            f"unknown stage: {stage!r}. valid stages are: {valid} "
            f"(例: cdk deploy --all -c stage=prod)"
        )

    config = STAGES[stage]

    # CLI からの上書きを許す。指定が無ければ StageConfig の値、
    # それも None なら cdk CLI が渡す CDK_DEFAULT_* を使う。
    import os

    return StageConfig(
        **{
            **config.__dict__,
            "account": (
                node.try_get_context("account")
                or config.account
                or os.environ.get("CDK_DEFAULT_ACCOUNT")
            ),
            "region": (
                node.try_get_context("region")
                or config.region
                or os.environ.get("CDK_DEFAULT_REGION")
            ),
        }
    )
