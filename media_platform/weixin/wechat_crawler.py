# media_platform/weixin/wechat_crawler.py

import asyncio
import json
import os
import random
import time

import config
from base.base_crawler import AbstractCrawler
from media_platform.weixin.search import SogouWeChatSearcher


class WeChatCrawler(AbstractCrawler):
    """
    微信公众号文章发现爬虫（基于 Sogou 搜索）
    只做“发现”，不访问正文
    """

    def __init__(self):
        self.results = []

    async def start(self):
        if not getattr(config, "ENABLE_WECHAT", False):
            print("[WeChat] Crawler disabled by config")
            return

        print("[WeChat] Crawler started")

        searcher = SogouWeChatSearcher()

        for account in config.WECHAT_ACCOUNTS:
            print(f"[WeChat] Crawling account: {account}")

            for page in range(config.WECHAT_MAX_PAGE):
                tokens = searcher.search(account, page)

                print(f"[DEBUG] Found {len(tokens)} tokens")

                for token in tokens:
                    self.results.append({
                        "platform": "wechat",
                        "account": account,
                        "source": "sogou",
                        "token": token,
                        "crawl_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    })

                await asyncio.sleep(
                    random.uniform(*config.WECHAT_REQUEST_DELAY)
                )

            await asyncio.sleep(
                random.uniform(*config.WECHAT_ACCOUNT_DELAY)
            )

        self._save_json()

    def _save_json(self):
        os.makedirs("data/wechat", exist_ok=True)

        filename = (
            f"data/wechat/"
            f"wechat_search_{time.strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(
            f"[WeChat] Saved {len(self.results)} items to {filename}"
        )

    # ====== 为了满足 AbstractCrawler 的接口，占位实现 ======

    async def search(self):
        pass

    async def launch_browser(self, *args, **kwargs):
        raise NotImplementedError(
            "WeChat crawler does not use browser"
        )
