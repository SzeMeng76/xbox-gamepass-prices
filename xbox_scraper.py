import asyncio
import re
import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from playwright.async_api import async_playwright

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

REGIONS = [
    # Middle East / North Africa
    'ar-AE', 'ar-BH', 'ar-DZ', 'ar-EG', 'ar-KW', 'ar-LY', 'ar-MA', 'ar-OM',
    'ar-QA', 'ar-SA', 'ar-TN', 'he-IL',
    # Europe
    'bg-BG', 'cs-CZ', 'da-DK', 'de-AT', 'de-CH', 'de-DE', 'de-LI', 'de-LU',
    'el-GR', 'en-CY', 'en-GB', 'en-IE', 'es-ES', 'et-EE', 'fi-FI',
    'fr-BE', 'fr-CH', 'fr-FR', 'fr-LU', 'hr-HR', 'hu-HU', 'is-IS', 'it-IT',
    'lt-LT', 'lv-LV', 'mk-MK', 'mt-MT', 'nb-NO', 'nl-BE', 'nl-NL', 'pl-PL',
    'pt-PT', 'ro-MD', 'ro-RO', 'ru-RU', 'sk-SK', 'sl-SL', 'sq-AL', 'sv-SE',
    'tr-TR', 'uk-UA',
    # Asia Pacific
    'en-AU', 'en-HK', 'en-IN', 'en-MY', 'en-NZ', 'en-PH', 'en-SG', 'id-ID',
    'ja-JP', 'ka-GE', 'ko-KR', 'th-TH', 'vi-VN', 'zh-HK', 'zh-TW',
    # Africa
    'en-ZA',
    # Americas
    'en-CA', 'en-US', 'es-AR', 'es-BO', 'es-CL', 'es-CO', 'es-CR', 'es-EC',
    'es-GT', 'es-HN', 'es-MX', 'es-NI', 'es-PA', 'es-PE', 'es-PY', 'es-SV',
    'es-UY', 'fr-CA', 'pt-BR',
]

