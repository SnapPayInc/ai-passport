import click

from snaplii.client import GatewayClient
from snaplii.output import print_json


@click.group("card-brands")
@click.pass_context
def card_brands_group(ctx):
    """Card brand operations (list, get)."""
    pass


@card_brands_group.command("list")
@click.pass_context
def card_brands_list(ctx):
    """List all available card brands (brandId + name)."""
    client: GatewayClient = ctx.obj["client"]
    resp = client.list_card_brands()
    print_json(resp)


@card_brands_group.command("get")
@click.option("--id", "card_brand_id", required=True, help="Card brand ID")
@click.pass_context
def card_brands_get(ctx, card_brand_id):
    """Get card brand details by ID."""
    client: GatewayClient = ctx.obj["client"]
    resp = client.get_card_brand(card_brand_id)
    print_json(resp)
