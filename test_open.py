import requests

token = "dn9a_-gY295K0Rci_xozVXfdMkSQTLW6cwJThYulHEtVjXrGTiVgS0m-TnK4-Kjt9aeFsYOPzXUglOopRc3FnFqXa8Fplpd9wLDq4ZYHPu"

url = "https://weixin.sogou.com/link"
headers = {
    "User-Agent": "Mozilla/5.0"
}

resp = requests.get(
    url,
    params={"url": token},
    headers=headers,
    allow_redirects=True,
    timeout=10
)

print("最终 URL：")
print(resp.url)
