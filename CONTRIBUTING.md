# Contributing to vibops-mcp

Thank you for your interest in contributing! vibops-mcp is an open MCP server for GPU infrastructure management, maintained by [VibOps](https://vibops.io).

## Ways to contribute

- **Bug reports** — open an issue with steps to reproduce
- **New tools** — propose via issue before implementing
- **Provider connectors** — see the roadmap for planned providers
- **Documentation** — fixes, examples, translations

## Before you start

For anything beyond a typo fix, open an issue first to discuss. This avoids wasted effort on PRs that don't align with the roadmap.

## Developer Certificate of Origin (DCO)

All contributions must be signed off with the DCO. Add this line to every commit:

```
Signed-off-by: Your Name <your@email.com>
```

Use `git commit -s` to add it automatically. By signing off, you certify that you wrote the code and have the right to submit it under the MIT license.

## Setting up

```bash
git clone https://github.com/VibOpsai/vibops-mcp.git
cd vibops-mcp
pip install -e "."
```

You need a running VibOps instance. Set:

```bash
export VIBOPS_URL=http://localhost:8003
export VIBOPS_TOKEN=vbops_xxx   # create one in VibOps → Admin → API Tokens
```

## Adding a tool

1. Pick the right module — `tools/observation.py` (read-only), `tools/actions.py` (write), `tools/config.py`
2. Add the function with a clear docstring — the docstring becomes the tool description seen by the LLM
3. Register it in `server.py` with `@mcp.tool()`
4. Test manually: `echo '...' | vibops-mcp`

## Pull request checklist

- [ ] Issue linked or discussed beforehand
- [ ] DCO sign-off on all commits (`git commit -s`)
- [ ] Docstring explains what the tool does and documents all parameters
- [ ] No credentials, tokens, or URLs hardcoded
- [ ] `pyproject.toml` version bumped if adding a tool

## Code style

- Python 3.11+
- Type hints on all function signatures
- No external dependencies beyond `mcp[cli]` and `httpx`

## Questions

Open an issue or reach out at [hello@vibops.io](mailto:hello@vibops.io).
