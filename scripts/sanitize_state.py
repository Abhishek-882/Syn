import json
from pathlib import Path

state_path = Path("results/syndicate_3d_state.json")
if state_path.exists():
    data = json.loads(state_path.read_text(encoding="utf-8"))
    launches = data.get("recent_token_launches", [])
    clean_launches = [
        l for l in launches
        if l.get("mint_address") != "4dNj3ykr7iHv2AfjgkC9YesgUvCZ4qEJ7beQxy3RZ3XX"
        and l.get("symbol") != "BELUGA"
    ]
    for l in clean_launches:
        if not l.get("gmgn_url"):
            mint = l.get("mint_address", "")
            l["gmgn_url"] = f"https://gmgn.ai/sol/token/{mint}"
    data["recent_token_launches"] = clean_launches
    state_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Sanitized syndicate_3d_state.json: {len(clean_launches)} launches remaining.")
    if clean_launches:
        print(f"Top Launch: {clean_launches[0]['symbol']} ({clean_launches[0]['mint_address']})")
        print(f"GMGN: {clean_launches[0]['gmgn_url']}")
        print(f"DexScreener: {clean_launches[0].get('dex_screener_url')}")
