# Odoo training

Odoo 19 Community and PostgreSQL 16, with built-in demo data for Contacts,
CRM, Sales, Purchase, Inventory, Invoicing, and eCommerce.

# Nginx patch


## PGWeb

```
sudo tee /etc/nginx/snippets/pgweb.conf > /dev/null <<'EOF'
location = /pgweb {
    return 301 /pgweb/;
}

location /pgweb/ {
    proxy_pass http://127.0.0.1:8807/pgweb/;

    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
EOF
```

```
sudo nano /etc/nginx/sites-available/default
```

paste this along with other include config like jupyter

```
include /etc/nginx/snippets/pgweb.conf;
```


## Connect

Open **http://your-hostname:9999**. Replace `your-hostname` with your server hostname.

| Setting | Value |
|---|---|
| Company name | `AlturaWave` |
| Odoo login | `team` |
| Odoo password | `team1234` |
| PostgreSQL host | `your-hostname` |
| PostgreSQL port | `55432` |
| PostgreSQL database | `odoo` |
| PostgreSQL username | `team` |
| PostgreSQL password | `team1234` |
| Containers / internal hostnames | `odoo`, `odoopgsql` |

These are shared training credentials. The database role has administrative
permissions. Keep access on the trusted training network.
Access PostgreSQL at `your-hostname:55432` and Odoo at `http://your-hostname:9999`.
Within Docker, PostgreSQL is `odoopgsql:5432` and Odoo is `odoo:8069`.

## Get started

Install Docker with Compose v2 on the computer that will run the services.
Clone the course repository and, from its root directory, run:


open terminal 

```
git clone https://github.com/training-sh/odoo-pg-docker
```

```
cd odoo-pg-docker
```

```bash
docker compose up -d --wait --wait-timeout 900
docker compose ps -a
docker compose logs --tail=60 odoo-init odoo
```

If you copy this folder separately, open the directory containing
`docker-compose.yaml` and run the same Compose commands there.
For a remote server, connect using `ssh your-username@your-hostname` first.
Run all commands below from the directory containing `docker-compose.yaml`.

Initialization can take several minutes. The application starts only after the
database is healthy and `odoo-init` completes successfully.

The first initialization sets the main company name to **AlturaWave**, installs demo data, and sets the administrator login.
Later runs detect the initialization marker and preserve records and passwords.
The stopped `odoo-init` container with exit code 0 is expected. Scheduled jobs
are disabled for this lab. No outgoing email or live payment service is configured.
Other internal demo logins are disabled; their sample records are retained.

```bash
# Stop/start without deleting data:
docker compose stop
docker compose up -d --wait --wait-timeout 900

# Database access on the VM:
docker compose exec odoopgsql psql -U team -d odoo

# Database access from another computer; enter team1234 when prompted:
psql -h your-hostname -p 55432 -U team -d odoo -W
```

Named volumes `odoo_training-postgres-data` and `odoo_training-odoo-data`
preserve the database and attachments. `docker compose down` preserves these;
**`docker compose down -v` deletes this training dataset**.

Database-manager pages are disabled (`list_db = False`). The configured master
password is `team1234master`; it is separate from the web login.

## PostgreSQL WAL / CDC

Logical decoding is enabled with `wal_level=logical`, 10 replication slots,
10 WAL senders, and `max_slot_wal_keep_size=1GB`. Publication `odoo_publication`
includes eight business tables: `res_partner`, `product_template`,
`product_product`, `sale_order`, `sale_order_line`, `account_move`,
`account_move_line`, and `stock_move`.

```bash
docker compose exec odoopgsql psql -U team -d odoo -c 'SHOW wal_level;'
docker compose exec odoopgsql psql -U team -d odoo -c 'TABLE pg_publication_tables;'
docker compose exec odoopgsql psql -U team -d odoo -c 'SELECT slot_name, plugin, active FROM pg_replication_slots;'
```

No permanent slot or CDC consumer is created automatically. A CDC exercise can
use `pgoutput` with the publication, or the built-in `test_decoding` plugin for
SQL decoding. Consume slots regularly and drop unused slots; the 1 GB retention
cap can invalidate a lagging slot. WAL decoding covers row changes, not a full
DDL audit trail. PostgreSQL WAL is enabled; no separate product named PGWall is
installed.

## References

