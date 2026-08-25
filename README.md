# cdk_template

簡単なアプリを立ち上げるための最小構成を CDK (Python) でまとめたテンプレート。

## 構成

| スタック | 中身 |
|---|---|
| `NetworkStack` | VPC (Public / Private / Isolated × 2AZ)、ALB 用 / ECS 用セキュリティグループ |
| `StorageStack` | S3、DynamoDB、ECR、Secrets Manager |
| `ApiStack` | Lambda + API Gateway (REST, プロキシ統合)、CloudWatch Logs |
| `ServiceStack` | ECS (Fargate) + ALB、CloudWatch Logs |
| `CdnStack` | CloudFront + OAC (S3 オリジン) |

依存は一方向。`Network` / `Storage` → `Api` / `Service` / `Cdn`。

```
construct/   # 1 サービス 1 ファイルの再利用単位 (Construct)
stacks/      # Construct を組み合わせたスタック
assets/      # Lambda のソース
```

## 使い方

```bash
docker compose build
docker compose run --rm cdk bash
```

コンテナ内で:

```bash
# 初回のみ。cdk.json の toolkitStackName に合わせる
cdk bootstrap --toolkit-stack-name myToolKit

cdk synth
cdk diff
cdk deploy --all
```

ステージを分ける場合は context で上書きする。スタック名の接頭辞になる。

```bash
cdk deploy --all -c stage=prd
```

## デプロイ順の注意

`ServiceStack` は ECR のイメージを引くため、**先に ECR にイメージを 1 つ push しておく**。
空のままだと ECS サービスが安定せず、スタックがロールバックする。

```bash
cdk deploy DevStorageStack          # ECR リポジトリだけ先に作る
aws ecr get-login-password | docker login --username AWS --password-stdin <acct>.dkr.ecr.<region>.amazonaws.com
docker build -t <repo-uri>:latest . && docker push <repo-uri>:latest
cdk deploy --all
```

タグを変えるなら `-c imageTag=v1.2.3`。

## 既定値と、本番前に見直すもの

- **RemovalPolicy** — S3 / DynamoDB / ECR とも `DESTROY`。消えて困るものは `RETAIN` に変える
- **NAT Gateway** — 1 台で常時課金される。検証で不要なら `app.py` の `nat_gateways=0`
- **ALB** — HTTP:80 のみ。ACM 証明書を取ったら 443 リスナーを足して 80 はリダイレクトへ
- **Secrets Manager** — 値は CDK に書かない。空の入れ物だけ作ってあるので中身は AWS 側で埋める
- **ログ保持** — 全ロググループ 30 日 (`construct/logs.py`)
- **DynamoDB PITR** — 既定 off。`construct/dynamodb.py` の `point_in_time_recovery`

## CloudFront + OAC のクロススタック参照について

CloudFront を S3 と別スタックに置くと、Distribution がバケットを参照し、バケットポリシーが
Distribution の ARN を参照するため循環参照になる。これを避けるため:

- `CdnStack` ではバケットを `from_bucket_name` でインポート扱いにする (CDK はポリシーを触らない)
- 読み取り許可は `StorageStack` 側で付ける。条件は `SourceArn` ではなく `SourceAccount`

`cdk synth` 時に出る "Cannot update bucket policy of an imported bucket" は、この設計による
想定内の警告。
