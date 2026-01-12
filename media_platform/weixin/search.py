# media_platform/weixin/search.py

import re
import requests
from typing import List


class SogouWeChatSearcher:
    """
    使用 Sogou 微信搜索
    仅提取文章 token（不访问 /link，避免反爬）
    """

    SEARCH_URL = "https://weixin.sogou.com/weixin"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": "https://weixin.sogou.com/",
        }

    def search(self, keyword: str, page: int) -> List[str]:
        params = {
            "type": 2,          # 2 = 文章
            "query": keyword,
            "page": page + 1,
        }

        resp = requests.get(
            self.SEARCH_URL,
            params=params,
            headers=self.headers,
            timeout=self.timeout,
        )

        if resp.status_code != 200:
            return []

        html = resp.text

        # ✅ 只抓 token，不请求 /link
        tokens = re.findall(
            r'/link\?url=([a-zA-Z0-9_-]+)',
            html,
        )

        print(f"[DEBUG] Found {len(tokens)} sogou tokens")

        # 去重
        return list(dict.fromkeys(tokens))