- [Official Odoo Docker image](https://github.com/odoo/docker/tree/master/19.0)
- [Odoo 19 command-line options](https://www.odoo.com/documentation/19.0/developer/reference/cli.html)
- [PostgreSQL 16 logical replication settings](https://www.postgresql.org/docs/16/logical-replication-config.html)

## Verify the setup

```bash
docker compose exec -T odoo python3 /opt/training/verify.py
```

The check authenticates the web login, verifies installed applications and sample
records, checks the eight publication tables, and opens and queries a temporary
logical decoding slot. It leaves no permanent replication slot. If you later
change the training password, update the check accordingly.

## Deployment verification (2026-09-29)

- Both application and database containers are healthy.
- Web login and database port `55432` were verified from a client computer.
- PostgreSQL authentication through published port `55432` returned user `team`
  and database `odoo`.
- Initial sample counts: 44 contacts, 53 product variants, 40 sales orders,
  11 purchase orders, 56 accounting entries, and 90 stock moves.
- Logical decoder slot creation/query and the eight-table publication passed.
- Repeating `docker compose up` preserved the login and sample counts.

`verification.json` contains the initial check results. Counts may change as
students use the application. Use Docker service names inside containers;
use `your-hostname:9999` and `your-hostname:55432` from client computers.

## Discuss interface

The Discuss application is hidden from the app menu. Users whose home action
was Discuss are directed to Sales (or Contacts), and the training administrator
gets that home action if none was set. These settings are applied automatically
on first initialization and subsequent Compose startup by `init/configure_ui.py`.

Odoo's underlying `mail` module remains installed because business applications
use it for record notes, activities, and notifications. This hides the Discuss
app; it does not remove all chat/notification icons or block direct Discuss URLs.

## Demo payments (no real money)

The built-in `payment_demo` module is installed automatically on first startup.
The Demo provider is published in **Test Mode** so students can simulate online
payments without a payment gateway account, real card, or money transfer.

Open **Website → Configuration → Payment Providers → Demo** to inspect its
settings. At website checkout, select **Demo**, choose a successful payment
status, and submit the payment. The resulting transaction is recorded in Odoo.
You can also simulate pending, cancelled, and failed payments using this provider.
Use fictional payment details only. Demo payment completion is separate from
invoice creation and accounting reconciliation.

## Printing and PDF reports

Initialization configures `report.url` to use Odoo's internal HTTP service.
This lets the PDF renderer load report styles and images without routing back
through the external server address. Browser access remains
`http://your-hostname:9999`. This setting is reapplied during Compose startup.

## JSON-2 API with Bearer authentication

Odoo 19 JSON-2 is enabled. Each user needs their own API key; the web password
is not a JSON-2 Bearer token. Create a key from the user's account security
settings. Keep keys outside source control and renew them before expiration.
Keys inherit the user's permissions; a `team` key has administrator access.

For the current training instance, a verified key is stored in the private
`.api.env` file beside `docker-compose.yaml` (expires 2026-10-29). This file is
not included in clones, and Compose does not automatically issue API keys.
To use the verification script on a new instance, create `.api.env` with
`ODOO_API_KEY=<your-key>` and `ODOO_API_KEY_EXPIRES=<expiration-date>`.

```bash
python3 init/verify_json2.py --url http://your-hostname:9999
```

Request example (Bash, from the project directory):

```bash
source .api.env
curl --fail-with-body http://your-hostname:9999/json/2/product.product/search_read \
  -H "Authorization: Bearer $ODOO_API_KEY" \
  -H "X-Odoo-Database: odoo" \
  -H "Content-Type: application/json" \
  --data '{"domain": [], "fields": ["id", "name", "qty_available"], "limit": 5}'
```

JSON-2 accepts the method arguments directly as JSON, without a JSON-RPC envelope.
Bearer access was verified for products, stock quantities, and sales orders
(HTTP 200); an invalid token was rejected (HTTP 401).

## Adminer database browser

Compose starts Adminer automatically alongside PostgreSQL. Open
**http://your-hostname:8806** and enter:

| Field | Value |
|---|---|
| System | PostgreSQL |
| Server | `odoopgsql` (preselected) |
| Username | `team` |
| Password | `team1234` |
| Database | `odoo` |

Adminer connects to PostgreSQL on its internal Docker port, so use `odoopgsql`
as the server, not the external port `55432`. The password is entered at login;
Adminer does not automatically log in. After login, select a table to browse
records or choose **SQL command** to run queries.

The container name `odoo-adminer` and host port `8806` must be available before
starting this Compose project.
