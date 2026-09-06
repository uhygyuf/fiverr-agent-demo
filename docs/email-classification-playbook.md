# 邮件分类服务 — 客户定制流程手册
### Email Classification Service — Client Playbook (CN/EN)

> 用途:每个客户交付前,用"通用默认分类 + 三个问题微调"定制他的分类规则。

---

## 一、通用默认分类表(Default Taxonomy)

> 规律:**按"邮件在客户生活/生意里的角色"分类**(钱?人?日程?),不是按发件人。

| 类目 Category | 含义 What it means | 默认动作 Action |
|---|---|---|
| 👤 真人来信 People | 客户/同事/任何人直接写的话,需要回复 | 保留 + 提醒回复 keep & flag to reply |
| 💰 钱 Money | 发票、订单、收据、账单、付款通知 | 保留 keep |
| 📅 日程/会议 Calendar | 会议邀请、预约确认、提醒 | 保留 keep |
| 🔐 账号安全/验证 Security & Verify | 登录提醒、2FA、改密、验证码 | 保留(过期的可归档)keep |
| 🚚 服务通知 Notifications | 快递、发货、状态更新、系统通知 | 默认归档 archive(可选保留) |
| 📰 订阅/营销 Newsletters | 广告、时事通讯、促销 | 归档 archive |
| 🗑️ 垃圾/钓鱼 Spam | 群发欺诈 | 归档 archive |
| ⚠️ 不确定 Unsure | 无法判断 | **不许自动动**,交客户 review |

---

## 二、给客户的三个问题(The 3 Intake Questions)

**Q1. 什么邮件绝对不能漏?**
> 比如:所有客户的邮件?账单?法院/税务局通知?

EN: Which emails must NEVER be missed? (e.g. every client email? invoices? official/legal notices?)

**Q2. 每天你处理邮件都干嘛?**
> 比如:回信?记账?盯订单?约会议?

EN: What do you actually do with your email every day? (reply? bookkeeping? tracking orders? scheduling?)

**Q3. 最近有没有因为漏看邮件吃过亏?**
> 比如:漏了账单被罚款?漏了客户消息丢单?

EN: Have you ever been burned by missing an email? (late bill penalty? lost client message?)

→ 客户的回答直接翻译成他专属的类目和"铁律"。

---

## 三、定制流程(每单照做)

1. **访谈**:问上面 3 个问题(10 分钟);
2. **定类目**:通用默认表 + 客户回答 → 列出他的专属类目(≤8 个);
3. **给例子**:从他邮箱抽 10–20 封代表邮件,让他标"该归哪类"(标准答案);
4. **跑测试**:在标准答案上报精确率/召回率,给客户看数字;
5. **上线 + 纠错循环**:交付后每封分错的都变成新例子,规则越用越准。

## 四、交付红线(写进 gig 描述)

- 永不删除任何邮件(只归档,可一键找回)
- 拿不准的邮件一律不动,列清单交客户决定
- 每封分类都带理由,可解释
- 客户每纠正一次,系统记住一条

---

*2026-09-06 · 配套:classify_v2.py(LLM + 用户规则分类引擎)*
