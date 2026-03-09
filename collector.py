import feedparser
import requests

REDDIT_HEADERS = {"User-Agent": "ddalkkak/1.0 (MVP collector)"}

SUBREDDITS = ["startups", "SideProject", "Entrepreneur", "productivity", "SaaS"]

RSS_FEEDS = [
    "https://feeds.feedburner.com/TechCrunch",
    "https://www.theverge.com/rss/index.xml",
]


def fetch_subreddit(subreddit: str, limit: int = 10) -> list[dict]:
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    try:
        response = requests.get(url, headers=REDDIT_HEADERS, timeout=10)
        response.raise_for_status()
        posts = response.json()["data"]["children"]
        result = []
        for p in posts:
            d = p["data"]
            if (
                d.get("score", 0) >= 100
                and d.get("upvote_ratio", 0) >= 0.8
                and d.get("is_self", False)
            ):
                result.append({
                    "title": d.get("title", ""),
                    "selftext": d.get("selftext", "")[:500],
                    "score": d.get("score", 0),
                    "num_comments": d.get("num_comments", 0),
                    "subreddit": d.get("subreddit", subreddit),
                    "permalink": f"https://reddit.com{d.get('permalink', '')}",
                })
        return result
    except Exception as e:
        print(f"[SKIP] Reddit r/{subreddit} 수집 실패: {e}")
        return []


def fetch_rss(feed_url: str, limit: int = 5) -> list[dict]:
    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo and not feed.entries:
            raise ValueError(feed.bozo_exception)
        result = []
        for entry in feed.entries[:limit]:
            result.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", "")[:300],
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
            })
        return result
    except Exception as e:
        print(f"[SKIP] RSS {feed_url} 수집 실패: {e}")
        return []


def collect() -> dict:
    reddit_items = []
    for sub in SUBREDDITS:
        reddit_items.extend(fetch_subreddit(sub))

    news_items = []
    for feed_url in RSS_FEEDS:
        news_items.extend(fetch_rss(feed_url))

    print(f"수집 완료 — Reddit: {len(reddit_items)}건, 뉴스: {len(news_items)}건")
    return {"reddit": reddit_items, "news": news_items}
