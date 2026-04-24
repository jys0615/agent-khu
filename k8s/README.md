# Kubernetes Manifests

## Directory structure

```
k8s/
├── namespace.yaml
├── configmap.yaml        # Non-sensitive env vars
├── ingress.yaml
├── postgres/
│   ├── statefulset.yaml
│   └── service.yaml
├── redis/
│   ├── deployment.yaml
│   └── service.yaml
├── backend/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── hpa.yaml
└── frontend/
    ├── deployment.yaml
    └── service.yaml
```

## Required secrets (create manually on the cluster)

Before applying manifests, create the following secret:

```bash
kubectl create namespace agent-khu

kubectl create secret generic agent-khu-secrets \
  -n agent-khu \
  --from-literal=POSTGRES_PASSWORD='<your-db-password>' \
  --from-literal=SECRET_KEY='<your-jwt-secret>' \
  --from-literal=ANTHROPIC_API_KEY='<your-anthropic-key>'
```

## CD pipeline

The `deploy` job in `.github/workflows/cd.yml` runs automatically when:
- A push lands on `main`
- The `KUBECONFIG` repository secret is set (base64-encoded kubeconfig)

```bash
# Encode your kubeconfig
cat ~/.kube/config | base64 | pbcopy
# Paste into GitHub → Settings → Secrets → KUBECONFIG
```

## Manual deploy

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/redis/
kubectl apply -f k8s/backend/
kubectl apply -f k8s/frontend/
kubectl apply -f k8s/ingress.yaml
```
