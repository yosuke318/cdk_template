"""API Gateway のプロキシ統合から呼ばれる最小のハンドラ。

TABLE_NAME 環境変数でテーブル名が渡ってくる。実装を差し替える際の起点。
"""

import json
import os

TABLE_NAME = os.environ.get("TABLE_NAME", "")


def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(
            {
                "message": "Hello from Lambda",
                "path": event.get("path"),
                "table": TABLE_NAME,
            }
        ),
    }
