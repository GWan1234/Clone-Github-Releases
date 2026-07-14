# -*- coding: UTF-8 -*-

import os
import json
import requests


def list_split(items, n):
    """每7天分成一组，与原项目保持一致"""
    return [items[i:i + n] for i in range(0, len(items), n)]


def getdata(username, token):
    url = "https://api.github.com/graphql"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "github-calendar-api"
    }

    query = """
    query($login: String!) {
      user(login: $login) {
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

    payload = {
        "query": query,
        "variables": {
            "login": username
        }
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    if "errors" in result:
        raise RuntimeError(result["errors"])

    calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]

    total = calendar["totalContributions"]

    datalist = []

    for week in calendar["weeks"]:
        for day in week["contributionDays"]:
            datalist.append({
                "date": day["date"],
                "count": day["contributionCount"]
            })

    # 保证日期升序
    datalist.sort(key=lambda x: x["date"])

    returndata = {
        "total": total,
        "contributions": list_split(datalist, 7)
    }

    return returndata


if __name__ == "__main__":

    # ===== 修改这里 =====
    username = "GWan1234"
    # ===================

    token = os.getenv("GITHUB_TOKEN")

    if not token:
        raise RuntimeError(
            "未找到环境变量 GITHUB_TOKEN，请在 GitHub Actions 中设置：\n"
            "env:\n"
            "  GITHUB_TOKEN: ${{ secrets.MY_TOKEN }}"
        )

    print(f"正在获取 {username} 的贡献数据...")

    data = getdata(username, token)

    filename = f"github_contributions_{username}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"数据已保存到 {filename}")
    print(f"总贡献数: {data['total']}")