#!/usr/bin/env bash
# Azure 리소스 최초 생성 스크립트 (GHCR 이미지 사용 — ACR 불필요)
# 실행 전: az login 완료 필요
# 사용법: bash azure/setup.sh

set -euo pipefail

# ── 설정값 ────────────────────────────────────────────────────────────────
RESOURCE_GROUP="agent-khu-rg"
LOCATION="koreacentral"
ENV_NAME="agent-khu-env"
BACKEND_APP="agent-khu-backend"
FRONTEND_APP="agent-khu-frontend"
PG_SERVER="agent-khu-pg"
PG_DB="agent_khu"
PG_USER="agentkhu"
REDIS_NAME="agent-khu-redis"

# GitHub 사용자명 (GHCR 이미지 경로)
GITHUB_USER="jys0615"
BACKEND_IMAGE="ghcr.io/${GITHUB_USER}/agent-khu-backend:latest"
FRONTEND_IMAGE="ghcr.io/${GITHUB_USER}/agent-khu-frontend:latest"

echo "=== 1. Resource Group ==="
az group create --name "$RESOURCE_GROUP" --location "eastus" 2>/dev/null || \
  echo "Resource Group already exists — skipping"

echo "=== 2. PostgreSQL Flexible Server ==="
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
echo "PostgreSQL 완료: $PG_SERVER"

echo "=== 3. Azure Cache for Redis ==="
az redis create \
  --resource-group "$RESOURCE_GROUP" \
  --name "$REDIS_NAME" \
  --location "$LOCATION" \
  --sku Basic \
  --vm-size c0

REDIS_HOST="${REDIS_NAME}.redis.cache.windows.net"
REDIS_KEY=$(az redis list-keys --resource-group "$RESOURCE_GROUP" --name "$REDIS_NAME" --query primaryKey -o tsv)
REDIS_URL="rediss://:${REDIS_KEY}@${REDIS_HOST}:6380/0"
echo "Redis 완료: $REDIS_NAME"

echo "=== 4. Container Apps Environment ==="
az containerapp env create \
  --name "$ENV_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION"
echo "Container Apps Environment 완료: $ENV_NAME"

echo "=== 5. Backend Container App ==="
az containerapp create \
  --name "$BACKEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENV_NAME" \
  --image "$BACKEND_IMAGE" \
  --target-port 8000 \
  --ingress external \
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
    allowed-origins="REPLACE_WITH_FRONTEND_URL" \
  --env-vars \
    DATABASE_URL=secretref:database-url \
    REDIS_URL=secretref:redis-url \
    ANTHROPIC_API_KEY=secretref:anthropic-api-key \
    GROQ_API_KEY=secretref:groq-api-key \
    ELASTICSEARCH_URL=secretref:elasticsearch-url \
    SECRET_KEY=secretref:secret-key \
    ALLOWED_ORIGINS=secretref:allowed-origins \
    OLLAMA_ENABLED=false \
    MCP_CLASSROOM_URL=http://localhost:8101/mcp \
    MCP_NOTICE_URL=http://localhost:8102/mcp \
    MCP_MEAL_URL=http://localhost:8103/mcp \
    MCP_LIBRARY_URL=http://localhost:8104/mcp \
    MCP_COURSE_URL=http://localhost:8105/mcp \
    MCP_CURRICULUM_URL=http://localhost:8106/mcp \
    MCP_SHUTTLE_URL=http://localhost:8107/mcp

echo "=== 6. Frontend Container App ==="
az containerapp create \
  --name "$FRONTEND_APP" \
  --resource-group "$RESOURCE_GROUP" \
  --environment "$ENV_NAME" \
  --image "$FRONTEND_IMAGE" \
  --target-port 80 \
  --ingress external \
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
echo "=== 다음 단계 ==="
echo ""
echo "1) 아래 명령으로 AZURE_CREDENTIALS 생성 후 GitHub Secrets에 등록:"
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "   az ad sp create-for-rbac --name agent-khu-deploy --role contributor \\"
echo "     --scopes /subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP} \\"
echo "     --sdk-auth"
echo ""
echo "2) GitHub Secrets에 추가로 등록:"
echo "   ANTHROPIC_API_KEY=실제값"
echo "   GROQ_API_KEY=실제값"
echo "   VITE_API_URL=https://$BACKEND_URL"
echo ""
echo "3) Backend secrets 실제 값으로 교체:"
echo "   az containerapp secret set -n $BACKEND_APP -g $RESOURCE_GROUP \\"
echo "     --secrets anthropic-api-key=실제값 groq-api-key=실제값 \\"
echo "              allowed-origins=https://$FRONTEND_URL"
echo ""
echo "⚠️  아래 값을 안전하게 보관하세요:"
echo "PG_PASSWORD: $PG_PASSWORD"
echo "REDIS_KEY:   $REDIS_KEY"
