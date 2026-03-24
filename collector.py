import time

import requests

SUBREDDITS = ["startups", "SideProject", "Entrepreneur", "productivity", "SaaS"]

LIMIT = 100
REQUEST_DELAY = 2   # 서브레딧 간 대기 (초)
RETRY_DELAY = 5     # 429 재시도 대기 (초)

HEADERS = {"User-Agent": "ddalkkak/1.0 (MVP collector)"}


def fetch_subreddit(subreddit: str, sort: str = "hot") -> list[dict]:
    if sort == "top":
        url = f"https://www.reddit.com/r/{subreddit}/top.json"
        params = {"limit": LIMIT, "t": "day"}
    elif sort == "new":
        url = f"https://www.reddit.com/r/{subreddit}/new.json"
        params = {"limit": LIMIT}
    else:
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        params = {"limit": LIMIT}

    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)

        if resp.status_code == 429:
            print(f"[WAIT] r/{subreddit} 레이트리밋 — {RETRY_DELAY}초 대기 후 재시도")
            time.sleep(RETRY_DELAY)
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)

        resp.raise_for_status()
        children = resp.json()["data"]["children"]

    except Exception as e:
        print(f"[SKIP] Reddit r/{subreddit} 수집 실패: {e}")
        return []

    posts = []
    for child in children:
        d = child["data"]
        posts.append({
            "title": d.get("title", ""),
            "selftext": (d.get("selftext") or "")[:500],
            "score": d.get("score", 0),
            "num_comments": d.get("num_comments", 0),
            "subreddit": d.get("subreddit", subreddit),
            "permalink": f"https://reddit.com{d.get('permalink', '')}",
            "created_utc": int(d.get("created_utc", 0)),
            "upvote_ratio": d.get("upvote_ratio", 0.0),
        })

    return posts


def collect(sort: str = "hot") -> dict:
    all_posts = []
    counts = []

    for i, sub in enumerate(SUBREDDITS):
        posts = fetch_subreddit(sub, sort=sort)
        all_posts.extend(posts)
        counts.append(f"r/{sub}: {len(posts)}건")

        if i < len(SUBREDDITS) - 1:
            time.sleep(REQUEST_DELAY)

    print(f"[COLLECT] ({sort}) {', '.join(counts)} | 총 {len(all_posts)}건")
    return {"reddit": all_posts}
