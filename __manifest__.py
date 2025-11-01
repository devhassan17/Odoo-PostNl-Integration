# -*- coding: utf-8 -*-
{
    "name": "Odoo-PostNL-Integration",
    "summary": "Single Odoo app for PostNL: stage orders, export, import shipments, and map shipping codes.",
    "version": "18.0.1.1.2",
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
        "security/security.xml",
        "security/ir.model.access.csv",
        "views/postnl_menus.xml",
        "views/postnl_order_views.xml",
        "views/postnl_shipping_rule_views.xml",
        "views/res_config_settings_views.xml",
        "data/ir_cron_data.xml",
    ],
    "application": True,
    "installable": True,
}
