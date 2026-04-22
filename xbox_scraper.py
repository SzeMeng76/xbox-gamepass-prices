import asyncio
import re
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

REGIONS = [
    'ar-BH', 'ar-DZ', 'ar-EG', 'ar-KW', 'ar-LY', 'ar-MA', 'ar-OM', 'ar-QA',
    'ar-TN', 'bg-BG', 'de-LI', 'de-LU', 'en-CY', 'en-MY', 'en-PH', 'en-US',
    'es-BO', 'es-CR', 'es-EC', 'es-GT', 'es-HN', 'es-NI', 'es-PA', 'es-PE',
    'es-PY', 'es-SV', 'es-UY', 'et-EE', 'fr-LU', 'hr-HR', 'id-ID', 'is-IS',
    'ka-GE', 'lt-LT', 'lv-LV', 'mk-MK', 'mt-MT', 'ro-MD', 'ro-RO', 'sl-SL',
    'sq-AL', 'th-TH', 'uk-UA', 'vi-VN',
]

# Per-region metadata: currency, decimal separator, thousand separator
REGION_INFO = {
    'ar-BH': {'currency': 'BHD', 'decimal': '.', 'thousand': ','},
    'ar-DZ': {'currency': 'DZD', 'decimal': '.', 'thousand': ','},
    'ar-EG': {'currency': 'EGP', 'decimal': '.', 'thousand': ','},
    'ar-KW': {'currency': 'KWD', 'decimal': '.', 'thousand': ','},
    'ar-LY': {'currency': 'LYD', 'decimal': '.', 'thousand': ','},
    'ar-MA': {'currency': 'MAD', 'decimal': '.', 'thousand': ','},
    'ar-OM': {'currency': 'OMR', 'decimal': '.', 'thousand': ','},
    'ar-QA': {'currency': 'QAR', 'decimal': '.', 'thousand': ','},
    'ar-TN': {'currency': 'TND', 'decimal': '.', 'thousand': ','},
    'bg-BG': {'currency': 'BGN', 'decimal': '.', 'thousand': ','},
    'de-LI': {'currency': 'CHF', 'decimal': '.', 'thousand': ','},
    'de-LU': {'currency': 'EUR', 'decimal': ',', 'thousand': '.'},
    'en-CY': {'currency': 'EUR', 'decimal': '.', 'thousand': ','},
    'en-MY': {'currency': 'MYR', 'decimal': '.', 'thousand': ','},
    'en-PH': {'currency': 'PHP', 'decimal': '.', 'thousand': ','},
    'en-US': {'currency': 'USD', 'decimal': '.', 'thousand': ','},
    'es-BO': {'currency': 'BOB', 'decimal': '.', 'thousand': ','},
    'es-CR': {'currency': 'CRC', 'decimal': '.', 'thousand': ','},
    'es-EC': {'currency': 'USD', 'decimal': '.', 'thousand': ','},
    'es-GT': {'currency': 'GTQ', 'decimal': '.', 'thousand': ','},
    'es-HN': {'currency': 'HNL', 'decimal': '.', 'thousand': ','},
    'es-NI': {'currency': 'NIO', 'decimal': '.', 'thousand': ','},
    'es-PA': {'currency': 'USD', 'decimal': '.', 'thousand': ','},
    'es-PE': {'currency': 'PEN', 'decimal': '.', 'thousand': ','},
    'es-PY': {'currency': 'PYG', 'decimal': ',', 'thousand': '.'},
    'es-SV': {'currency': 'USD', 'decimal': '.', 'thousand': ','},
    'es-UY': {'currency': 'UYU', 'decimal': ',', 'thousand': '.'},
    'et-EE': {'currency': 'EUR', 'decimal': ',', 'thousand': '.'},
    'fr-LU': {'currency': 'EUR', 'decimal': ',', 'thousand': '.'},
    'hr-HR': {'currency': 'EUR', 'decimal': ',', 'thousand': '.'},
    'id-ID': {'currency': 'IDR', 'decimal': ',', 'thousand': '.'},
    'is-IS': {'currency': 'ISK', 'decimal': ',', 'thousand': '.'},
    'ka-GE': {'currency': 'GEL', 'decimal': '.', 'thousand': ','},
    'lt-LT': {'currency': 'EUR', 'decimal': ',', 'thousand': '.'},
    'lv-LV': {'currency': 'EUR', 'decimal': ',', 'thousand': '.'},
    'mk-MK': {'currency': 'MKD', 'decimal': '.', 'thousand': ','},
    'mt-MT': {'currency': 'EUR', 'decimal': '.', 'thousand': ','},
    'ro-MD': {'currency': 'MDL', 'decimal': '.', 'thousand': ','},
    'ro-RO': {'currency': 'RON', 'decimal': ',', 'thousand': '.'},
    'sl-SL': {'currency': 'EUR', 'decimal': ',', 'thousand': '.'},
    'sq-AL': {'currency': 'ALL', 'decimal': ',', 'thousand': '.'},
    'th-TH': {'currency': 'THB', 'decimal': '.', 'thousand': ','},
    'uk-UA': {'currency': 'UAH', 'decimal': ',', 'thousand': '.'},
    'vi-VN': {'currency': 'VND', 'decimal': ',', 'thousand': '.'},
}


