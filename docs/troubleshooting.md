# Troubleshooting

## Empty container resource panels on Docker Desktop

**Symptom:** cAdvisor repeatedly logs `failed to identify the read-write layer ID` and per-container CPU, memory or filesystem panels are empty.

**Cause:** Docker Desktop reports the `overlayfs` storage driver while using the containerd image store. cAdvisor v0.49.2 expects Docker layer IDs that are not present in the containerd image store metadata.

**Fix:** In Docker Desktop settings, turn off the containerd image store and restart Docker Desktop. On Linux, set this in `/etc/docker/daemon.json` and restart Docker:

```json
{
  "features": {
    "containerd-snapshotter": false
  }
}
```

An isolated test of cAdvisor v0.60.6 reported named container CPU metrics on this Docker Desktop host with the existing mounts. Release v0.54.0 added containerd snapshotter support and v0.60.6 was published on 2026-09-18. See the [v0.54.0 release notes](https://github.com/google/cadvisor/releases/tag/v0.54.0) and [v0.60.6 release notes](https://github.com/google/cadvisor/releases/tag/v0.60.6). The project still pins v0.49.2 until the tested upgrade is committed separately.

**Verify:** Run `.\scripts\check-docker-storage.ps1`, query `http://localhost:8085/metrics` for `container_cpu_usage_seconds_total` with a `name` label and check cAdvisor logs for the repeated layer-ID error. Run `python chaos/run.py cpu-stress` only after named container metrics are present. Container alert firing remains unverified until its scenario completes successfully.
