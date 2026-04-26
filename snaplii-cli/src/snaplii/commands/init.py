import click

from snaplii.client import GatewayClient
from snaplii.output import print_json


@click.command("init")
@click.option("--agent-id", required=True, help="Agent ID for session isolation")
@click.option("--api-key", required=True, help="API key (snp_sk_live_...)")
@click.pass_context
def init_cmd(ctx, agent_id, api_key):
    """Login with agent ID + API key and store credentials."""
    client: GatewayClient = ctx.obj["client"]
    store = ctx.obj["config_store"]

    store.set_many({"agent_id": agent_id, "api_key": api_key})
    resp = client.login(agent_id, api_key)
    safe = {k: v for k, v in resp.items() if k not in ("access_token", "token_type", "expires_in")}
    safe["status"] = "authenticated"
    print_json(safe)
