# Xbox Game Pass PC Prices

🎮 Automated price tracking for Xbox Game Pass PC across all supported regions.

## Overview

This project automatically scrapes Xbox Game Pass PC subscription prices from all supported regions and converts them to CNY (Chinese Yuan) for easy comparison.

## Features

- 🌍 Tracks prices across 40+ regions
- 💱 Automatic currency conversion to CNY
- 📊 Price ranking by lowest to highest
- 🤖 Automated daily updates via GitHub Actions
- 📈 Price change detection and history

## Latest Prices

See [xbox_gamepass_prices_processed.json](xbox_gamepass_prices_processed.json) for the latest prices with CNY conversion.

## Price Ranking

The cheapest regions for Xbox Game Pass PC (auto-renew price):

| Rank | Region | Price (Local) | Price (CNY) |
|------|--------|---------------|-------------|
| TBD | TBD | TBD | TBD |

*Updated automatically by GitHub Actions*

## How It Works

1. **Scraper** (`xbox_scraper.py`) - Uses Playwright to fetch prices from Xbox website
2. **Converter** (`xbox_rate_converter.py`) - Converts all prices to CNY using live exchange rates
3. **GitHub Actions** - Runs automatically every day at 9:00 AM UTC

## Data Files

- `xbox_gamepass_prices.json` - Raw scraped data
- `xbox_gamepass_prices_processed.json` - Processed data with CNY conversion
- `archive/` - Historical price data

## Usage

### Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run scraper
python xbox_scraper.py

# Convert to CNY
python xbox_rate_converter.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License

## Disclaimer

This project is for educational and informational purposes only. Prices are scraped from public Xbox websites and may not reflect current promotional offers or regional restrictions.
