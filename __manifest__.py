# postnl_odoo_integration/__manifest__.py
{
    "name": "Odoo-PostNL-Integration",
    "summary": "Connect Odoo 18 with PostNL (orders export, shipments import, weight-based shipping codes).",
    "version": "18.0.1.0.0",
    "author": "Ali Hassan4",
    "license": "LGPL-3",
    "category": "Inventory/Shipping",
    "depends": [
        "base",
        "sale_management",
        "stock",
        "product",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/postnl_shipping_rule_views.xml",
        "views/sale_order_views.xml",
        "views/stock_picking_views.xml",
        "data/ir_cron_postnl_shipment_import.xml",
    ],
    "installable": True,
    "application": False,
}
