from app.mcp_server import mcp

if __name__ == "__main__":
    # stdio is what Claude Desktop expects for a locally-configured server.
    # The hosted server doesn't use this file: app/api.py serves the same
    # tools over HTTP at /mcp.
    mcp.run(transport="stdio")
