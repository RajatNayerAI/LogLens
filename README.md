
# LogLensAI CLI 🚀

<p align="center">
   <b>AI-powered log analysis & insights in one file</b><br>
   <img src="https://img.shields.io/badge/Python-3.11%2B-blue" alt="Python 3.11+">
   <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License">
</p>

LogLens is an AI-assisted command-line tool to parse, analyze, and summarize logs from many sources. Fast, portable, and under 250 lines!


## ✨ Features
- **Multi-format log parsing:** Python, Java, Node.js, Syslog, Android logcat\*.
- **Quick stats & top issues:** Instantly see error/warning counts and most critical problems.
- **AI summaries & chat:** Get OpenAI-powered summaries or chat about your logs.
- **Automatic hints:** Detects common issues (OOM, NPE, connection errors, etc.).
- **Export:** Save results as JSON or CSV for further analysis.
- **Easy API key config:** `.env` file for OpenAI key.

\*Android logcat support: _partial_ (timestamp, level, tag, message).


## 🚀 Installation

**Requirements:** Python 3.11+

1. Clone this repo or copy `loglens_ai.py` into your project.
2. Install dependencies:
   ```bash
   pip install openai
   ```
3. Create a `.env` file in the same directory:
   ```env
   OPENAI_API_KEY=sk-...   # Add your OpenAI key
   ```


## ⚡ Usage

Run from terminal:

```bash
python loglens_ai.py <command> [options]
```


## 🛠️ Commands

**Analyze logs:**
```bash
python loglens_ai.py analyse prod.log -n 5 --level ERROR
# Shows stats + top 5 errors
```

**Tail logs:**
```bash
python loglens_ai.py tail prod.log -n 20
```

**AI summary:**
```bash
python loglens_ai.py ai-summary prod.log
```

**Interactive AI chat:**
```bash
python loglens_ai.py chat prod.log
```

**Export results:**
```bash
python loglens_ai.py export prod.log results.json
python loglens_ai.py export prod.log results.csv
```

**Config API key:**
```bash
python loglens_ai.py config set-key
python loglens_ai.py config show-key
```

**Other commands:**
```bash
python loglens_ai.py version
python loglens_ai.py scope
```


## 📋 Example

**Input log (`app.log`):**

INFO 2025-09-28 10:01:23 Service auth started
WARN 2025-09-28 10:02:11 CPU usage > 85%
ERROR 2025-09-28 10:03:00 Connection refused



Run:

```bash
python loglens_ai.py analyse app.log -n 3
```



**Output:**

```
Stats: INFO=1 WARN=1 ERROR=1
Top Issues:
ERROR 2025-09-28 10:03:00 Connection refused (severity 2)
   → Service unreachable/network.
WARN 2025-09-28 10:02:11 CPU usage > 85% (severity 2)
   → Unknown issue, needs review
INFO 2025-09-28 10:01:23 Service auth started (severity 1)
   → Unknown issue, needs review
```


## 🗂️ Sample Logs
Sample logs for testing are available in the `Logs-Sample Data` folder.

---