# Email Classification Service — Client Playbook

> How every client order is customised: start from the default taxonomy below, then fine-tune with the 3 intake questions.

---

## 1. Default taxonomy

> Principle: classify by the **role the email plays in the client's life or business** (money? people? schedule?) — not by sender.

| Category | What it means | Default action |
|---|---|---|
| 👤 People | Written directly by a human (client, colleague, anyone) and needs a reply | keep + flag to reply |
| 💰 Money | Invoices, orders, receipts, bills, payment notices | keep |
| 📅 Calendar | Meeting invites, appointment confirmations, reminders | keep |
| 🔐 Security & Verify | Login alerts, 2FA, password changes, verification codes | keep (archive once stale, optional) |
| 🚚 Notifications | Shipping, delivery, status updates, system notices | archive by default (may keep) |
| 📰 Newsletters | Ads, digests, promos, subscriptions | archive |
| 🗑️ Spam / Phishing | Mass fraud | archive |
| ⚠️ Unsure | Cannot decide | **never auto-touch** — hand to the client for review |

---

## 2. The 3 intake questions

**Q1 — What must NEVER be missed?**
> e.g. every client email? invoices? official/legal notices?

**Q2 — What do you actually do with your email every day?**
> reply? bookkeeping? tracking orders? scheduling?

**Q3 — Have you ever been burned by missing an email?**
> late-bill penalty? a lost client message?

→ The client's answers translate directly into their personal categories and "hard rules".

---

## 3. Customisation workflow (repeat for every order)

1. **Interview** — ask the 3 questions (~10 min).
2. **Categories** — default taxonomy + the client's answers → their personal list (≤ 8).
3. **Examples** — pull 10–20 representative emails from their inbox and have the client label each one (ground truth).
4. **Test** — report precision/recall against that ground truth; show the client the numbers.
5. **Go live + correction loop** — after delivery, every misclassified email becomes a new example; the rules get better with use.

---

## 4. Delivery guarantees (mirror these in the gig description)

- Never deletes anything — archive only, recoverable in one click.
- Unsure emails are never touched — listed for the client to decide.
- Every decision is explainable (each classification carries a short reason).
- Every client correction is remembered as a new rule example.

---

*2026-09-06 · Companion: classify_v2.py (LLM + user-rule classification engine)*
