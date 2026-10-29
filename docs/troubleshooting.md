# Troubleshooting

## Empty container resource panels on Docker Desktop

**Symptom:** cAdvisor repeatedly logs `failed to identify the read-write layer ID` and per-container CPU, memory or filesystem panels are empty.

**Cause:** Docker Desktop reports the `overlayfs` storage driver while using the containerd image store. cAdvisor v0.49.2 expected Docker layer IDs that are not present in the containerd image store metadata.

**Fix:** In Docker Desktop settings, turn off **Use containerd for pulling and storing images** and restart Docker Desktop. Do not change the cAdvisor mounts. On Linux, set this in Docker Engine settings or `/etc/docker/daemon.json` and restart Docker:

```json
{
  "features": {
    "containerd-snapshotter": false
  }
}
```

The original cAdvisor v0.49.2 produced the layer error on this host. The project now pins cAdvisor v0.60.6. Release v0.54.0 added containerd snapshotter support and v0.60.6 was published on 2026-09-18. An isolated test and the production-style stack returned named container CPU and memory samples with the existing mounts. See the [v0.54.0 release notes](https://github.com/google/cadvisor/releases/tag/v0.54.0) and [v0.60.6 release notes](https://github.com/google/cadvisor/releases/tag/v0.60.6).

**Verify:** Run `.\scripts\check-docker-storage.ps1`, query `http://localhost:8085/metrics` for `container_cpu_usage_seconds_total` and `container_memory_working_set_bytes` samples with a `name` label and check cAdvisor logs for the repeated layer-ID error. Named container metrics and the CPU and memory chaos alerts were confirmed in recorded local runs. The disk-fill alert remains unconfirmed.
