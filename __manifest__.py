# -*- coding: utf-8 -*-
{
    "name": "PostNL Connector (WooCommerce Bridge)",
    "summary": "One app to stage orders for PostNL and configure shipping-code rules (Odoo 18).",
    "version": "18.0.1.0.0",
    "category": "Operations/Warehouse",
    "author": "Your Company",
    "website": "https://example.com",
    "license": "LGPL-3",
    "depends": ["base", "mail", "sale_management", "stock", "contacts"],
    "data": [
        # Security
        "security/security.xml",
        "security/ir.model.access.csv",
        # Menus first (root before children)
        "views/postnl_menus.xml",
        # Views
        "views/postnl_order_views.xml",
        "views/postnl_shipping_rule_views.xml",
        "views/res_config_settings_views.xml",
        # Crons
        "data/ir_cron_data.xml",
    ],
    "assets": {},
    "application": True,
    "installable": True,
}