# Security boundaries

The deterministic core reads bounded local JSON and safe YAML, validates strict
contracts, and renders escaped text. It does not deserialize model files or run
expressions. Treat adapter results, metadata, definitions, and reports as untrusted.
Accepted identities are included in local reports/bundles: collectors must remove
secrets and sensitive IDs before producing evidence. Automatic arbitrary-secret
detection, tamper-proof evidence, and authenticated attestations are not implemented.

Do not execute repository code with deployment credentials to infer configuration.
The example CI uses separate candidate-evaluation and trusted-review jobs without
secrets. Production use needs protected workflows, trusted producers, and digest binding.

No public repository or private vulnerability-reporting channel is configured yet.
Before public publication, enable a private reporting channel and replace this note
with real contact instructions. Do not post sensitive vulnerability details in public
issues. Only 0.1.0 is currently implemented; there is no long-term support commitment.
