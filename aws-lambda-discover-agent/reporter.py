import json, csv

SYMBOLS = {"Easy":"[OK]","Moderate":"[~~]","Hard":"[!!]","Rewrite needed":"[XX]"}

def print_report(results):
    counts = {}
    for r in results:
        counts[r["label"]] = counts.get(r["label"], 0) + 1
    print("\n" + "="*60)
    print("LAMBDA -> AZURE MIGRATION FEASIBILITY REPORT")
    print("="*60)
    print(f"Total functions : {len(results)}")
    for label, count in counts.items():
        sym = SYMBOLS.get(label,"")
        print(f"  {sym} {label:20s}: {count}")
    print("\n--- Per-function detail (hardest first) ---\n")
    for r in results:
        sym = SYMBOLS.get(r["label"],"")
        print(f"{sym} [{r['score']:3}/100] {r['function']} ({r['runtime']})")
        for issue in r["issues"]:
            print(f"     > {issue}")
        print()

def save_csv(results, path="migration_report.csv"):
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["function","runtime",
                                           "score","label","issues"])
        w.writeheader()
        for r in results:
            row = dict(r)
            row["issues"] = " | ".join(r["issues"])
            w.writerow(row)
    print(f"CSV saved: {path}")

def save_json(results, path="migration_report.json"):
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"JSON saved: {path}")
