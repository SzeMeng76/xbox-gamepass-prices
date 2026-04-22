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
    'ar-BH': {'currency': 'BHD', 'name_en': 'Bahrain',        'name_cn': '巴林'},
    'ar-DZ': {'currency': 'DZD', 'name_en': 'Algeria',        'name_cn': '阿尔及利亚'},
    'ar-EG': {'currency': 'EGP', 'name_en': 'Egypt',          'name_cn': '埃及'},
    'ar-KW': {'currency': 'KWD', 'name_en': 'Kuwait',         'name_cn': '科威特'},
    'ar-LY': {'currency': 'USD', 'name_en': 'Libya',          'name_cn': '利比亚'},
    'ar-MA': {'currency': 'MAD', 'name_en': 'Morocco',        'name_cn': '摩洛哥'},
    'ar-OM': {'currency': 'OMR', 'name_en': 'Oman',           'name_cn': '阿曼'},
    'ar-QA': {'currency': 'QAR', 'name_en': 'Qatar',          'name_cn': '卡塔尔'},
    'ar-TN': {'currency': 'TND', 'name_en': 'Tunisia',        'name_cn': '突尼斯'},
    'bg-BG': {'currency': 'BGN', 'name_en': 'Bulgaria',       'name_cn': '保加利亚'},
    'de-LI': {'currency': 'CHF', 'name_en': 'Liechtenstein',  'name_cn': '列支敦士登'},
    'de-LU': {'currency': 'EUR', 'name_en': 'Luxembourg',     'name_cn': '卢森堡'},
    'en-CY': {'currency': 'EUR', 'name_en': 'Cyprus',         'name_cn': '塞浦路斯'},
    'en-MY': {'currency': 'MYR', 'name_en': 'Malaysia',       'name_cn': '马来西亚'},
    'en-PH': {'currency': 'PHP', 'name_en': 'Philippines',    'name_cn': '菲律宾'},
    'en-US': {'currency': 'USD', 'name_en': 'United States',  'name_cn': '美国'},
    'es-BO': {'currency': 'BOB', 'name_en': 'Bolivia',        'name_cn': '玻利维亚'},
    'es-CR': {'currency': 'CRC', 'name_en': 'Costa Rica',     'name_cn': '哥斯达黎加'},
    'es-EC': {'currency': 'USD', 'name_en': 'Ecuador',        'name_cn': '厄瓜多尔'},
    'es-GT': {'currency': 'GTQ', 'name_en': 'Guatemala',      'name_cn': '危地马拉'},
    'es-HN': {'currency': 'HNL', 'name_en': 'Honduras',       'name_cn': '洪都拉斯'},
    'es-NI': {'currency': 'NIO', 'name_en': 'Nicaragua',      'name_cn': '尼加拉瓜'},
    'es-PA': {'currency': 'USD', 'name_en': 'Panama',         'name_cn': '巴拿马'},
    'es-PE': {'currency': 'PEN', 'name_en': 'Peru',           'name_cn': '秘鲁'},
    'es-PY': {'currency': 'PYG', 'name_en': 'Paraguay',       'name_cn': '巴拉圭'},
    'es-SV': {'currency': 'USD', 'name_en': 'El Salvador',    'name_cn': '萨尔瓦多'},
    'es-UY': {'currency': 'UYU', 'name_en': 'Uruguay',        'name_cn': '乌拉圭'},
    'et-EE': {'currency': 'EUR', 'name_en': 'Estonia',        'name_cn': '爱沙尼亚'},
    'fr-LU': {'currency': 'EUR', 'name_en': 'Luxembourg (FR)','name_cn': '卢森堡(法语)'},
    'hr-HR': {'currency': 'EUR', 'name_en': 'Croatia',        'name_cn': '克罗地亚'},
    'id-ID': {'currency': 'IDR', 'name_en': 'Indonesia',      'name_cn': '印度尼西亚'},
    'is-IS': {'currency': 'ISK', 'name_en': 'Iceland',        'name_cn': '冰岛'},
    'ka-GE': {'currency': 'USD', 'name_en': 'Georgia',        'name_cn': '格鲁吉亚'},
    'lt-LT': {'currency': 'EUR', 'name_en': 'Lithuania',      'name_cn': '立陶宛'},
    'lv-LV': {'currency': 'EUR', 'name_en': 'Latvia',         'name_cn': '拉脱维亚'},
    'mk-MK': {'currency': 'USD', 'name_en': 'North Macedonia','name_cn': '北马其顿'},
    'mt-MT': {'currency': 'EUR', 'name_en': 'Malta',          'name_cn': '马耳他'},
    'ro-MD': {'currency': 'USD', 'name_en': 'Moldova',        'name_cn': '摩尔多瓦'},
    'ro-RO': {'currency': 'RON', 'name_en': 'Romania',        'name_cn': '罗马尼亚'},
    'sl-SL': {'currency': 'EUR', 'name_en': 'Slovenia',       'name_cn': '斯洛文尼亚'},
    'sq-AL': {'currency': 'USD', 'name_en': 'Albania',        'name_cn': '阿尔巴尼亚'},
    'th-TH': {'currency': 'THB', 'name_en': 'Thailand',       'name_cn': '泰国'},
    'uk-UA': {'currency': 'UAH', 'name_en': 'Ukraine',        'name_cn': '乌克兰'},
    'vi-VN': {'currency': 'VND', 'name_en': 'Vietnam',        'name_cn': '越南'},
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

    output = {
        '_updated_at': updated_at,
        '_top10_cheapest_pc_game_pass': {
            'description': 'Top 10 cheapest regions for PC Game Pass (auto-renew monthly price, converted to CNY)',
            'updated_at': updated_at,
            'data': top10,
        },
        'regions': all_regions,
    }

    with open('xbox_gamepass_prices_processed.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f'\nProcessed {len(all_regions)} regions -> xbox_gamepass_prices_processed.json')
    print(f'\nTop 10 cheapest PC Game Pass (auto-renew):')
    for item in top10:
        print(f"  {item['rank']:2d}. {item['region_code']:8s} {item['auto_renew_price']:10.2f} {item['currency']:4s} = ¥{item['auto_renew_price_cny']:.2f}")


if __name__ == '__main__':
    process()
