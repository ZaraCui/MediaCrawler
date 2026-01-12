import requests
import re
from urllib.parse import unquote

url = "https://weixin.sogou.com/weixin"
params = {
    "type": 2,
    "query": "新民晚报",
    "page": 1,
}

headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

resp = requests.get(url, params=params, headers=headers, timeout=10)
print(resp.status_code)

links = re.findall(r'/link\?url=([^"]+)', resp.text)
print("found:", len(links))

for l in links[:5]:
    print(unquote(l))
