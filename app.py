#!/usr/bin/env python3
from aws_cdk import App, Environment, Tags

import config as stage_config
from stacks.api import ApiStack
from stacks.cdn import CdnStack
from stacks.network import NetworkStack
from stacks.service import ServiceStack
from stacks.storage import StorageStack

app = App()

# ステージ設定。cdk deploy --all -c stage=prod のように切り替える。
# 未知のステージ名はここで ValueError になる。
config = stage_config.resolve(app.node)

# account / region を指定しないと environment-agnostic になり、
# VPC の AZ 参照などで詰まる。CDK_DEFAULT_* は cdk CLI が注入する。
env = Environment(account=config.account, region=config.region)

image_tag = app.node.try_get_context("imageTag") or "latest"
prefix = config.prefix

network = NetworkStack(app, f"{prefix}NetworkStack", env=env, config=config)

storage = StorageStack(app, f"{prefix}StorageStack", env=env, config=config)

api = ApiStack(
    app,
    f"{prefix}ApiStack",
    env=env,
    config=config,
    table=storage.table,
)

service = ServiceStack(
    app,
    f"{prefix}ServiceStack",
    env=env,
    config=config,
    vpc=network.vpc,
    alb_security_group=network.alb_security_group,
    service_security_group=network.service_security_group,
    repository=storage.repository,
    secret=storage.secret,
    image_tag=image_tag,
)

cdn = CdnStack(app, f"{prefix}CdnStack", env=env, bucket=storage.bucket)

# クロススタック参照だけでは表現しきれない順序を明示する。
service.add_dependency(network)
service.add_dependency(storage)
api.add_dependency(storage)
cdn.add_dependency(storage)

Tags.of(app).add("Project", "cdk-template")
Tags.of(app).add("Stage", config.stage)
Tags.of(app).add("ManagedBy", "cdk")

app.synth()
