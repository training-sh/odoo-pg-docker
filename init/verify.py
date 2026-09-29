"""Run inside the Odoo container: python3 /opt/training/verify.py."""
import json
import os
import urllib.request

import psycopg2

report = {}
request = urllib.request.Request(
    os.environ.get("ODOO_URL", "http://127.0.0.1:8069") + "/web/session/authenticate",
    data=json.dumps({"jsonrpc": "2.0", "method": "call", "id": 1,
                     "params": {"db": "odoo", "login": "team", "password": "team1234"}}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=30) as response:
    result = json.load(response)
assert result.get("result", {}).get("uid"), result
report["web_login"] = {"login": "team", "uid": result["result"]["uid"]}
connection = psycopg2.connect(
    host=os.environ.get("VERIFY_PGHOST", "odoopgsql"),
    port=os.environ.get("VERIFY_PGPORT", "5432"),
    user="team", password="team1234", dbname="odoo", connect_timeout=10,
)
connection.autocommit = True
try:
    with connection.cursor() as cursor:
        cursor.execute("SHOW wal_level")
        report["wal_level"] = cursor.fetchone()[0]
        assert report["wal_level"] == "logical"
        cursor.execute("SELECT name, state FROM ir_module_module WHERE name IN ('contacts','crm','sale_management','purchase','stock','account','website_sale') ORDER BY name")
        report["modules"] = dict(cursor.fetchall())
        assert len(report["modules"]) == 7 and set(report["modules"].values()) == {"installed"}
        report["rows"] = {}
        for table in ["res_partner", "product_product", "sale_order", "purchase_order", "account_move", "stock_move"]:
            cursor.execute("SELECT count(*) FROM " + table)
            report["rows"][table] = cursor.fetchone()[0]
            assert report["rows"][table] > 0, table
        cursor.execute("SELECT tablename FROM pg_publication_tables WHERE pubname = 'odoo_publication' ORDER BY tablename")
        report["publication_tables"] = [row[0] for row in cursor.fetchall()]
        assert len(report["publication_tables"]) == 8
        # Temporary slots are released automatically when this connection closes.
        cursor.execute("SELECT slot_name FROM pg_create_logical_replication_slot('odoo_verify_' || pg_backend_pid(), 'test_decoding', true)")
        slot = cursor.fetchone()[0]
        # Slot creation verifies the logical decoder can start on this database.
        cursor.execute("SELECT count(*) FROM pg_logical_slot_peek_changes(%s, NULL, NULL)", (slot,))
        report["logical_decoder"] = "test_decoding temporary slot created and queried"
finally:
    connection.close()
print(json.dumps(report, indent=2))
