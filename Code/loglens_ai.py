#!/usr/bin/env python3
"""
LogLens AI-assisted CLI (Hackathon-ready, ≤250 lines)
Usage:
  python loglens_ai.py analyse prod.log -n 5 --level ERROR
  python loglens_ai.py ai-summary prod.log
  python loglens_ai.py chat prod.log
"""
import os, sys, re, json, argparse, collections, csv, getpass
from pathlib import Path
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

PATTERN_FILE = "patterns.json"
ENV_FILES = [Path.cwd() / ".env", Path.home() / ".loglens.env"]
LEVEL_ORDER = {"ERROR":3,"WARN":2,"WARNING":2,"INFO":1,"UNKNOWN":0}
VERSION="1.0.0"
MODEL="gpt-4o-mini"

def load_env_file(path):
    data={}
    try:
        with open(path,"r",encoding="utf-8") as f:
            for ln in f:
                ln=ln.strip()
                if not ln or ln.startswith("#") or "=" not in ln: continue
                k,v=ln.split("=",1)
                data[k.strip()]=v.strip().strip('"').strip("'")
    except: pass
    return data

def get_api_key(prompt_if_missing=True):
    k=os.getenv("OPENAI_API_KEY")
    if k: return k.strip()
    for p in ENV_FILES:
        if p.exists():
            d=load_env_file(p)
            if "OPENAI_API_KEY" in d and d["OPENAI_API_KEY"]: return d["OPENAI_API_KEY"].strip()
    if prompt_if_missing:
        try: key=getpass.getpass("Enter OpenAI API key: ").strip()
        except: key=input("Enter OpenAI API key: ").strip()
        if not key: return None
        save=input("Save key to .env? (y/N): ").strip().lower()
        if save=="y":
            try: open(Path.cwd()/".env","a",encoding="utf-8").write(f'\nOPENAI_API_KEY="{key}"\n'); print("Saved .env")
            except: pass
        return key
    return None

def load_patterns():
    if os.path.exists(PATTERN_FILE):
        try: return json.load(open(PATTERN_FILE,"r",encoding="utf-8"))
        except: return {}
    return {}

def save_patterns(p):
    try: json.dump(p,open(PATTERN_FILE,"w",encoding="utf-8"),indent=2)
    except: pass

def parse_line(line):
    line=line.rstrip("\n")

    # Format 1: 2025-09-28 10:01:23 [LEVEL] [source] message
    m=re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+\[(\w+)\]\s+\[(.*?)\]\s+(.*)",line,re.I)
    if m:
        return {"timestamp":m[1],"level":m[2].upper(),"source":m[3],"message":m[4].strip()}

    # Format 2: LEVEL 2025-09-28 10:01:23 message
    m2=re.match(r"(INFO|WARN|WARNING|ERROR)\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(.*)",line,re.I)
    if m2:
        return {"timestamp":m2[2],"level":m2[1].upper(),"source":"","message":m2[3].strip()}

    # Format 3: [LEVEL] 2025-09-28 10:01:23 source - message
    m3=re.match(r"\[(INFO|WARN|WARNING|ERROR)\]\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(.*?)\s*-\s*(.*)",line,re.I)
    if m3:
        return {"timestamp":m3[2],"level":m3[1].upper(),"source":m3[3],"message":m3[4].strip()}

    # NEW: Android logcat format → MM-DD HH:MM:SS.mmm pid tid LEVEL tag: message
    m4=re.match(r"(\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+\d+\s+\d+\s+([A-Z])\s+(\S+):\s+(.*)",line)
    if m4:
        level_map={"V":"VERBOSE","D":"DEBUG","I":"INFO","W":"WARN","E":"ERROR","F":"FATAL"}
        return {"timestamp":m4[1],"level":level_map.get(m4[2],m4[2]),"source":m4[3],"message":m4[4].strip()}

    return {"timestamp":"","level":"UNKNOWN","source":"","message":line.strip()}

def suggest_hint(msg,patterns):
    for pat,h in patterns.items():
        if pat and pat in msg: return h
    low=msg.lower()
    if "outofmemory" in low or "heap space" in low: return "Possible memory issue."
    if "connection refused" in low: return "Service unreachable/network."
    if "timeout" in low: return "Network timeout."
    if "nullpointer" in low: return "Null reference detected."
    return "Unknown issue, needs review"

def collect_lines(path,level=None):
    if not os.path.exists(path): print("File not found:",path); return [],{}
    patterns=load_patterns()
    counts=collections.Counter()
    entries=[]
    with open(path,"r",encoding="utf-8",errors="ignore") as f:
        for line in f:
            d=parse_line(line)
            counts[d["level"]]+=1
            if level and d["level"].upper()!=level.upper(): continue
            hint=suggest_hint(d["message"],patterns)
            entries.append({"line":line.strip(),"level":d["level"],"timestamp":d["timestamp"],"message":d["message"],"hint":hint})
            if hint.startswith("Unknown") and d["message"] not in patterns: patterns[d["message"]]="Unknown issue"
    save_patterns(patterns)
    return entries,counts

def print_summary(entries,counts,n=10):
    print(f"Stats: INFO={counts.get('INFO',0)} WARN={counts.get('WARN',0)} ERROR={counts.get('ERROR',0)}")
    sorted_lines=sorted(entries,key=lambda x:(-LEVEL_ORDER.get(x["level"],0),x["timestamp"]))
    print("Top Issues:")
    for t in sorted_lines[:n]:
        sev=1 if t["level"]=="INFO" else 2
        print(f"{t['line']} (severity {sev})\n   → {t['hint']}")

