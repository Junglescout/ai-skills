# Jungle Scout Cobalt Claude Plugin Marketplace

This repository defines a custom Claude plugin marketplace for Jungle Scout Cobalt. Users can add this marketplace to their Claude organization, install the Jungle Scout Cobalt plugin, and receive the latest packaged skills and MCP server configuration from one place.

## What It Includes

- A Claude marketplace manifest at `.claude-plugin/marketplace.json`.
- One plugin: `jungle-scout-cobalt`.
- Jungle Scout Cobalt skills for Amazon data workflows.
- An MCP server configuration pointing Claude to `https://ai.junglescout.com/mcp`.

## Jungle Scout MCP

The Jungle Scout MCP connects Claude to Jungle Scout's Amazon market data. It lets users ask plain-language questions about products, brands, sellers, categories, keywords, price tiers, share of voice, and their own Jungle Scout-managed brands.

Typical questions include:

- "How is this brand trending against its category?"
- "Show the top products in this category and their year-over-year sales change."
- "What keywords does this ASIN rank for?"
- "How does revenue split across price tiers in this category?"
- "How has this brand's Share of Voice changed over time?"

## Setup

1. Add this repository as a custom marketplace in the customer's Claude organization.
2. Install the `jungle-scout-cobalt` plugin from that marketplace.
3. Connect the Jungle Scout MCP when prompted.
4. Authenticate with Jungle Scout Cobalt credentials.
5. Start a new Claude session and confirm the Jungle Scout connector is enabled.

## Notes

- The MCP server uses live Jungle Scout data, but assistant-generated conclusions should still be reviewed against the underlying tool results.
- If a connector call fails, read the error message and correct the input or authentication issue before retrying.
