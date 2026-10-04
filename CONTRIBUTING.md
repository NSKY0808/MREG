# Contributing

Start with the README setup and development commands. Run pytest, Ruff checks and
formatting, mypy, and Bandit before submitting changes. Regenerate schemas/reason-code
docs after contract changes; tests detect schema drift. Add boundary cases, not just
happy paths. The normalized evidence contract and existing reason codes are public.

Good contributions include real integration feedback, regression fixtures, documented
policy recipes, and optional adapters with parity tests. Discuss broad new task support
before adding it. Do not add mandatory registries, cloud services, LLMs, or deployment
credentials. Use synthetic or redistributable examples and never commit secrets.
