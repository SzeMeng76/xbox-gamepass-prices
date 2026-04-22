import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional


def get_exchange_rates() -> Dict[str, float]:
    """获取最新汇率（相对于CNY）"""
    try:
        # 使用免费的汇率API
        response = requests.get('https://api.exchangerate-api.com/v4/latest/CNY', timeout=10)
        response.raise_for_status()
        data = response.json()

        # 转换为 1 外币 = X CNY 的格式
        rates = {}
        for currency, rate in data['rates'].items():
            if rate > 0:
                rates[currency] = 1 / rate  # 反转汇率

        return rates
    except Exception as e:
        print(f"Error fetching exchange rates: {e}")
        # 返回备用汇率（2024年4月大致汇率）
        return {
            'USD': 7.25, 'EUR': 7.85, 'GBP': 9.15, 'JPY': 0.048,
            'KRW': 0.0054, 'THB': 0.20, 'VND': 0.00029, 'PHP': 0.13,
            'MYR': 1.54, 'IDR': 0.00046, 'SGD': 5.38,
            'BHD': 19.23, 'DZD': 0.054, 'EGP': 0.15, 'KWD': 23.62,
            'LYD': 1.49, 'MAD': 0.72, 'OMR': 18.84, 'QAR': 1.99,
            'TND': 2.32, 'BGN': 4.01, 'CHF': 8.12,
            'BOB': 1.05, 'CRC': 0.014, 'GTQ': 0.93, 'HNL': 0.29,
            'NIO': 0.20, 'PEN': 1.94, 'PYG': 0.00098, 'UYU': 0.19,
            'ISK': 0.052, 'GEL': 2.71, 'MKD': 0.13, 'MDL': 0.41,
            'RON': 1.58, 'ALL': 0.077, 'UAH': 0.18,
        }


def convert_to_cny(price: Optional[float], currency: str, rates: Dict[str, float]) -> Optional[float]:
    """将价格转换为CNY"""
    if price is None or price == 0:
        return None

    if currency == 'CNY':
        return price

    rate = rates.get(currency)
    if rate is None:
        print(f"Warning: No exchange rate for {currency}")
        return None

    return round(price * rate, 2)


def process_prices():
    """处理价格数据，转换为CNY"""
    # 读取原始数据
    try:
        with open('xbox_gamepass_prices.json', 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print("Error: xbox_gamepass_prices.json not found. Run xbox_scraper.py first.")
        return

    # 获取汇率
    print("Fetching exchange rates...")
    rates = get_exchange_rates()
    print(f"✓ Got rates for {len(rates)} currencies")

    # 处理每个地区的数据
    processed_data = []

    for item in raw_data:
        region_code = item['region_code']
        currency = item['currency']

        processed_item = {
            'region_code': region_code,
            'currency': currency,
            'url': item['url'],
            'scraped_at': item['scraped_at'],
        }

        # 转换价格
        if 'intro_price' in item and item['intro_price']:
            processed_item['intro_price'] = item['intro_price']
            processed_item['intro_price_cny'] = convert_to_cny(item['intro_price'], currency, rates)

        if 'regular_price' in item and item['regular_price']:
            processed_item['regular_price'] = item['regular_price']
            processed_item['regular_price_cny'] = convert_to_cny(item['regular_price'], currency, rates)

        if 'auto_renew_price' in item and item['auto_renew_price']:
            processed_item['auto_renew_price'] = item['auto_renew_price']
            processed_item['auto_renew_price_cny'] = convert_to_cny(item['auto_renew_price'], currency, rates)

        # 保留原始字符串
        if 'intro_price_raw' in item:
            processed_item['intro_price_raw'] = item['intro_price_raw']
        if 'regular_price_raw' in item:
            processed_item['regular_price_raw'] = item['regular_price_raw']
        if 'auto_renew_price_raw' in item:
            processed_item['auto_renew_price_raw'] = item['auto_renew_price_raw']

        if 'error' in item:
            processed_item['error'] = item['error']

        processed_data.append(processed_item)

    # 保存处理后的数据
    output_file = 'xbox_gamepass_prices_processed.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)

    print(f"✓ Processed data saved to {output_file}")

    # 生成排行榜
    generate_ranking(processed_data)


def generate_ranking(data: list):
    """生成价格排行榜"""
    # 按自动续订价格排序（最常用的价格）
    valid_prices = [
        item for item in data
        if item.get('auto_renew_price_cny') is not None
    ]

    if not valid_prices:
        print("No valid prices to rank")
        return

    # 排序
    ranked = sorted(valid_prices, key=lambda x: x['auto_renew_price_cny'])

    print("\n" + "="*60)
    print("TOP 10 CHEAPEST REGIONS (Auto-Renew Price)")
    print("="*60)

    for i, item in enumerate(ranked[:10], 1):
        region = item['region_code']
        price_local = item['auto_renew_price']
        currency = item['currency']
        price_cny = item['auto_renew_price_cny']

        print(f"{i:2d}. {region:8s} {price_local:10.2f} {currency:4s} = ¥{price_cny:7.2f} CNY")

    # 保存排行榜到文件
    ranking_data = {
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'ranking': [
            {
                'rank': i,
                'region_code': item['region_code'],
                'currency': item['currency'],
                'auto_renew_price': item['auto_renew_price'],
                'auto_renew_price_cny': item['auto_renew_price_cny'],
            }
            for i, item in enumerate(ranked, 1)
        ]
    }

    with open('xbox_gamepass_ranking.json', 'w', encoding='utf-8') as f:
        json.dump(ranking_data, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Ranking saved to xbox_gamepass_ranking.json")


if __name__ == '__main__':
    process_prices()
