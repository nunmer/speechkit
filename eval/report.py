import csv
from pathlib import Path

try:
    from tabulate import tabulate
    _HAS_TABULATE = True
except ImportError:
    _HAS_TABULATE = False


def aggregate(records: list[dict], by: str = "condition") -> list[dict]:
    groups: dict[str, list] = {}
    for rec in records:
        if rec.get("status") != "ok":
            continue
        key = rec.get(by, "unknown")
        groups.setdefault(key, []).append(rec)

    rows = []
    for key, recs in sorted(groups.items()):
        wers = [float(r["wer"]) for r in recs if r["wer"] != ""]
        cers = [float(r["cer"]) for r in recs if r["cer"] != ""]
        rtfs = [float(r["rtf"]) for r in recs if r["rtf"] != ""]
        rows.append({
            "condition": key,
            "n": len(recs),
            "mean_wer": round(sum(wers) / len(wers), 4) if wers else "",
            "mean_cer": round(sum(cers) / len(cers), 4) if cers else "",
            "mean_rtf": round(sum(rtfs) / len(rtfs), 4) if rtfs else "",
        })

    # Overall row
    all_ok = [r for r in records if r.get("status") == "ok"]
    if all_ok:
        wers = [float(r["wer"]) for r in all_ok if r["wer"] != ""]
        cers = [float(r["cer"]) for r in all_ok if r["cer"] != ""]
        rtfs = [float(r["rtf"]) for r in all_ok if r["rtf"] != ""]
        rows.append({
            "condition": "OVERALL",
            "n": len(all_ok),
            "mean_wer": round(sum(wers) / len(wers), 4) if wers else "",
            "mean_cer": round(sum(cers) / len(cers), 4) if cers else "",
            "mean_rtf": round(sum(rtfs) / len(rtfs), 4) if rtfs else "",
        })

    return rows


def write_csv(records: list[dict], path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not records:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)


def print_table(rows: list[dict]):
    if not rows:
        print("No results.")
        return
    if _HAS_TABULATE:
        print(tabulate(rows, headers="keys", tablefmt="simple", floatfmt=".4f"))
    else:
        headers = list(rows[0].keys())
        print("\t".join(headers))
        for row in rows:
            print("\t".join(str(row[h]) for h in headers))


def mos_summary(rating_rows: list[dict]) -> list[dict]:
    groups: dict[str, list] = {}
    for row in rating_rows:
        cat = row.get("category", "unknown")
        nat = row.get("naturalness_1_5", "")
        intel = row.get("intelligibility_1_5", "")
        if nat == "" and intel == "":
            continue
        groups.setdefault(cat, []).append((nat, intel))

    summaries = []
    for cat, scores in sorted(groups.items()):
        nats = [float(n) for n, _ in scores if n != ""]
        intels = [float(i) for _, i in scores if i != ""]
        summaries.append({
            "category": cat,
            "n": len(scores),
            "mean_naturalness": round(sum(nats) / len(nats), 2) if nats else "",
            "mean_intelligibility": round(sum(intels) / len(intels), 2) if intels else "",
        })

    return summaries
