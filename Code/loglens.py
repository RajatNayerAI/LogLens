import sys,json,re,os,collections,argparse,csv

PATTERN_FILE="patterns.json"
LEVEL_ORDER={"ERROR":3,"WARN":2,"WARNING":2,"INFO":1,"UNKNOWN":0}

def load_patterns():
    if os.path.exists(PATTERN_FILE):
        with open(PATTERN_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_patterns(pats):
    with open(PATTERN_FILE,"w",encoding="utf-8") as f:
        json.dump(pats,f,indent=2)

def parse_line(line):
    # VS Code style: timestamp [level] [source] message
    m=re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)\s+\[(\w+)\]\s+\[(.*?)\]\s+(.*)",line,re.IGNORECASE)
    if m: return {"timestamp":m[1],"level":m[2].upper(),"source":m[3],"message":m[4].strip()}
    # Simple dev/server style: LEVEL TIMESTAMP MESSAGE
   # Java server log: [LEVEL] TIMESTAMP SOURCE - Message
    m2 = re.match(r"\[(INFO|WARN|WARNING|ERROR)\]\s+(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(.*?)\s*-\s*(.*)", line, re.IGNORECASE)
    if m2:
        return {"timestamp": m2[2], "level": m2[1].upper(), "source": m2[3], "message": m2[4].strip()}
    return {"timestamp":"","level":"UNKNOWN","source":"","message":line.strip()}

def colour_line(d):
    c={"INFO":"\033[32m","WARN":"\033[33m","WARNING":"\033[33m","ERROR":"\033[31m","UNKNOWN":"\033[0m"}
    return f"{c.get(d['level'],'\033[0m')}{d['timestamp']} [{d['level']}] [{d['source']}] {d['message']}\033[0m"

def suggest_hint(msg,patterns):
    for pat,hint in patterns.items():
        if pat in msg: return hint
    return "Unknown issue, needs review"

def analyse_file(path,level=None,n=10,export=None):
    if not os.path.exists(path): print("File not found"); return
    pats=load_patterns()
    counts=collections.Counter();all_lines=[]
    with open(path,"r",encoding="utf-8",errors="ignore") as f:
        for line in f:
            d=parse_line(line)
            counts[d["level"]]+=1
            if level and d["level"].upper()!=level.upper(): continue
            hint=suggest_hint(d["message"],pats)
            all_lines.append({"line":line.strip(),"level":d["level"],"timestamp":d["timestamp"],"hint":hint})
            if hint.startswith("Unknown") and d["message"] not in pats:
                pats[d["message"]]="Unknown issue, needs review"
    # Sort by severity and timestamp
    sorted_lines=sorted(all_lines,key=lambda x:(-LEVEL_ORDER.get(x["level"],0),x["timestamp"]))
    print(f"Stats: INFO={counts.get('INFO',0)} WARN={counts.get('WARN',0)} ERROR={counts.get('ERROR',0)}")
    print(f"Likely Source Language: Unknown\n")
    print("Top Critical Issues:")
    for t in sorted_lines[:n]:
        sev=1 if t["level"]=="INFO" else 2
        print(f"{t['line']} (severity {sev})\n   → {t['hint']}")
    if export:
        if export.endswith(".json"):
            with open(export,"w",encoding="utf-8") as f: json.dump(sorted_lines[:n],f,indent=2)
        elif export.endswith(".csv"):
            keys=["line","level","hint","timestamp"]
            with open(export,"w",newline="",encoding="utf-8") as f:
                writer=csv.DictWriter(f,fieldnames=keys)
                writer.writeheader()
                writer.writerows(sorted_lines[:n])
        print(f"Exported results to {export}")
    save_patterns(pats)

def tail_file(path,lines=10):
    with open(path,"rb") as f: f.seek(0,2);sz=f.tell();l=[];blk=1024
    while len(l)<lines and sz>0:
        to_read=min(blk,sz)
        f.seek(sz-to_read)
        blk_data=f.read(to_read).decode(errors="ignore").splitlines()
        l=blk_data+l
        sz-=to_read
    return l[-lines:]

def main():
    parser=argparse.ArgumentParser(description="LogLens CLI - Analyse logs quickly")
    parser.add_argument("action",choices=["analyse","tail"],help="Action to perform")
    parser.add_argument("file",help="Log file path")
    parser.add_argument("--level",help="Filter by level INFO/WARN/ERROR")
    parser.add_argument("--lines","-n",type=int,default=10,help="Number of top lines")
    parser.add_argument("--export",help="Export results to JSON/CSV")
    args=parser.parse_args()
    if args.action=="analyse": analyse_file(args.file,args.level,args.lines,args.export)
    elif args.action=="tail":
        for l in tail_file(args.file,args.lines): print(l)

if __name__=="__main__": main()
