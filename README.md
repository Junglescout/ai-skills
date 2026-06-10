# Jungle Scout Cobalt AI Skills

This repository distributes Jungle Scout Cobalt skills and MCP configuration for AI assistants.

- **Claude users** can add this repository as a custom Claude plugin marketplace and install the `jungle-scout-cobalt` plugin.
- **ChatGPT users** can download the latest skills zip and upload it at <https://chatgpt.com/skills>.

The packaged skills help users work with Jungle Scout's Amazon market data through the Jungle Scout MCP server.

## What This Repository Includes

- A Claude marketplace manifest at `.claude-plugin/marketplace.json`.
- One Claude plugin: `jungle-scout-cobalt`.
- Jungle Scout Cobalt skills for Amazon data workflows.
- An MCP server configuration for Claude pointing to `https://ai.junglescout.com/mcp`.
- A downloadable skills zip for ChatGPT users.

## Jungle Scout MCP

The Jungle Scout MCP connects Claude to Jungle Scout's Amazon market data. It lets users ask plain-language questions about products, brands, sellers, categories, keywords, price tiers, share of voice, and their own Jungle Scout-managed brands.

Typical questions include:

- "How is this brand trending against its category?"
- "Show the top products in this category and their year-over-year sales change."
- "What keywords does this ASIN rank for?"
- "How does revenue split across price tiers in this category?"
- "How has this brand's Share of Voice changed over time?"

## Claude Setup

1. Add this repository as a custom marketplace in the customer's Claude organization.
2. Install the `jungle-scout-cobalt` plugin from that marketplace.
3. Connect the Jungle Scout MCP when prompted.
4. Authenticate with Jungle Scout Cobalt credentials.
5. Start a new Claude session and confirm the Jungle Scout connector is enabled.

## ChatGPT Setup

ChatGPT does not have plugins. The steps in this setup are only for adding skills. Follow [this guide](https://junglescout.notion.site/Jungle-Scout-MCP-Getting-Started-guide-3742362b8e5b802288bec7a7f7941566) to add Jungle Scout MCP as an App to your ChatGPT account, then follow the steps below to add the skills.

1. Download the latest skills zip: <https://github.com/Junglescout/ai-skills/releases/download/latest/jungle-scout-cobalt-skills.zip>.
2. Go to <https://chatgpt.com/skills>.
3. Press **+ New Skill**.
4. Select **Upload from your computer**.
5. Select the downloaded zip file.

## Notes

- The MCP server uses live Jungle Scout data, but assistant-generated conclusions should still be reviewed against the underlying tool results.
- If a connector call fails, read the error message and correct the input or authentication issue before retrying.
