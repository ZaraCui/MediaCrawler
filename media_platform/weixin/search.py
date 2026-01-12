# media_platform/weixin/search.py

import re
import base64
import requests
from urllib.parse import urlparse, parse_qs, unquote
from typing import List


class BingWeChatSearcher:
    """
    使用 Bing 搜索微信公众号文章（解析 ck/a 跳转链接）
    """

    BASE_URL = "https://www.bing.com/search"

    def __init__(self, headers: dict, timeout: int = 15):
        self.headers = headers
        self.timeout = timeout

    def search(self, keyword: str, page: int) -> List[str]:
        """
        搜索指定关键词的一页结果
        """
        params = {
            "q": f"site:mp.weixin.qq.com/s {keyword}",
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

        urls: List[str] = []

        # 1️⃣ 找到 Bing 的跳转链接
        for href in re.findall(r'href="(https://www\.bing\.com/ck/a\?[^"]+)"', html):
            try:
                parsed = urlparse(href)
                qs = parse_qs(parsed.query)

                if "u" not in qs:
                    continue

                # 2️⃣ Base64 解码真实 URL
                encoded = qs["u"][0]
                decoded = base64.b64decode(encoded).decode("utf-8", errors="ignore")

                decoded = unquote(decoded)

                # 3️⃣ 过滤公众号文章
                if decoded.startswith("https://mp.weixin.qq.com/s/"):
                    urls.append(decoded)

            except Exception:
                continue

        # 去重
        return list(dict.fromkeys(urls))
