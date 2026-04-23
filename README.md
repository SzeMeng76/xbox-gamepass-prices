# Xbox Game Pass Global Prices

🎮 Automated price tracking for Xbox Game Pass subscriptions across all supported regions, with CNY conversion and global rankings.

## Overview

This project scrapes Xbox Game Pass subscription prices from all supported regions using Playwright, converts them to CNY via live exchange rates, and publishes structured JSON data updated weekly via GitHub Actions.

## Features

- 🌍 Covers **88 regions** worldwide
- 🎯 Tracks **4 subscription plans**: PC Game Pass, Game Pass Core, Game Pass Standard, Game Pass Ultimate
- 💱 Automatic currency conversion to CNY using live exchange rates (openexchangerates.org)
- 📊 Pre-built **Top 10 cheapest rankings** for PC Game Pass and Ultimate plans
- 💰 Intro (first month) pricing captured where available
- 🤖 Automated weekly updates every Sunday via GitHub Actions
- 📈 Price change detection and CHANGELOG

## Subscription Plans

| Plan | Regions Covered |
|------|----------------|
| PC Game Pass | 63 regions |
| Game Pass Core | 14 regions |
| Game Pass Standard | 14 regions |
| Game Pass Ultimate | 14 regions |

## Top 10 Cheapest — PC Game Pass

> Auto-renew monthly price, converted to CNY. Updated 2026-04-22.

| Rank | Region | Country | Price (Local) | Price (CNY) |
|------|--------|---------|---------------|-------------|
| 🥇 | ar-AE | 阿联酋 | AED 9.99 | ¥18.57 |
| 🥈 | vi-VN | 越南 | VND 79,000 | ¥20.49 |
| 🥉 | en-PH | 菲律宾 | PHP 225 | ¥25.52 |
| 4 | th-TH | 泰国 | THB 129 | ¥27.31 |
| 5 | id-ID | 印度尼西亚 | IDR 82,999 | ¥32.90 |
| 6 | en-MY | 马来西亚 | MYR 20 | ¥34.55 |
| 7 | uk-UA | 乌克兰 | UAH 230 | ¥35.57 |
| 8 | ar-MA | 摩洛哥 | MAD 60 | ¥44.35 |
| 9 | ar-LY | 利比亚 | USD 6.99 | ¥47.73 |
| 10 | bg-BG | 保加利亚 | BGN 11.99 | ¥49.00 |

*Rankings are regenerated automatically on every update run.*

## Data Files

| File | Description |
|------|-------------|
| `xbox_gamepass_prices.json` | Raw scraped data from Xbox website |
| `xbox_gamepass_prices_processed.json` | Processed data with CNY conversion and Top 10 rankings |
| `xbox_price_changes_latest.json` | Latest detected price changes |
| `CHANGELOG.md` | Full price change history |
| `archive/` | Historical snapshots of raw data |

### Processed JSON Structure

```json
{
  "_updated_at": "2026-04-22",
  "_top10_cheapest_pc_game_pass": {
    "description": "...",
    "updated_at": "2026-04-22",
    "data": [ { "rank": 1, "region_code": "ar-AE", "currency": "AED", "auto_renew_price": 9.99, "auto_renew_price_cny": 18.57, ... } ]
  },
  "_top10_cheapest_ultimate": {
    "description": "...",
    "updated_at": "2026-04-22",
    "data": [ ... ]
  },
  "regions": [
    {
      "region_code": "ar-AE",
      "name_en": "UAE",
      "name_cn": "阿联酋",
      "currency": "AED",
      "plans": [
        {
          "plan": "PC Game Pass",
          "regular_price": 9.99,
          "regular_price_cny": 18.57,
          "intro_price": null
        },
        {
          "plan": "Game Pass Ultimate",
          "regular_price": 15.99,
          "regular_price_cny": 29.72,
          "intro_price": null
        }
      ]
    }
  ]
}
```

## How It Works

1. **Scraper** (`xbox_scraper.py`) — Uses Playwright (headless Chromium) to fetch live prices from `xbox.com` for each region. Handles 20+ language price formats including currency-before and currency-after number layouts.
2. **Converter** (`xbox_rate_converter.py`) — Fetches live USD exchange rates, converts all prices to CNY, and generates the Top 10 rankings for PC Game Pass and Ultimate plans.
3. **Change Detector** (`xbox_price_change_detector.py`) — Diffs the new data against the previous run and records any price changes to `CHANGELOG.md`.
4. **GitHub Actions** — Runs the full pipeline every Sunday at UTC 09:00 (Beijing time 17:00). Commits and pushes only when file changes are detected.

## Usage

### Run Locally

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# 1. Scrape prices from Xbox website
python xbox_scraper.py

# 2. Convert to CNY and generate rankings
#    Requires OPENEXCHANGERATES_API_KEY env var (free tier works)
API_KEY=your_key python xbox_rate_converter.py
```

### GitHub Actions Setup

Add the following secret to your repository:

| Secret | Description |
|--------|-------------|
| `OPENEXCHANGERATES_API_KEY` | Free API key from [openexchangerates.org](https://openexchangerates.org/) |

The workflow runs automatically every Sunday. You can also trigger it manually via **Actions → Weekly Xbox Game Pass Price Scraper → Run workflow**.

## Notes on Coverage

Some regions display placeholder prices (`XX,XX $`) on the Xbox website rather than real prices — these are scraped as empty `plans: []` and excluded from rankings. Known affected regions include `de-DE`, `de-CH`, and `ru-RU`.

## License

MIT License

## Disclaimer

This project is for informational purposes only. Prices are scraped from public Xbox websites and may not reflect current promotional offers or regional restrictions.
