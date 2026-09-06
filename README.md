# AI Triage Tools (Fiverr Portfolio Demos)

Lightweight, LLM-powered triage tools built as freelance (Fiverr) portfolio demos.
Both tools share one idea: **let the user define the rules in plain language, let an LLM
read the actual content, and never touch anything you're not sure about.**

## Tools

### 1. Customer-Message Triage Agent (`agent.py`)
Classifies a batch of customer messages (email/chat, EN or ZH) into
order / support / refund / complaint / spam, detects urgency, and **drafts a reply
in the customer's language**. Outputs structured JSON + a human-readable report.

```bash
python agent.py                              # processes sample_messages.txt
python agent.py --input my_messages.txt      # your own file
```

### 2. Email Classifier with User Rules (`email_classifier/classify_v2.py`)
Classifies personal Gmail messages by **content** (sender + subject + body snippet),
following categories the user defines. Built-in default rules keep:
crypto-exchange fund operations, security alerts, real social messages, verification
codes, and important personal mail (exams, replies) — everything else gets archived.
Uncertain messages are flagged `review` and **never auto-processed**.

```bash
python email_classifier/classify_v2.py --input envelopes.json --output result.jsonl
```

Resumable (skip already-classified ids), batch-friendly, ~¥1 (≈$0.15) per 900 emails
on DeepSeek.

## Requirements

- Python 3.10+
- An LLM API key (OpenAI-compatible): `export LLM_API_KEY=sk-...`
- Optional: `LLM_BASE_URL` / `LLM_MODEL` to switch providers (defaults to DeepSeek)

## Docs

- `docs/email-classification-playbook.md` — client intake workflow (3 questions → custom taxonomy → accuracy test → feedback loop), CN/EN
- `docs/client-communication-scripts.md` — client-facing scripts for accuracy/support conversations, CN/EN

## Design principles (also your selling points)

1. **Never delete** — archiving only, everything recoverable.
2. **Uncertain → ask** — `review` decisions are never auto-applied.
3. **Explainable** — every decision carries a reason.
4. **Learns** — every client correction becomes a new rule example.

No real personal data is included in this repo — all samples are synthetic.
