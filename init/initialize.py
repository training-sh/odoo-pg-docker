"""Initialize this training database once; ordinary restarts preserve all edits."""
import os
import subprocess
from pathlib import Path

import psycopg2

def configure_ui():
    subprocess.run([
        "odoo", "shell", "--config=/etc/odoo/odoo.conf", "--database=odoo", "--no-http",
    ], input=Path(__file__).with_name("configure_ui.py").read_text(), text=True, check=True)


with psycopg2.connect(
    host=os.environ["HOST"], port=os.environ["PORT"],
    user=os.environ["USER"], password=os.environ["PASSWORD"], dbname="odoo",
) as connection:
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('public.ir_config_parameter')")
        if cursor.fetchone()[0]:
            cursor.execute(
                "SELECT value FROM ir_config_parameter WHERE key = %s",
                ("training.initialized",),
            )
            if cursor.fetchone() == ("yes",):
                print("Training database already initialized; preserving users and data.", flush=True)
                configure_ui()
                raise SystemExit(0)

subprocess.run([
    "odoo", "--config=/etc/odoo/odoo.conf", "--database=odoo",
    "--init=base,contacts,crm,sale_management,purchase,stock,account,website_sale,payment_demo",
    "--with-demo", "--stop-after-init", "--no-http",
], check=True)

subprocess.run([
    "odoo", "shell", "--config=/etc/odoo/odoo.conf", "--database=odoo", "--no-http",
], input='''
env.ref("base.main_company").write({"name": "AlturaWave"})
admin = env.ref("base.user_admin")
admin.write({"login": "team", "password": "team1234", "name": "Training Team"})
# Disable other interactive demo logins; their business sample records remain.
env["res.users"].search([("id", "!=", admin.id), ("active", "=", True), ("share", "=", False)]).write({"active": False})
env.cr.execute("SELECT 1 FROM pg_publication WHERE pubname = 'odoo_publication'")
if not env.cr.fetchone():
    env.cr.execute("""CREATE PUBLICATION odoo_publication FOR TABLE
        res_partner, product_template, product_product, sale_order,
        sale_order_line, account_move, account_move_line, stock_move""")
env["ir.config_parameter"].sudo().set_param("training.initialized", "yes")
env.cr.commit()
print("Training database initialized with demo data and login team.")
''', text=True, check=True)

configure_ui()
