# Kubernetes — Operator, CRDs, Cloud Platforms

## Operator Overview

| CRD | Group/Version | Purpose |
|-----|---------------|---------|
| `AntflyCluster` | `antfly.io/v1` | Cluster: metadata nodes, data nodes, storage, networking |
| `AntflyBackup` | `antfly.io/v1` | Scheduled backups (CronJob) |
| `AntflyRestore` | `antfly.io/v1` | One-shot restore (Job) |
| `InferencePool` | `antfly.io/v1alpha1` | Pool of Antfly inference replicas |
| `InferenceProxy` | `antfly.io/v1alpha1` | Routing front end for inference pools |
| `ExternalInferencePool` | `antfly.io/v1alpha1` | Reference to a pool the operator does not own |

The operator creates StatefulSets, Services, PVCs, ConfigMaps, PodDisruptionBudgets, HorizontalPodAutoscalers, CronJobs (backup schedules), Jobs (restores and HA admin tasks), and coordination Leases. When the HA runtime-lease watchdog is enabled it also creates a ServiceAccount, Role, and RoleBinding scoped to the fencing Lease.

Requires Kubernetes **1.23+**. On 1.25+ you can additionally install `kustomize/overlays/kubernetes-1.25` to enforce the CRD CEL transition rule at API admission; the webhook and reconciler remain authoritative on 1.23–1.24.

## Minimal Cluster

The required top-level fields are `config`, `image`, and `storage`. `metadataNodes` requires
`metadataAPI`, `metadataRaft`, and `resources`; `dataNodes` requires `api`, `raft`, and `resources`
(the two node blocks themselves are optional so Standalone mode can omit them). Node `resources`
need a `limits` member, and `spec.internalServiceAuth` is required in Distributed mode (the default
`spec.mode`).

```yaml
apiVersion: antfly.io/v1
kind: AntflyCluster
metadata:
  name: small-antfly-cluster
  namespace: default
spec:
  image: ghcr.io/antflydb/antfly:latest
  imagePullPolicy: IfNotPresent

  internalServiceAuth:
    secretKeyRef:
      name: antflydb-internal-service-auth
      key: secret
      optional: false      # must not be true

  metadataNodes:
    replicas: 3            # must be odd (1, 3, or 5 in practice)
    metadataAPI:
      port: 12377
    metadataRaft:
      port: 9017
    resources:
      cpu: "250m"
      memory: "256Mi"
      limits:
        cpu: "500m"
        memory: "512Mi"

  dataNodes:
    replicas: 3
    api:
      port: 12380
    raft:
      port: 9021
    resources:
      cpu: "250m"
      memory: "512Mi"
      limits:
        cpu: "500m"
        memory: "1Gi"

  storage:
    storageClass: ""       # EKS: "gp2"/"gp3", GKE: "standard-rwo", minikube: "standard"
    metadataStorage: "1Gi"
    dataStorage: "5Gi"

  publicAPI:
    enabled: true          # default is false — without this no public-api Service is created

  config: |
    {
      "log": { "level": "info", "style": "json" },
      "max_shard_size_bytes": 134217728
    }
```

`spec.internalServiceAuth` references a Secret by name — the operator never reads its value. See `secrets.md`.

The webhook does not content-validate `resources.limits` cpu/memory strings; only the
structural `limits` member is required (a `limits.gpu` value, if set, must parse as a quantity).

Apply: `kubectl apply -f cluster.yaml`
Watch: `kubectl get pods -w`
Access: `kubectl port-forward service/small-antfly-cluster-public-api 8080:80` — this requires `spec.publicAPI.enabled: true`

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

Scaling is gradual: scale-up is capped at +50% or +2 replicas (whichever is larger), scale-down at −25% or −1. Metadata nodes do **not** autoscale; their replica count must stay odd (any odd count ≥ 1) and is **immutable after creation** — the webhook rejects any change, 3 → 5 included. Changing it means creating a differently named cluster at the target count so it gets fresh metadata PVCs, restoring a backup into it, and cutting over. Data-node replicas are mutable: the controller drains and deregisters one highest ordinal at a time before shrinking the StatefulSet.

## Cloud Platforms

