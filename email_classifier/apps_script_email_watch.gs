/*******************************************************
 * AI Email Watch — Google Apps Script (runs in the cloud)
 * Fixes in v2: id-prefix matching + zero-match guard + retry helpers
 * Deploy order: testKey → main (first run builds the baseline) → installTrigger
 *******************************************************/

// ================= Configuration =================
var LLM_API_KEY='***'; // ⚠️ Replace with the client's own key before deploying
var API_URL  = 'https://api.deepseek.com/chat/completions';
var MODEL    = 'deepseek-chat';
var DONE_LABEL   = 'AI-Done';     // label for already-processed mail
var REVIEW_LABEL = 'AI-Review';   // label for mail that needs a human decision
var MAX_PER_RUN  = 20;

var SYSTEM_PROMPT = [
  "You classify new Gmail messages by READING content (sender + subject + body).",
  "User rules — KEEP, never archive:",
  "- keep_exchange: crypto-exchange fund ops (Binance/Bybit/Neverless): deposit/withdrawal/transfer done, C2C dispute result, risk control. Exchange MARKETING -> archive.",
  "- keep_security: account security: new-device login, security alert, 2FA changed.",
  "- keep_social_human: social media messages FROM A REAL HUMAN (message, invite with a note, recruiter InMail). NOT digests like 'X and 8 others shared'/'37 notifications' -> archive.",
  "- keep_verify: verification codes, email verification links, OTPs.",
  "- keep_important: exam bookings/results (TOEFL/ETS etc.), personal emails needing reply, university contacts, bills, service-expiry notices, replies to your enquiries.",
  "- archive: ads, marketing, newsletters, digests, promos, notification roundups.",
  "- review: genuinely cannot decide. Never guess on important-looking mail.",
  "Output ONLY JSON: {\"messages\":[{\"id\":\"...\",\"decision\":\"keep|archive|review\",\"category\":\"...\",\"confidence\":\"high|medium|low\",\"reason\":\"short\"}]}"
].join('\n');

// ================= Helpers =================
function ensureLabels_() {
  var out = {};
  [DONE_LABEL, REVIEW_LABEL].forEach(function (n) {
    try { out[n] = GmailApp.getUserLabelByName(n); } catch (e) {}
    if (!out[n]) { try { out[n] = GmailApp.createLabel(n); } catch (e) {} }
  });
  return out;
}

// Labels live on threads (not messages), so hasLabel_ takes a thread
function hasLabel_(thread, name) {
  var labels = thread.getLabels();
  for (var i = 0; i < labels.length; i++) if (labels[i].getName() === name) return true;
  return false;
}

