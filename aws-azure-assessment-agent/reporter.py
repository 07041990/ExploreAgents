import json, csv
from collections import defaultdict

SYMBOLS = {
    "Easy":           "[OK]",
    "Moderate":       "[~~]",
    "Hard":           "[!!]",
    "Rewrite needed": "[XX]",
}

def print_report(results):
    by_service = defaultdict(list)
    for r in results:
        by_service[r.get("service","Lambda")].append(r)

    total_counts = {}
    for r in results:
        total_counts[r["label"]] = total_counts.get(r["label"], 0) + 1

    print("\n" + "="*65)
    print("MULTI-SERVICE AWS -> AZURE MIGRATION FEASIBILITY REPORT")
    print("="*65)
    print(f"Total resources scanned: {len(results)}")
    for label, count in total_counts.items():
        print(f"  {SYMBOLS.get(label,'')} {label:22s}: {count}")

    for svc, items in sorted(by_service.items()):
        print(f"\n{'─'*65}")
        print(f"  {svc}  ({len(items)} resources)")
        print(f"{'─'*65}")
        for r in items:
            sym = SYMBOLS.get(r["label"],"")
            rt  = r.get("runtime","")
            rt_str = f" ({rt})" if rt else ""
            print(f"{sym} [{r['score']:3}/100] {r['function']}{rt_str}")
            for issue in r.get("issues",[]):
                print(f"       > {issue}")
            print()

def save_csv(results, path="migration_report.csv"):
    fieldnames = ["service","function","runtime","score","label","issues"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in results:
            row = dict(r)
            row["issues"] = " | ".join(r.get("issues",[]))
            w.writerow(row)
    print(f"CSV report saved: {path}")

def save_json(results, path="migration_report.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"JSON report saved: {path}")