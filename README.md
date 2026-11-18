# 🔎 TikTok Viral Finder

**Stop copying TikToks by their view count. Find the ones that really went viral, and the hook each one used.**

A free Claude Code skill. Give Claude the TikTok accounts in your niche and say **"run tiktok research"**. It scrapes their recent videos, ranks every video against **its own account's normal views**, has Gemini watch the top ones, and writes a report with hook formulas you can reuse.

Why "its own normal": a big account getting 2 million views on a quiet day teaches you nothing. A 6,000-follower account getting 500,000 views found something you can copy.

---

## What a real run found

First scan, 9 AI/automation accounts, last 30 days, 10 videos each:

| | |
|---|---|
| Videos scanned | 81 |
| Cost | $0.41 of Apify credit |
| Top video | 501,800 views from an account with 6,294 followers: **150x** its normal |
| Next | 120x, 57x, 27x, 18x |

The big account in the list (156K followers) had nothing above 5x.

---

## What it does

| Step | What happens |
|---|---|
| 1. Accounts | You list 6-12 TikTok accounts in `tiktok-accounts.md` (or ask Claude to add them) |
| 2. Fetch | Apify's TikTok scraper pulls their recent videos with views, likes, saves, shares, sound and caption |
| 3. Rank | `rank_by_account.py`: each video's views ÷ that account's median views. Above 3x is a signal |
| 4. Watch | Gemini watches the top 3-5 videos: hook, replicable formula, structure, pacing, delivery, call to action |
| 5. Report | `report.md`: outliers table, hook formulas, patterns, video ideas for your niche |

---

## Before you start

| You need | Where to get it |
|---|---|
| **Claude Code** (it runs Python on your computer; the Claude website and phone app can't) | claude.com/claude-code |
| Python 3.10+ | python.org |
| An **Apify** API token | apify.com → Settings → API & Integrations. The free plan includes $5 of credit a month |
| A **Gemini** API key (for step 4 only) | aistudio.google.com → Get API key. The free tier allows about 20 video analyses a day |

Set both keys as environment variables yourself (`APIFY_TOKEN`, `GEMINI_API_KEY`), never in the chat. On Windows: `setx APIFY_TOKEN "your-token"`, then restart Claude Code.

## Install

Open Claude Code and say:

> Install this skill for me: https://github.com/alphalifejourney/tiktok-viral-finder

Or by hand: copy both folders in `skills/` into `~/.claude/skills/`, then

```bash
python -m pip install -r ~/.claude/skills/tiktok-research/requirements.txt
```

## Use

1. "Add these TikTok accounts to track: @... @... @..."
2. "Run tiktok research"
3. Read `tiktok-research/<date>/report.md`

---

## Credits and changes

Based on [bradautomates/head-of-content](https://github.com/bradautomates/head-of-content) (MIT), the `tiktok-research` and `video-content-analyzer` skills. Changes in this version:

- **Ranks by each account's own median** (`rank_by_account.py`). The original ranks engagement rate against followers pooled across all accounts, which flagged 2 of the 81 videos above and missed most breakouts.
- **Works with current apify-client** (newer versions return an object, not a dict; the original crashes).
- **Gemini really watches the video.** The original first sent the TikTok link to Gemini as plain text, so Gemini never saw the video and could make up an analysis. Now every video is downloaded with yt-dlp and uploaded.
- **Current Gemini model** (`gemini-3.8-flash`; `gemini-2.5-flash` is no longer available to new users), changeable with `GEMINI_MODEL`.
- **Retries** when Gemini is overloaded (503) or rate-limited (429).
- Installs as a global skill (works from any folder), with a "Before you start" check list.

MIT License. By [Automate Leverage](https://automateleverage.com).
