# Azure 배포 가이드

## 사전 요구사항

```bash
# Azure CLI 설치 (Mac)
brew install azure-cli

# 로그인
az login

# 학생 구독 확인
az account show
```

---

## Step 1. Azure 리소스 생성 (최초 1회)

```bash
bash azure/setup.sh
```

생성되는 리소스:
- Resource Group: `agent-khu-rg`
- Azure Container Registry (ACR): `agentkhuacr`
- PostgreSQL Flexible Server (Basic)
- Azure Cache for Redis (C0)
- Container Apps Environment
- Backend Container App
- Frontend Container App

---

## Step 2. GitHub Secrets 설정

GitHub 레포 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 |
|-------------|-----|
| `AZURE_CREDENTIALS` | 아래 명령 결과 JSON |
| `ANTHROPIC_API_KEY` | Anthropic API 키 |
| `GROQ_API_KEY` | Groq API 키 |

```bash
# AZURE_CREDENTIALS 생성 명령
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
az ad sp create-for-rbac \
  --name agent-khu-deploy \
  --role contributor \
  --scopes /subscriptions/${SUBSCRIPTION_ID}/resourceGroups/agent-khu-rg \
  --sdk-auth
```

출력된 JSON 전체를 `AZURE_CREDENTIALS` secret에 붙여넣기.

---

## Step 3. Backend secrets 업데이트

setup.sh 실행 후 실제 값으로 교체:

```bash
RESOURCE_GROUP="agent-khu-rg"
BACKEND_APP="agent-khu-backend"

az containerapp secret set \
  --name $BACKEND_APP \
  --resource-group $RESOURCE_GROUP \
  --secrets \
    anthropic-api-key="실제_ANTHROPIC_API_KEY" \
    groq-api-key="실제_GROQ_API_KEY" \
    elasticsearch-url="http://your-es-endpoint:9200"

# ALLOWED_ORIGINS에 프론트엔드 URL 설정
FRONTEND_URL=$(az containerapp show -n agent-khu-frontend -g $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv)

az containerapp secret set \
  --name $BACKEND_APP \
  --resource-group $RESOURCE_GROUP \
  --secrets allowed-origins="https://${FRONTEND_URL}"
```

---

## Step 4. 배포 실행

main 브랜치에 push하면 자동으로 CD 파이프라인 실행:

```bash
git push origin main
```

GitHub Actions → CD 워크플로우에서 진행 상황 확인.

---

## Elasticsearch 처리 옵션

| 옵션 | 비용 | 난이도 |
|------|------|--------|
| Container App으로 ES 컨테이너 실행 | 낮음 | 보통 |
| Elastic Cloud 무료 티어 (14일) | 무료 | 쉬움 |

**추천: Container App에 ES 컨테이너 추가**

```bash
az containerapp create \
  --name agent-khu-elasticsearch \
  --resource-group agent-khu-rg \
  --environment agent-khu-env \
  --image docker.elastic.co/elasticsearch/elasticsearch:8.11.0 \
  --target-port 9200 \
  --ingress internal \
  --cpu 1.0 --memory 2.0Gi \
  --min-replicas 1 --max-replicas 1 \
  --env-vars \
    discovery.type=single-node \
    xpack.security.enabled=false \
    "ES_JAVA_OPTS=-Xms512m -Xmx512m"
```

내부 통신 URL: `http://agent-khu-elasticsearch/`

---

## 비용 예상 (월)

| 리소스 | SKU | 예상 비용 |
|--------|-----|----------|
| Container Apps (backend + 7 MCP + ES) | Consumption | ~$20 |
| Container Apps (frontend) | Consumption | ~$3 |
| PostgreSQL Flexible Server | Standard_B1ms | ~$15 |
| Redis Cache | C0 Basic | ~$16 |
| Container Registry | Basic | ~$5 |
| **합계** | | **~$59/월** |

학생 크레딧 $100/년 → 약 1.5개월치 (크레딧 소진 주의)
