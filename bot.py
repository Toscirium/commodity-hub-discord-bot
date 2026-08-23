#!/usr/bin/env python3
"""Commodity Hub Discord bot — /price and /cot slash commands.

/curve is intentionally not implemented: forward-curve data lives behind
commodity-hub.eu's Pro-tier gate (JWT-verified, checks user's paid tier
server-side). Adding it here would either require a service-role bypass
of that gate (not appropriate for a public bot) or a deliberate product
decision to expose a trimmed public version of that endpoint. See the
Commodity Hub Marketing Plan for that decision — this bot picks it up
automatically once that's resolved (see the TODO near COT_SLUGS below).
"""
from __future__ import annotations

import logging
import os

import discord
from discord import app_commands
from dotenv import load_dotenv

from cot_report import latest_with_context
from pricing import SYMBOLS, fetch_price

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("commodity-hub-bot")

DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")

# Bot's short keys (matching pricing.SYMBOLS, what users type) -> cot_report's slugs.
COT_SLUGS = {
    "wti": "wti-crude-oil",
    "brent": "brent-crude-oil",
    "natgas": "natural-gas",
    "gold": "gold",
    "silver": "silver",
    "copper": "copper",
    "corn": "corn",
    "wheat": "wheat",
}
# TODO once a public curve endpoint exists: add a `curve` command here
# following the same pattern as `price`/`cot` below.

COMMODITY_CHOICES = [app_commands.Choice(name=meta["label"], value=key) for key, meta in SYMBOLS.items()]


class CommodityHubBot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
        logger.info("Slash commands synced.")


client = CommodityHubBot()


@client.tree.command(name="price", description="Live commodity price")
@app_commands.describe(commodity="Which commodity")
@app_commands.choices(commodity=COMMODITY_CHOICES)
async def price(interaction: discord.Interaction, commodity: app_commands.Choice[str]):
    await interaction.response.defer()
    try:
        data = fetch_price(commodity.value)
    except Exception as e:  # noqa: BLE001
        await interaction.followup.send(f"Couldn't fetch a price right now ({e}). Try commodity-hub.eu directly.")
        return

    pct = data["change_pct"] or 0.0
    arrow = "🟢▲" if pct > 0 else "🔴▼" if pct < 0 else "⚪—"
    embed = discord.Embed(
        title=f"{data['label']}",
        description=f"**${data['price']:,.2f}**  {arrow} {pct:+.2f}%",
        url=f"https://commodity-hub.eu/commodities/{COT_SLUGS.get(commodity.value, '')}",
        color=0x2ECC71 if pct > 0 else 0xE74C3C if pct < 0 else 0x95A5A6,
    )
    embed.set_footer(text="Commodity Hub · live price")
    await interaction.followup.send(embed=embed)


@client.tree.command(name="cot", description="Current CFTC COT positioning (managed money)")
@app_commands.describe(commodity="Which commodity")
@app_commands.choices(commodity=COMMODITY_CHOICES)
async def cot(interaction: discord.Interaction, commodity: app_commands.Choice[str]):
    await interaction.response.defer()
    slug = COT_SLUGS.get(commodity.value)
    if not slug:
        await interaction.followup.send(f"No COT data mapping for {commodity.value}.")
        return

    try:
        ctx = latest_with_context(slug, weeks=156)
    except Exception as e:  # noqa: BLE001
        await interaction.followup.send(f"Couldn't fetch COT data right now ({e}).")
        return
    if ctx.get("error"):
        await interaction.followup.send(f"No COT data available for {commodity.name} yet.")
        return

    net = ctx["managed_money_net"]
    direction = "long" if net >= 0 else "short"
    extreme_note = ""
    if ctx.get("extreme") == "crowded_long":
        extreme_note = "\n⚠️ **Crowded long** — top decile of trailing 3-year range."
    elif ctx.get("extreme") == "crowded_short":
        extreme_note = "\n⚠️ **Crowded short** — bottom decile of trailing 3-year range."

    embed = discord.Embed(
        title=f"{ctx['label']} — COT Positioning",
        description=(
            f"Managed money net **{direction} {abs(net):,}** contracts "
            f"({ctx['managed_money_net_pct_oi']}% of open interest)\n"
            f"Percentile vs. trailing {ctx['trailing_weeks']} weeks: **{ctx['percentile_vs_trailing']}%**"
            f"{extreme_note}"
        ),
        url=f"https://commodity-hub.eu/now/{slug}",
        color=0xD9A44A,
    )
    embed.set_footer(text=f"Commodity Hub · CFTC report {ctx['report_date']}")
    await interaction.followup.send(embed=embed)


def main() -> None:
    if not DISCORD_TOKEN:
        raise SystemExit("DISCORD_BOT_TOKEN is not set — see README.md for how to create one.")
    client.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
