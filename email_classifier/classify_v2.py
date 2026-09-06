#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件分类器 v2 - 内容级 LLM 分类(按用户自定义规则)
==================================================
用法:
    python classify_v2.py --input inbox_env_all.json --output classify_result.jsonl
    (需要环境变量 LLM_API_KEY)

分类规则(用户 2026-09-05 定义,必须保留的 5 类):
  keep_exchange    币安/Bybit/Neverless 等交易所的资金操作:充值/提现/转账/C2C申诉/风控
  keep_security    账户安全:新设备登录、安全提醒、2FA 变更
  keep_social_human 社交媒体中真人发起的消息/好友请求/带个性化内容的通知
  keep_verify      验证码 / 邮箱验证 / 确认链接
  keep_important   考试(TOEFL等)报名订单成绩、真人来信、学校联系、账单、服务到期、主动咨询的回复
  archive          广告/营销/订阅通讯/纯系统汇总通知(如"X和8人分享了")
  review           无法判断 -> 不许自动处理,留给用户
"""
import argparse, json, os, sys, time, urllib.error, urllib.request

API_KEY = os.environ.get("LLM_API_KEY", "")
BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

SYSTEM_PROMPT = """You classify personal Gmail messages for a user. For EACH message below, decide its fate by READING the content (sender + subject + body snippet).

User's rules — MUST KEEP (never archive):
- keep_exchange: crypto-exchange fund operations (Binance/Bybit/Neverless): deposit/withdrawal succeeded, transfer completed, C2C dispute result, risk-control notice. EXAMPLE subject: "【币安】USDT 提现成功提醒" -> keep_exchange. But exchange MARKETING (promotions, new coin listings, ads) -> archive.
- keep_security: account security: new-device login, security alert, 2FA changed, passkey enabled.
- keep_social_human: social media messages actually FROM A HUMAN or personalized: a specific person's message, connection request with a note, recruiter InMail, someone commented on/mentioned you. NOT system digests like "X and 8 others shared", "You have 37 notifications", weekly summaries -> archive.
- keep_verify: verification/confirmation codes, email verification links, OTPs.
- keep_important: exam/test bookings or results (TOEFL/ETS order confirmations, scores), personal emails needing a reply, university/school contacts, invoices/bills, service-expiry notices, replies to your own enquiries.
- archive: ads, marketing, newsletters, subscription digests, product promos, event invites with no personal content, pure notification roundups.
- review: genuinely cannot decide. NEVER guess on important-looking mail.

Output ONLY JSON (no markdown): {"messages": [{"id": "...", "decision": "keep|archive|review", "category": "keep_exchange|keep_security|keep_social_human|keep_verify|keep_important|archive|review", "confidence": "high|medium|low", "reason": "one short reason"}]}"""

def call_llm(payload_text: str) -> dict:
    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                     {"role": "user", "content": payload_text}],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
        "max_tokens": 3000,
    }
    req = urllib.request.Request(BASE_URL + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + API_KEY},
        method="POST")
    with urllib.request.urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return json.loads(data["choices"][0]["message"]["content"].strip().removeprefix("```json").removesuffix("```").strip())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", default="classify_result.jsonl")
    ap.add_argument("--batch-size", type=int, default=25)
    ap.add_argument("--max-mails", type=int, default=0, help="0=全部")
    args = ap.parse_args()

    if not API_KEY:
        print("❌ 没有 LLM_API_KEY"); sys.exit(1)
    envs = json.load(open(args.input, encoding="utf-8"))
    if args.max_mails: envs = envs[:args.max_mails]

    # 断点续跑:已分类的跳过
    done = {}
    if os.path.exists(args.output):
        for line in open(args.output, encoding="utf-8"):
            try:
                r = json.loads(line); done[r["id"]] = r
            except Exception: pass
    todo = [e for e in envs if str(e["id"]) not in done]
    print(f"总共 {len(envs)},已完成 {len(done)},待分类 {len(todo)}", flush=True)

    out = open(args.output, "a", encoding="utf-8")
    for i in range(0, len(todo), args.batch_size):
        batch = todo[i:i+args.batch_size]
        text_lines = []
        for e in batch:
            f = (e.get("from") or [{}])[0]
            subj = (e.get("subject") or "(no subject)").replace("\n", " ")
            text_lines.append(f"[M{str(e['id'])}] FROM: {f.get('name','')} <{f.get('email','')}> | SUBJECT: {subj}")
        for attempt in range(3):
            try:
                res = call_llm("\n".join(text_lines))
                for m in res.get("messages", []):
                    rec = {"id": str(m["id"]).removeprefix("M"),
                           "decision": m.get("decision","review"),
                           "category": m.get("category","review"),
                           "confidence": m.get("confidence","low"),
                           "reason": m.get("reason","")}
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                break
            except urllib.error.HTTPError as e:
                print(f"批次 {i//args.batch_size+1} HTTP {e.code}: {e.read()[:200]}", flush=True)
                time.sleep(5)
            except Exception as e:
                print(f"批次 {i//args.batch_size+1} 错误: {e}", flush=True)
                time.sleep(3)
        if (i // args.batch_size) % 4 == 0:
            print(f"进度: {min(i+args.batch_size, len(todo))}/{len(todo)}", flush=True)
    out.close()
    print("完成。结果在", args.output, flush=True)

if __name__ == "__main__":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
    main()
