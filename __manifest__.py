# -*- coding: utf-8 -*-
{
    "name": "PostNL Logistics Hub",
    "summary": "PostNL hub for Odoo: stage orders, export (orders/products), import (shipments/stock), delivery options, age-check, gift messages, and rule-based shipping codes.",
    "version": "18.0.2.2.0",
    "category": "Operations/Warehouse",
    "author": "Your Company",
    "website": "https://example.com",
    "license": "LGPL-3",
    "depends": ["base", "mail", "sale_management", "stock", "contacts"],
    # Apps card thumbnail (launcher icon comes from menu web_icon below)
    "icon": "static/description/icon.png",
    "images": ["static/description/icon.png"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/postnl_menus.xml",               # ROOT FIRST (creates launcher tile)
        "views/postnl_order_views.xml",
        "views/postnl_shipping_rule_views.xml",
        "views/res_config_settings_views.xml",
        "views/sale_postnl_views.xml",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
    ],
    "application": True,
    "installable": True,
}
