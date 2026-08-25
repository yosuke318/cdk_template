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
config.py    # ステージ (dev/stg/prod) ごとの設定
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

## ステージ (dev / stg / prod)

`-c stage=...` で切り替える。既定は `dev`。設定の実体は `config.py` の `STAGES`。

```bash
cdk deploy --all                 # dev
cdk deploy --all -c stage=stg
cdk deploy --all -c stage=prod
```

スタック名に接頭辞が付き (`DevStorageStack` / `StgStorageStack` / `ProdStorageStack`)、
`Stage` タグも付く。実際に変わる値は次の通り。

| | dev | stg | prod |
|---|---|---|---|
| RemovalPolicy (S3/DynamoDB/ECR/Secret/Logs) | `DESTROY` | `DESTROY` | `RETAIN` |
| S3 auto delete objects | 有効 | 有効 | 無効 |
| ECR empty on delete | 有効 | 有効 | 無効 |
| DynamoDB PITR | off | on | on |
| NAT Gateway | 1 | 1 | 2 (AZ ごと) |
| ECS desired count | 1 | 2 | 2 |
| ログ保持 | 7 日 | 30 日 | 180 日 |
| API Gateway ステージ名 | `dev` | `stg` | `prod` |

**prod は `RETAIN`** なので、`cdk destroy` してもバケット・テーブル・ECR・Secret は
残る。作り直す時は手で消すか、`config.py` を一時的に変える。

未知のステージ名は synth 時に落ちる。typo でうっかり新環境を作らないため。

```
ValueError: unknown stage: 'prdo'. valid stages are: dev, stg, prod
```

### アカウント / リージョン

既定では全ステージが同じアカウント (`CDK_DEFAULT_ACCOUNT`) に載る。ステージごとに
アカウントを分けるなら `config.py` の `StageConfig.account` / `region` に直接書く。
一時的な上書きは `-c account=... -c region=...`。

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

ステージ差のある値 (RemovalPolicy / NAT 数 / PITR / ログ保持 / タスク数) は `config.py`
に集約してある。それ以外で見直すもの:

- **ALB** — HTTP:80 のみ。ACM 証明書を取ったら 443 リスナーを足して 80 はリダイレクトへ
- **Secrets Manager** — 値は CDK に書かない。空の入れ物だけ作ってあるので中身は AWS 側で埋める
- **NAT Gateway** — 1 台でも常時課金される。`config.py` で `nat_gateways=0` にはできるが、
  サブネットは PRIVATE_WITH_EGRESS のまま残り default route だけが消えるため、ECS が
  ECR からイメージを引けなくなる (エラーにならず分かりにくい形で失敗する)。NAT を
  無くすなら ECR / Logs / Secrets Manager への VPC エンドポイントを張ること
- **API Gateway の CloudWatch ロール** — リージョンに 1 つの設定。同じアカウントで
  複数の CDK アプリを動かすなら `construct/api_gateway.py` の `cloud_watch_role` を要調整

## CloudFront + OAC のクロススタック参照について

CloudFront を S3 と別スタックに置くと、Distribution がバケットを参照し、バケットポリシーが
Distribution の ARN を参照するため循環参照になる。これを避けるため:

- `CdnStack` ではバケットを `from_bucket_name` でインポート扱いにする (CDK はポリシーを触らない)
- 読み取り許可は `StorageStack` 側で付ける。条件は `SourceArn` ではなく `SourceAccount`

`cdk synth` 時に出る "Cannot update bucket policy of an imported bucket" は、この設計による
想定内の警告。
