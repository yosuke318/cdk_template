#!/usr/bin/env python3
import os

from aws_cdk import App, Environment, Tags

from stacks.api import ApiStack
from stacks.cdn import CdnStack
from stacks.network import NetworkStack
from stacks.service import ServiceStack
from stacks.storage import StorageStack

app = App()

# 環境。CDK_DEFAULT_* は cdk CLI が現在のプロファイルから注入する。
# ここを指定しないと environment-agnostic になり、VPC の AZ 参照などで詰まる。
env = Environment(
    account=app.node.try_get_context("account") or os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=app.node.try_get_context("region") or os.environ.get("CDK_DEFAULT_REGION"),
)

# cdk deploy -c stage=prd のように上書きする。
stage = app.node.try_get_context("stage") or "dev"
image_tag = app.node.try_get_context("imageTag") or "latest"
container_port = int(app.node.try_get_context("containerPort") or 80)

prefix = f"{stage.capitalize()}"

network = NetworkStack(
    app,
    f"{prefix}NetworkStack",
    env=env,
    container_port=container_port,
    # 検証用に落とすなら 0。ただし PRIVATE_WITH_EGRESS からの外向き通信が切れる。
    nat_gateways=1,
)

storage = StorageStack(app, f"{prefix}StorageStack", env=env)

api = ApiStack(
    app,
    f"{prefix}ApiStack",
    env=env,
    table=storage.table,
)

service = ServiceStack(
    app,
    f"{prefix}ServiceStack",
    env=env,
    vpc=network.vpc,
    alb_security_group=network.alb_security_group,
    service_security_group=network.service_security_group,
    repository=storage.repository,
    secret=storage.secret,
    image_tag=image_tag,
    container_port=container_port,
)

cdn = CdnStack(app, f"{prefix}CdnStack", env=env, bucket=storage.bucket)

# クロススタック参照だけでは表現しきれない順序を明示する。
service.add_dependency(network)
service.add_dependency(storage)
api.add_dependency(storage)
cdn.add_dependency(storage)

Tags.of(app).add("Project", "cdk-template")
Tags.of(app).add("Stage", stage)
Tags.of(app).add("ManagedBy", "cdk")

app.synth()
