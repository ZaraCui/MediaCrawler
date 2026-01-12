# media_platform/weixin/search.py

import re
import requests
from urllib.parse import urlparse, parse_qs, unquote
from typing import List


class BingWeChatSearcher:
    """
    使用 Bing 搜索微信公众号文章（解析 ck/a 跳转链接）
    """

    BASE_URL = "https://www.bing.com/search"

    def __init__(self, headers: dict | None = None, timeout: int = 15):
        self.headers = headers or {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        self.timeout = timeout

    def search(self, keyword: str, page: int) -> List[str]:
        params = {
            "q": f"site:mp.weixin.qq.com {keyword}",
            "first": page * 10 + 1,
        }

        resp = requests.get(
            self.BASE_URL,
            params=params,
            headers=self.headers,
            timeout=self.timeout,
        )

        if resp.status_code != 200:
            return []

        html = resp.text
        results: List[str] = []

        # 1️⃣ 抓 Bing 跳转链接
        for href in re.findall(r'href="(https://www\.bing\.com/ck/a\?[^"]+)"', html):
            try:
                parsed = urlparse(href)
                qs = parse_qs(parsed.query)

                if "u" not in qs:
                    continue

                real_url = unquote(qs["u"][0])

                # 2️⃣ 判断是否为公众号文章
                if "mp.weixin.qq.com/s" in real_url:
                    results.append(real_url)

            except Exception:
                continue

        # 去重，保持顺序
        return list(dict.fromkeys(results))
