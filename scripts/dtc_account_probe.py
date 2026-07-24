#!/usr/bin/env python3
"""Read-only DTC probe (runs ON the Sierra box): logon, list trade accounts, positions, and
balance. Places NOTHING. Prints the exact Lucid account id + $ balance + open positions.

    python -m scripts.dtc_account_probe            # 127.0.0.1:11099
    python -m scripts.dtc_account_probe 11099
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.desk.dtc_client import DTCClient, DTCConfig  # noqa: E402

TRADE_ACCOUNTS_REQUEST = 400
TRADE_ACCOUNT_RESPONSE = 401


def main(port: int = 11099) -> int:
    c = DTCClient(DTCConfig(host="127.0.0.1", port=port))
    if not c.connect():
        print("LOGON FAILED — is Sierra's DTC server up on 127.0.0.1:%d?" % port)
        return 1
    print(f"logged on: {c.logged_on}")

    c._send(TRADE_ACCOUNTS_REQUEST, {"RequestID": 1})
    accts = [m for m in c._await(TRADE_ACCOUNT_RESPONSE, 4.0)
             if m.get("Type") == TRADE_ACCOUNT_RESPONSE]
    for a in accts:
        print(f"TRADE_ACCOUNT: {a.get('TradeAccount')!r}  "
              f"(index {a.get('TradeAccountNumber')}/{a.get('TotalNumberMessages')})")

    for p in c.positions():
        print("POSITION:", {k: p.get(k) for k in
                            ("TradeAccount", "Symbol", "Quantity", "AveragePrice")})
    b = c.account_balance()
    if b:
        print("BALANCE:", {k: b.get(k) for k in
                          ("TradeAccount", "CashBalance", "AccountCurrency",
                           "SecuritiesValue", "MarginRequirement")})
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 11099))
