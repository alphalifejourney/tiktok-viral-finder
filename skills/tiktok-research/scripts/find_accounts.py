#!/usr/bin/env python3
"""
Find TikTok accounts worth tracking, starting from hashtags (Apify TikTok Scraper).

Pulls the top videos for each hashtag, groups them by creator, and lists the creators
with follower count, how many of their videos showed up, and their best views. Use it
to fill tiktok-accounts.md with accounts near your own size (followers within ~10x).

Costs Apify credit (about $0.05 per 10 videos at current rates).

Usage:
  python find_accounts.py --hashtags aitraining aieducation --per-hashtag 40 \
      [--min-followers 1000] [--max-followers 500000] -o candidates.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from apify_client import ApifyClient
except ImportError:
    print("Error: apify-client not installed. Run: pip install apify-client")
    sys.exit(1)

ACTOR = "GdWCkxBtKWOsKjdch"  # clockworks/tiktok-scraper


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description='Find TikTok creators to track from hashtags')
    ap.add_argument('--hashtags', nargs='+', required=True, help='hashtags without #')
    ap.add_argument('--per-hashtag', type=int, default=40, help='videos per hashtag (default 40)')
    ap.add_argument('--min-followers', type=int, default=1000)
    ap.add_argument('--max-followers', type=int, default=500000)
    ap.add_argument('--output', '-o', required=True)
    args = ap.parse_args()

    token = os.environ.get('APIFY_TOKEN')
    if not token:
        print("Error: APIFY_TOKEN environment variable not set")
        sys.exit(1)
    client = ApifyClient(token)
    tags = [h.lstrip('#') for h in args.hashtags]
    print(f"Fetching up to {args.per_hashtag} videos for: {', '.join('#' + t for t in tags)}")
    run = client.actor(ACTOR).call(run_input={
        "hashtags": tags,
        "resultsPerPage": args.per_hashtag,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
    })
    dataset_id = run["defaultDatasetId"] if isinstance(run, dict) else run.default_dataset_id
    cost = (run.get('usageTotalUsd') if isinstance(run, dict) else getattr(run, 'usage_total_usd', None))

    creators = {}
    for item in client.dataset(dataset_id).iterate_items():
        a = item.get('authorMeta', {}) or {}
        name = a.get('name')
        if not name:
            continue
        c = creators.setdefault(name, {
            'username': name, 'nickname': a.get('nickName', ''), 'followers': a.get('fans', 0) or 0,
            'total_likes': a.get('heart', 0) or 0, 'videos_on_account': a.get('video', 0) or 0,
            'bio': (a.get('signature') or '').replace('\n', ' ')[:120],
            'hits': 0, 'best_views': 0, 'best_video': '', 'best_hook': '', 'hashtags_seen': set(),
        })
        c['hits'] += 1
        views = item.get('playCount', 0) or 0
        if views > c['best_views']:
            c['best_views'] = views
            c['best_video'] = item.get('webVideoUrl', '')
            c['best_hook'] = (item.get('text') or '').split('\n')[0][:90]
        for h in item.get('hashtags', []) or []:
            n = h.get('name') if isinstance(h, dict) else str(h)
            if n and n.lower() in tags:
                c['hashtags_seen'].add(n.lower())

    rows = [dict(c, hashtags_seen=sorted(c['hashtags_seen'])) for c in creators.values()]
    keep = [r for r in rows if args.min_followers <= r['followers'] <= args.max_followers]
    keep.sort(key=lambda r: (r['best_views'] / max(r['followers'], 1)), reverse=True)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({'hashtags': tags, 'apify_cost_usd': cost, 'creators_found': len(rows),
                   'in_follower_range': keep}, f, indent=2)

    print(f"{len(rows)} creators found, {len(keep)} with {args.min_followers:,}-{args.max_followers:,} followers"
          + (f" · Apify cost ${cost:.2f}" if cost else ""))
    print(f"{'account':<26}{'followers':>11}{'best views':>12}{'hits':>6}  best hook")
    for r in keep[:30]:
        print(f"@{r['username']:<25}{r['followers']:>11,}{r['best_views']:>12,}{r['hits']:>6}  {r['best_hook'][:60]!r}")
    print(f"Saved: {args.output}\nAdd the ones that fit your niche to tiktok-accounts.md.")


if __name__ == '__main__':
    main()