### AWS EKS
- Storage class: EBS CSI driver (`gp3` recommended)
- Auth: IAM Roles for Service Accounts (IRSA) for S3 access
- Spot instances: `spec.eks.enabled: true` plus `spec.eks.useSpotInstances: true`. The operator injects the `eks.amazonaws.com/capacityType: SPOT` nodeSelector, the matching toleration, and a 25s termination grace period itself — hand-written nodeSelector/tolerations are not the mechanism. (GKE's equivalent is per node group: `spec.metadataNodes.useSpotPods` / `spec.dataNodes.useSpotPods`.)
- Pod Disruption Budgets: `spec.eks.podDisruptionBudget.enabled: true` alongside `spec.eks.enabled: true`. Either cloud's PDB block is opt-in, EKS wins if both are set, and with neither `maxUnavailable` nor `minAvailable` given, `maxUnavailable` is 1

### GCP GKE
- Storage class: `standard-rwo` (default) or `premium-rwo`
- GKE Autopilot: `spec.gke.autopilot: true`. Autopilot rejects node-group `nodeSelector` on `spec.metadataNodes`, `spec.dataNodes`, and `spec.standalone`, and requires `useSpotPods` to be false — select spot capacity with `spec.gke.autopilotComputeClass` instead
- Pod Disruption Budgets are opt-in and unrelated to Autopilot: `spec.gke.podDisruptionBudget.enabled: true`
- Workload Identity for GCS access; note that primary object storage on GCS is the `antfly serverless` `gs://` URI path, since the `storage.engine: object` config path is S3-only (see `storage.md`)

### Generic Kubernetes
- Any conformant distribution 1.23+ (minikube, kind, bare metal)
- Bring your own storage class and ingress

## Backup & Restore

```yaml
apiVersion: antfly.io/v1
kind: AntflyBackup
metadata:
  name: daily-backup
  namespace: antfly-prod
spec:
  clusterRef:
    name: prod-cluster
    # namespace: antfly-prod   # optional, defaults to the resource's namespace
  schedule: "0 2 * * *"
  destination:
    location: s3://antfly-backups/prod
    connection: backup-archive   # webhook-required on create; an external_io connection granting backup.write
  # tables: [users, products]
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
```

`destination.connection` names an `external_io` connection configured on the referenced `AntflyCluster`; it must grant `backup.write` and authorize `location`. Credentials live on that connection. `location` also accepts `file:///...` for a persistent-volume destination.

`connection` is optional in the CRD schema but required by the admission webhook on create, so every new `AntflyBackup` must name one. `destination.credentialsSecret` is **deprecated** — it exists only so legacy resources can be read and migrated, and cannot be combined with a connection. The controller parks *any* resource whose `destination.connection` is empty, legacy `credentialsSecret` holders included; that parking is the migration path. It sets phase `Pending` with reason `ConnectionRequired` and suspends the CronJob — preserving the CronJob and its history — until `connection` is set.

```yaml
apiVersion: antfly.io/v1
kind: AntflyRestore
metadata:
  name: restore-from-daily
  namespace: antfly-staging
spec:
  clusterRef:
    name: staging-cluster
  source:
    backupId: daily-backup-20250118020000   # required
    location: s3://antfly-backups/prod
    connection: backup-archive   # webhook-required on create; an external_io connection granting restore.read
  restoreMode: fail_if_exists   # fail_if_exists | skip_if_exists | overwrite
  # tables: [users]
```

`source.connection` follows the same contract as a backup destination, with the `restore.read` capability; `source.credentialsSecret` is deprecated and legacy-only, and the webhook requires a connection on create. Without one the controller parks the resource with reason `ConnectionRequired` and creates no restore Job — unless a restore Job from before the upgrade already exists, in which case it keeps observing that Job rather than parking, since replacing a running restore would be unsafe.

`AntflyRestore` is one-shot: delete and recreate the resource to run another restore.

## Service Mesh

```yaml
spec:
  serviceMesh:
    enabled: true
    annotations:
      sidecar.istio.io/inject: "true"
      traffic.sidecar.istio.io/excludeOutboundPorts: "9017,9021"
```

The operator applies the pod annotations you supply — Istio, Linkerd, and Consul Connect are examples of what those annotations can target. It does not configure mTLS itself; that is the mesh's job.

## RBAC

The operator's service account manages a broad set of cluster resources — StatefulSets, Services, PVCs, ConfigMaps, ServiceAccounts, Roles/RoleBindings, Pods and pod logs, Events, Jobs and CronJobs, HorizontalPodAutoscalers, PodDisruptionBudgets, Leases, EndpointSlices, StorageClasses, CustomResourceDefinitions, `metrics.k8s.io` pod metrics, and the Antfly CRDs. It does **not** need `get`/`list`/`watch` on Secrets — it only references them by name.

## Sharp Edges

1. **`spec.config` is required** — a cluster without it is rejected
2. **Metadata replicas must be odd** and at least 1; the webhook rejects even counts but accepts any odd number — 1, 3, and 5 are recommendations, not a validated set
3. **Node `resources` need a `limits` member** — the cpu/memory strings themselves are not content-validated by the webhook
4. **Distributed clusters require `spec.internalServiceAuth`** unconditionally — Distributed is the default `spec.mode`, and the field must be omitted entirely in Standalone mode
5. **Storage class must support ReadWriteOnce** — StatefulSets use per-pod PVCs
6. **PVCs are retained by default, but retention is configurable** — `spec.storage.pvcRetentionPolicy.whenDeleted` and `.whenScaled` each take `Retain` (default) or `Delete`. Leave them at `Retain` and reclaim storage manually, or set `Delete`; `whenScaled: Delete` is rejected alongside `dataNodes.autoScaling.enabled` or `dataNodes.suspend`
7. **AntflyCluster autoscaling is data-nodes only** — metadata replicas are fixed at deploy time. `InferencePool` has its own `spec.autoscaling` (all lowercase, unlike `dataNodes.autoScaling`) backed by a real HorizontalPodAutoscaler. `dataNodes.suspend` and `dataNodes.autoScaling.enabled: true` conflict, and the webhook rejects that pair
8. Pin a version tag rather than `ghcr.io/antflydb/antfly:latest` in production
9. Use `kubectl port-forward service/<name>-public-api 8080:80` for local access — the Service exists only when `spec.publicAPI.enabled: true` (default `false`); a LoadBalancer may take time to provision
10. Backup and restore credentials belong on the named `external_io` connection; the `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_REGION` / `AWS_ENDPOINT_URL` env-key contract is for `spec.metadataNodes.envFrom` and `spec.dataNodes.envFrom` — both forbidden in Standalone mode, which uses `spec.standalone.envFrom` — not the deprecated `credentialsSecret`