def clean_price(raw: str, decimal_sep: str, thousand_sep: str) -> Optional[float]:
    """Parse a price string using region-specific separators."""
    if not raw:
        return None
    s = raw.strip()
    # Remove everything except digits and separators
    s = re.sub(r'[^\d' + re.escape(decimal_sep) + re.escape(thousand_sep) + r']', '', s)
    if not s:
        return None
    # Remove thousand separators
    s = s.replace(thousand_sep, '')
    # Normalize decimal separator to '.'
    if decimal_sep != '.':
        s = s.replace(decimal_sep, '.')
    try:
        return float(s)
    except Exception:
        return None


def extract_prices(html: str, region_code: str) -> Dict[str, Any]:
    info = REGION_INFO.get(region_code, {'decimal': '.', 'thousand': ','})
    dec = info['decimal']
    tho = info['thousand']

    result: Dict[str, Any] = {
        'intro_price_raw': None,
        'regular_price_raw': None,
        'auto_renew_price_raw': None,
        'intro_price': None,
        'regular_price': None,
        'auto_renew_price': None,
    }

    # Number pattern using region separators
    # matches e.g. "4.500" (BHD with . thousand) or "79.000,00" (VND with . thousand , decimal)
    num = r'[\d]+(?:[' + re.escape(tho) + r'][\d]+)*(?:[' + re.escape(dec) + r'][\d]+)?'

    # ── intro + regular from __PRELOADED_STATE__ (unicode-escaped JSON in <script>)
    # Examples found in debug:
    #   en-PH: "Get your first 14 days for ₱59, then ₱320\/month"
    #   ar-BH: "Get your first 14 days for BD 0.40, then BD 4.50\/month"
    #   vi-VN: "với 24.900 ₫, sau đó là 129.000 ₫\/tháng"
    #   uk-UA: "за 39,99 ₴, далі за ціною 290,00 ₴\/міс"
    #   id-ID: "Dapatkan 14 hari pertama ... seharga Rp14.000, lalu Rp89.999\/bulan"
    #   ro-RO: "Obțineți primele ... pentru X lei, apoi Y lei\/lună"
    intro_patterns = [
        # English: "for PRICE, then PRICE/month"
        rf'for\s+[^\d]*({num})[^,\"]*,\s*then\s+[^\d]*({num})\s*(?:\\u002F|/)(?:month|mo)[^t]',
        # Vietnamese
        rf'v[oớ]i\s+({num})\s*[^\d,\"]*,\s*sau đó là\s+({num})\s*[^\d\"]*(?:\\u002F|/)tháng',
        # Ukrainian
        rf'за\s+({num})\s*[^,\"]*,\s*далі за ціною\s+({num})\s*[^\"]*(?:\\u002F|/)(?:міс|мес)',
        # Spanish
        rf'por\s+[^\d]*({num})[^,\"]*,\s*(?:luego|después)\s+[^\d]*({num})\s*[^\"]*(?:\\u002F|/)mes',
        # Indonesian: "seharga RpX, lalu RpY/bulan"
        rf'seharga\s+[^\d]*({num})[^,\"]*,\s*lalu\s+[^\d]*({num})\s*[^\"]*(?:\\u002F|/)bulan',
        # Romanian: "pentru X, apoi Y/lună"
        rf'pentru\s+[^\d]*({num})[^,\"]*,\s*apoi\s+[^\d]*({num})\s*[^\"]*(?:\\u002F|/)lun',
    ]

    for pattern in intro_patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            raw1, raw2 = m.group(1), m.group(2)
            p1 = clean_price(raw1, dec, tho)
            p2 = clean_price(raw2, dec, tho)
            if p1 and p2 and p1 != p2:
                result['intro_price_raw'] = raw1
                result['regular_price_raw'] = raw2
                result['intro_price'] = p1
                result['regular_price'] = p2
                break

    # ── auto_renew from rendered HTML
    # Examples:
    #   en-PH: "subscription continues automatically at ₱225.00/month"
    #   vi-VN: "mức phí 79.000,00 ₫/tháng"
    #   uk-UA: "вартістю 230,00 ₴ на місяць"
    #   ar-BH: "automatically at 3,500 BHD‏/month"   ← BHD uses , as thousand sep
    auto_patterns = [
        # English: "automatically at PRICE/month"
        rf'automatically at\s+[^\d]*({num})\s*[^\/\"<]*(?:/|\\u002F)(?:month|mo)[^t]',
        # Vietnamese
        rf'mức phí\s+({num})\s*[^\d\"<]*(?:/|\\u002F)tháng',
        # Ukrainian
        rf'вартістю\s+({num})\s*[^\d\"<]*на місяць',
        # Indonesian
        rf'diperpanjang otomatis seharga\s+[^\d]*({num})\s*[^\/\"<]*(?:/|\\u002F)bulan',
        # Romanian
        rf'reînnoire automat[ă]\s+[^\d]*({num})\s*[^\/\"<]*(?:/|\\u002F)lun',
        # Thai
        rf'ต่ออายุอัตโนมัติ[^฿\d]*({num})\s*[^\/\"<]*(?:/|ต่อ)เดือน',
    ]

    for pattern in auto_patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            raw = m.group(1)
            price = clean_price(raw, dec, tho)
            if price:
                result['auto_renew_price_raw'] = raw
                result['auto_renew_price'] = price
                break

    return result


