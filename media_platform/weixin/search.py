# media_platform/wechat/search.py

import re
import requests
from typing import List


class BingWeChatSearcher:
    """
    使用 Bing 搜索微信公众号文章
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

        return re.findall(
            r'https://mp\.weixin\.qq\.com/s/[^\s"&<>]+',
            html,
        )
