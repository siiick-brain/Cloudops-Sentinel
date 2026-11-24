# ChaosContainerDiskHigh

## Symptoms and impact

The chaos container's 64 MiB scratch filesystem is more than 80 percent full. Only the
disk-fill exercise writes there, so service traffic is not affected. In a real service the
same pattern, a filesystem filling, ends in failed writes, crashed processes and lost data.

## Dashboards and queries

- Node and container health dashboard.
- `1 - chaos_scratch_avail_bytes / chaos_scratch_size_bytes` shows the fill ratio.
- `chaos_scratch_avail_bytes` comes from `df` on `/scratch` inside `chaos-tools`, published
  through the node-exporter textfile collector. cAdvisor cannot report per-container
  filesystem use on Docker Desktop with the containerd image store.

## Diagnosis

1. Confirm the disk-fill scenario is running: `docker compose --profile chaos ps chaos-tools`.
2. Check the file size: `docker compose exec chaos-tools du -sh /scratch`.
3. If nothing should be running, look for a stale `/textfile/chaos.prom` left by an
   interrupted run.

## Mitigation

Remove the test file and the metric file, then stop the container:

```sh
docker compose exec chaos-tools rm -f /scratch/fill /textfile/chaos.prom
docker compose --profile chaos stop chaos-tools
```

The alert resolves once the metric is gone or the ratio drops below 80 percent.

## Escalation

Escalate to the platform owner if node filesystem alerts (`NodeDiskHigh`,
`NodeDiskFillingSoon`) fire at the same time, since that means the host disk is affected.
