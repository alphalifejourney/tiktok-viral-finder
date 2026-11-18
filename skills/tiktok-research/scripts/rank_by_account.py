#!/usr/bin/env python3
"""
Rank TikTok videos by how far each one beat its OWN account's normal views.

multiple = video views / median views of that account's videos in the same scrape.
A big account's quiet day scores about 1x; a small account's breakout scores 50x+.
This is the main ranking for tiktok-research. analyze_posts.py (engagement rate vs
followers, pooled across all accounts) is still useful for topics, but it misses most
breakouts from small accounts.

Usage:
  python rank_by_account.py -i raw.json -o outliers-by-account.json [--min-multiple 2] [--min-videos 3]
"""

import argparse
import json
import statistics
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description="Rank TikToks against each account's own median views")
    ap.add_argument('--input', '-i', required=True, help='raw.json from fetch_tiktok.py')
    ap.add_argument('--output', '-o', required=True, help='output JSON ({"outliers": [...]})')
    ap.add_argument('--min-multiple', type=float, default=2.0, help='keep videos at or above this multiple (default 2)')
    ap.add_argument('--min-videos', type=int, default=3,
                    help='skip accounts with fewer videos than this; their median is not reliable (default 3)')
    args = ap.parse_args()

    with open(args.input, 'r', encoding='utf-8') as f:
        videos = json.load(f)

    by_account = {}
    for v in videos:
        by_account.setdefault(v.get('authorUsername') or 'unknown', []).append(v)

    ranked, skipped = [], []
    print(f"{'account':<24}{'videos':>7}{'median views':>14}{'followers':>12}")
    for account, vids in sorted(by_account.items()):
        views = [v.get('playCount') or 0 for v in vids]
        median = statistics.median(views) if views else 0
        followers = vids[0].get('authorFollowers') or 0
        print(f"@{account:<23}{len(vids):>7}{median:>14,.0f}{followers:>12,}")
        if len(vids) < args.min_videos or median <= 0:
            skipped.append(account)
            continue
        for v in vids:
            out = {k: val for k, val in v.items() if k != '_raw'}
            out['_account_median_views'] = median
            out['_multiple'] = round((v.get('playCount') or 0) / median, 2)
            ranked.append(out)

    ranked.sort(key=lambda v: v['_multiple'], reverse=True)
    outliers = [v for v in ranked if v['_multiple'] >= args.min_multiple]

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({
            'method': "views / the account's own median views in this scrape",
            'min_multiple': args.min_multiple,
            'total_videos': len(videos),
            'accounts_skipped_too_few_videos': skipped,
            'outlier_count': len(outliers),
            'outliers': outliers,
        }, f, indent=2, default=str)

    print(f"\nTop by own-account multiple (>= {args.min_multiple}x): {len(outliers)} of {len(videos)} videos")
    for v in outliers[:10]:
        hook = (v.get('text') or '').split('\n')[0][:70]
        print(f"{v['_multiple']:>7.1f}x  @{v.get('authorUsername')}  {v.get('playCount') or 0:>10,} views  {hook!r}")
    if skipped:
        print(f"Skipped (fewer than {args.min_videos} videos): {', '.join('@' + a for a in skipped)}")
    print(f"Saved: {args.output}")


if __name__ == '__main__':
    main()
