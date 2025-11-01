# -*- coding: utf-8 -*-
{
    "name": "Odoo-PostNL-Integration",
    "summary": "Single Odoo app for PostNL: stage orders, export (orders/products), import (shipments/stock), delivery options, age-check, gift messages, and rule-based shipping codes.",
    "version": "18.0.2.0.0",
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
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        # Menus and views
        "views/postnl_menus.xml",
        "views/postnl_order_views.xml",
        "views/postnl_shipping_rule_views.xml",
        "views/res_config_settings_views.xml",
        "views/sale_postnl_views.xml",

        # Data
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
    ],
    "application": True,
    "installable": True,
}
