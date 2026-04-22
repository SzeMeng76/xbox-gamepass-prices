import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


def load_json(filepath: str) -> Any:
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None


def _plan_prices(region: Dict) -> Dict[str, Dict]:
    """Return {plan_name: {auto_renew_price_cny, regular_price_cny}} for a processed region."""
    result = {}
    for plan in region.get('plans', []):
        name = plan.get('plan', '')
        result[name] = {
            'auto_renew_price_cny': plan.get('auto_renew_price_cny'),
            'regular_price_cny': plan.get('regular_price_cny'),
        }
    return result


def detect_price_changes() -> Dict[str, Any]:
    current_data = load_json('xbox_gamepass_prices_processed.json')
    if not current_data:
        print("No current price data found")
        return {'changes': [], 'summary': {}}

    archive_dir = 'archive'
    if not os.path.exists(archive_dir):
        print("No archive directory found, this might be the first run")
        return {'changes': [], 'summary': {}}

    archive_files = sorted([
        f for f in os.listdir(archive_dir)
        if f.startswith('xbox_gamepass_prices_') and f.endswith('.json')
    ])

    if not archive_files:
        print("No previous data found in archive")
        return {'changes': [], 'summary': {}}

    latest_archive = os.path.join(archive_dir, archive_files[-1])
    previous_raw = load_json(latest_archive)
    if not previous_raw:
        print("Could not load previous data")
        return {'changes': [], 'summary': {}}

    # previous_raw is the raw scrape file (list), current is processed (has 'regions' key)
    current_regions = {r['region_code']: r for r in current_data.get('regions', [])}

    # Build previous plan prices from raw scrape data
    # Raw format: list of {region_code, plans: [{plan, auto_renew_price, ...}]}
    previous_regions: Dict[str, Dict] = {}
    if isinstance(previous_raw, list):
        for item in previous_raw:
            rc = item.get('region_code', '')
            previous_regions[rc] = item
    elif isinstance(previous_raw, dict):
        for item in previous_raw.get('regions', []):
            rc = item.get('region_code', '')
            previous_regions[rc] = item

    changes = []

    for region_code, current in current_regions.items():
        previous = previous_regions.get(region_code)
        currency = current.get('currency', '')

        current_plans = _plan_prices(current)

        if not previous:
            for plan_name, prices in current_plans.items():
                cny = prices.get('auto_renew_price_cny') or prices.get('regular_price_cny')
                if cny is not None:
                    changes.append({
                        'region': region_code,
                        'plan': plan_name,
                        'type': 'new',
                        'new_price_cny': cny,
                    })
            continue

        previous_plans = _plan_prices(previous)

        for plan_name, cur_prices in current_plans.items():
            prev_prices = previous_plans.get(plan_name, {})
            for price_key in ('auto_renew_price_cny', 'regular_price_cny'):
                cur_val = cur_prices.get(price_key)
                prev_val = prev_prices.get(price_key)
                if cur_val is None or prev_val is None:
                    continue
                if abs(cur_val - prev_val) > 0.01:
                    pct = ((cur_val - prev_val) / prev_val) * 100
                    changes.append({
                        'region': region_code,
                        'plan': plan_name,
                        'type': 'price_change',
                        'price_type': price_key.replace('_cny', ''),
                        'previous_price_cny': prev_val,
                        'new_price_cny': cur_val,
                        'change_percent': round(pct, 2),
                        'direction': 'increase' if cur_val > prev_val else 'decrease',
                    })

    summary = {
        'total_changes': len(changes),
        'price_increases': len([c for c in changes if c.get('direction') == 'increase']),
        'price_decreases': len([c for c in changes if c.get('direction') == 'decrease']),
        'new_regions': len([c for c in changes if c['type'] == 'new']),
        'detected_at': datetime.utcnow().isoformat() + 'Z',
    }

    result = {'changes': changes, 'summary': summary}

    with open('xbox_price_changes_latest.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print("PRICE CHANGE DETECTION")
    print("=" * 60)
    print(f"Total changes detected: {summary['total_changes']}")
    print(f"  - Price increases: {summary['price_increases']}")
    print(f"  - Price decreases: {summary['price_decreases']}")
    print(f"  - New regions: {summary['new_regions']}")

    if changes:
        print("\nDetailed changes:")
        for change in changes:
            plan = change.get('plan', '')
            if change['type'] == 'new':
                print(f"  [NEW] {change['region']} / {plan}: ¥{change['new_price_cny']:.2f} CNY")
            else:
                sym = "↑" if change['direction'] == 'increase' else "↓"
                print(f"  [{change['region']}] {plan} {change['price_type']}: "
                      f"¥{change['previous_price_cny']:.2f} → ¥{change['new_price_cny']:.2f} "
                      f"({sym} {abs(change['change_percent']):.1f}%)")

    return result


def generate_changelog():
    changes_data = load_json('xbox_price_changes_latest.json')
    if not changes_data or not changes_data['changes']:
        print("\nNo changes to add to changelog")
        return

    changelog_file = 'CHANGELOG.md'
    if os.path.exists(changelog_file):
        with open(changelog_file, 'r', encoding='utf-8') as f:
            existing_changelog = f.read()
    else:
        existing_changelog = "# Changelog\n\nAll notable price changes will be documented in this file.\n\n"

    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')
    summary = changes_data['summary']
    new_entry = f"## {timestamp}\n\n"
    new_entry += f"**Summary:** {summary['total_changes']} changes detected\n\n"
    if summary['price_increases'] > 0:
        new_entry += f"- {summary['price_increases']} price increase(s)\n"
    if summary['price_decreases'] > 0:
        new_entry += f"- {summary['price_decreases']} price decrease(s)\n"
    if summary['new_regions'] > 0:
        new_entry += f"- {summary['new_regions']} new region(s)\n"
    new_entry += "\n### Details\n\n"

    for change in changes_data['changes']:
        plan = change.get('plan', '')
        if change['type'] == 'new':
            new_entry += f"- **{change['region']}** / {plan} (NEW): ¥{change['new_price_cny']:.2f} CNY\n"
        else:
            direction = "increased" if change['direction'] == 'increase' else "decreased"
            arrow = "up" if change['direction'] == 'increase' else "down"
            new_entry += (f"- **{change['region']}** / {plan} ({change['price_type']}) {direction}: "
                          f"¥{change['previous_price_cny']:.2f} → ¥{change['new_price_cny']:.2f} "
                          f"({change['change_percent']:+.1f}%)\n")

    new_entry += "\n---\n\n"

    lines = existing_changelog.split('\n')
    header_end = 0
    for i, line in enumerate(lines):
        if line.startswith('## ') or (i > 0 and not line.startswith('#')):
            header_end = i
            break

    new_changelog = '\n'.join(lines[:header_end]) + '\n\n' + new_entry + '\n'.join(lines[header_end:])
    with open(changelog_file, 'w', encoding='utf-8') as f:
        f.write(new_changelog)
    print(f"\nChangelog updated: {changelog_file}")

    timestamp_file = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    archive_changelog = f'archive/changelog_{timestamp_file}.md'
    with open(archive_changelog, 'w', encoding='utf-8') as f:
        f.write(new_entry)
    print(f"Archived changelog: {archive_changelog}")


if __name__ == '__main__':
    detect_price_changes()
    generate_changelog()