async def fetch_xbox_price(browser, region_code: str) -> Dict[str, Any]:
    url = f"https://www.xbox.com/{region_code}/xbox-game-pass/pc-game-pass"
    currency = REGION_INFO.get(region_code, {}).get('currency', 'USD')
    page = await browser.new_page()

    try:
        print(f"[{region_code}] Fetching...")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        html = await page.content()

        prices = extract_prices(html, region_code)

        result: Dict[str, Any] = {
            'region_code': region_code,
            'currency': currency,
            'url': url,
            'scraped_at': datetime.now(timezone.utc).isoformat(),
            **prices,
        }

        parts = []
        if prices['intro_price']:
            parts.append(f"intro={prices['intro_price']}")
        if prices['regular_price']:
            parts.append(f"regular={prices['regular_price']}")
        if prices['auto_renew_price']:
            parts.append(f"auto={prices['auto_renew_price']}")
        print(f"[{region_code}] {'OK  ' + ', '.join(parts) if parts else '--  no prices found'}")

        return result

    except Exception as e:
        print(f"[{region_code}] ERR {e}")
        return {
            'region_code': region_code,
            'currency': currency,
            'url': url,
            'error': str(e),
            'scraped_at': datetime.now(timezone.utc).isoformat(),
        }
    finally:
        await page.close()


async def main():
    print(f"Starting to scrape {len(REGIONS)} regions...")
    print("=" * 60)

    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        for region in REGIONS:
            result = await fetch_xbox_price(browser, region)
            results.append(result)
            await asyncio.sleep(1)
        await browser.close()

    with open('xbox_gamepass_prices.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    ok = sum(1 for r in results if r.get('intro_price') or r.get('regular_price') or r.get('auto_renew_price'))
    print("=" * 60)
    print(f"Done. {ok}/{len(results)} regions with prices.")


if __name__ == '__main__':
    asyncio.run(main())
