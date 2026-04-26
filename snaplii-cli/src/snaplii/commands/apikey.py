import click

from snaplii.client import GatewayClient
from snaplii.output import print_json


def _mask_key(key: str) -> str:
    if not key or len(key) < 16:
        return "***"
    return key[:12] + "..." + key[-4:]


@click.group("apikey")
@click.pass_context
def apikey_group(ctx):
    """API key management (create, list, delete)."""
    pass


@apikey_group.command("list")
@click.pass_context
def apikey_list(ctx):
    """List all your API keys (keys are masked)."""
    client: GatewayClient = ctx.obj["client"]
    resp = client.list_api_keys()
    for key in resp.get("keys", []):
        if "apiKey" in key:
            key["apiKey"] = _mask_key(key["apiKey"])
    print_json(resp)


@apikey_group.command("create")
@click.option("--name", required=True, help="API key name")
@click.option("--scope", default="PAY_READ", help="Permission: PAY_READ (view cards only) or PAY_WRITE (view + purchase)")
@click.option("--limit", default=None, type=float, help="Consumption limit in dollars")
@click.option("--reveal", is_flag=True, default=False, help="Show full API key (use with caution)")
@click.pass_context
def apikey_create(ctx, name, scope, limit, reveal):
    """Create a new API key. Full key is only returned once."""
    client: GatewayClient = ctx.obj["client"]
    resp = client.create_api_key(name, scope, limit)
    if not reveal and "apiKey" in resp:
        full_key = resp["apiKey"]
        resp["apiKey"] = _mask_key(full_key)
        resp["_notice"] = "Key created. Run with --reveal to see the full key. It is only shown once."
    print_json(resp)


@apikey_group.command("delete")
@click.option("--key-id", required=True, help="API key ID to delete")
@click.pass_context
def apikey_delete(ctx, key_id):
    """Delete an API key."""
    client: GatewayClient = ctx.obj["client"]
    resp = client.delete_api_key(key_id)
    print_json(resp)
