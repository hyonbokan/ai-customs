### Run the Linters

Ensure pre-commit is installed (`pip install pre-commit`).

```bash
# From the ai-auditor project root, to catch frontend files too if hooks are configured for them
pre-commit install
pre-commit run --all-files -v
```
