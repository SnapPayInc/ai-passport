import click

from snaplii.client import GatewayClient
from snaplii.output import print_json


@click.group("giftcard")
@click.pass_context
def giftcard_group(ctx):
    """Gift card operations (list owned cards, view details)."""
    pass


@giftcard_group.command("list")
@click.option("--status", default="ACTIVE", help="Card status: ACTIVE or INACTIVE")
@click.option("--page", default=1, type=int, help="Page number")
@click.option("--page-size", default=20, type=int, help="Page size")
@click.pass_context
def giftcard_list(ctx, status, page, page_size):
    """List your gift cards."""
    client: GatewayClient = ctx.obj["client"]
    resp = client.list_user_cards(status=status, page=page, page_size=page_size)
    print_json(resp)


@giftcard_group.command("detail")
@click.option("--card-no", required=True, help="Card number")
@click.pass_context
def giftcard_detail(ctx, card_no):
    """Get details of a specific gift card (including redemption code)."""
    client: GatewayClient = ctx.obj["client"]
    resp = client.get_card_detail(card_no)
    print_json(resp)
