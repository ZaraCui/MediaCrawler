import re
import random
import time
import requests
from typing import List, Optional
from urllib3.exceptions import InsecureRequestWarning

# 禁用SSL警告（可选，减少日志干扰）
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class SogouWeChatSearcher:
    """
    优化版 Sogou 微信搜索器
    核心：仅提取文章 token（不访问 /link），强化反爬规避，提升稳定性
    """
    SEARCH_URL = "https://weixin.sogou.com/weixin"
    
    # 扩充UA池（覆盖不同浏览器/版本，避免单一特征）
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.61",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    # 多语言池（模拟不同地区用户）
    ACCEPT_LANGUAGES = [
        "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "zh-CN,zh;q=0.9,ja;q=0.8",
        "zh-CN,zh;q=0.9",
        "zh-TW,zh;q=0.9,en;q=0.8"
    ]

    def __init__(self, timeout: int = 15, delay_range: tuple = (3, 8)):
        self.timeout = timeout
        self.delay_range = delay_range  # 请求间隔随机延时范围（秒）
        self.session = requests.Session()  # 复用会话，保持Cookie
        self._init_session()  # 初始化会话（模拟真人先访问首页）

    def _init_session(self):
        """初始化会话：先访问搜狗微信首页，获取初始Cookie，规避直接搜索的爬虫特征"""
        try:
            # 随机延时后访问首页
            time.sleep(random.uniform(*self.delay_range))
            headers = self._get_random_headers()
            # 访问首页，不解析内容，仅获取Cookie
            self.session.get(
                "https://weixin.sogou.com/",
                headers=headers,
                timeout=self.timeout,
                verify=False  # 生产环境建议启用CA验证
            )
        except Exception as e:
            print(f"[WARN] 初始化会话失败: {e}")

    def _get_random_headers(self) -> dict:
        """生成随机请求头，消除固定特征"""
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept-Language": random.choice(self.ACCEPT_LANGUAGES),
            "Referer": random.choice([  # 模拟从不同来源跳转
                "https://www.sogou.com/",
                "https://weixin.sogou.com/",
                "https://www.baidu.com/"
            ]),
            # 补充现代浏览器核心字段，避免被识别为爬虫
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Cache-Control": "max-age=0"
        }
        return headers

    def _check_anti_spider(self, html: str) -> bool:
        """检测是否触发反爬（验证码/访问限制）"""
        anti_spider_keywords = [
            "验证码", "人机验证", "访问频率限制", "请输入验证码",
            "您的访问过于频繁", "滑块验证", "安全验证"
        ]
        for keyword in anti_spider_keywords:
            if keyword in html:
                print(f"[WARN] 触发搜狗反爬机制：检测到关键词「{keyword}」")
                return True
        # 检测是否返回空页面/首页（无搜索结果但有反爬特征）
        if "weixin.sogou.com/weixin?type=2" in html and len(re.findall(r'/link\?url=', html)) == 0:
            print(f"[WARN] 搜索结果为空，疑似被反爬拦截")
            return True
        return False

    def search(self, keyword: str, page: int) -> List[str]:
        """
        优化版搜索方法：提取Token，强化反爬规避和容错
        :param keyword: 搜索关键词
        :param page: 页码（从0开始）
        :return: 去重后的Token列表
        """
        # 1. 搜索前随机延时（核心反爬措施）
        time.sleep(random.uniform(*self.delay_range))
        
        # 2. 构造搜索参数（补充分页参数，提升兼容性）
        params = {
            "type": 2,          # 2 = 文章
            "query": keyword,
            "page": page + 1,   # 搜狗页码从1开始
            "ie": "utf8",       # 编码格式，避免乱码
            "tsn": 1,           # 补充默认参数，模拟真人请求
            "ft": "",
            "et": "",
            "interation": ""
        }

        try:
            # 3. 发送请求（复用会话，随机请求头）
            resp = self.session.get(
                self.SEARCH_URL,
                params=params,
                headers=self._get_random_headers(),
                timeout=self.timeout,
                verify=False
            )
            
            # 4. 状态码容错
            if resp.status_code != 200:
                print(f"[ERROR] 搜索请求失败，状态码：{resp.status_code}")
                return []
            
            # 5. 统一编码，避免乱码导致Token提取失败
            resp.encoding = "utf-8"
            html = resp.text
            
            # 6. 检测反爬，提前退出
            if self._check_anti_spider(html):
                return []
            
            # 7. 提取Token（优化正则，提升匹配准确性）
            # 正则优化：匹配/link?url=后的所有字符（包含特殊符号），且排除多余参数
            tokens = re.findall(
                r'/link\?url=([a-zA-Z0-9_\-]+)(?:&|")',  # 非捕获组，避免匹配&后的参数
                html,
                re.IGNORECASE
            )
            
            # 8. 去重并返回
            unique_tokens = list(dict.fromkeys(tokens))
            print(f"[DEBUG] 第{page+1}页 - 找到 {len(unique_tokens)} 个有效Token（原始{len(tokens)}个）")
            return unique_tokens
            
        except requests.exceptions.Timeout:
            print(f"[ERROR] 搜索请求超时（关键词：{keyword}，页码：{page}）")
            return []
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] 搜索请求连接失败（关键词：{keyword}，页码：{page}）")
            return []
        except Exception as e:
            print(f"[ERROR] 搜索异常（关键词：{keyword}，页码：{page}）: {str(e)}")
            return []

    def batch_search(self, keyword: str, max_page: int = 3) -> List[str]:
        """
        批量搜索多页Token（封装分页逻辑，增加全局延时）
        :param keyword: 搜索关键词
        :param max_page: 最大页码（从0开始，默认3页）
        :return: 所有页的Token合并去重列表
        """
        all_tokens = []
        for page in range(max_page):
            tokens = self.search(keyword, page)
            if not tokens:
                print(f"[WARN] 第{page+1}页无Token，停止批量搜索")
                break
            all_tokens.extend(tokens)
            # 分页间增加更长的随机延时（避免高频分页）
            time.sleep(random.uniform(5, 10))
        
        # 全局去重
        all_tokens = list(dict.fromkeys(all_tokens))
        print(f"[INFO] 批量搜索完成 - 总计获取 {len(all_tokens)} 个唯一Token")
        return all_tokens


# ==================== 使用示例 ====================
if __name__ == "__main__":
    # 初始化搜索器（设置延时3-8秒，避免反爬）
    searcher = SogouWeChatSearcher(timeout=15, delay_range=(3, 8))
    
    # 单页搜索
    tokens = searcher.search("Python 教程", page=0)
    print(f"单页Token列表: {tokens}")
    
    # 批量搜索（最多3页）
    # all_tokens = searcher.batch_search("Python 教程", max_page=3)
    # print(f"批量Token列表: {all_tokens}")