REGION_INFO = {
    # Middle East / North Africa
    'ar-AE': {'currency': 'AED'},
    'ar-BH': {'currency': 'BHD'},
    'ar-DZ': {'currency': 'DZD'},
    'ar-EG': {'currency': 'EGP'},
    'ar-KW': {'currency': 'KWD'},
    'ar-LY': {'currency': 'USD'},
    'ar-MA': {'currency': 'MAD'},
    'ar-OM': {'currency': 'OMR'},
    'ar-QA': {'currency': 'QAR'},
    'ar-SA': {'currency': 'SAR'},
    'ar-TN': {'currency': 'TND'},
    'he-IL': {'currency': 'ILS'},
    # Europe
    'bg-BG': {'currency': 'BGN'},
    'cs-CZ': {'currency': 'CZK'},
    'da-DK': {'currency': 'DKK'},
    'de-AT': {'currency': 'EUR'},
    'de-CH': {'currency': 'CHF'},
    'de-DE': {'currency': 'EUR'},
    'de-LI': {'currency': 'CHF'},
    'de-LU': {'currency': 'EUR'},
    'el-GR': {'currency': 'EUR'},
    'en-CY': {'currency': 'EUR'},
    'en-GB': {'currency': 'GBP'},
    'en-IE': {'currency': 'EUR'},
    'es-ES': {'currency': 'EUR'},
    'et-EE': {'currency': 'EUR'},
    'fi-FI': {'currency': 'EUR'},
    'fr-BE': {'currency': 'EUR'},
    'fr-CH': {'currency': 'CHF'},
    'fr-FR': {'currency': 'EUR'},
    'fr-LU': {'currency': 'EUR'},
    'hr-HR': {'currency': 'EUR'},
    'hu-HU': {'currency': 'HUF'},
    'is-IS': {'currency': 'ISK'},
    'it-IT': {'currency': 'EUR'},
    'lt-LT': {'currency': 'EUR'},
    'lv-LV': {'currency': 'EUR'},
    'mk-MK': {'currency': 'USD'},
    'mt-MT': {'currency': 'EUR'},
    'nb-NO': {'currency': 'NOK'},
    'nl-BE': {'currency': 'EUR'},
    'nl-NL': {'currency': 'EUR'},
    'pl-PL': {'currency': 'PLN'},
    'pt-PT': {'currency': 'EUR'},
    'ro-MD': {'currency': 'USD'},
    'ro-RO': {'currency': 'RON'},
    'ru-RU': {'currency': 'RUB'},
    'sk-SK': {'currency': 'EUR'},
    'sl-SL': {'currency': 'EUR'},
    'sq-AL': {'currency': 'USD'},
    'sv-SE': {'currency': 'SEK'},
    'tr-TR': {'currency': 'TRY'},
    'uk-UA': {'currency': 'UAH'},
    # Asia Pacific
    'en-AU': {'currency': 'AUD'},
    'en-HK': {'currency': 'HKD'},
    'en-IN': {'currency': 'INR'},
    'en-MY': {'currency': 'MYR'},
    'en-NZ': {'currency': 'NZD'},
    'en-PH': {'currency': 'PHP'},
    'en-SG': {'currency': 'SGD'},
    'id-ID': {'currency': 'IDR'},
    'ja-JP': {'currency': 'JPY'},
    'ka-GE': {'currency': 'USD'},
    'ko-KR': {'currency': 'KRW'},
    'th-TH': {'currency': 'THB'},
    'vi-VN': {'currency': 'VND'},
    'zh-HK': {'currency': 'HKD'},
    'zh-TW': {'currency': 'TWD'},
    # Africa
    'en-ZA': {'currency': 'ZAR'},
    # Americas
    'en-CA': {'currency': 'CAD'},
    'en-US': {'currency': 'USD'},
    'es-AR': {'currency': 'ARS'},
    'es-BO': {'currency': 'USD'},
    'es-CL': {'currency': 'CLP'},
    'es-CO': {'currency': 'COP'},
    'es-CR': {'currency': 'CRC'},
    'es-EC': {'currency': 'USD'},
    'es-GT': {'currency': 'GTQ'},
    'es-HN': {'currency': 'USD'},
    'es-MX': {'currency': 'MXN'},
    'es-NI': {'currency': 'USD'},
    'es-PA': {'currency': 'USD'},
    'es-PE': {'currency': 'PEN'},
    'es-PY': {'currency': 'USD'},
    'es-SV': {'currency': 'USD'},
    'es-UY': {'currency': 'USD'},
    'fr-CA': {'currency': 'CAD'},
    'pt-BR': {'currency': 'BRL'},
}

# Plan IDs found in HTML → display name
PLAN_IDS = {
    'pcgamepass':       'PC Game Pass',
    'coregamepass':     'Game Pass Core',
    'standardgamepass': 'Game Pass Standard',
    'ultimategamepass': 'Game Pass Ultimate',
}

# Currencies with 3 decimal places — comma/dot before 3 digits is decimal
_THREE_DECIMAL_CURRENCIES = {'BHD', 'KWD', 'OMR', 'TND', 'LYD'}


def clean_price(raw: str, currency: str = '') -> Optional[float]:
    if not raw:
        return None
    s = re.sub(r'[^\d.,]', '', raw.strip())
    if not s:
        return None

    has_dot = '.' in s
    has_comma = ',' in s
    three_dec = currency.upper() in _THREE_DECIMAL_CURRENCIES

    if has_dot and has_comma:
        if s.rindex('.') > s.rindex(','):
            s = s.replace(',', '')
        else:
            s = s.replace('.', '').replace(',', '.')
    elif has_comma:
        after_comma = s.rsplit(',', 1)[-1]
        if len(after_comma) == 2:
            s = s.replace(',', '.')
        elif len(after_comma) == 3 and three_dec:
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')
    elif has_dot:
        after_dot = s.rsplit('.', 1)[-1]
        if len(after_dot) == 3 and not three_dec:
            s = s.replace('.', '')

    try:
        return float(s)
    except Exception:
        return None


def _empty_plan(name: str) -> Dict[str, Any]:
    return {
        'plan': name,
        'intro_price_raw': None,
        'regular_price_raw': None,
        'auto_renew_price_raw': None,
        'intro_price': None,
        'regular_price': None,
        'auto_renew_price': None,
    }


