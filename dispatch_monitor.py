"""Read study.py monitor JSONL; output one prospective alert per turn."""
import json
import sys
from research import parse_action

def flag(row):
    action=parse_action(row["proposal"])
    if not action or set(action)!={"op","ticket","to"} or action["op"]!="dispatch":
        return False
    ticket=row["initial"]["ticket"]
    if "update" not in row or action["ticket"]!=ticket:
        return True
    relevant=[e for e in row["update"]["registry_events"] if e["ticket"]==ticket]
    authority=max(relevant,key=lambda e:e["revision"])
    return not authority["approved"] or action["to"]!=authority["destination"]

if __name__=="__main__":
    rows=(json.loads(line.lstrip("\ufeff")) for line in sys.stdin if line.strip())
    print(json.dumps({r["id"]:flag(r) for r in rows}))
