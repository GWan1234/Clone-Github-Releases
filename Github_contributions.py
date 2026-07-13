# -*- coding: UTF-8 -*-
import requests
import re
import json
from http.server import BaseHTTPRequestHandler


def list_split(items, n):
    return [items[i:i + n] for i in range(0, len(items), n)]


def getdata(name):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    url = f"https://github.com/users/{name}/contributions"

    r = requests.get(url, headers=headers, timeout=30)

    if r.status_code != 200:
        return {
            "total": 0,
            "contributions": []
        }

    data = r.text

    # SVG 中每一天都是一个 rect
    pattern = re.compile(
        r'data-date="([^"]+)".*?data-count="(\d+)"',
        re.S
    )

    result = pattern.findall(data)

    if not result:
        return {
            "total": 0,
            "contributions": []
        }

    datalist = []

    total = 0

    for date, count in result:
        count = int(count)
        total += count

        datalist.append({
            "date": date,
            "count": count
        })

    # 日期排序
    datalist.sort(key=lambda x: x["date"])

    returndata = {
        "total": total,
        "contributions": list_split(datalist, 7)
    }

    return returndata


class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path

        user = None

        if "?" in path:
            query = path.split("?")[1]
            for kv in query.split("&"):
                if "=" not in kv:
                    continue
                key, value = kv.split("=", 1)
                if key == "user":
                    user = value
                    break

        if not user:
            user = "octocat"

        data = getdata(user)

        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-type", "application/json")
        self.end_headers()

        self.wfile.write(json.dumps(data).encode("utf-8"))


if __name__ == "__main__":

    username = "GWan1234"

    print(f"正在获取 {username} 的贡献数据...")

    data = getdata(username)

    filename = f"github_contributions_{username}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"数据已保存到 {filename}")
    print(f"总贡献数: {data['total']}")