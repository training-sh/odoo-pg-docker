"""Run with Odoo shell; all synthetic verification writes are rolled back."""
from uuid import uuid4
provider = env.ref("payment.payment_provider_demo")
assert provider.code == "demo" and provider.state == "test" and provider.is_published
method = env.ref("payment_demo.payment_method_demo")
assert method in provider.payment_method_ids and method.active
website = env["website"].search([], limit=1)
assert website.company_id == provider.company_id
transaction = env["payment.transaction"].create({
    "provider_id": provider.id,
    "payment_method_id": method.id,
    "reference": "DEMO-VERIFY-" + uuid4().hex[:12],
    "amount": 1.0,
    "currency_id": provider.company_id.currency_id.id,
    "partner_id": env.ref("base.user_admin").partner_id.id,
    "operation": "online_direct",
})
transaction.action_demo_set_done()
assert transaction.state == "done", transaction.state
print("PASS: published Demo provider in Test Mode; simulated payment completed without a gateway.")
env.cr.rollback()
