# -*- coding: utf-8 -*-
{
    "name": "Odoo-PostNL-Integration",
    "summary": "Single Odoo app for PostNL: stage orders, export (orders/products), import (shipments/stock), delivery options, age-check, gift messages, and rule-based shipping codes.",
    "version": "18.0.2.1.0",
    "category": "Operations/Warehouse",
    "author": "Your Company",
    "website": "https://example.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "sale_management",
        "stock",
        "contacts",
    ],
    # The Apps store card uses this file; the home launcher uses the root menu's web_icon.
    "icon": "static/description/icon.png",
    "images": ["static/description/icon.png"],
    "data": [
        # ROOT MENU FIRST so the launcher tile exists
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/postnl_menus.xml",
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
