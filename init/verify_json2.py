"""Check JSON-2 Bearer authentication using the private project .api.env file."""
import argparse
import json
from pathlib import Path
import urllib.request
import urllib.error

parser = argparse.ArgumentParser()
parser.add_argument("--url", required=True, help="http://your-hostname:9999")
args = parser.parse_args()
settings = dict(line.split("=", 1) for line in (Path(__file__).resolve().parents[1] / ".api.env").read_text().splitlines() if line and not line.startswith("#"))
def request(model, body, token):
    req = urllib.request.Request(args.url.rstrip("/") + "/json/2/" + model + "/search_read",
        data=json.dumps(body).encode(), headers={"Authorization": "Bearer " + token,
        "X-Odoo-Database": "odoo", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.status, json.load(response)
for model, fields in [("product.product", ["id", "name", "qty_available"]), ("stock.quant", ["id", "product_id", "quantity"]), ("sale.order", ["id", "name", "amount_total"])]:
    status, rows = request(model, {"domain": [], "fields": fields, "limit": 3}, settings["ODOO_API_KEY"])
    assert status == 200 and isinstance(rows, list) and rows
    print(f"PASS {model}: HTTP {status}, {len(rows)} records")
try:
    request("product.product", {"domain": [], "fields": ["id"], "limit": 1}, "invalid-test-token")
except urllib.error.HTTPError as exc:
    assert exc.code == 401, exc.code
    print("PASS invalid Bearer token: HTTP 401")
else:
    raise AssertionError("Invalid token was accepted")
print("API key expires: " + settings["ODOO_API_KEY_EXPIRES"])
