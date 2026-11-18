---
name: tiktok-research
description: |
  Find the TikToks that are really going viral in your niche: scrape the accounts you track with Apify,
  rank every video against its own account's normal views (a 6K-follower account at 150x beats a big
  account's quiet day), have Gemini watch the top ones, and write a report with replicable hook formulas.

  Use when asked to:
  - Find trending or viral TikTok content in a niche
  - Research what's performing on TikTok, or analyze competitors' TikToks
  - Identify high-performing video patterns or hook formulas
  - Generate content ideas from TikTok trends

  Triggers: "tiktok research", "tt research", "find trending tiktoks", "find viral tiktoks", "analyze tiktok accounts",
  "what's working on tiktok", "content research tiktok", "tiktok analysis", "tiktok trends"
---

# TikTok Research

Find outlier TikToks in the accounts you track, rank them against each account's own normal, and pull out the hooks and structure that made them work.

## Before you start

Check every item below before doing anything else. If any is missing, STOP and tell the user what is missing and how to add it.

| Needs | Check | How to add if missing |
|---|---|---|
| Claude Code (runs Python on your computer) | you are in Claude Code | This skill does not work in the Claude website or phone app |
| Python 3.10+ | `python --version` (`python3` on macOS/Linux) | Install from python.org |
| Python packages | verify script below | `python -m pip install -r ~/.claude/skills/tiktok-research/requirements.txt` |
| `yt-dlp` on PATH (downloads the top videos so Gemini can watch them) | `yt-dlp --version` | `python -m pip install yt-dlp` |
| `APIFY_TOKEN` env var | verify script below | apify.com → Settings → API & Integrations → Personal API token. The free plan includes $5 of credit a month; a scan of 9 accounts × 10 videos cost about $0.41. Set it as an environment variable (Windows: `setx APIFY_TOKEN "..."`, then restart Claude Code) or put it in a `.env` file in the folder you run from |
| `GEMINI_API_KEY` env var (only for step 4) | verify script below | aistudio.google.com → Get API key. The free tier allows about 20 video analyses a day per model, and retries count |
| Accounts to track | `~/.claude/skills/tiktok-research/tiktok-accounts.md` has real `@handles`, not only `@example` | Ask the user for 6-12 accounts (4 same niche, 4 nearby niche with the same audience, 2-4 bigger ones for format only) and add them to the table |

The user sets both keys on their own computer. Do not request them in the chat.

Verify setup:
```bash
python -c "
import os
try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass
from apify_client import ApifyClient
from google import genai
assert os.environ.get('APIFY_TOKEN'), 'APIFY_TOKEN not set'
assert os.environ.get('GEMINI_API_KEY'), 'GEMINI_API_KEY not set (only needed for step 4)'
" && echo "Prerequisites OK"
```

Windows notes: run Python with `PYTHONUTF8=1`. If `APIFY_TOKEN` was set with `setx` after this Claude Code session started, the session can't see it yet: restart Claude Code, or in Git Bash load it with
`export APIFY_TOKEN=$(powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('APIFY_TOKEN','User')" | tr -d '\r')`.

## Workflow

### 0. No accounts yet? Find some from hashtags (optional, costs credit)

```bash
python ~/.claude/skills/tiktok-research/scripts/find_accounts.py --hashtags aieducation claudecode \
  --per-hashtag 40 --min-followers 1000 --max-followers 500000 -o tiktok-research/candidates.json
```

It lists the creators behind each hashtag's top videos with followers and best views. Show the user the ones that fit their niche (some hashtags are noisy: #aitraining is mostly "get paid to train AI" job content) and add the chosen handles to `tiktok-accounts.md`. Aim for accounts within about 10x of the user's own follower count, plus 2-4 bigger ones.

### 1. Create a run folder

```bash
RUN_FOLDER="tiktok-research/$(date +%Y-%m-%d_%H%M%S)" && mkdir -p "$RUN_FOLDER" && echo "$RUN_FOLDER"
```

### 2. Fetch videos (Apify, costs credit)