def extract_plan_prices_from_blocks(html: str, currency: str) -> List[Dict[str, Any]]:
    """
    Extract prices from structured plan blocks (id='pcgamepass', etc.).
    Each block looks like:
      <... id="pcgamepass"><...>$13.99/month</...>
      or: <... id="coregamepass"><span>Get your first month for $1, <br> then $9.99/month
    Returns list of plan dicts, or empty list if no plan blocks found.
    """
    num = r'[\d]+(?:[.,][\d]+)*'
    plans = []

    for plan_id, plan_name in PLAN_IDS.items():
        # Find the block starting at id="<plan_id>"
        m = re.search(rf'id="{plan_id}"(.*?)(?:id="(?:{"|}".join(PLAN_IDS.keys())})|</section|</div>\s*</div>\s*</div)', html, re.DOTALL | re.IGNORECASE)
        if not m:
            continue

        block = m.group(1)
        plan = _empty_plan(plan_name)

        # Try intro + regular: "for $1, then $9.99/month"
        m2 = re.search(
            rf'for\s+(?![\d]+\s+days)[^\d]*({num})[^,<]*,\s*(?:<[^>]+>)*\s*then\s+[^\d]*({num})[^<]*(?:/|\\u002F)(?:month|mo)\b',
            block, re.IGNORECASE
        )
        if m2:
            r1, r2 = m2.group(1), m2.group(2)
            p1, p2 = clean_price(r1, currency), clean_price(r2, currency)
            if p1 and p2 and p1 != p2:
                plan['intro_price_raw'] = r1
                plan['regular_price_raw'] = r2
                plan['intro_price'] = p1
                plan['regular_price'] = p2

        # Try standalone price: "$22.99/month" or "LOWER PRICE<br>$22.99/month"
        if not plan['regular_price']:
            m3 = re.search(rf'[^\d]*({num})[^<\"]*(?:/|\\u002F)(?:month|mo)\b', block, re.IGNORECASE)
            if m3:
                raw = m3.group(1)
                price = clean_price(raw, currency)
                if price:
                    plan['regular_price_raw'] = raw
                    plan['regular_price'] = price

        # Auto-renew: "automatically at $X.XX/month"
        m4 = re.search(
            rf'automatically at\s+[^\d]*({num})\s*[^\"<]*(?:/|\\u002F)(?:month|mo)\b',
            block, re.IGNORECASE
        )
        if m4:
            raw = m4.group(1)
            price = clean_price(raw, currency)
            if price:
                plan['auto_renew_price_raw'] = raw
                plan['auto_renew_price'] = price

        if plan['intro_price'] or plan['regular_price'] or plan['auto_renew_price']:
            plans.append(plan)

    return plans


