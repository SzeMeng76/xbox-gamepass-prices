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

REGION_CURRENCY = {
    'ar-BH': 'BHD', 'ar-DZ': 'DZD', 'ar-EG': 'EGP', 'ar-KW': 'KWD',
    'ar-LY': 'LYD', 'ar-MA': 'MAD', 'ar-OM': 'OMR', 'ar-QA': 'QAR',
    'ar-TN': 'TND', 'bg-BG': 'BGN', 'de-LI': 'CHF', 'de-LU': 'EUR',
    'en-CY': 'EUR', 'en-MY': 'MYR', 'en-PH': 'PHP', 'en-US': 'USD',
    'es-BO': 'BOB', 'es-CR': 'CRC', 'es-EC': 'USD', 'es-GT': 'GTQ',
    'es-HN': 'HNL', 'es-NI': 'NIO', 'es-PA': 'USD', 'es-PE': 'PEN',
    'es-PY': 'PYG', 'es-SV': 'USD', 'es-UY': 'UYU', 'et-EE': 'EUR',
    'fr-LU': 'EUR', 'hr-HR': 'EUR', 'id-ID': 'IDR', 'is-IS': 'ISK',
    'ka-GE': 'GEL', 'lt-LT': 'EUR', 'lv-LV': 'EUR', 'mk-MK': 'MKD',
    'mt-MT': 'EUR', 'ro-MD': 'MDL', 'ro-RO': 'RON', 'sl-SL': 'EUR',
    'sq-AL': 'ALL', 'th-TH': 'THB', 'uk-UA': 'UAH', 'vi-VN': 'VND',
}

# 数字模式：匹配 1,234.56 / 1.234,56 / 1234 / 1,234
NUM = r'[\d]+(?:[.,][\d]+)*'


def clean_price(price_str: str) -> Optional[float]:
    if not price_str:
        return None
    s = price_str.strip()
    # 1.234,56 -> 1234.56 (European)
    if re.search(r'\d\.\d{3},', s):
        s = s.replace('.', '').replace(',', '.')
    # 1,234.56 -> 1234.56 (US)
    elif re.search(r'\d,\d{3}\.', s):
        s = s.replace(',', '')
    # 1,234 (no decimal) -> 1234
    elif re.search(r'\d,\d{3}$', s):
        s = s.replace(',', '')
    # 39,99 -> 39.99 (European decimal)
    elif ',' in s and '.' not in s:
        parts = s.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')
    s = re.sub(r'[^\d.]', '', s)
    try:
        return float(s)
    except Exception:
        return None


def extract_prices(html: str, region_code: str) -> Dict[str, Any]:
    """
    从渲染后的HTML中提取3种价格：
    - intro_price: 首次优惠价
    - regular_price: 常规月费（__PRELOADED_STATE__里的标价）
    - auto_renew_price: 自动续订价
    """
    result: Dict[str, Any] = {
        'intro_price_raw': None,
        'regular_price_raw': None,
        'auto_renew_price_raw': None,
        'intro_price': None,
        'regular_price': None,
        'auto_renew_price': None,
    }

    # ── 1. intro + regular：从__PRELOADED_STATE__ JSON里取（unicode转义，最干净）
    # 格式示例:
    #   vi-VN: "Sử dụng 14 ngày ... với 24.900 ₫, sau đó là 129.000 ₫\/tháng"
    #   en-PH: "Get your first 14 days for ₱59, then ₱320\/month"
    #   ar-BH: "Get your first 14 days for BD 0.40, then BD 4.50\/month"
    #   uk-UA: "Отримайте перші 14 днів ... за 39,99 ₴, далі за ціною 290,00 ₴\/міс."

    preloaded_patterns = [
        # English: "for PRICE, then PRICE/month"
        rf'for\s+([^,\"]+?),\s*then\s+([^\\\"\/]+?)(?:\\u002F|/)(?:month|mo)',
        # Vietnamese: "với PRICE ..., sau đó là PRICE\/tháng"
        rf'v[oớ]i\s+([^,\"]+?),?\s*sau đó là\s+([^\\\"\/]+?)(?:\\u002F|/)th[aá]ng',
        # Ukrainian/Russian: "за PRICE, далі за ціною PRICE\/міс"
        rf'за\s+([^,\"]+?),\s*далі за ціною\s+([^\\\"\/]+?)(?:\\u002F|/)(?:міс|мес)',
        # Spanish: "por PRICE, luego PRICE\/mes"
        rf'por\s+([^,\"]+?),\s*luego\s+([^\\\"\/]+?)(?:\\u002F|/)mes',
    ]

    for pattern in preloaded_patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            raw1 = m.group(1).strip()
            raw2 = m.group(2).strip()
            p1 = clean_price(re.sub(r'[^\d.,]', '', raw1))
            p2 = clean_price(re.sub(r'[^\d.,]', '', raw2))
            if p1 and p2 and p1 != p2:
                result['intro_price_raw'] = raw1
                result['regular_price_raw'] = raw2
                result['intro_price'] = p1
                result['regular_price'] = p2
                break

    # ── 2. auto_renew：从渲染后的HTML里取（"continues automatically at PRICE/month"）
    auto_patterns = [
        # English: "continues automatically at ₱225.00/month"
        rf'(?:continues?|renew[s]?) automatically at\s+([^\/<\"]+?)(?:/|\s*per\s*)(?:month|mo)',
        # Vietnamese: "mức phí 79.000,00 ₫/tháng"
        rf'mức phí\s+([^\/<\"]+?)\s*(?:/|\\u002F)tháng',
        # Ukrainian: "230,00 ₴ на місяць"
        rf'вартістю\s+([^\s<\"]+\s*₴)\s+на місяць',
        # German/European: "wird automatisch zum Preis von X € pro Monat verlängert"
        rf'automatisch.*?(?:Preis von|Preis:)\s+([^\s<\"]+\s*€)',
        # Indonesian: "diperpanjang otomatis seharga X/bulan"
        rf'otomatis seharga\s+([^\/<\"]+?)(?:/|\\u002F)bulan',
        # Thai: "ต่ออายุอัตโนมัติ"
        rf'ต่ออายุอัตโนมัติ[^฿\d]*([฿\d][^\/<\"]+?)(?:/|ต่อ)เดือน',
    ]

    for pattern in auto_patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            price = clean_price(re.sub(r'[^\d.,]', '', raw))
            if price:
                result['auto_renew_price_raw'] = raw
                result['auto_renew_price'] = price
                break

    return result


async def fetch_xbox_price(browser, region_code: str) -> Dict[str, Any]:
    url = f"https://www.xbox.com/{region_code}/xbox-game-pass/pc-game-pass"
    currency = REGION_CURRENCY.get(region_code, 'USD')
    page = await browser.new_page()

    try:
        print(f"[{region_code}] Fetching...")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        html = await page.content()

        prices = extract_prices(html, region_code)

        result = {
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

        if parts:
            print(f"[{region_code}] OK  {', '.join(parts)}")
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
