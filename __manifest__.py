# -*- coding: utf-8 -*-
{
    "name": "monta — postnl integration",
    "summary": "PostNL for Odoo via Monta: stage orders, export orders/products, import shipments/stock, delivery options, age check, gift messages, rule-based shipping codes.",
    "version": "18.0.3.0.0",
    "category": "Operations/Warehouse",
    "author": "Your Company",
    "website": "https://example.com",
    "license": "LGPL-3",
    "depends": ["base", "mail", "sale_management", "stock", "contacts"],
    # We no longer need our own launcher tile; we live under Monta
    "application": True,
    "installable": True,
    "icon": "static/description/icon.png",
    "images": ["static/description/icon.png"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/postnl_menus.xml",               # load menus early
        "views/postnl_order_views.xml",
        "views/postnl_shipping_rule_views.xml",
        "views/res_config_settings_views.xml",
        "views/sale_postnl_views.xml",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
    ],
    "post_init_hook": "post_init_hook",         # <— reparent our app under Monta
}
