import json
import os
from datetime import datetime


def update_readme_with_ranking():
    """更新README中的价格排行榜"""
    # 读取排行榜数据
    ranking_file = 'xbox_gamepass_ranking.json'
    if not os.path.exists(ranking_file):
        print("Ranking file not found")
        return

    with open(ranking_file, 'r', encoding='utf-8') as f:
        ranking_data = json.load(f)

    # 读取README
    readme_file = 'README.md'
    with open(readme_file, 'r', encoding='utf-8') as f:
        readme_content = f.read()

    # 生成排行榜表格
    top_10 = ranking_data['ranking'][:10]

    table = "| Rank | Region | Price (Local) | Price (CNY) |\n"
    table += "|------|--------|---------------|-------------|\n"

    for item in top_10:
        rank = item['rank']
        region = item['region_code']
        price_local = item['auto_renew_price']
        currency = item['currency']
        price_cny = item['auto_renew_price_cny']

        table += f"| {rank} | {region} | {price_local:.2f} {currency} | ¥{price_cny:.2f} |\n"

    # 添加更新时间
    updated_at = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    table += f"\n*Last updated: {updated_at}*\n"

    # 替换README中的排行榜部分
    # 查找 "## Price Ranking" 到下一个 "##" 之间的内容
    lines = readme_content.split('\n')
    new_lines = []
    in_ranking_section = False
    skip_until_next_section = False

    for line in lines:
        if line.startswith('## Price Ranking'):
            in_ranking_section = True
            skip_until_next_section = True
            new_lines.append(line)
            new_lines.append('')
            new_lines.append('The cheapest regions for Xbox Game Pass PC (auto-renew price):')
            new_lines.append('')
            new_lines.append(table)
            continue

        if skip_until_next_section:
            if line.startswith('## ') and not line.startswith('## Price Ranking'):
                skip_until_next_section = False
                in_ranking_section = False
                new_lines.append(line)
            continue

        new_lines.append(line)

    # 保存更新后的README
    new_readme = '\n'.join(new_lines)

    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(new_readme)

    print(f"✓ README updated with top 10 ranking")


def update_readme_stats():
    """更新README中的统计信息"""
    # 读取处理后的数据
    processed_file = 'xbox_gamepass_prices_processed.json'
    if not os.path.exists(processed_file):
        return

    with open(processed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 统计
    total_regions = len(data)
    regions_with_prices = len([d for d in data if d.get('auto_renew_price_cny')])

    # 找到最便宜和最贵的地区
    valid_prices = [d for d in data if d.get('auto_renew_price_cny')]

    if valid_prices:
        cheapest = min(valid_prices, key=lambda x: x['auto_renew_price_cny'])
        most_expensive = max(valid_prices, key=lambda x: x['auto_renew_price_cny'])

        print(f"\nStatistics:")
        print(f"  Total regions: {total_regions}")
        print(f"  Regions with prices: {regions_with_prices}")
        print(f"  Cheapest: {cheapest['region_code']} (¥{cheapest['auto_renew_price_cny']:.2f})")
        print(f"  Most expensive: {most_expensive['region_code']} (¥{most_expensive['auto_renew_price_cny']:.2f})")


if __name__ == '__main__':
    update_readme_with_ranking()
    update_readme_stats()
