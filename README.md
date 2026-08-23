# Commodity Hub Discord Bot

Slash commands for trading Discord servers: `/price <commodity>` and
`/cot <commodity>`. Idea #4 from the Commodity Hub marketing plan — put
the product where the Serious Retail audience already spends time daily,
as a bot rather than a member (sidesteps the self-promotion etiquette
problem entirely).

`/curve` is intentionally not built — forward-curve data is behind
commodity-hub.eu's Pro-tier gate. Adding it needs either a service-role
bypass (not appropriate for a public bot) or a decision to expose a
trimmed public curve endpoint. Once that's resolved, it's a small
addition following the same pattern as `/price`/`/cot` — see the `TODO`
in `bot.py`.

## What's real vs. what needs setup

- `pricing.py` (live commodity prices) and the COT positioning logic
  (via the [`cot-report`](https://github.com/Toscirium/cot-report)
  library) are **tested against live data** — see the commands below.
- The bot itself has **not been run against Discord** — that needs a bot
  token only you can create (Discord requires a human to register the
  application). Everything except that one step is done.

## Setup

1. **Publish `cot-report` first** (or point `requirements.txt` at a local
   path instead of the GitHub URL, if you're not publishing it yet):
   `pip install -e /path/to/cot-report`

2. **Create the Discord application:**
   - [discord.com/developers/applications](https://discord.com/developers/applications) → New Application
   - Bot tab → Reset Token → copy it into `.env` as `DISCORD_BOT_TOKEN`
   - Bot tab → disable "Public Bot" if you only want it in your own servers, or leave it on to let other trading servers add it themselves (recommended — that's the whole distribution play)
   - OAuth2 → URL Generator → scopes: `bot`, `applications.commands` → permissions: `Send Messages`, `Embed Links` → open the generated URL to invite it to a server

3. **Run it:**
   ```bash
   python3 -m venv .venv
   ./.venv/bin/pip install -r requirements.txt
   cp .env.example .env   # paste in DISCORD_BOT_TOKEN
   ./.venv/bin/python bot.py
   ```

4. **Deploy** wherever you run long-lived processes today (the bot needs
   to stay connected — a small always-on box or container, not a
   scheduled job). A single instance can serve every server it's invited
   to.

## Commands

```
/price commodity:Gold
  → Gold
    $4,692.40  🔴▼ -0.18%

/cot commodity:Copper
  → Copper — COT Positioning
    Managed money net long 78,648 contracts (27.93% of open interest)
    Percentile vs. trailing 156 weeks: 99.4%
    ⚠️ Crowded long — top decile of trailing 3-year range.
```

(both real, live output from testing — not mockups)
