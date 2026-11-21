"""Holt fuer jeden Spieler in tiers.json die echten Tiers von MCTiers, PvPTiers und SubTiers.
Laeuft automatisch per GitHub Actions (siehe .github/workflows/tiers.yml)."""
import json, time, urllib.request, urllib.error

SOURCES = {
    "mctiers": "https://mctiers.com/api/v2/profile/",
    "pvptiers": "https://pvptiers.com/api/profile/",
    "subtiers": "https://subtiers.net/api/profile/",
}

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "PrimeTiers-Bot"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None

def modes_of(profile):
    out = {}
    for mode, r in (profile.get("rankings") or {}).items():
        if not isinstance(r, dict) or r.get("tier") is None or r.get("pos") is None:
            continue
        tag = ("HT" if int(r["pos"]) == 0 else "LT") + str(int(r["tier"]))
        if str(r.get("retired")).lower() == "true":
            tag = "R" + tag
        out[mode] = tag
    return out

def main():
    with open("tiers.json", encoding="utf-8") as f:
        data = json.load(f)
    players = data.get("players", data)
    for name, p in players.items():
        if not isinstance(p, dict):
            continue
        uuid = p.get("uuid")
        if not uuid:
            st, j = get("https://api.mojang.com/users/profiles/minecraft/" + name)
            if st != 200 or not j:
                continue
            uuid = p["uuid"] = j["id"]
        ext, complete = {}, True
        for src, base in SOURCES.items():
            st, j = get(base + uuid.replace("-", ""))
            if st == 200 and isinstance(j, dict):
                m = modes_of(j)
                if m:
                    ext[src] = {"modes": m, "points": j.get("points"), "region": j.get("region")}
            elif st != 404:
                complete = False          # Seite nicht erreichbar -> alte Daten behalten
                if src in (p.get("external") or {}):
                    ext[src] = p["external"][src]
            time.sleep(0.4)
        if ext:
            p["external"] = ext
        elif complete:
            p.pop("external", None)
    with open("tiers.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

if __name__ == "__main__":
    main()
