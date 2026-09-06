#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户消息自动处理 Agent (客服分诊器)
====================================
Fiverr 作品集 demo:把客户来信批量分类 + 提取信息 + 草拟回复。

用法:
    python agent.py                      # 处理默认的 sample_messages.txt
    python agent.py --input 你的文件.txt  # 处理你自己的文件
    python agent.py --output out.json    # 自定义输出文件

配置(环境变量):
    LLM_API_KEY   你的 API key   (必填)
    LLM_BASE_URL  API 地址       (默认 DeepSeek: https://api.deepseek.com)
    LLM_MODEL     模型名         (默认 deepseek-chat)

第一次跑之前:
    1. 去 platform.deepseek.com 注册 -> 充值(最低 ¥10)-> 创建 API key
    2. 在终端设置:export LLM_API_KEY=sk-你的key
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

# ---------- 配置 ----------
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
MODEL    = os.environ.get("LLM_MODEL", "deepseek-chat")
API_KEY  = os.environ.get("LLM_API_KEY", "")

# 系统提示词:告诉 AI 它的角色、任务、输出格式
SYSTEM_PROMPT = """You are a customer-service triage agent for a small online business.
Your job: read ALL customer messages below, and for EACH message output:
  - id: message number (M1, M2, ...)
  - language: "en" or "zh"
  - category: one of ["order", "support", "refund", "complaint", "spam", "other"]
  - summary: one short sentence describing what the customer wants
  - urgency: "low", "medium" or "high"
  - needs_human: true if it needs a human (refund/complaint/legal), false otherwise
  - draft_reply: a short professional reply IN THE SAME LANGUAGE as the customer
    (order/support questions get helpful answers; complaints get apology + next step;
     spam gets no reply, write "NO REPLY NEEDED")

Rules:
- Detect spam/ads and mark them so the business can ignore them.
- Reply tone: warm, concise, professional.
- Output ONLY a JSON object (no markdown, no comments), in this exact shape:
{"messages": [{"id": "...", "language": "...", "category": "...", "summary": "...",
"urgency": "...", "needs_human": true, "draft_reply": "..."}]}"""


def call_llm(user_text: str) -> str:
    """调用大模型,返回原始回复文本。"""
    if not API_KEY:
        print("❌ 没有找到 API key!")
        print("   请先设置: export LLM_API_KEY=sk-你的key")
        print("   (还不会?看同目录 README.md 第一步)")
        sys.exit(1)

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text},
        ],
        "response_format": {"type": "json_object"},  # 强制 JSON 输出
        "temperature": 0.2,                          # 低温度 = 更稳定
    }
    req = urllib.request.Request(
        BASE_URL + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + API_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # 把常见的 HTTP 错误翻译成人话
        body = e.read().decode("utf-8", errors="ignore")[:300]
        hints = {
            401: "API key 无效或没填对,去 platform.deepseek.com 检查",
            402: "账户余额不足,去充值(最低 ¥10)",
            429: "请求太频繁被限流,等几秒重试",
        }
        print(f"❌ API 请求失败 (HTTP {e.code})")
        print(f"   可能原因: {hints.get(e.code, '见下方服务商返回')}")
        print(f"   服务商返回: {body}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ 网络错误: {e.reason}")
        print("   DeepSeek 在大陆可直连,如果失败检查网络/防火墙")
        sys.exit(1)

    # 解析返回,取出 AI 写的正文
    return data["choices"][0]["message"]["content"]


def clean_json(raw: str) -> dict:
    """AI 有时会包一层 markdown 代码块,剥掉再解析。"""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description="客户消息自动处理 Agent")
    parser.add_argument("--input", default="sample_messages.txt", help="输入消息文件")
    parser.add_argument("--output", default="triage_result.json", help="输出 JSON 文件")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"❌ 找不到输入文件: {args.input}")
        sys.exit(1)

    with open(args.input, encoding="utf-8") as f:
        messages_text = f.read()

    print("🤖 正在分析消息...")
    raw = call_llm(messages_text)
    result = clean_json(raw)

    # 1) 保存结构化 JSON(给系统/程序用)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"✅ 结构化结果已保存到 {args.output}")

    # 2) 打印人类可读的摘要(给你看/录屏用)
    print("\n" + "=" * 60)
    print("📋 分诊报告")
    print("=" * 60)
    for m in result.get("messages", []):
        flag = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(m.get("urgency", "low"), "⚪")
        human = "👤 需人工" if m.get("needs_human") else "🤖 可自动回"
        print(f"\n{flag} [{m.get('id')}] {m.get('category','?').upper()} ({m.get('language','?')}) {human}")
        print(f"   摘要: {m.get('summary')}")
        print(f"   草拟回复: {m.get('draft_reply')}")


if __name__ == "__main__":
    # Windows 控制台中文不乱码
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    main()
