# Kubernetes — Operator, CRDs, Cloud Platforms

## Operator Overview

The Antfly Kubernetes operator manages cluster lifecycle via Custom Resource Definitions (CRDs):

| CRD | Purpose |
|-----|---------|
| `AntflyCluster` | Defines a cluster: metadata nodes, data nodes, storage, networking |
| `AntflyBackup` | Schedules and manages backups to S3/GCS |
| `AntflyRestore` | Restores from a backup |

The operator creates StatefulSets, Services, PVCs, and ConfigMaps automatically.

## Minimal Cluster

```yaml
apiVersion: antfly.io/v1
kind: AntflyCluster
metadata:
  name: my-cluster
  namespace: antfly
spec:
  image: ghcr.io/antflydb/antfly:latest

  metadataNodes:
    replicas: 3
    metadataAPI:
      port: 12377
    metadataRaft:
      port: 9017
    resources:
      cpu: "250m"
      memory: "256Mi"

  dataNodes:
    replicas: 3
    api:
      port: 12380
    raft:
      port: 9021
    resources:
      cpu: "500m"
      memory: "512Mi"

  publicAPI:
    enabled: true

  storage:
    storageClass: "standard-rwo"
    metadataStorage: "1Gi"
    dataStorage: "5Gi"
```

Apply: `kubectl apply -f cluster.yaml`
Watch: `kubectl get pods -n antfly -w`
Connect: `kubectl port-forward -n antfly svc/my-cluster-metadata 12377:12377`

## Autoscaling (Data Nodes Only)

```yaml
dataNodes:
  autoScaling:
    enabled: true
    minReplicas: 3
    maxReplicas: 10
    targetCPUUtilizationPercentage: 70
    targetMemoryUtilizationPercentage: 80
    scaleUpCooldown: 60s
    scaleDownCooldown: 300s
```

Scaling is gradual: +50%/+2 nodes up, -25%/-1 node down. Metadata nodes do **not** autoscale.

## Cloud Platforms

### AWS EKS
- Storage class: EBS CSI driver (`gp3` recommended)
- Auth: IAM Roles for Service Accounts (IRSA) for S3 access
- Spot instances supported for data nodes (use `nodeSelector` + tolerations)
- Key config: `storageClass: "gp3"`, IRSA annotation on service account

### GCP GKE
- Storage class: `standard-rwo` (default) or `premium-rwo`
- GKE Autopilot: use compute classes and Pod Disruption Budgets
- Key config: `storageClass: "standard-rwo"`, Workload Identity for GCS access

### Generic Kubernetes
- Works with any K8s 1.24+ (Minikube, kind, bare metal)
- Bring your own storage class and ingress

## Backup & Restore

```yaml
apiVersion: antfly.io/v1
kind: AntflyBackup
metadata:
  name: daily-backup
spec:
  cluster: my-cluster
  schedule: "0 2 * * *"
  destination:
    s3:
      bucket: antfly-backups
      prefix: daily/
```

Restore:
```yaml
apiVersion: antfly.io/v1
kind: AntflyRestore
metadata:
  name: restore-from-daily
spec:
  cluster: my-cluster
  source:
    s3:
      bucket: antfly-backups
      prefix: daily/2026-04-03/
```

## Service Mesh

Operator supports auto-configuration for:
- **Istio** — automatic mTLS, traffic policies
- **Linkerd** — proxy injection annotations
- **Consul Connect** — Connect sidecar injection

## RBAC

The operator requires a service account (`antfly-operator-service-account`) with permissions to manage StatefulSets, Services, PVCs, ConfigMaps, and the Antfly CRDs.

## Sharp Edges

1. **Metadata replicas must be odd** (3 or 5) — even numbers risk split-brain during network partitions
2. **Storage class must support ReadWriteOnce** — Antfly uses StatefulSets with per-pod PVCs
3. **PVCs persist after cluster deletion** — manual cleanup needed if you want to reclaim storage
4. **Autoscaling is data-nodes only** — metadata nodes are fixed at deploy time
5. **Image pull**: `ghcr.io/antflydb/antfly:latest` — pin to a specific version tag in production
6. **Port-forward for local access** — the publicAPI LoadBalancer may take time to provision
7. **Backup destination credentials** — use Kubernetes Secrets or IRSA/Workload Identity, not inline credentials
