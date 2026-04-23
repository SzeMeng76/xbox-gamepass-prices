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
    'pt-PT', 'ro-MD', 'ro-RO', 'ru-RU', 'sk-SK', 'sl-SI', 'sq-AL', 'sv-SE',
    'tr-TR', 'uk-UA', 'bs-Latn-BA', 'sr-Latn-ME', 'sr-Latn-RS',
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
    'ar-AE': {'currency': 'USD'},
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
    'sl-SI': {'currency': 'EUR'},
    'sq-AL': {'currency': 'USD'},
    'sv-SE': {'currency': 'SEK'},
    'tr-TR': {'currency': 'TRY'},
    'uk-UA': {'currency': 'UAH'},
    'bs-Latn-BA': {'currency': 'USD'},
    'sr-Latn-ME': {'currency': 'EUR'},
    'sr-Latn-RS': {'currency': 'RSD'},
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

        # Try intro + regular: "for $1, then $9.99/month" or Czech "za X, poté Y měsíčně"
        m2 = re.search(
            rf'for\s+(?![\d]+\s+days)[^\d]*({num})[^,<]*,\s*(?:<[^>]+>)*\s*then\s+[^\d]*({num})[^<]*(?:/|\\u002F)(?:month|mo)\b',
            block, re.IGNORECASE
        )
        if not m2:
            # Try German pattern (€ before number): "für €1, danach €8,99/Monat"
            m2 = re.search(
                rf'für\s+€[\s\xa0&nbsp;]*({num})[^,<]*,\s*danach\s+€[\s\xa0&nbsp;]*({num})[^<]*(?:/|\\u002F)Monat',
                block, re.IGNORECASE
            )
        if not m2:
            # Try German pattern (€ after number): "für 1 €, danach 8,99 €/Monat" or "für CHF 1, danach CHF 9.99/Monat"
            m2 = re.search(
                rf'für\s+(?:CHF[\s\xa0&nbsp;]*)?({num})[\s\xa0&nbsp;]*(?:€|CHF)?[^,<]*,\s*danach\s+(?:CHF[\s\xa0&nbsp;]*)?({num})[\s\xa0&nbsp;]*(?:€|CHF)?[^<]*(?:/|\\u002F)Monat',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Czech pattern
            m2 = re.search(
                rf'za\s+({num})[^,<]*,\s*poté\s+({num})[^<]*(?:měsíčně|Kč\s+měsíčně)',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Danish pattern
            m2 = re.search(
                rf'for\s+({num})[^,<]*(?:og\s+)?derefter\s+({num})[^<]*(?:kr\.|pr\.måned)',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Greek pattern: "με 1 €, στη συνέχεια 8,99 € /μήνα"
            m2 = re.search(
                rf'με\s+({num})[\s\xa0&nbsp;]*€[^,<]*,\s*στη συνέχεια\s+({num})[\s\xa0&nbsp;]*€[^<]*/μήνα',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Spanish (Spain) pattern: "por 1 €, y luego 8,99 €/mes"
            m2 = re.search(
                rf'por\s+({num})[\s\xa0&nbsp;]*€[^,<]*,\s*y luego\s+({num})[\s\xa0&nbsp;]*€/mes',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Spanish (Latin America) pattern: "por USD$1.00, <br> luego USD$7.99 al mes" or "por Q7.99, luego Q65.99 al mes"
            m2 = re.search(
                rf'por\s+(?:USD\$|Q)?({num})[^,]*,(?:[^a-z]|\s|<[^>]+>)*(?:luego|después)\s+(?:USD\$|Q)?({num})[^<\"]*al\s+mes',
                block, re.IGNORECASE
            )
        if not m2:
            # Try French pattern: "pour seulement 1 €, puis 8,99 € par mois"
            m2 = re.search(
                rf'pour\s+(?:seulement\s+)?[^\d]*({num})[\s\xa0&nbsp;]*€[^,<]*,\s*puis\s+[^\d]*({num})[\s\xa0&nbsp;]*€\s*(?:par\s+mois|/mois)',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Finnish pattern: "1 €:lla, minkä jälkeen tilaus maksaa 8,99 €/kuukausi"
            m2 = re.search(
                rf'({num})[\s\xa0&nbsp;]*€[^,<]*,\s*minkä jälkeen tilaus maksaa\s+({num})[\s\xa0&nbsp;]*€/kuukausi',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Hungarian pattern: "350 Ft, majd 3590 Ft/hónap"
            m2 = re.search(
                rf'({num})[\s\xa0&nbsp;]*Ft[^,<]*,\s*majd\s+({num})[\s\xa0&nbsp;]*Ft/hónap',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Italian pattern: "a 1 €, e i successivi a 8,99 € al mese"
            m2 = re.search(
                rf'a\s+({num})[\s\xa0&nbsp;]*€[^,<]*,\s*(?:e\s+)?i successivi a\s+({num})[\s\xa0&nbsp;]*€\s+al mese',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Norwegian pattern: "10 kr, deretter 105 kr/månedlig"
            m2 = re.search(
                rf'({num})[\s\xa0&nbsp;]*kr[^,<]*,\s*deretter\s+({num})[\s\xa0&nbsp;]*kr/månedlig',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Dutch pattern: "€1, daarna €8,99/maand"
            m2 = re.search(
                rf'€[\s\xa0&nbsp;]*({num})[^,<]*,\s*daarna\s+€[\s\xa0&nbsp;]*({num})/maand',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Polish pattern: might have intro pricing
            m2 = re.search(
                rf'({num})[\s\xa0&nbsp;]*zł[^,<]*,\s*(?:a\s+)?(?:potem|następnie)\s+({num})[\s\xa0&nbsp;]*zł/mies',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Portuguese pattern: "1 €, e depois por 8,99 €/mês"
            m2 = re.search(
                rf'({num})[\s\xa0&nbsp;]*€[^,<]*,\s*e depois por\s+({num})[\s\xa0&nbsp;]*€/mês',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Slovak pattern: "1 €, následne 8,99 €/mesiac"
            m2 = re.search(
                rf'({num})[\s\xa0&nbsp;]*€[^,<]*,\s*následne\s+({num})[\s\xa0&nbsp;]*€/mesiac',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Swedish pattern: "10 kr, därefter 95 kr/månad"
            m2 = re.search(
                rf'({num})[\s\xa0&nbsp;]*kr[^,<]*,\s*därefter\s+({num})[\s\xa0&nbsp;]*kr/månad',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Turkish pattern: might have intro pricing
            m2 = re.search(
                rf'({num})[\s\xa0&nbsp;]*₺[^,<]*,\s*(?:sonra|daha sonra)\s+({num})[\s\xa0&nbsp;]*₺',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Japanese pattern: "￥150、以降は月額 ￥850 円"
            m2 = re.search(
                rf'￥[\s\xa0&nbsp;]*({num})[^、<]*、\s*以降は月額\s+￥[\s\xa0&nbsp;]*({num})',
                block, re.IGNORECASE
            )
        if not m2:
            # Try Chinese (Taiwan) pattern: "$30，之後每月 $259" or "$30，之後每個月 $349"
            m2 = re.search(
                rf'\$[\s\xa0&nbsp;]*({num})[^，<]*，\s*之後每(?:個)?月\s+\$[\s\xa0&nbsp;]*({num})',
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

        # Try standalone price: various formats
        if not plan['regular_price']:
            # Try currency-after-number format first
            m3 = re.search(rf'[^\d]*({num})[\s\xa0&nbsp;]*(?:円|kr/månad|€/mesiac|€\s+al mese|€/mês|€\s*/μήνα|€/mes|€/Monat|€\s+par\s+mois|€/kuukausi|€/maand|Ft/hónap|kr/månedlig|zł/mies|[^<\"]*(?:(?:/|\\u002F)(?:month|mo|月)|Kč\s+měsíčně|měsíčně|kr\.\s+pr\.måned|pr\.måned))\b', block, re.IGNORECASE)
            if not m3:
                # Try currency-before-number format: "€12,99/Monat" or "CHF 13.99/Monat" or "₺419" or "￥1,300" or "₩15,500" or "HK$60" or "$259"
                m3 = re.search(rf'(?:€|CHF|₺|￥|₩|HK\$|\$)[\s\xa0&nbsp;]*({num})[^<\"]*(?:(?:/|\\u002F)(?:Monat|maand|월|月|月份)|ödeyin|円)?', block, re.IGNORECASE)
            if m3:
                raw = m3.group(1)
                price = clean_price(raw, currency)
                if price:
                    # Check if this is a multi-month bundle (e.g., "3 meses por $22,490")
                    multi_month = re.search(r'\b(\d+)\s*(?:meses|months|mois|Monate)\b', block, re.IGNORECASE)
                    if multi_month:
                        months = int(multi_month.group(1))
                        price = price / months
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
        # Czech
        rf'za\s+({num})[^,<]*,\s*poté\s+({num})[^<]*(?:měsíčně|Kč\s+měsíčně)',
        # Danish
        rf'for\s+({num})[^,<]*(?:og\s+)?derefter\s+({num})[^<]*(?:kr\.|pr\.måned)',
        # Greek
        rf'με\s+({num})[\s\xa0&nbsp;]*€[^,\"]*,\s*στη συνέχεια\s+({num})[\s\xa0&nbsp;]*€[^\"]*/μήνα',
        # Finnish
        rf'({num})[\s\xa0&nbsp;]*€[^,\"]*,\s*minkä jälkeen tilaus maksaa\s+({num})[\s\xa0&nbsp;]*€/kuukausi',
        # Hungarian
        rf'({num})[\s\xa0&nbsp;]*Ft[^,\"]*,\s*majd\s+({num})[\s\xa0&nbsp;]*Ft/hónap',
        # Italian
        rf'a\s+({num})[\s\xa0&nbsp;]*€[^,\"]*,\s*(?:e\s+)?i successivi a\s+({num})[\s\xa0&nbsp;]*€\s+al mese',
        # Norwegian
        rf'({num})[\s\xa0&nbsp;]*kr[^,\"]*,\s*deretter\s+({num})[\s\xa0&nbsp;]*kr/månedlig',
        # Dutch
        rf'€[\s\xa0&nbsp;]*({num})[^,\"]*,\s*daarna\s+€[\s\xa0&nbsp;]*({num})/maand',
        # Polish
        rf'({num})[\s\xa0&nbsp;]*zł[^,\"]*,\s*(?:a\s+)?(?:potem|następnie)\s+({num})[\s\xa0&nbsp;]*zł/mies',
        # Portuguese
        rf'({num})[\s\xa0&nbsp;]*€[^,\"]*,\s*e depois por\s+({num})[\s\xa0&nbsp;]*€/mês',
        # Slovak
        rf'({num})[\s\xa0&nbsp;]*€[^,\"]*,\s*následne\s+({num})[\s\xa0&nbsp;]*€/mesiac',
        # Swedish
        rf'({num})[\s\xa0&nbsp;]*kr[^,\"]*,\s*därefter\s+({num})[\s\xa0&nbsp;]*kr/månad',
        # Turkish
        rf'({num})[\s\xa0&nbsp;]*₺[^,\"]*,\s*(?:sonra|daha sonra)\s+({num})[\s\xa0&nbsp;]*₺',
        # Japanese
        rf'￥[\s\xa0&nbsp;]*({num})[^、\"]*、\s*以降は月額\s+￥[\s\xa0&nbsp;]*({num})',
        # Chinese (Taiwan)
        rf'\$[\s\xa0&nbsp;]*({num})[^，\"]*，\s*之後每(?:個)?月\s+\$[\s\xa0&nbsp;]*({num})',
        # Vietnamese
        rf'v[oớ]i\s+({num})\s*[^\d,\"]*,\s*sau đó là\s+({num})\s*[^\d\"]*(?:/|\\u002F)tháng',
        # Ukrainian (uses \xa0 non-breaking spaces)
        rf'за[\s\xa0]+({num})[\s\xa0]*[^,\"]*,\s*далі за[\s\xa0]+ціною[\s\xa0]+({num})[\s\xa0]*[^\"]*(?:/|/міс)',
        # Spanish (Latin America) "por USD$1.00, luego USD$7.99 al mes" or "por Q7.99, luego Q65.99 al mes"
        rf'por\s+(?:USD\$|Q)?({num})[^,]*,(?:[^a-z]|\s|<[^>]+>)*(?:luego|después)\s+(?:USD\$|Q)?({num})[^<\"]*al\s+mes',
        # Indonesian
        rf'seharga\s+[^\d]*({num})[^,\"]*,\s*lalu\s+[^\d]*({num})\s*[^\"]*(?:/|\\u002F)bulan',
        # Romanian
        rf'pentru\s+[^\d]*({num})[^,\"]*,\s*apoi\s+[^\d]*({num})\s*[^\"]*(?:/|\\u002F)lun',
        # Thai
        rf'เพียง\s+[^\d]*({num})\s*[^\d,\"]*(?:จากนั้น|,)\s*[^\d]*({num})\s*[^\"]*(?:/|\\u002F)เดือน',
        # German (€ before number)
        rf'für\s+€[\s\xa0&nbsp;]*({num})[^,\"]*,\s*danach\s+€[\s\xa0&nbsp;]*({num})\s*[^\"]*(?:/|\\u002F)Monat',
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
    currency = REGION_INFO.get(region_code, {}).get('currency', 'USD')
    page = await browser.new_page()

    try:
        # Try /xbox-game-pass first (has all 4 plans for some regions)
        url = f"https://www.xbox.com/{region_code}/xbox-game-pass"
        print(f"[{region_code}] Fetching...")
        await page.goto(url, wait_until='networkidle', timeout=30000)
        html = await page.content()
        html = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), html)

        # Try structured plan blocks first
        plans = extract_plan_prices_from_blocks(html, currency)

        # If no plans found, try /pc-game-pass page
        if not plans:
            url = f"https://www.xbox.com/{region_code}/xbox-game-pass/pc-game-pass"
            await page.goto(url, wait_until='networkidle', timeout=30000)
            html = await page.content()
            html = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), html)
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
