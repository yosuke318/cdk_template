FROM python:3.11-slim

WORKDIR /app

# CDK CLI は Node 製。python の CDK ライブラリだけでは cdk deploy が打てない。
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g aws-cdk@2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ソースは docker-compose でバインドマウントする想定。
# コンテナに入って cdk diff / cdk deploy を打つのが基本の使い方。
CMD ["bash"]
