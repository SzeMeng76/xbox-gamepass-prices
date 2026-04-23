import json
import os
import requests
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Optional

# Requires API_KEY env var from openexchangerates.org (free tier works)
API_KEY = os.getenv('API_KEY', '')
API_URL = f'https://openexchangerates.org/api/latest.json?app_id={API_KEY}&base=USD'

REGION_INFO = {
    # Middle East / North Africa
    'ar-AE': {'currency': 'USD', 'name_en': 'UAE',            'name_cn': '阿联酋'},
    'ar-BH': {'currency': 'BHD', 'name_en': 'Bahrain',        'name_cn': '巴林'},
    'ar-DZ': {'currency': 'DZD', 'name_en': 'Algeria',        'name_cn': '阿尔及利亚'},
    'ar-EG': {'currency': 'EGP', 'name_en': 'Egypt',          'name_cn': '埃及'},
    'ar-KW': {'currency': 'KWD', 'name_en': 'Kuwait',         'name_cn': '科威特'},
    'ar-LY': {'currency': 'USD', 'name_en': 'Libya',          'name_cn': '利比亚'},
    'ar-MA': {'currency': 'MAD', 'name_en': 'Morocco',        'name_cn': '摩洛哥'},
    'ar-OM': {'currency': 'OMR', 'name_en': 'Oman',           'name_cn': '阿曼'},
    'ar-QA': {'currency': 'QAR', 'name_en': 'Qatar',          'name_cn': '卡塔尔'},
    'ar-SA': {'currency': 'SAR', 'name_en': 'Saudi Arabia',   'name_cn': '沙特阿拉伯'},
    'ar-TN': {'currency': 'TND', 'name_en': 'Tunisia',        'name_cn': '突尼斯'},
    'he-IL': {'currency': 'ILS', 'name_en': 'Israel',         'name_cn': '以色列'},
    # Europe
    'bg-BG': {'currency': 'BGN', 'name_en': 'Bulgaria',       'name_cn': '保加利亚'},
    'cs-CZ': {'currency': 'CZK', 'name_en': 'Czech Republic', 'name_cn': '捷克'},
    'da-DK': {'currency': 'DKK', 'name_en': 'Denmark',        'name_cn': '丹麦'},
    'de-AT': {'currency': 'EUR', 'name_en': 'Austria',        'name_cn': '奥地利'},
    'de-CH': {'currency': 'CHF', 'name_en': 'Switzerland (DE)','name_cn': '瑞士(德语)'},
    'de-DE': {'currency': 'EUR', 'name_en': 'Germany',        'name_cn': '德国'},
    'de-LI': {'currency': 'CHF', 'name_en': 'Liechtenstein',  'name_cn': '列支敦士登'},
    'de-LU': {'currency': 'EUR', 'name_en': 'Luxembourg (DE)','name_cn': '卢森堡(德语)'},
    'el-GR': {'currency': 'EUR', 'name_en': 'Greece',         'name_cn': '希腊'},
    'en-CY': {'currency': 'EUR', 'name_en': 'Cyprus',         'name_cn': '塞浦路斯'},
    'en-GB': {'currency': 'GBP', 'name_en': 'United Kingdom', 'name_cn': '英国'},
    'en-IE': {'currency': 'EUR', 'name_en': 'Ireland',        'name_cn': '爱尔兰'},
    'es-ES': {'currency': 'EUR', 'name_en': 'Spain',          'name_cn': '西班牙'},
    'et-EE': {'currency': 'EUR', 'name_en': 'Estonia',        'name_cn': '爱沙尼亚'},
    'fi-FI': {'currency': 'EUR', 'name_en': 'Finland',        'name_cn': '芬兰'},
    'fr-BE': {'currency': 'EUR', 'name_en': 'Belgium (FR)',   'name_cn': '比利时(法语)'},
    'fr-CH': {'currency': 'CHF', 'name_en': 'Switzerland (FR)','name_cn': '瑞士(法语)'},
    'fr-FR': {'currency': 'EUR', 'name_en': 'France',         'name_cn': '法国'},
    'fr-LU': {'currency': 'EUR', 'name_en': 'Luxembourg (FR)','name_cn': '卢森堡(法语)'},
    'hr-HR': {'currency': 'EUR', 'name_en': 'Croatia',        'name_cn': '克罗地亚'},
    'hu-HU': {'currency': 'HUF', 'name_en': 'Hungary',        'name_cn': '匈牙利'},
    'is-IS': {'currency': 'ISK', 'name_en': 'Iceland',        'name_cn': '冰岛'},
    'it-IT': {'currency': 'EUR', 'name_en': 'Italy',          'name_cn': '意大利'},
    'lt-LT': {'currency': 'EUR', 'name_en': 'Lithuania',      'name_cn': '立陶宛'},
    'lv-LV': {'currency': 'EUR', 'name_en': 'Latvia',         'name_cn': '拉脱维亚'},
    'mk-MK': {'currency': 'USD', 'name_en': 'North Macedonia','name_cn': '北马其顿'},
    'mt-MT': {'currency': 'EUR', 'name_en': 'Malta',          'name_cn': '马耳他'},
    'nb-NO': {'currency': 'NOK', 'name_en': 'Norway',         'name_cn': '挪威'},
    'nl-BE': {'currency': 'EUR', 'name_en': 'Belgium (NL)',   'name_cn': '比利时(荷语)'},
    'nl-NL': {'currency': 'EUR', 'name_en': 'Netherlands',    'name_cn': '荷兰'},
    'pl-PL': {'currency': 'PLN', 'name_en': 'Poland',         'name_cn': '波兰'},
    'pt-PT': {'currency': 'EUR', 'name_en': 'Portugal',       'name_cn': '葡萄牙'},
    'ro-MD': {'currency': 'USD', 'name_en': 'Moldova',        'name_cn': '摩尔多瓦'},
    'ro-RO': {'currency': 'RON', 'name_en': 'Romania',        'name_cn': '罗马尼亚'},
    'ru-RU': {'currency': 'RUB', 'name_en': 'Russia',         'name_cn': '俄罗斯'},
    'sk-SK': {'currency': 'EUR', 'name_en': 'Slovakia',       'name_cn': '斯洛伐克'},
    'sl-SL': {'currency': 'EUR', 'name_en': 'Slovenia',       'name_cn': '斯洛文尼亚'},
    'sq-AL': {'currency': 'USD', 'name_en': 'Albania',        'name_cn': '阿尔巴尼亚'},
    'sv-SE': {'currency': 'SEK', 'name_en': 'Sweden',         'name_cn': '瑞典'},
    'tr-TR': {'currency': 'TRY', 'name_en': 'Turkey',         'name_cn': '土耳其'},
    'uk-UA': {'currency': 'UAH', 'name_en': 'Ukraine',        'name_cn': '乌克兰'},
    # Asia Pacific
    'en-AU': {'currency': 'AUD', 'name_en': 'Australia',      'name_cn': '澳大利亚'},
    'en-HK': {'currency': 'HKD', 'name_en': 'Hong Kong',      'name_cn': '香港'},
    'en-IN': {'currency': 'INR', 'name_en': 'India',          'name_cn': '印度'},
    'en-MY': {'currency': 'MYR', 'name_en': 'Malaysia',       'name_cn': '马来西亚'},
    'en-NZ': {'currency': 'NZD', 'name_en': 'New Zealand',    'name_cn': '新西兰'},
    'en-PH': {'currency': 'PHP', 'name_en': 'Philippines',    'name_cn': '菲律宾'},
    'en-SG': {'currency': 'SGD', 'name_en': 'Singapore',      'name_cn': '新加坡'},
    'id-ID': {'currency': 'IDR', 'name_en': 'Indonesia',      'name_cn': '印度尼西亚'},
    'ja-JP': {'currency': 'JPY', 'name_en': 'Japan',          'name_cn': '日本'},
    'ka-GE': {'currency': 'USD', 'name_en': 'Georgia',        'name_cn': '格鲁吉亚'},
    'ko-KR': {'currency': 'KRW', 'name_en': 'South Korea',    'name_cn': '韩国'},
    'th-TH': {'currency': 'THB', 'name_en': 'Thailand',       'name_cn': '泰国'},
    'vi-VN': {'currency': 'VND', 'name_en': 'Vietnam',        'name_cn': '越南'},
    'zh-HK': {'currency': 'HKD', 'name_en': 'Hong Kong (ZH)', 'name_cn': '香港(中文)'},
    'zh-TW': {'currency': 'TWD', 'name_en': 'Taiwan',         'name_cn': '台湾'},
    # Africa
    'en-ZA': {'currency': 'ZAR', 'name_en': 'South Africa',   'name_cn': '南非'},
    # Americas
    'en-CA': {'currency': 'CAD', 'name_en': 'Canada (EN)',    'name_cn': '加拿大(英语)'},
    'en-US': {'currency': 'USD', 'name_en': 'United States',  'name_cn': '美国'},
    'es-AR': {'currency': 'ARS', 'name_en': 'Argentina',      'name_cn': '阿根廷'},
    'es-BO': {'currency': 'USD', 'name_en': 'Bolivia',        'name_cn': '玻利维亚'},
    'es-CL': {'currency': 'CLP', 'name_en': 'Chile',          'name_cn': '智利'},
    'es-CO': {'currency': 'COP', 'name_en': 'Colombia',       'name_cn': '哥伦比亚'},
    'es-CR': {'currency': 'CRC', 'name_en': 'Costa Rica',     'name_cn': '哥斯达黎加'},
    'es-EC': {'currency': 'USD', 'name_en': 'Ecuador',        'name_cn': '厄瓜多尔'},
    'es-GT': {'currency': 'GTQ', 'name_en': 'Guatemala',      'name_cn': '危地马拉'},
    'es-HN': {'currency': 'USD', 'name_en': 'Honduras',       'name_cn': '洪都拉斯'},
    'es-MX': {'currency': 'MXN', 'name_en': 'Mexico',         'name_cn': '墨西哥'},
    'es-NI': {'currency': 'USD', 'name_en': 'Nicaragua',      'name_cn': '尼加拉瓜'},
    'es-PA': {'currency': 'USD', 'name_en': 'Panama',         'name_cn': '巴拿马'},
    'es-PE': {'currency': 'PEN', 'name_en': 'Peru',           'name_cn': '秘鲁'},
    'es-PY': {'currency': 'USD', 'name_en': 'Paraguay',       'name_cn': '巴拉圭'},
    'es-SV': {'currency': 'USD', 'name_en': 'El Salvador',    'name_cn': '萨尔瓦多'},
    'es-UY': {'currency': 'USD', 'name_en': 'Uruguay',        'name_cn': '乌拉圭'},
    'fr-CA': {'currency': 'CAD', 'name_en': 'Canada (FR)',    'name_cn': '加拿大(法语)'},
    'pt-BR': {'currency': 'BRL', 'name_en': 'Brazil',         'name_cn': '巴西'},
}