Tell the user roughly what it costs before the first run (about $0.05 per 10 videos per account at Apify's current rates). Use `--limit 10` or more: the ranking needs at least 10 videos per account to be reliable (accounts under 5 are skipped, under 10 get a warning).

```bash
python ~/.claude/skills/tiktok-research/scripts/fetch_tiktok.py --days 30 --limit 10 --output "$RUN_FOLDER/raw.json"
```

- `--days`: days back (default 30) · `--limit`: max videos per account (default 50) · `--sorting`: latest | popular | oldest
- `--usernames a b c`: override the accounts file

### 3. Rank against each account's own normal (main ranking)

```bash
python ~/.claude/skills/tiktok-research/scripts/rank_by_account.py -i "$RUN_FOLDER/raw.json" -o "$RUN_FOLDER/outliers-by-account.json"
```

`multiple = views / that account's median views`. Above 3x is a signal; under 1.5x is that account's normal day, however big the number looks. Accounts with fewer than 5 videos in the window are skipped and accounts under 10 get a warning (their median is shaky).

Optional, for hashtags / sounds / keywords:
```bash
python ~/.claude/skills/tiktok-research/scripts/analyze_posts.py -i "$RUN_FOLDER/raw.json" -o "$RUN_FOLDER/outliers.json"
```
(Its outlier list uses engagement rate vs followers pooled across all accounts, which misses most small-account breakouts. Use it for `topics` only.)

### 4. Have Gemini watch the top videos

```bash
python ~/.claude/skills/video-content-analyzer/scripts/analyze_videos.py \
  -i "$RUN_FOLDER/outliers-by-account.json" -o "$RUN_FOLDER/video-analysis.json" -p tiktok -n 3
```

Each video is downloaded with yt-dlp and uploaded to Gemini (deleted after). It extracts the hook and a replicable formula, the structure, pacing, delivery and CTA. Results are added to `video-analysis.json`, never overwritten: videos already analyzed are skipped, so after a quota stop just run the same command again the next day. On a 503 (overloaded) it retries; on a used-up daily quota (429) it stops at once. If no analysis ran, say so and write the report from the numbers and captions.

### 5. Write the report

Read `outliers-by-account.json` (and `video-analysis.json`, `outliers.json` if present), then write `$RUN_FOLDER/report.md`:

```markdown
# TikTok Research Report
Generated: {date} · {accounts} accounts · {videos} videos · last {days} days

## Top outliers (views ÷ the account's own median)
| x own median | Account | Views | Saves | Length | Hook (first caption line) |

## Top performing hooks   (from video-analysis.json, if it ran)
### Hook 1: {technique} - @{username}
- Opening: "{opening_line}"
- Why it works: {attention_grab}
- Replicable formula: {replicable_formula}
- [Watch]({webVideoUrl})

## Content structure patterns
| Video | Format | Pacing | Retention techniques |

## CTA strategies
| Video | CTA type | CTA text | Placement |

## Patterns
[4-7 patterns across the outliers: hook type, length, sound, saves vs likes, topics]

## Hook formulas to reuse
[templates with blanks, e.g. "Keep using [tool] for free, even past [limit]"]

## Video ideas for the user
[3-5 ideas that fit the user's own niche]

## Accounts analyzed
[list, with median views and followers; note any skipped]
```

Lead with the outliers table and the hook formulas. Quote at most the first caption line of other creators' videos.

## Quick reference

```bash
RUN_FOLDER="tiktok-research/$(date +%Y-%m-%d_%H%M%S)" && mkdir -p "$RUN_FOLDER" && \
python ~/.claude/skills/tiktok-research/scripts/fetch_tiktok.py --limit 10 -o "$RUN_FOLDER/raw.json" && \
python ~/.claude/skills/tiktok-research/scripts/rank_by_account.py -i "$RUN_FOLDER/raw.json" -o "$RUN_FOLDER/outliers-by-account.json" && \
python ~/.claude/skills/video-content-analyzer/scripts/analyze_videos.py -i "$RUN_FOLDER/outliers-by-account.json" -o "$RUN_FOLDER/video-analysis.json" -p tiktok -n 3
```

## TikTok fields

`diggCount` likes · `shareCount` shares · `playCount` views · `commentCount` comments · `collectCount` saves · `authorFollowers` followers · `musicName` sound · `musicOriginal` original sound or not.
