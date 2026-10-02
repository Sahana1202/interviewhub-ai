const API_URL = "http://127.0.0.1:5000/analyze";

const $ = (id) => document.getElementById(id);

function localAnalysis(url, page) {
  const parsed = new URL(url);
  const host = parsed.hostname.toLowerCase();
  const signals = []; let score = 0;
  const add = (points, label, detail) => { score += points; signals.push({ points, label, detail }); };
  if (parsed.protocol === "http:") add(12, "Unencrypted connection", "This page uses HTTP instead of HTTPS.");
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) add(28, "IP address used as domain", "A named domain is safer and easier to verify.");
  if ((host.match(/-/g) || []).length >= 2) add(10, "Hyphen-heavy domain", "Common in impersonation domains.");
  if (/\.(zip|top|xyz|click|work|gq|tk|ml)$/.test(host)) add(15, "High-risk domain ending", "This domain ending is commonly abused.");
  const words = (host + parsed.pathname).match(/[a-z]+/g) || [];
  const hits = [...new Set(words.filter((w) => ["login","verify","secure","update","account","wallet","signin","banking","password"].includes(w)))];
  if (hits.length) add(Math.min(18, hits.length * 5), "Credential-related wording", `Found: ${hits.join(", ")}.`);
  const brand = ["paypal","microsoft","google","apple","amazon","netflix","facebook","instagram"].find((b) => host.includes(b));
  if (brand && host !== `${brand}.com` && !host.endsWith(`.${brand}.com`)) add(22, "Possible brand impersonation", `Brand term found: ${brand}.`);
  if (page.passwordFields) add(12, "Password field detected", "The page requests a password.");
  if (page.passwordFields && parsed.protocol === "http:") add(25, "Password requested over HTTP", "Credentials could be exposed in transit.");
  if (page.externalFormAction) add(20, "External login submission", "The form submits to another domain.");
  score = Math.min(score, 100);
  const level = score >= 75 ? "Critical" : score >= 50 ? "High" : score >= 25 ? "Medium" : "Low";
  const verdict = score >= 50 ? "Avoid entering credentials." : score >= 25 ? "Review carefully before sharing sensitive information." : "No strong phishing signals were found.";
  return { score, level, verdict, signals };
}

function render(result) {
  const level = result.level.toLowerCase();
  $("score").textContent = result.score;
  $("score").className = `score ${level}`;
  $("level").textContent = `${result.level} risk`;
  $("verdict").textContent = result.verdict;
  $("signals").innerHTML = result.signals.length ? result.signals.map((s) => `<li><strong>+${s.points} · ${s.label}</strong><small>${s.detail}</small></li>`).join("") : '<li class="muted">No suspicious signals detected.</li>';
}

async function scan() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.url || !/^https?:/.test(tab.url)) { $("domain").textContent = "Unsupported page"; $("url").textContent = "Open an HTTP or HTTPS website to scan it."; return; }
  const parsed = new URL(tab.url); $("domain").textContent = parsed.hostname; $("url").textContent = tab.url;
  let page = { title: "", passwordFields: 0, forms: 0, externalFormAction: false };
  try { page = await chrome.tabs.sendMessage(tab.id, { type: "PAGE_INSPECTION" }); } catch (_) {}
  let result = localAnalysis(tab.url, page);
  try {
    const response = await fetch(API_URL, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url: tab.url, page }) });
    if (response.ok) { result = await response.json(); $("engine").textContent = "Python ML heuristic engine"; }
  } catch (_) { $("engine").textContent = "Local heuristic engine"; }
  render(result);
}
$("rescan").addEventListener("click", scan);
scan();
