# AI Passport by Snaplii

**Safe, limited-authorization payments for AI agents.**

AI Passport lets AI agents browse, purchase, and manage gift cards through Snaplii — with spending limits and scoped permissions. Agents pay with Snaplii Cash (prepaid balance), so exposure is capped and controllable.

## Requirements

- Python **3.9+** for the CLI, **3.10+** if you also want the MCP server
- `git`
- An agent ID and API key issued by Snaplii

## Quick Start

### 1. Get the code

```bash
git clone https://github.com/SnapPayInc/ai-passport.git
cd ai-passport
```

### 2. Install the CLI

`pipx` is the smoothest path — it installs the CLI into its own isolated environment and puts the `snaplii` executable on your PATH:

```bash
# macOS
brew install pipx && pipx ensurepath

# Linux
python3 -m pip install --user pipx && python3 -m pipx ensurepath

# Windows (PowerShell)
py -m pip install --user pipx ; py -m pipx ensurepath

# All platforms
pipx install -e ./snaplii-cli
```

Open a new shell so the updated PATH takes effect.

<details>
<summary>No pipx? Use a venv.</summary>

```bash
python3 -m venv ~/.venvs/snaplii
source ~/.venvs/snaplii/bin/activate          # Windows: ~\.venvs\snaplii\Scripts\activate
pip install -e ./snaplii-cli
```

The CLI is only available while the venv is activated (or when you call `~/.venvs/snaplii/bin/snaplii` directly).
</details>

<details>
<summary>Last resort: install with raw pip.</summary>

```bash
pip3 install --user -e ./snaplii-cli
# If pip refuses with "error: externally-managed-environment", append --break-system-packages.
```

The `snaplii` script may land in a directory that isn't on your PATH:

| OS | Likely location |
|---|---|
| macOS (system Python 3.9) | `~/Library/Python/3.9/bin` |
| Linux | `~/.local/bin` |
| Windows | `%APPDATA%\Python\Python3xx\Scripts` |

Add it to PATH if `snaplii` isn't found. See [Troubleshooting](#troubleshooting).
</details>

### 3. Verify

```bash
snaplii --help
```

If you see "command not found", jump to [Troubleshooting](#troubleshooting).

### 4. Authenticate

```bash
snaplii init --agent-id "<your-agent-id>" --api-key "snp_sk_live_..."
```

### 5. Use

```bash
snaplii browse tags                                  # browse gift card categories
snaplii browse brand --id CB...                      # see denominations & cashback
snaplii giftcard list                                # view owned cards
snaplii purchase --item-id CB...-CT... --price 50    # buy a card
```

`--item-id` is `{cardBrandId}-{cardTemplateId}`; both IDs come from `browse brand`.

## Components

```
ai-passport/
├── snaplii-cli/     # Python CLI — pip-installable
├── mcp-server/      # MCP server for Claude Desktop
├── skills/          # Claude Code skill definition
└── docs/            # API reference documentation
```

### CLI Commands

| Command | Purpose |
|---------|---------|
| `snaplii init` | Authenticate with agent ID + API key |
| `snaplii config show` | Show current config & auth status |
| `snaplii browse tags` | Browse card categories & brands |
| `snaplii browse brand --id ID` | Brand details (denominations, cashback) |
| `snaplii giftcard list` | List owned gift cards |
| `snaplii giftcard detail --card-no NO` | Card redemption code & PIN |
| `snaplii purchase --item-id ID --price P` | Purchase a gift card |
| `snaplii smart cashback --brand-id ID --amount A` | Calculate cashback savings |
| `snaplii smart dashboard` | View card inventory summary |
| `snaplii apikey list \| create \| delete` | Manage API keys |

### MCP Server (Claude Desktop)

The MCP server depends on the `mcp` Python package. Install it (and any other server deps) into a Python environment, then point Claude Desktop at that interpreter.

```bash
# Pick any environment — pipx, venv, or system pip — that uses Python 3.10+
pip install -e ./mcp-server
```

Then add to `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS (the equivalent path on Linux / Windows works the same way):

```json
{
  "mcpServers": {
    "snaplii": {
      "command": "/absolute/path/to/python",
      "args": ["/absolute/path/to/ai-passport/mcp-server/server.py"]
    }
  }
}
```

- `command` must be the Python interpreter where you just installed `mcp` (e.g. `~/.venvs/snaplii/bin/python`, or whatever `head -1 $(which snaplii)` shows on Unix).
- `args[0]` must be the absolute path to `server.py` inside your clone — the server reads sibling files via `Path(__file__).parent.parent`, so do not move `server.py` out of the repo.

Restart Claude Desktop after editing the config.

### Claude Code Skill

Claude Code expects each skill in its own directory containing a `SKILL.md`:

```bash
mkdir -p ~/.claude/skills/snaplii-cli
cp skills/snaplii-cli.md ~/.claude/skills/snaplii-cli/SKILL.md
```

Then open `~/.claude/skills/snaplii-cli/SKILL.md`. If the file contains a line like:

```
Always prepend `export PATH="$PATH:/Users/.../bin" &&` before any snaplii command.
```

— replace the path with the directory that holds **your** `snaplii` binary. Find it with:

```bash
which snaplii          # Unix
where.exe snaplii      # Windows
```

If `snaplii` is already on the default PATH for new shells (typical with `pipx`), delete the `export PATH=...` prefix from the skill entirely.

The skill becomes available in Claude Code on the next session.

## Troubleshooting

**`snaplii: command not found` after install.** The console script was placed somewhere not on your PATH. Run `python3 -m pip show -f snaplii-cli` and look for an entry ending in `bin/snaplii` (or `Scripts\snaplii.exe` on Windows). Either prepend that directory to PATH in your shell rc, or reinstall via `pipx`.

**`error: externally-managed-environment` from pip.** Your system Python forbids global package installs (PEP 668). Use `pipx` (recommended) or a venv. Last resort: append `--break-system-packages` to the pip command — at the cost of polluting the system Python.

**Claude Desktop logs `ModuleNotFoundError: No module named 'mcp'` (or `'snaplii'`).** The Python interpreter referenced by `command` in `claude_desktop_config.json` doesn't have the deps installed. Confirm with:

```bash
/absolute/path/to/python -c "import mcp, snaplii; print('ok')"
```

If it fails, install the missing package into that interpreter (`pip install -e ./mcp-server` and/or `pip install -e ./snaplii-cli`), or change `command` to a Python that already has them.

**Claude Code does not pick up the skill.** Make sure the file is at `~/.claude/skills/snaplii-cli/SKILL.md` (folder + `SKILL.md`), not `~/.claude/skills/snaplii-cli.md` directly.

## API Documentation

See `docs/` for full API reference:
- [API Key Management](docs/apikey-doc.md)
- [Card Tags & Brands](docs/card-tags-doc.md)
- [Purchase (createOrderAndPay)](docs/create-order-and-pay-doc.md)

## Security

- **Limited authorization**: Agents can only spend from Snaplii Cash (prepaid balance)
- **Scoped API keys**: `PAY_READ` (view only) or `PAY_WRITE` (view + purchase)
- **Spending limits**: Per-key consumption caps
- **Sensitive data protection**: Card codes and PINs are never exposed without explicit user consent

## License

Proprietary — Snaplii Inc.
