# -*- coding: utf-8 -*-
def _find_monta_root_menu(env):
    Menu = env["ir.ui.menu"]
    # Try a few common xmlids from Monta; fall back to heuristic search
    for xmlid in ("monta.menu_monta_root", "monta.menu_root", "monta.main_menu", "monta.monta_menu_root"):
        try:
            m = env.ref(xmlid)
            if m and not m.parent_id:
                return m
        except Exception:
            pass
    # Heuristic: a top-level menu whose name contains 'monta' and has a web_icon
    return Menu.search([("parent_id", "=", False), ("name", "ilike", "monta")], limit=1)

def post_init_hook(cr, registry):
    from odoo.api import Environment
    env = Environment(cr, 1, dict(active_test=False))
    monta_root = _find_monta_root_menu(env)
    if not monta_root:
        return  # Monta not installed; keep our own root (no crash)

    Menu = env["ir.ui.menu"]
    try:
        root = env.ref("Odoo-PostNl-Integration.menu_postnl_root")
    except Exception:
        try:
            root = env.ref("Odoo-PostNl-Integration.menu_postnl_root", raise_if_not_found=False)
        except Exception:
            root = Menu.search([("xml_id", "=", "menu_postnl_root")], limit=1)

    if root:
        # Move our entire subtree under Monta root; this hides our separate tile automatically
        root.write({"parent_id": monta_root.id})
