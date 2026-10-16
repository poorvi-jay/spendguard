from app.mcp_server import mcp

if __name__ == "__main__":
    # stdio is what Claude Desktop expects for a locally-configured server.
    # Switch to transport="streamable-http" when this runs on Render so
    # remote MCP clients can connect over a URL instead.
    mcp.run(transport="stdio")
