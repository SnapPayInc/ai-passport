# AI Passport by Snaplii

**Safe, limited-authorization payments for AI agents.**

AI Passport lets AI agents browse, purchase, and manage gift cards through Snaplii — with spending limits and scoped permissions. Agents pay with Snaplii Cash (prepaid balance), so exposure is capped and controllable.

## Quick Start

### 1. Install the CLI

```bash
pip install -e snaplii-cli/
```

### 2. Authenticate

```bash
snaplii init --agent-id "my-agent" --api-key "snp_sk_live_..."
```

### 3. Use

```bash
snaplii browse tags              # browse gift card categories
snaplii browse brand --id CB...  # see denominations & cashback
snaplii giftcard list            # view owned cards
snaplii purchase --item-id CB...-CT... --price 50  # buy a card
```

## Components

```
ai-passport/
├── snaplii-cli/     # Python CLI — pip-installable
├── mcp-server/      # MCP server for Claude Desktop integration
├── skills/          # Claude Code skill definition
└── docs/            # API reference documentation
```

### CLI Commands

| Command | Purpose |
|---------|---------|
| `snaplii init` | Authenticate with API key |
| `snaplii browse tags` | Browse card categories & brands |
| `snaplii browse brand --id ID` | Get brand details (denominations, cashback) |
| `snaplii giftcard list` | List owned gift cards |
| `snaplii giftcard detail --card-no NO` | Get card redemption code & PIN |
| `snaplii purchase --item-id ID --price P` | Purchase a gift card |
| `snaplii smart cashback --brand-id ID --amount A` | Calculate cashback savings |
| `snaplii smart dashboard` | View card inventory summary |
| `snaplii apikey list/create/delete` | Manage API keys |

### MCP Server (Claude Desktop)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "snaplii": {
      "command": "python3",
      "args": ["/path/to/ai-passport/mcp-server/server.py"]
    }
  }
}
```

Restart Claude Desktop. 12 tools will be available for natural-language gift card operations.

### Claude Code Skill

Copy `skills/snaplii-cli.md` to `~/.claude/skills/` to enable the Snaplii skill in Claude Code.

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
