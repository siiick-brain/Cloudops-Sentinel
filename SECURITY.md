# Security policy

This repository is a local demonstration. It is not a security certification or an independently reviewed deployment.

## Reporting

Do not post credentials, exploit details or personal data in a public issue. Contact the repository owner privately with a concise report and steps to reproduce.

## Credential handling

Keep local values in ignored `.env` and automation values in GitHub secrets. Rotate any value that is exposed. The default tokens and password in `.env.example` are placeholders for local use only.

## Scope and limitations

The chaos endpoint injects faults and must remain protected. Do not expose it to an untrusted network. Mock service state is in memory. Container hardening and image scans require validation on the target host.

