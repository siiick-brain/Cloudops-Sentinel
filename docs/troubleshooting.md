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

## cAdvisor scrapes time out on Docker Desktop

**Symptom:** the `cadvisor` target is down with `context deadline exceeded`, the container is unhealthy and its logs show `disk usage and inodes count ... took 1m...`.

**Cause:** cAdvisor walks every container layer to measure disk use. On Docker Desktop's overlayfs this takes minutes and with every metric family enabled the container ran out of its CPU and memory limits.

**Fix:** the compose file passes `--docker_only`, a 15 s housekeeping interval and `--disable_metrics` for every family the rules and dashboards do not use and gives cAdvisor 384 MiB and one CPU. Scrapes now take about 50 ms.

## Disk-fill alert never fires

**Cause:** with the containerd image store, cAdvisor reports `container_fs_usage_bytes` only for the root cgroup, never per container, so `container_fs_usage_bytes{name=~".*chaos-tools.*"}` has no series.

**Fix:** the disk-fill scenario fills a 64 MiB tmpfs at `/scratch` in `chaos-tools` and writes its `df` numbers to the node-exporter textfile collector as `chaos_scratch_size_bytes` and `chaos_scratch_avail_bytes`. `ChaosContainerDiskHigh` alerts when the ratio passes 80 percent.
