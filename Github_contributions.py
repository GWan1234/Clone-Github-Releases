# -*- coding: UTF-8 -*-
import requests
import json
import os
from http.server import BaseHTTPRequestHandler

def list_split(items, n):
    """按每组 n 个元素切分列表"""
    return [items[i:i + n] for i in range(0, len(items), n)]

def getdata(name):
    """
    通过 GitHub GraphQL API 获取用户贡献日历数据
    返回格式与原脚本完全一致:
    {
        "total": 总贡献数,
        "contributions": [
            [{"date": "YYYY-MM-DD", "count": int}, ...],  # 每周
            ...
        ]
    }
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return {"total": 0, "contributions": [], "error": "GITHUB_TOKEN not set"}

    # GraphQL 查询
    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """

    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": query, "variables": {"username": name}},
            headers=headers
        )
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            # 例如用户不存在或 API 错误
            error_msg = "; ".join(e.get("message", "") for e in result["errors"])
            return {"total": 0, "contributions": [], "error": error_msg}

        calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        total = calendar["totalContributions"]
        weeks = calendar["weeks"]

        # 转换为原格式：所有日期对象按顺序放入列表，再按7天分组
        all_days = []
        for week in weeks:
            for day in week["contributionDays"]:
                all_days.append({
                    "date": day["date"],
                    "count": day["contributionCount"]
                })

        contributions_split = list_split(all_days, 7)

        return {
            "total": total,
            "contributions": contributions_split
        }

    except requests.RequestException as e:
        return {"total": 0, "contributions": [], "error": str(e)}
    except (KeyError, TypeError):
        return {"total": 0, "contributions": [], "error": "Unexpected API response structure"}

class handler(BaseHTTPRequestHandler):
    """用于 Vercel Serverless 部署的请求处理器"""
    def do_GET(self):
        path = self.path
        # 解析 user 参数（保持原逻辑）
        spl = path.split('?')[1:]
        user = ""
        for kv in spl:
            key, value = kv.split("=")
            if key == "user":
                user = value
                break

        data = getdata(user)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
        return

if __name__ == "__main__":
    # 本地直接运行：指定用户名，保存到 JSON 文件
    username = "GWan1234"  # 替换为实际用户名
    
    print(f"正在获取 {username} 的贡献数据...")
    data = getdata(username)

    if "error" in data:
        print(f"获取失败: {data['error']}")
    else:
        filename = f"github_contributions_{username}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到 {filename}")
        print(f"总贡献数: {data['total']}")