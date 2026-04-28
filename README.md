AI Passport by Snaplii
Safe, limited-authorization payments for AI agents.
AI Passport lets AI agents browse, purchase, and manage gift cards through Snaplii — with spending limits and scoped permissions. Agents pay with Snaplii Cash (prepaid balance), so exposure is capped and controllable.
Requirements
•	Python 3.10+ (CLI works on 3.9+, but MCP server needs 3.10+)
•	git
•	Snaplii Mobile App (required to generate your API key)
<details>
<summary>Mac users: check your Python version</summary>
python3 --version

If below 3.10, install via Homebrew:
brew install python@3.12

Then use python3.12 and pip3.12 instead of python3 / pip3 in the steps below.
</details>
Quick Start
1. Get Your API Key via Snaplii App
Before using the CLI or configuring your AI agent, you must generate a secure API key from the Snaplii mobile app:
	1.	Download the Snaplii app (iOS / Android).
	2.	Register an account and bind a payment method to load your Snaplii Cash balance.
	3.	In the app, navigate to More → Payment Methods → AI Payment Management.
	4.	Tap + New API Key. Here, you will set a name, define the permission scope (e.g., Read-only vs. Purchase), and set a hard spending limit.
	5.	Copy the API key (format: snp_sk_live_...). Keep this safe — it will only be shown once!
2. Get the Code
git clone https://github.com/SnapPayInc/ai-passport.git
cd ai-passport

3. Install the CLI
pipx is the smoothest path — it installs the CLI into its own isolated environment and puts the snaplii executable on your PATH:
# macOS
brew install pipx && pipx ensurepath

# Linux
python3 -m pip install --user pipx && python3 -m pipx ensurepath

# Windows (PowerShell)
py -m pip install --user pipx ; py -m pipx ensurepath

# All platforms
pipx install -e ./snaplii-cli

Open a new terminal window so the updated PATH takes effect, then verify the installation:
snaplii --help

(If you see "command not found", jump to Troubleshooting.)
4. Authenticate
Link your local CLI to your Snaplii account using the API key you generated in Step 1:
snaplii init --api-key "snp_sk_live_..."

5. Use the CLI
snaplii browse tags                                  # Browse gift card categories
snaplii browse brand --id CB...                      # See denominations & cashback
snaplii giftcard list                                # View owned cards
snaplii purchase --item-id CB...-CT... --price 50    # Buy a card

Note: --item-id is formatted as {cardBrandId}-{cardTemplateId}. Both IDs can be found using the browse brand command.
Components
ai-passport/
├── snaplii-cli/     # Python CLI — pip-installable
├── mcp-server/      # MCP server for Claude Desktop
└── skills/          # Claude Code skill definition

CLI Commands
Command	Purpose
snaplii init	Authenticate with your Snaplii API key
snaplii config show	Show current config & auth status
snaplii browse tags	Browse card categories & brands
snaplii browse brand --id ID	Brand details (denominations, cashback)
snaplii giftcard list	List owned gift cards
snaplii giftcard detail --card-no NO	Card redemption code & PIN
snaplii purchase --item-id ID --price P	Purchase a gift card
snaplii smart cashback --brand-id ID --amount A	Calculate cashback savings
snaplii smart dashboard	View card inventory summary
Claude Desktop Setup (MCP Server)
Claude Desktop cannot run CLI commands directly — it requires an MCP server to bridge the gap. The Snaplii MCP server exposes 12 tools that let Claude browse gift cards and make purchases through natural conversation.
Step 1: Install dependencies
The MCP server requires Python 3.10+ and the mcp package. Install both the CLI and server dependencies:
pip3 install -e ./snaplii-cli
pip3 install "mcp[cli]"

# If you get an "externally-managed-environment" error, add:
pip3 install -e ./snaplii-cli --break-system-packages
pip3 install "mcp[cli]" --break-system-packages

Step 2: Authenticate (one-time)
The MCP server reads credentials from ~/.snaplii/config.json. If you haven't authenticated yet, run this once:
snaplii init --api-key "snp_sk_live_..."

Step 3: Configure Claude Desktop
Edit the Claude Desktop config file:
OS	Config file location
macOS	~/Library/Application Support/Claude/claude_desktop_config.json
Windows	%APPDATA%\Claude\claude_desktop_config.json
Linux	~/.config/Claude/claude_desktop_config.json
Add the mcpServers section (create the file if it doesn't exist). Ensure you use absolute paths:
{
  "mcpServers": {
    "snaplii": {
      "command": "/absolute/path/to/python",
      "args": ["/absolute/path/to/ai-passport/mcp-server/server.py"]
    }
  }
}

Important:
•	command must point to the Python interpreter where mcp is installed. Find it using which python3 or echo ~/.venvs/snaplii/bin/python.
•	args must be the exact path to server.py inside your cloned repo.
Step 4: Restart Claude Desktop
Fully quit Claude Desktop (e.g., Cmd+Q on Mac), then reopen it. You should now see the Snaplii tools available.
Step 5: Verify
In a new Claude Desktop conversation, try asking:
"What gift cards are available on Snaplii?"
Claude should automatically call snaplii_browse_tags and display the categories.
Claude Code Skill
Claude Code expects each skill in its own directory containing a SKILL.md:
mkdir -p ~/.claude/skills/snaplii-cli
cp skills/snaplii-cli.md ~/.claude/skills/snaplii-cli/SKILL.md

Then open ~/.claude/skills/snaplii-cli/SKILL.md. If the file contains a line like:
Always prepend `export PATH="$PATH:/Users/.../bin" &&` before any snaplii command.

Replace the path with the directory that holds your snaplii binary. You can find it with which snaplii (Unix) or where.exe snaplii (Windows). If snaplii is already on your default PATH, you can delete that export PATH=... prefix entirely.
Troubleshooting
snaplii: command not found after install. The console script was placed somewhere not on your PATH. Run python3 -m pip show -f snaplii-cli and look for an entry ending in bin/snaplii (or Scripts\snaplii.exe on Windows). Either prepend that directory to PATH in your shell configuration, or reinstall using pipx.
error: externally-managed-environment from pip. Your system Python forbids global package installs. Use pipx (recommended) or a virtual environment. As a last resort, append --break-system-packages to the pip command.
Claude Desktop logs ModuleNotFoundError: No module named 'mcp' (or 'snaplii'). The Python interpreter referenced by command in claude_desktop_config.json doesn't have the required dependencies. Confirm by running:
/absolute/path/to/python -c "import mcp, snaplii; print('ok')"

If it fails, install the missing packages into that specific interpreter (pip install -e ./snaplii-cli and pip install "mcp[cli]").
Security
•	Limited authorization: Agents can only spend from Snaplii Cash (your prepaid balance).
•	Scoped API keys: Keys can be restricted to PAY_READ (view only) or PAY_WRITE (view + purchase).
•	Spending limits: Strict per-key consumption caps set via the mobile app.
•	Data protection: Card redemption codes and PINs are strictly masked and never exposed without explicit user consent.
License
Proprietary — Snaplii Inc.