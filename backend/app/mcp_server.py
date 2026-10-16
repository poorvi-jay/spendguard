"""
MCP tool surface for SpendGuard. Runs over stdio by default, which is what
Claude Desktop expects for a locally-configured server. For Render, switch
the transport in run_mcp.py to "streamable-http" so remote MCP clients can
connect over a URL instead.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer

from app import core

mcp = MCPServer("SpendGuard")


@mcp.tool()
def start_session(original_request: str) -> dict:
    """Record what the user actually asked for, before any shopping happens.
    Call this once at the start of a shopping task -- every later checkout()
    is checked against this, not against whatever the agent says later."""
    return core.start_session(original_request)


@mcp.tool()
def search_products(query: str = "", max_price: Optional[float] = None) -> list[dict]:
    """Search the product catalog by keyword and optional max price."""
    return core.search_products(query, max_price)


@mcp.tool()
def get_product(product_id: str) -> dict:
    """Get full details for one product by id."""
    product = core.get_product(product_id)
    return product or {"error": f"Unknown product_id '{product_id}'."}


@mcp.tool()
def checkout(product_id: str) -> dict:
    """Start a purchase. Runs the budget/cap/category rules immediately. If
    they pass, creates a PayPal order and returns an approval_url the buyer
    must open and approve before calling confirm_purchase(order_id)."""
    return core.checkout(product_id)


@mcp.tool()
def confirm_purchase(order_id: str) -> dict:
    """Call after the buyer has approved the order in PayPal's UI. Runs the
    final intent-match check and either captures or voids the payment."""
    return core.confirm_purchase(order_id)


@mcp.tool()
def get_spending_summary() -> dict:
    """Budget used this month and progress toward the savings goal."""
    return core.get_spending_summary()


@mcp.tool()
def get_audit_log() -> list[dict]:
    """Every past guard decision and the reason behind it."""
    return core.get_audit_log()


if __name__ == "__main__":
    mcp.run()