def export_results(entries,out):
    if out.endswith(".json"): json.dump(entries,open(out,"w",encoding="utf-8"),indent=2)
    elif out.endswith(".csv"):
        keys=["timestamp","level","message","hint","line"]
        with open(out,"w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=keys); w.writeheader()
            for e in entries: w.writerow({k:e.get(k,"") for k in keys})
    print("Exported to",out)

def tail_file(path,lines=10):
    with open(path,"rb") as f:
        f.seek(0,2); sz=f.tell(); block=1024; data=[]
        while len(data)<lines and sz>0:
            read=min(block,sz); f.seek(sz-read)
            chunk=f.read(read).decode(errors="ignore").splitlines()
            data=chunk+data; sz-=read
    for l in data[-lines:]: print(l)

def build_context(entries,counts,top_n=10):
    top=sorted(entries,key=lambda x:(-LEVEL_ORDER.get(x["level"],0),x["timestamp"]))[:top_n]
    return {"stats":{"INFO":counts.get("INFO",0),"WARN":counts.get("WARN",0),"ERROR":counts.get("ERROR",0)},
            "top":[{"level":t["level"],"timestamp":t["timestamp"],"message":t["message"]} for t in top]}

def heuristic_summary(entries,counts):
    s=[]
    if counts.get("ERROR",0): s.append(f"{counts.get('ERROR')} error(s) detected")
    if counts.get("WARN",0): s.append(f"{counts.get('WARN')} warning(s) detected")
    if counts.get("INFO",0): s.append(f"{counts.get('INFO')} info messages")
    top_msgs=[e["message"] for e in entries[:5]]
    if top_msgs: s.append("Top messages: "+"; ".join(top_msgs))
    return "\n".join(s) if s else "No significant events."

def call_openai_chat(prompt,api_key,model=MODEL):
    if OpenAI is None: raise RuntimeError("openai not installed")
    client=OpenAI(api_key=api_key)
    resp=client.chat.completions.create(model=model,messages=[{"role":"user","content":prompt}],temperature=0.2,max_tokens=400)
    return resp.choices[0].message.content.strip()

def ai_summary(path,level=None,top_n=10):
    entries,counts=collect_lines(path,level)
    ctx=build_context(entries,counts,top_n)
    prompt="You are a DevOps assistant. Summarize logs.\nStats: "+str(ctx["stats"])+"\nTop issues:\n"
    for t in ctx["top"]: prompt+=f"- [{t['level']}] {t['timestamp']}: {t['message']}\n"
    prompt+="\nShort summary (3 bullets max)."
    api_key=get_api_key(False)
    if api_key and OpenAI:
        try: out=call_openai_chat(prompt,api_key); print("AI Summary:\n",out); return
        except Exception as e: print("AI failed, fallback. Error:",e)
    print("AI not available — heuristic summary:\n"); print(heuristic_summary(entries,counts))

def ai_chat(path):
    api_key=get_api_key(True)
    if not api_key or OpenAI is None: print("Chat unavailable."); return
    entries,counts=collect_lines(path)
    ctx=build_context(entries,counts,15)
    system="You are LogLens assistant."
    summary_text="Stats: "+str(ctx["stats"])+"\nTop:\n"
    for t in ctx["top"]: summary_text+=f"- [{t['level']}] {t['timestamp']}: {t['message']}\n"
    print("Context ready. Type questions (quit to exit).")
    client=OpenAI(api_key=api_key)
    while True:
        q=input("You: ").strip()
        if q.lower() in ("quit","exit"): break
        prompt=system+"\n\nLog context:\n"+summary_text+"\n\nUser question:\n"+q
        try:
            resp=client.chat.completions.create(model=MODEL,messages=[{"role":"user","content":prompt}],temperature=0.2,max_tokens=400)
            out=resp.choices[0].message.content.strip(); print("AI:",out)
        except Exception as e: print("AI error:",e); break

def show_version(): print("LogLens CLI version",VERSION)
def show_scope(): print("Supported logs: Python, Java, Node.js, Syslog. Android partial.")

def main():
    p=argparse.ArgumentParser(prog="loglens",description="LogLensAI CLI")
    sp=p.add_subparsers(dest="cmd")
    
    a = sp.add_parser("analyse"); a.add_argument("file"); a.add_argument("-n",type=int,default=10); a.add_argument("--level")
    t = sp.add_parser("tail"); t.add_argument("file"); t.add_argument("-n",type=int,default=10)
    s = sp.add_parser("ai-summary"); s.add_argument("file"); s.add_argument("--level"); s.add_argument("-n",type=int,default=10)
    c = sp.add_parser("chat"); c.add_argument("file")
    e = sp.add_parser("export"); e.add_argument("file"); e.add_argument("out")
    cfg = sp.add_parser("config"); cfg.add_argument("action",choices=["show-key","set-key"])
    sp.add_parser("version"); sp.add_parser("scope")
    
    args=p.parse_args()
    if not args.cmd: p.print_help(); sys.exit(1)
    
    if args.cmd=="analyse": entries,counts=collect_lines(args.file,args.level); print_summary(entries,counts,args.n)
    elif args.cmd=="tail": tail_file(args.file,args.n)
    elif args.cmd=="ai-summary": ai_summary(args.file,args.level,args.n)
    elif args.cmd=="chat": ai_chat(args.file)
    elif args.cmd=="export": entries,counts=collect_lines(args.file); export_results(entries,args.out)
    elif args.cmd=="version": show_version()
    elif args.cmd=="scope": show_scope()
    elif args.cmd=="config":
        if args.action=="show-key": k=get_api_key(False); print("Key present." if k else "No key.")
        elif args.action=="set-key": key=get_api_key(True); print("Key set." if key else "Not set.")
    else: p.print_help()

if __name__=="__main__": main()
