from aws_cdk import Duration, RemovalPolicy, aws_ecr as ecr
from constructs import Construct


class EcrConstruct(Construct):
    """ECS タスクが参照するコンテナイメージのリポジトリ。

    タグ無しイメージが溜まり続けると地味に課金されるのでライフサイクルを入れてある。
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        repository_name: str | None = None,
        max_image_count: int = 10,
        removal_policy: RemovalPolicy = RemovalPolicy.DESTROY,
    ) -> None:
        super().__init__(scope, construct_id)

        self.repository = ecr.Repository(
            self,
            "Repository",
            repository_name=repository_name,
            image_scan_on_push=True,
            image_tag_mutability=ecr.TagMutability.MUTABLE,
            encryption=ecr.RepositoryEncryption.AES_256,
            removal_policy=removal_policy,
            # removal_policy=DESTROY でもイメージが残っていると削除に失敗するため
            empty_on_delete=(removal_policy == RemovalPolicy.DESTROY),
            lifecycle_rules=[
                ecr.LifecycleRule(
                    rule_priority=1,
                    description="Expire untagged images after 1 day",
                    tag_status=ecr.TagStatus.UNTAGGED,
                    max_image_age=Duration.days(1),
                ),
                ecr.LifecycleRule(
                    rule_priority=2,
                    description=f"Keep only the last {max_image_count} images",
                    tag_status=ecr.TagStatus.ANY,
                    max_image_count=max_image_count,
                ),
            ],
        )
