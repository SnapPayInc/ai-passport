import click

from snaplii.client import GatewayClient
from snaplii.output import print_json


@click.command("purchase")
@click.option("--item-id", required=True, help="Item ID (e.g. CB0000000000135-CT0000000000897)")
@click.option("--price", required=True, help="Price in dollars (e.g. 50)")
@click.option("--payment-method", default="SNAPLII_CREDIT", help="Payment method")
@click.option("--payment-token", required=True, help="Payment token for the payment card")
@click.option("--prov", default="ON", help="Province code")
@click.pass_context
def purchase_cmd(ctx, item_id, price, payment_method, payment_token, prov):
    """Create an order and pay for a gift card."""
    client: GatewayClient = ctx.obj["client"]
    resp = client.create_order_and_pay(
        item_id=item_id,
        price=price,
        payment_method=payment_method,
        payment_token=payment_token,
        location_prov=prov,
    )
    print_json(resp)
