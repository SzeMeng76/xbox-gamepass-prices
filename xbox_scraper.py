import asyncio
import re
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

# 设置UTF-8编码
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# 支持的地区列表
REGIONS = [
    'ar-BH', 'ar-DZ', 'ar-EG', 'ar-KW', 'ar-LY', 'ar-MA', 'ar-OM', 'ar-QA',
    'ar-TN', 'bg-BG', 'de-LI', 'de-LU', 'en-CY', 'en-MY', 'en-PH', 'en-US',
    'es-BO', 'es-CR', 'es-EC', 'es-GT', 'es-HN', 'es-NI', 'es-PA', 'es-PE',
    'es-PY', 'es-SV', 'es-UY', 'et-EE', 'fr-LU', 'hr-HR', 'id-ID', 'is-IS',
    'ka-GE', 'lt-LT', 'lv-LV', 'mk-MK', 'mt-MT', 'ro-MD', 'ro-RO', 'sl-SL',
    'sq-AL', 'th-TH', 'uk-UA', 'vi-VN',
]

# 地区到货币的映射
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


def clean_price(price_str: str) -> Optional[float]:
    """清理价格字符串，转换为浮点数"""
    if not price_str:
        return None

    # 移除货币符号和空格
    cleaned = re.sub(r'[^\d.,]', '', price_str)

    # 处理不同的数字格式
    # 1.234,56 -> 1234.56
    # 1,234.56 -> 1234.56
    if ',' in cleaned and '.' in cleaned:
        if cleaned.rindex(',') > cleaned.rindex('.'):
            # 欧洲格式: 1.234,56
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            # 美国格式: 1,234.56
            cleaned = cleaned.replace(',', '')
    elif ',' in cleaned:
        # 可能是欧洲格式的小数点
        if cleaned.count(',') == 1 and len(cleaned.split(',')[1]) == 2:
            cleaned = cleaned.replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')

    try:
        return float(cleaned)
    except:
        return None


async def fetch_xbox_price(region_code: str) -> Dict[str, Any]:
    """获取指定地区的Xbox Game Pass PC价格"""
    url = f"https://www.xbox.com/{region_code}/xbox-game-pass/pc-game-pass"
    currency = REGION_CURRENCY.get(region_code, 'USD')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            print(f"[{region_code}] Fetching...")

            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(3000)

            html = await page.content()

            result = {
                'region_code': region_code,
                'currency': currency,
                'url': url,
                'intro_price_raw': None,
                'regular_price_raw': None,
                'auto_renew_price_raw': None,
                'intro_price': None,
                'regular_price': None,
                'auto_renew_price': None,
                'scraped_at': datetime.utcnow().isoformat() + 'Z',
            }

            # 查找所有价格（通用模式）
            price_pattern = r'(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)'

            # 模式1: 查找 "for X, then Y" 或 "với X, sau đó là Y"
            intro_patterns = [
                rf'for\s*[^\d]*{price_pattern}[^,]*,?\s*then\s*[^\d]*{price_pattern}',
                rf'với\s*{price_pattern}[^,]*,?\s*sau đó là\s*{price_pattern}',
            ]

            for pattern in intro_patterns:
                matches = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if matches:
                    result['intro_price_raw'] = matches.group(1)
                    result['regular_price_raw'] = matches.group(2)
                    result['intro_price'] = clean_price(matches.group(1))
                    result['regular_price'] = clean_price(matches.group(2))
                    break

            # 模式2: 查找自动续订价格
            auto_patterns = [
                rf'mức phí\s*{price_pattern}[^/]*/tháng',  # 越南语
                rf'at\s*[^\d]*{price_pattern}\s*/\s*month',  # 英语
                rf'renew.*?at\s*[^\d]*{price_pattern}',  # 英语变体
            ]

            for pattern in auto_patterns:
                auto_match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if auto_match:
                    result['auto_renew_price_raw'] = auto_match.group(1)
                    result['auto_renew_price'] = clean_price(auto_match.group(1))
                    break

            # 打印结果
            if result['intro_price'] or result['regular_price'] or result['auto_renew_price']:
                prices = []
                if result['intro_price']:
                    prices.append(f"intro={result['intro_price']}")
                if result['regular_price']:
                    prices.append(f"regular={result['regular_price']}")
                if result['auto_renew_price']:
                    prices.append(f"auto={result['auto_renew_price']}")
                print(f"[{region_code}] ✓ {', '.join(prices)}")
            else:
                print(f"[{region_code}] ✗ No prices found")

            return result

        except Exception as e:
            print(f"[{region_code}] ✗ Error: {e}")
            return {
                'region_code': region_code,
                'currency': currency,
                'url': url,
                'error': str(e),
                'scraped_at': datetime.utcnow().isoformat() + 'Z',
            }
        finally:
            await browser.close()


async def main():
    """主函数：爬取所有地区的价格"""
    print(f"Starting to scrape {len(REGIONS)} regions...\n")

    results = []

    # 逐个爬取
    for region in REGIONS:
        result = await fetch_xbox_price(region)
        results.append(result)

        # 延迟避免请求过快
        await asyncio.sleep(2)

    # 保存结果
    output_file = 'xbox_gamepass_prices.json'

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Completed! Results saved to {output_file}")

    # 统计
    success_count = sum(1 for r in results if r.get('intro_price') or r.get('regular_price') or r.get('auto_renew_price'))
    print(f"Successfully scraped: {success_count}/{len(results)} regions")


if __name__ == '__main__':
    asyncio.run(main())
