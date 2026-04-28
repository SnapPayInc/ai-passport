import hashlib

import click

from snaplii.client import GatewayClient
from snaplii.output import print_json


def _derive_agent_id(api_key: str) -> str:
    """Derive a stable agent_id from api_key: 'agent-' + first 8 chars of MD5."""
    digest = hashlib.md5(api_key.encode()).hexdigest()
    return f"agent-{digest[:8]}"


@click.command("init")
@click.option("--agent-id", default=None, help="Agent ID (optional — auto-derived from API key if omitted)")
@click.option("--api-key", required=True, help="API key (snp_sk_live_...)")
@click.pass_context
def init_cmd(ctx, agent_id, api_key):
    """Login with API key and store credentials."""
    client: GatewayClient = ctx.obj["client"]
    store = ctx.obj["config_store"]

    if not agent_id:
        agent_id = _derive_agent_id(api_key)

    store.set_many({"agent_id": agent_id, "api_key": api_key})
    resp = client.login(agent_id, api_key)
    safe = {k: v for k, v in resp.items() if k not in ("access_token", "token_type", "expires_in")}
    safe["status"] = "authenticated"
    safe["agent_id"] = agent_id
    safe["credential_storage"] = "system keychain" if store._use_keyring else "config file (keyring not available)"
    print_json(safe)
