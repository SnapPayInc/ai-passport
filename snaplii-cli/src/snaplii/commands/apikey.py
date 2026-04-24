import click

from snaplii.client import GatewayClient
from snaplii.output import print_json


@click.group("apikey")
@click.pass_context
def apikey_group(ctx):
    """API key management (create, list, delete)."""
    pass


@apikey_group.command("list")
@click.pass_context
def apikey_list(ctx):
    """List all your API keys."""
    client: GatewayClient = ctx.obj["client"]
    resp = client.list_api_keys()
    print_json(resp)


@apikey_group.command("create")
@click.option("--name", required=True, help="API key name")
@click.option("--scope", default="PAY_READ", help="Scope: PAY_READ or PAY_WRITE")
@click.option("--limit", default=None, type=float, help="Consumption limit in dollars")
@click.pass_context
def apikey_create(ctx, name, scope, limit):
    """Create a new API key."""
    client: GatewayClient = ctx.obj["client"]
    resp = client.create_api_key(name, scope, limit)
    print_json(resp)


@apikey_group.command("delete")
@click.option("--key-id", required=True, help="API key ID to delete")
@click.pass_context
def apikey_delete(ctx, key_id):
    """Delete an API key."""
    client: GatewayClient = ctx.obj["client"]
    resp = client.delete_api_key(key_id)
    print_json(resp)
