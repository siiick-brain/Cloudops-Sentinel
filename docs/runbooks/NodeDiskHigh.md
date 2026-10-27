# NodeDiskHigh

## Symptoms and impact

Filesystem use is above 85 percent. Writes may fail when available space is exhausted.

## Dashboards and queries

Review node filesystem metrics and query `node_filesystem_avail_bytes`.

## Diagnosis

Check filesystem labels and locate large files or growing volumes.

## Mitigation

Remove only known disposable data and restore adequate free space. Do not delete unknown service data.

## Escalation

Escalate when free space continues to fall or the host filesystem is affected.