function classifyAll_(text) {
  var payload = {
    model: MODEL,
    messages: [{ role: 'system', content: SYSTEM_PROMPT }, { role: 'user', content: text }],
    response_format: { type: 'json_object' },
    temperature: 0
  };
  var resp = UrlFetchApp.fetch(API_URL, {
    method: 'post',
    contentType: 'application/json',
    headers: { Authorization: 'Bearer ' + LLM_API_KEY },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  });
  var code = resp.getResponseCode();
  if (code !== 200) throw new Error('API ' + code + ': ' + resp.getContentText().slice(0, 200));
  var data = JSON.parse(resp.getContentText());
  var content = data.choices[0].message.content.trim();
  if (content.indexOf('```') === 0) content = content.split('\n').slice(1).join('\n').replace(/```$/, '').trim();
  return JSON.parse(content).messages || [];
}

// ================= Main entry (called by the time trigger) =================
function main() {
  var labels = ensureLabels_();
  var props  = PropertiesService.getScriptProperties();
  var baselineDone = props.getProperty('BASELINE_DONE');

  var threads = GmailApp.getInboxThreads(0, 100);

  // First run: mark existing mail AI-Done, touch nothing else
  if (!baselineDone) {
    for (var i = 0; i < threads.length; i++) threads[i].addLabel(labels[DONE_LABEL]);
    props.setProperty('BASELINE_DONE', '1');
    Logger.log('Baseline built: marked ' + threads.length + ' existing thread(s); only new mail is processed from now on');
    return;
  }

  // Collect new mail: threads without the AI-Done label
  var todo = [];
  for (var j = 0; j < threads.length && todo.length < MAX_PER_RUN; j++) {
    var msgs = threads[j].getMessages();
    var m = msgs[msgs.length - 1];
    if (!hasLabel_(threads[j], DONE_LABEL)) todo.push({ thread: threads[j], msg: m });
  }
  if (todo.length === 0) { Logger.log('Routine check: no new mail'); return; }

  Logger.log('Found ' + todo.length + ' new message(s), classifying...');
  var lines = todo.map(function (t) {
    var body = (t.msg.getPlainBody() || '').replace(/\s+/g, ' ').slice(0, 400);
    return '[M' + t.msg.getId() + '] FROM: ' + t.msg.getFrom() + ' | SUBJECT: ' + t.msg.getSubject() + ' | BODY: ' + body;
  });

  // Key fix: the LLM may echo "Mxxx" or "xxx" — strip the M prefix and key by raw id
  var decisions = {};
  classifyAll_(lines.join('\n')).forEach(function (r) {
    decisions[String(r.id).replace(/^M/i, '')] = r;
  });
  Logger.log('LLM returned ' + Object.keys(decisions).length + ' classification(s)');

  // Build the plan first; if nothing matched, abort the whole round (touch no mail, auto-retry next run)
  var plan = todo.map(function (t) {
    var d = decisions[String(t.msg.getId())] || {};
    return { t: t, dec: d.decision || '', cat: d.category || '', conf: d.confidence || '' };
  });
  var matched = plan.filter(function (p) { return p.dec !== ''; }).length;
  if (matched === 0) {
    Logger.log('⚠️ No classification matched the message ids — skipping this round, no mail touched (auto-retry next run)');
    return;
  }

  var kept = 0, archived = 0, reviews = 0;
  plan.forEach(function (p) {
    try {
      if (p.dec === 'keep')            { p.t.msg.star(); kept++; }
      else if (p.dec === 'archive')    { p.t.thread.addLabel(labels[DONE_LABEL]); p.t.thread.moveToArchive(); archived++; }
      else                             { p.t.thread.addLabel(labels[REVIEW_LABEL]); reviews++; }
      p.t.thread.addLabel(labels[DONE_LABEL]);
    } catch (e) { Logger.log('Failed to process a message: ' + e); }
  });
  Logger.log('Done: starred ' + kept + ' | archived ' + archived + ' | review ' + reviews + ' | matched ' + matched + '/' + todo.length);
}

// ================= Clear the baseline flag (safety) =================
function resetBaseline() {
  PropertiesService.getScriptProperties().deleteProperty('BASELINE_DONE');
  Logger.log('Baseline flag cleared — run main() again to rebuild the baseline safely');
}

// ================= Reset mis-labelled mail so it gets re-processed =================
function retryTestMails() {
  var labels = ensureLabels_();
  var threads = GmailApp.getInboxThreads(0, 100);
  var n = 0;
  threads.forEach(function (t) {
    var hasReview = false;
    try { hasReview = hasLabel_(t, REVIEW_LABEL); } catch (e) {}
    if (hasReview) {
      t.removeLabel(labels[REVIEW_LABEL]);
      t.removeLabel(labels[DONE_LABEL]);
      n++;
    }
  });
  Logger.log('Reset labels on ' + n + ' thread(s) — they can be processed again');
}

// ================= Install the 10-minute time trigger =================
function installTrigger() {
  ScriptApp.getProjectTriggers().forEach(function (t) { ScriptApp.deleteTrigger(t); });
  ScriptApp.newTrigger('main').timeBased().everyMinutes(10).create();
  Logger.log('✅ Trigger installed: main() runs every 10 minutes');
}

// ================= Test the API key =================
function testKey() {
  try {
    var r = classifyAll_('[Mtest] FROM: x <x@x.com> | SUBJECT: newsletter | BODY: promo ad');
    Logger.log('Key OK. Classification result: ' + JSON.stringify(r));
  } catch (e) {
    Logger.log('Key or network error: ' + e);
  }
}
