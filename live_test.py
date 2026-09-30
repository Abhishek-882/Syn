import sys; sys.path.insert(0,'src')
from dotenv import load_dotenv; load_dotenv('.env')
from crypto_syndicate.api.gmgn_client import GMGNClient
import json

client = GMGNClient(mock_mode=False)
launches = client.get_new_token_launches(chain='sol', limit=20)
print(f"Got {len(launches)} live launches")
for t in launches[:5]:
    print(f"  Token: {t.symbol} | deployer: {t.deployer_address[:16]}... | launch: {t.launch_timestamp}")
    trades = client.get_token_trades(chain='sol', token_address=t.token_address, limit=50)
    if trades:
        buy_times = [tr.timestamp - t.launch_timestamp for tr in trades if tr.direction=='buy']
        early = [bt for bt in buy_times if 0 < bt < 300]
        print(f"    Trades: {len(trades)} | Early buyers (<5min): {len(early)} | Fastest: {min(early) if early else 'none'}s")
