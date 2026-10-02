# PhishGuard

PhishGuard is a mini-project that flags suspicious pages using URL signals and fake login-page heuristics.

## What it does

- Chrome/Edge browser extension with a popup risk report
- URL checks for suspicious keywords, lookalike domains, raw IP addresses, risky TLDs, and unsafe HTTP
- Page checks for credential forms, password fields, misleading branding, and suspicious redirects
- Risk score from 0–100 with Low, Medium, High, or Critical severity
- Optional Python API for a slightly richer scoring model

## Run the Python analyser (optional)

```powershell
cd api
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The service runs at `http://127.0.0.1:5000/analyze`.

## Install the extension

1. Open `chrome://extensions` (or `edge://extensions`).
2. Enable **Developer mode**.
3. Choose **Load unpacked** and select the `extension` folder.
4. Pin PhishGuard, then open a website and click the extension icon.

The extension works locally even without the Python API. To use the API, change `API_URL` in `extension/popup.js` if needed.

## Safety note

This is an educational phishing detector, not a security guarantee. It does not send browsing data anywhere except to the optional local API when enabled.
