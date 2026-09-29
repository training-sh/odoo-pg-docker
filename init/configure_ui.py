"""Apply the training interface settings through the Odoo ORM."""
for xmlid in ("mail.menu_root_discuss", "mail.main_menu_discuss"):
    menu = env.ref(xmlid)
    if menu.active:
        menu.write({"active": False})

# Avoid landing on Discuss after login when a user has it as their home action.
discuss = env.ref("mail.action_discuss")
sales = env.ref("sale.action_quotations_with_onboarding", raise_if_not_found=False)
home = sales or env.ref("contacts.action_contacts")
users = env["res.users"].with_context(active_test=False).search([("action_id", "=", discuss.id)])
users.write({"action_id": home.id})
admin = env.ref("base.user_admin")
if not admin.action_id:
    admin.write({"action_id": home.id})
# PDF rendering must fetch assets locally rather than through the external host.
env["ir.config_parameter"].sudo().set_param("report.url", "http://127.0.0.1:8069")
env.cr.commit()
env.registry.signal_changes()
print("Discuss app hidden; messaging dependencies retained for business applications.")