def extract_prices_fallback(html: str, currency: str) -> Optional[Dict[str, Any]]:
    """
    Legacy regex-based extraction for regions with no plan blocks.
    Returns a single PC Game Pass plan dict, or None.
    """
    num = r'[\d]+(?:[.,][\d]+)*'
    plan = _empty_plan('PC Game Pass')

    intro_patterns = [
        # English: "for PRICE, then PRICE/month" (exclude "for N days")
        rf'for\s+(?![\d]+\s+days)[^\d]*({num})[^,\"]*,\s*then\s+[^\d]*({num})[^\"<]*(?:/|\\u002F)(?:month|mo)[^t]',
        # Vietnamese
        rf'v[oớ]i\s+({num})\s*[^\d,\"]*,\s*sau đó là\s+({num})\s*[^\d\"]*(?:/|\\u002F)tháng',
        # Ukrainian (uses \xa0 non-breaking spaces)
        rf'за[\s\xa0]+({num})[\s\xa0]*[^,\"]*,\s*далі за[\s\xa0]+ціною[\s\xa0]+({num})[\s\xa0]*[^\"]*(?:/|/міс)',
        # Spanish
        rf'por\s+[^\d]*({num})[^,\"]*,\s*(?:luego|después)\s+[^\d]*({num})\s*[^\"]*(?:al\s+mes|(?:/|\\u002F)mes)',
        # Indonesian
        rf'seharga\s+[^\d]*({num})[^,\"]*,\s*lalu\s+[^\d]*({num})\s*[^\"]*(?:/|\\u002F)bulan',
        # Romanian
        rf'pentru\s+[^\d]*({num})[^,\"]*,\s*apoi\s+[^\d]*({num})\s*[^\"]*(?:/|\\u002F)lun',
        # Thai
        rf'เพียง\s+[^\d]*({num})\s*[^\d,\"]*(?:จากนั้น|,)\s*[^\d]*({num})\s*[^\"]*(?:/|\\u002F)เดือน',
        # German
        rf'f[üu]r\s+[^\d]*({num})[^,\"]*,\s*danach\s+[^\d]*({num})\s*[^\"]*(?:/|\\u002F)Monat',
        # French
        rf'pour\s+(?:seulement\s+)?[^\d]*({num})\s*[^,\"]*,\s*puis\s+[^\d]*({num})\s*[^\"]*(?:par\s+mois|(?:/|\\u002F)mois)',
    ]

    for pattern in intro_patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            r1, r2 = m.group(1), m.group(2)
            p1, p2 = clean_price(r1, currency), clean_price(r2, currency)
            if p1 and p2 and p1 != p2:
                plan['intro_price_raw'] = r1
                plan['regular_price_raw'] = r2
                plan['intro_price'] = p1
                plan['regular_price'] = p2
                break

    auto_patterns = [
        rf'automatically at\s+[^\d]*({num})\s*[^\"<]*(?:/|\\u002F)(?:month|mo)[^t]',
        rf'mức phí\s+({num})\s*[^\d\"<]*(?:/|\\u002F)tháng',
        rf'вартістю[\s\xa0]+({num})[\s\xa0]*[^\d\"<]*на[\s\xa0]+місяць',
        rf'(?:di harga|seharga)\s+[^\d]*({num})\s*[^\/\"<]*(?:/|\\u002F)(?:bulan|bln)',
        rf'reînnoire automat[ă]\s+[^\d]*({num})\s*[^\/\"<]*(?:/|\\u002F)lun',
        rf'อัตโนมัติ[^฿\d]*[฿\s]*({num})\s*[^\/\"<]*(?:/|ต่อ)เดือน',
        rf'automatisch\s+f[üu]r\s+[^\d]*({num})\s*[^\/\"<]*(?:/|\\u002F)Monat',
        rf'automatiquement\s+au\s+(?:tarif|prix)\s+[^\d]*({num})\s*[^\/\"<]*(?:(?:/|\\u002F)mois|par\s+mois)',
        rf'autom[aá]ticamente\s+(?:a\s+)?[^\d]*({num})\s*[^\/\"<]*(?:al\s+mes|(?:/|\\u002F)mes)',
    ]

    for pattern in auto_patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            raw = m.group(1)
            price = clean_price(raw, currency)
            if price:
                plan['auto_renew_price_raw'] = raw
                plan['auto_renew_price'] = price
                break

    if plan['intro_price'] or plan['regular_price'] or plan['auto_renew_price']:
        return plan
    return None


async def fetch_xbox_price(browser, region_code: str) -> Dict[str, Any]:
    url = f"https://www.xbox.com/{region_code}/xbox-game-pass/pc-game-pass"
    currency = REGION_INFO.get(region_code, {}).get('currency', 'USD')
    page = await browser.new_page()

    try:
        print(f"[{region_code}] Fetching...")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        html = await page.content()
        html = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), html)

        # Try structured plan blocks first
        plans = extract_plan_prices_from_blocks(html, currency)

        # Fall back to legacy regex for regions without plan blocks
        if not plans:
            fallback = extract_prices_fallback(html, currency)
            if fallback:
                plans = [fallback]

        result: Dict[str, Any] = {
            'region_code': region_code,
            'currency': currency,
            'url': url,
            'scraped_at': datetime.now(timezone.utc).isoformat(),
            'plans': plans,
        }

        if plans:
            summary = ', '.join(
                f"{p['plan']}(auto={p['auto_renew_price'] or p['regular_price']})"
                for p in plans
            )
            print(f"[{region_code}] OK  {summary}")
        else:
            print(f"[{region_code}] --  no prices found")

        return result

    except Exception as e:
        print(f"[{region_code}] ERR {e}")
        return {
            'region_code': region_code,
            'currency': currency,
            'url': url,
            'error': str(e),
            'scraped_at': datetime.now(timezone.utc).isoformat(),
            'plans': [],
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

    ok = sum(1 for r in results if r.get('plans'))
    print("=" * 60)
    print(f"Done. {ok}/{len(results)} regions with prices.")


if __name__ == '__main__':
    asyncio.run(main())
