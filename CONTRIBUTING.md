# Contributing

## Local checks

Install `requirements-dev.txt`, then run:

```powershell
python -m pip install -r requirements-dev.txt
pytest
ruff check .
mypy
docker compose config
```

The monitoring checks use Prometheus and Alertmanager tools. The CI workflow runs the configuration checks in versioned containers.

## Changes

Keep changes focused. Add or update tests for behavior changes. Do not include secrets or live customer data. Document limitations and checks that were not run.

