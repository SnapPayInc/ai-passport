#!/usr/bin/env python3
"""Snaplii MCP Server — exposes Snaplii gift card operations as MCP tools."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

_CLI_SRC = Path(__file__).parent.parent / "snaplii-cli" / "src"
if str(_CLI_SRC) not in sys.path:
    sys.path.insert(0, str(_CLI_SRC))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from snaplii.client import GatewayClient
from snaplii.config_store import ConfigStore
from snaplii.exceptions import ConfigError, GatewayApiError, GatewayConnectionError

app = Server("snaplii")

_DEFAULT_BASE_URL = "https://aipayment.snaplii.com"


def _get_client() -> GatewayClient:
    store = ConfigStore()
    base_url = store.get("base_url", _DEFAULT_BASE_URL)
    return GatewayClient(base_url, store)


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="snaplii_config_show",
            description="Show current Snaplii config and auth status.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="snaplii_init",
            description="Login with agent ID and API key (snp_sk_live_...). Run this before any other operation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "Agent identifier for session isolation"},
                    "api_key": {"type": "string", "description": "API key (snp_sk_live_...)"},
                },
                "required": ["agent_id", "api_key"],
            },
        ),
        types.Tool(
            name="snaplii_browse_tags",
            description="Browse all gift card categories with brand summaries (name, cashback rate, brandId). IMPORTANT: Before calling this, always ask the user which country/region they are in (Canada or US). Then filter results accordingly — some brands are marked with country flags (🇺🇸 = US only, 🇨🇦 = Canada only, 🇺🇸🇨🇦 = both). Only show brands available in the user's region. When users describe a scenario (e.g. travel, dining), YOU should analyze the data, filter by region, compare cashback rates, and recommend the best options.",
            inputSchema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "HOME_PAGE or SEND_GIFT", "default": "HOME_PAGE"},
                    "prov": {"type": "string", "description": "Province code (ON, QC, BC)", "default": "ON"},
                },
                "required": [],
            },
        ),
        types.Tool(
            name="snaplii_browse_brand",
            description="Get brand details: available denominations, discounts, templateIds. Use brandId from browse_tags.",
            inputSchema={
                "type": "object",
                "properties": {
                    "brand_id": {"type": "string", "description": "Card brand ID (e.g. CB00000000000086)"},
                },
                "required": ["brand_id"],
            },
        ),
        types.Tool(
            name="snaplii_giftcard_list",
            description="List user's owned gift cards. IMPORTANT: Only show brand name, face value, status, and masked card number (first 4 + last 4 digits). NEVER show full card code, PIN, or barcode unless user explicitly asks.",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "ACTIVE or INACTIVE", "default": "ACTIVE"},
                },
                "required": [],
            },
        ),
        types.Tool(
            name="snaplii_giftcard_detail",
            description="Get full card details including redemption code and PIN. Only use when user explicitly asks to see sensitive card info.",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_no": {"type": "string", "description": "Card number from giftcard_list"},
                },
                "required": ["card_no"],
            },
        ),
        types.Tool(
            name="snaplii_purchase",
            description="Purchase a gift card. item_id = brandId-templateId (e.g. CB00000000000086-CT0000000000734). ALWAYS confirm with user first.",
            inputSchema={
                "type": "object",
                "properties": {
                    "item_id": {"type": "string", "description": "Item ID: {brandId}-{templateId}"},
                    "price": {"type": "string", "description": "Price in dollars"},
                    "payment_method": {"type": "string", "description": "SNAPLII_CASH, SNAPLII_CREDIT, or SNAPLII_DEBIT", "default": "SNAPLII_CASH"},
                },
                "required": ["item_id", "price"],
            },
        ),
        types.Tool(
            name="snaplii_apikey_list",
            description="List all API keys for the current user.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
        types.Tool(
            name="snaplii_apikey_create",
            description="Create a new API key. The full key is only returned once — display it clearly.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Key name"},
                    "scope": {"type": "string", "description": "PAY_READ or PAY_WRITE", "default": "PAY_READ"},
                    "limit": {"type": "number", "description": "Consumption limit in dollars"},
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="snaplii_apikey_delete",
            description="Delete an API key by its ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "key_id": {"type": "string", "description": "API key ID"},
                },
                "required": ["key_id"],
            },
        ),
        types.Tool(
            name="snaplii_cashback_calc",
            description="Calculate exact cashback savings for a brand and amount. Shows how much user saves and effective cost.",
            inputSchema={
                "type": "object",
                "properties": {
                    "brand_id": {"type": "string", "description": "Card brand ID"},
                    "amount": {"type": "number", "description": "Purchase amount in dollars"},
                },
                "required": ["brand_id", "amount"],
            },
        ),
        types.Tool(
            name="snaplii_dashboard",
            description="Show a summary dashboard of all owned gift cards: total count, total face value, breakdown by brand.",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    def _text(data) -> list[types.TextContent]:
        text = json.dumps(data, indent=2) if not isinstance(data, str) else data
        return [types.TextContent(type="text", text=text)]

    try:
        if name == "snaplii_config_show":
            store = ConfigStore()
            data = store.load()
            safe = {k: v for k, v in data.items() if k not in ("access_token", "token_expires_at")}
            if "api_key" in safe and safe["api_key"]:
                safe["api_key"] = safe["api_key"][:12] + "..."
            safe["has_valid_token"] = bool(store.get_cached_token())
            return _text(safe)

        elif name == "snaplii_init":
            store = ConfigStore()
            client = _get_client()
            store.set_many({"agent_id": arguments["agent_id"], "api_key": arguments["api_key"]})
            result = client.login(arguments["agent_id"], arguments["api_key"])
            return _text({"status": "authenticated", "user": result.get("usrNo"), "scope": result.get("scope")})

        elif name == "snaplii_browse_tags":
            client = _get_client()
            result = client.get_all_card_tags(
                channel=arguments.get("channel", "HOME_PAGE"),
                location_prov=arguments.get("prov", "ON"),
            )
            return _text(result)

        elif name == "snaplii_browse_brand":
            client = _get_client()
            result = client.get_card_brand_by_id(arguments["brand_id"])
            return _text(result)

        elif name == "snaplii_giftcard_list":
            client = _get_client()
            result = client.list_user_cards(status=arguments.get("status", "ACTIVE"))
            return _text(result)

        elif name == "snaplii_giftcard_detail":
            client = _get_client()
            result = client.get_card_detail(arguments["card_no"])
            # Wrap with security notice so agent handles display carefully
            return _text({
                "_sensitive": True,
                "_notice": "Contains redemption code and PIN. Show to user only upon explicit confirmation. Do NOT include in summaries or logs.",
                "data": result,
            })

        elif name == "snaplii_purchase":
            client = _get_client()
            result = client.create_order_and_pay(
                item_id=arguments["item_id"],
                price=arguments["price"],
                payment_method=arguments.get("payment_method", "SNAPLII_CASH"),
            )
            return _text(result)

        elif name == "snaplii_apikey_list":
            client = _get_client()
            result = client.list_api_keys()
            if isinstance(result, dict):
                for key in result.get("keys", []):
                    if "apiKey" in key:
                        key["apiKey"] = key["apiKey"][:12] + "..." if len(key.get("apiKey", "")) > 12 else "***"
            return _text(result)

        elif name == "snaplii_apikey_create":
            client = _get_client()
            result = client.create_api_key(
                name=arguments["name"],
                scope=arguments.get("scope", "PAY_READ"),
                consumption_limit=arguments.get("limit"),
            )
            # Never return full API key in MCP context — it would leak into conversation
            if isinstance(result, dict) and "apiKey" in result:
                result["apiKey"] = result["apiKey"][:12] + "..." if len(result.get("apiKey", "")) > 12 else "***"
                result["_notice"] = "Key created but masked for security. User must run 'snaplii apikey create --reveal' via CLI to see the full key."
            return _text(result)

        elif name == "snaplii_apikey_delete":
            client = _get_client()
            result = client.delete_api_key(arguments["key_id"])
            return _text(result)

        elif name == "snaplii_cashback_calc":
            client = _get_client()
            detail = client.get_card_brand_by_id(arguments["brand_id"])
            cards = detail.get("data", {}).get("cards", [])
            amount = float(arguments["amount"])
            best = None
            for c in cards:
                fv = c.get("faceValueRules", {})
                if fv.get("type") == "FIXED" and float(fv.get("priceStart", 0)) == amount:
                    best = c
                    break
                elif fv.get("type") == "VARIABLE":
                    if float(fv.get("priceStart", 0)) <= amount <= float(fv.get("priceEnd", 0)):
                        best = c
            if best:
                pct = float(best.get("discount", 0) or 0)
                savings = amount * pct / 100
                return _text({
                    "amount": f"${amount:.2f}",
                    "cashback": f"{pct}%",
                    "you_save": f"${savings:.2f}",
                    "effective_cost": f"${amount - savings:.2f}",
                    "item_id": f"{arguments['brand_id']}-{best.get('cardTemplateId', '')}",
                })
            else:
                return _text({"error": f"No matching denomination for ${amount}"})

        elif name == "snaplii_dashboard":
            client = _get_client()
            resp = client.list_user_cards(status="ACTIVE", page=1, page_size=100)
            cards = resp.get("data", [])
            total_value = 0
            by_brand = {}
            for card in cards:
                fv = float(card.get("faceValue", 0))
                total_value += fv
                bid = card.get("cardBrandId", "unknown")
                brand_name = card.get("cardTemplate", {}).get("desc", {}).get("name", bid)
                if bid in by_brand:
                    by_brand[bid]["count"] += 1
                    by_brand[bid]["total"] += fv
                else:
                    by_brand[bid] = {"name": brand_name, "count": 1, "total": fv}
            return _text({
                "total_cards": len(cards),
                "total_face_value": f"${total_value:.2f}",
                "brands": [
                    {"brand": v["name"], "cards": v["count"], "total_value": f"${v['total']:.2f}"}
                    for v in sorted(by_brand.values(), key=lambda x: x["total"], reverse=True)
                ],
            })

        else:
            return _text(f"Unknown tool: {name}")

    except ConfigError as e:
        return _text({"error": "config_error", "message": str(e)})
    except GatewayConnectionError as e:
        return _text({"error": "connection_error", "message": str(e)})
    except GatewayApiError as e:
        friendly = e.body.get("friendly_message") if hasattr(e, 'body') else None
        return _text({"error": friendly or str(e), "error_code": e.body.get("rspMsgCd", "") if hasattr(e, 'body') else ""})
    except Exception as e:
        return _text({"error": "unexpected_error", "message": str(e)})


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main_sync():
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
