import json
import os
from datetime import datetime
from typing import Dict, List, Any


def load_json(filepath: str) -> Any:
    """加载JSON文件"""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def detect_price_changes() -> Dict[str, Any]:
    """检测价格变化"""
    # 读取当前价格
    current_data = load_json('xbox_gamepass_prices_processed.json')
    if not current_data:
        print("No current price data found")
        return {'changes': [], 'summary': {}}

    # 查找最近的历史数据
    archive_dir = 'archive'
    if not os.path.exists(archive_dir):
        print("No archive directory found, this might be the first run")
        return {'changes': [], 'summary': {}}

    # 获取最新的归档文件
    archive_files = sorted([f for f in os.listdir(archive_dir) if f.startswith('xbox_gamepass_prices_') and f.endswith('.json')])

    if not archive_files:
        print("No previous data found in archive")
        return {'changes': [], 'summary': {}}

    # 读取最新的历史数据
    latest_archive = os.path.join(archive_dir, archive_files[-1])
    previous_data = load_json(latest_archive)

    if not previous_data:
        print("Could not load previous data")
        return {'changes': [], 'summary': {}}

    # 创建价格映射
    previous_prices = {
        item['region_code']: item
        for item in previous_data
    }

    # 检测变化
    changes = []

    for current_item in current_data:
        region = current_item['region_code']
        previous_item = previous_prices.get(region)

        if not previous_item:
            # 新增的地区
            if current_item.get('auto_renew_price_cny'):
                changes.append({
                    'region': region,
                    'type': 'new',
                    'price_type': 'auto_renew',
                    'new_price_cny': current_item['auto_renew_price_cny'],
                })
            continue

        # 检查自动续订价格变化
        if current_item.get('auto_renew_price_cny') and previous_item.get('auto_renew_price_cny'):
            current_price = current_item['auto_renew_price_cny']
            previous_price = previous_item['auto_renew_price_cny']

            if abs(current_price - previous_price) > 0.01:  # 避免浮点数误差
                change_percent = ((current_price - previous_price) / previous_price) * 100
                changes.append({
                    'region': region,
                    'type': 'price_change',
                    'price_type': 'auto_renew',
                    'previous_price_cny': previous_price,
                    'new_price_cny': current_price,
                    'change_percent': round(change_percent, 2),
                    'direction': 'increase' if current_price > previous_price else 'decrease',
                })

        # 检查常规价格变化
        if current_item.get('regular_price_cny') and previous_item.get('regular_price_cny'):
            current_price = current_item['regular_price_cny']
            previous_price = previous_item['regular_price_cny']

            if abs(current_price - previous_price) > 0.01:
                change_percent = ((current_price - previous_price) / previous_price) * 100
                changes.append({
                    'region': region,
                    'type': 'price_change',
                    'price_type': 'regular',
                    'previous_price_cny': previous_price,
                    'new_price_cny': current_price,
                    'change_percent': round(change_percent, 2),
                    'direction': 'increase' if current_price > previous_price else 'decrease',
                })

    # 生成摘要
    summary = {
        'total_changes': len(changes),
        'price_increases': len([c for c in changes if c.get('direction') == 'increase']),
        'price_decreases': len([c for c in changes if c.get('direction') == 'decrease']),
        'new_regions': len([c for c in changes if c['type'] == 'new']),
        'detected_at': datetime.utcnow().isoformat() + 'Z',
    }

    result = {
        'changes': changes,
        'summary': summary,
    }

    # 保存变化检测结果
    with open('xbox_price_changes_latest.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print("\n" + "="*60)
    print("PRICE CHANGE DETECTION")
    print("="*60)
    print(f"Total changes detected: {summary['total_changes']}")
    print(f"  - Price increases: {summary['price_increases']}")
    print(f"  - Price decreases: {summary['price_decreases']}")
    print(f"  - New regions: {summary['new_regions']}")

    if changes:
        print("\nDetailed changes:")
        for change in changes:
            if change['type'] == 'new':
                print(f"  [NEW] {change['region']}: ¥{change['new_price_cny']:.2f} CNY")
            else:
                direction_symbol = "↑" if change['direction'] == 'increase' else "↓"
                print(f"  [{change['region']}] {change['price_type']}: "
                      f"¥{change['previous_price_cny']:.2f} → ¥{change['new_price_cny']:.2f} "
                      f"({direction_symbol} {abs(change['change_percent']):.1f}%)")

    return result


def generate_changelog():
    """生成changelog"""
    changes_data = load_json('xbox_price_changes_latest.json')

    if not changes_data or not changes_data['changes']:
        print("\nNo changes to add to changelog")
        return

    # 读取现有的changelog
    changelog_file = 'CHANGELOG.md'
    if os.path.exists(changelog_file):
        with open(changelog_file, 'r', encoding='utf-8') as f:
            existing_changelog = f.read()
    else:
        existing_changelog = "# Changelog\n\nAll notable price changes will be documented in this file.\n\n"

    # 生成新的changelog条目
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    new_entry = f"## {timestamp}\n\n"

    summary = changes_data['summary']
    new_entry += f"**Summary:** {summary['total_changes']} changes detected\n\n"

    if summary['price_increases'] > 0:
        new_entry += f"- 📈 {summary['price_increases']} price increase(s)\n"
    if summary['price_decreases'] > 0:
        new_entry += f"- 📉 {summary['price_decreases']} price decrease(s)\n"
    if summary['new_regions'] > 0:
        new_entry += f"- 🆕 {summary['new_regions']} new region(s)\n"

    new_entry += "\n### Details\n\n"

    for change in changes_data['changes']:
        if change['type'] == 'new':
            new_entry += f"- **{change['region']}** (NEW): ¥{change['new_price_cny']:.2f} CNY\n"
        else:
            direction = "increased" if change['direction'] == 'increase' else "decreased"
            emoji = "📈" if change['direction'] == 'increase' else "📉"
            new_entry += (f"- {emoji} **{change['region']}** ({change['price_type']}): "
                         f"¥{change['previous_price_cny']:.2f} → ¥{change['new_price_cny']:.2f} "
                         f"({change['change_percent']:+.1f}%)\n")

    new_entry += "\n---\n\n"

    # 插入新条目到changelog开头（在标题之后）
    lines = existing_changelog.split('\n')
    header_end = 0
    for i, line in enumerate(lines):
        if line.startswith('## ') or (i > 0 and not line.startswith('#')):
            header_end = i
            break

    new_changelog = '\n'.join(lines[:header_end]) + '\n\n' + new_entry + '\n'.join(lines[header_end:])

    # 保存changelog
    with open(changelog_file, 'w', encoding='utf-8') as f:
        f.write(new_changelog)

    print(f"\n✓ Changelog updated: {changelog_file}")

    # 同时保存带时间戳的changelog到archive
    timestamp_file = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    archive_changelog = f'archive/changelog_{timestamp_file}.md'

    with open(archive_changelog, 'w', encoding='utf-8') as f:
        f.write(new_entry)

    print(f"✓ Archived changelog: {archive_changelog}")


if __name__ == '__main__':
    # 检测价格变化
    detect_price_changes()

    # 生成changelog
    generate_changelog()
