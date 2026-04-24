import sys

import click

from snaplii.client import GatewayClient
from snaplii.commands.apikey import apikey_group
from snaplii.commands.browse import browse_group
from snaplii.commands.config import config_group
from snaplii.commands.giftcard import giftcard_group
from snaplii.commands.init import init_cmd
from snaplii.commands.purchase import purchase_cmd
from snaplii.commands.smart import smart_group
from snaplii.config_store import ConfigStore
from snaplii.exceptions import SnapliiCliError
from snaplii.output import print_error

_DEFAULT_BASE_URL = "https://gateway.snaplii.com/gateway/mrpay"


@click.group()
@click.option(
    "--base-url",
    envvar="SNAPLII_BASE_URL",
    default=None,
    help="Gateway base URL (overrides config)",
)
@click.pass_context
def main(ctx, base_url):
    """Snaplii Agent Gateway CLI.

    Browse gift card brands, manage your cards, purchase new ones,
    and manage API keys.
    """
    ctx.ensure_object(dict)
    store = ConfigStore()
    resolved_url = base_url or store.get("base_url", _DEFAULT_BASE_URL)
    ctx.obj["config_store"] = store
    ctx.obj["client"] = GatewayClient(resolved_url, store)


main.add_command(init_cmd)
main.add_command(browse_group)
main.add_command(giftcard_group)
main.add_command(purchase_cmd)
main.add_command(apikey_group)
main.add_command(smart_group)
main.add_command(config_group)


@main.command("help")
@click.pass_context
def help_cmd(ctx):
    """Show full CLI documentation."""
    click.echo(ctx.parent.get_help())


def _cli():
    try:
        main(standalone_mode=False)
    except click.exceptions.Exit:
        pass
    except click.UsageError as e:
        print_error({"error": "Usage error", "message": str(e)})
        sys.exit(1)
    except SnapliiCliError as e:
        print_error(e.to_dict())
        sys.exit(1)
