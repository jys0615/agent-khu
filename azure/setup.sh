#!/usr/bin/env bash
# Azure 리소스 최초 생성 스크립트
# 실행 전: az login 완료 필요
# 사용법: bash azure/setup.sh

set -euo pipefail

# ── 설정값 (필요 시 수정) ─────────────────────────────────────────────────
RESOURCE_GROUP="agent-khu-rg"
LOCATION="eastus"
ACR_NAME="agentkhuacr"           # 전 세계 고유해야 함
ENV_NAME="agent-khu-env"
BACKEND_APP="agent-khu-backend"
FRONTEND_APP="agent-khu-frontend"
PG_SERVER="agent-khu-pg"
PG_DB="agent_khu"
PG_USER="agentkhu"
REDIS_NAME="agent-khu-redis"

echo "=== 1. Resource Group ==="
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

echo "=== 2. Azure Container Registry ==="
az acr create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$ACR_NAME" \
  --sku Basic \
  --admin-enabled true

ACR_SERVER="${ACR_NAME}.azurecr.io"
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv)

echo "=== 3. PostgreSQL Flexible Server ==="
PG_PASSWORD=$(openssl rand -base64 20 | tr -dc 'A-Za-z0-9' | head -c 20)
az postgres flexible-server create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$PG_SERVER" \
  --location "$LOCATION" \
  --admin-user "$PG_USER" \
  --admin-password "$PG_PASSWORD" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --database-name "$PG_DB" \
  --public-access 0.0.0.0

DATABASE_URL="postgresql://${PG_USER}:${PG_PASSWORD}@${PG_SERVER}.postgres.database.azure.com:5432/${PG_DB}?sslmode=require"

echo "=== 4. Azure Cache for Redis ==="
az redis create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$REDIS_NAME" \
  --location "$LOCATION" \
  --sku Basic \
  --vm-size c0

REDIS_HOST="${REDIS_NAME}.redis.cache.windows.net"
REDIS_KEY=$(az redis list-keys --resource-group "$RESOURCE_GROUP" --name "$REDIS_NAME" --query primaryKey -o tsv)
REDIS_URL="rediss://:${REDIS_KEY}@${REDIS_HOST}:6380/0"

echo "=== 5. Container Apps Environment ==="
az containerapp env create \
  --name "$ENV_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION"

echo "=== 6. Backend Container App ==="
# 환경변수는 배포 후 GitHub Actions secrets로 관리
az containerapp create \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENV_NAME" \
  --image "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest" \
  --target-port 8000 \
  --ingress external \
  --registry-server "$ACR_SERVER" \
  --registry-username "$ACR_USERNAME" \
  --registry-password "$ACR_PASSWORD" \
  --cpu 1.0 \
  --memory 2.0Gi \
  --min-replicas 1 \
  --max-replicas 3 \
  --secrets \
    database-url="$DATABASE_URL" \
    redis-url="$REDIS_URL" \
    anthropic-api-key="REPLACE_ME" \
    groq-api-key="REPLACE_ME" \
    elasticsearch-url="REPLACE_ME" \
    secret-key="$(openssl rand -hex 32)" \
    allowed-origins="REPLACE_WITH_FRONTEND_URL"

echo "=== 7. Frontend Container App ==="
az containerapp create \
  --name "$FRONTEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENV_NAME" \
  --image "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest" \
  --target-port 80 \
  --ingress external \
  --registry-server "$ACR_SERVER" \
  --registry-username "$ACR_USERNAME" \
  --registry-password "$ACR_PASSWORD" \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 1 \
  --max-replicas 2

echo ""
echo "=== 완료 ==="
BACKEND_URL=$(az containerapp show -n "$BACKEND_APP" -g "$RESOURCE_GROUP" --query properties.configuration.ingress.fqdn -o tsv)
FRONTEND_URL=$(az containerapp show -n "$FRONTEND_APP" -g "$RESOURCE_GROUP" --query properties.configuration.ingress.fqdn -o tsv)
echo "Backend:  https://$BACKEND_URL"
echo "Frontend: https://$FRONTEND_URL"

echo ""
echo "=== GitHub Secrets에 설정할 값 ==="
echo "AZURE_CREDENTIALS: az ad sp create-for-rbac 명령 결과 (아래 실행)"
echo ""
echo "서비스 주체 생성 명령어:"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "az ad sp create-for-rbac --name agent-khu-deploy --role contributor \\"
echo "  --scopes /subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP} \\"
echo "  --sdk-auth"
echo ""
echo "위 명령 결과 JSON을 GitHub → Settings → Secrets → AZURE_CREDENTIALS 에 저장"
echo ""
echo "ACR_NAME: $ACR_NAME"
echo "ACR_SERVER: $ACR_SERVER"
echo ""
echo "⚠️  아래 값을 안전하게 보관하세요:"
echo "PG_PASSWORD: $PG_PASSWORD"
echo "REDIS_KEY: $REDIS_KEY"