def get_exchange_rates() -> Optional[dict]:
    if not API_KEY:
        print('ERROR: API_KEY environment variable not set.')
        print('Get a free key at https://openexchangerates.org/')
        return None
    try:
        resp = requests.get(API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        rates = data.get('rates', {})
        rates['USD'] = 1.0
        print(f'Exchange rates fetched ({len(rates)} currencies)')
        return rates
    except Exception as e:
        print(f'ERROR fetching exchange rates: {e}')
        return None


def to_cny(amount: float, currency: str, rates: dict) -> Optional[float]:
    """Convert amount in given currency to CNY."""
    if currency == 'CNY':
        return round(amount, 2)
    usd_rate = rates.get(currency)
    cny_rate = rates.get('CNY')
    if not usd_rate or not cny_rate:
        return None
    # amount / usd_rate = USD, USD * cny_rate = CNY
    try:
        result = Decimal(str(amount)) / Decimal(str(usd_rate)) * Decimal(str(cny_rate))
        return float(result.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    except (InvalidOperation, ZeroDivisionError):
        return None


def process():
    with open('xbox_gamepass_prices.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    rates = get_exchange_rates()
    if not rates:
        return

    updated_at = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    all_regions = []

    for item in raw_data:
        region_code = item['region_code']
        info = REGION_INFO.get(region_code, {})
        currency = item['currency']

        entry = {
            'region_code': region_code,
            'name_en': info.get('name_en', region_code),
            'name_cn': info.get('name_cn', region_code),
            'currency': currency,
            'scraped_at': item['scraped_at'],
        }

        if 'error' in item:
            entry['error'] = item['error']
            all_regions.append(entry)
            continue

        # Process plans array
        plans_out = []
        for plan in item.get('plans', []):
            plan_out = {'plan': plan['plan']}
            for price_type in ('intro_price', 'regular_price', 'auto_renew_price'):
                val = plan.get(price_type)
                raw = plan.get(price_type + '_raw')
                if val is not None:
                    plan_out[price_type] = val
                    plan_out[price_type + '_raw'] = raw
                    plan_out[price_type + '_cny'] = to_cny(val, currency, rates)
            plans_out.append(plan_out)

        entry['plans'] = plans_out
        all_regions.append(entry)

    # Build top-10 ranking by PC Game Pass auto_renew_price_cny
    rankable = []
    for r in all_regions:
        for plan in r.get('plans', []):
            if plan.get('plan') == 'PC Game Pass':
                price_cny = plan.get('auto_renew_price_cny') or plan.get('regular_price_cny')
                if price_cny is not None:
                    rankable.append({
                        'region_code': r['region_code'],
                        'name_en': r['name_en'],
                        'name_cn': r['name_cn'],
                        'currency': r['currency'],
                        'auto_renew_price': plan.get('auto_renew_price') or plan.get('regular_price'),
                        'auto_renew_price_cny': price_cny,
                    })

    ranked = sorted(rankable, key=lambda x: x['auto_renew_price_cny'])

    top10 = [
        {
            'rank': i + 1,
            'region_code': r['region_code'],
            'name_en': r['name_en'],
            'name_cn': r['name_cn'],
            'currency': r['currency'],
            'auto_renew_price': r['auto_renew_price'],
            'auto_renew_price_cny': r['auto_renew_price_cny'],
        }
        for i, r in enumerate(ranked[:10])
    ]

    # Generate Ultimate ranking
    rankable_ultimate = []
    for region_data in all_regions:
        plans = region_data.get('plans', [])
        ultimate_plan = next((p for p in plans if p.get('plan') == 'Game Pass Ultimate'), None)

        if ultimate_plan:
            price = ultimate_plan.get('auto_renew_price') or ultimate_plan.get('regular_price')
            if price:
                currency = region_data['currency']
                price_cny = to_cny(price, currency, rates)
                if price_cny:
                    rankable_ultimate.append({
                        'region_code': region_data['region_code'],
                        'name_en': region_data['name_en'],
                        'name_cn': region_data['name_cn'],
                        'currency': currency,
                        'auto_renew_price': price,
                        'auto_renew_price_cny': price_cny,
                    })

    ranked_ultimate = sorted(rankable_ultimate, key=lambda x: x['auto_renew_price_cny'])

    top10_ultimate = [
        {
            'rank': i + 1,
            'region_code': r['region_code'],
            'name_en': r['name_en'],
            'name_cn': r['name_cn'],
            'currency': r['currency'],
            'auto_renew_price': r['auto_renew_price'],
            'auto_renew_price_cny': r['auto_renew_price_cny'],
        }
        for i, r in enumerate(ranked_ultimate[:10])
    ]

    output = {
        '_updated_at': updated_at,
        '_top10_cheapest_pc_game_pass': {
            'description': 'Top 10 cheapest regions for PC Game Pass (auto-renew monthly price, converted to CNY)',
            'updated_at': updated_at,
            'data': top10,
        },
        '_top10_cheapest_ultimate': {
            'description': 'Top 10 cheapest regions for Game Pass Ultimate (auto-renew monthly price, converted to CNY)',
            'updated_at': updated_at,
            'data': top10_ultimate,
        },
        'regions': all_regions,
    }

    with open('xbox_gamepass_prices_processed.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\nProcessed {len(all_regions)} regions -> xbox_gamepass_prices_processed.json')
    print(f'\nTop 10 cheapest PC Game Pass (auto-renew):')
    for item in top10:
        print(f"  {item['rank']:2d}. {item['region_code']:8s} {item['auto_renew_price']:10.2f} {item['currency']:4s} = ¥{item['auto_renew_price_cny']:.2f}")

    print(f'\nTop 10 cheapest Game Pass Ultimate (auto-renew):')
    for item in top10_ultimate:
        print(f"  {item['rank']:2d}. {item['region_code']:8s} {item['auto_renew_price']:10.2f} {item['currency']:4s} = ¥{item['auto_renew_price_cny']:.2f}")


if __name__ == '__main__':
    process()
