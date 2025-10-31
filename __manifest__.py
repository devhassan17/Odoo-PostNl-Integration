{
    "name": "PostNL Base (Odoo 18)",
    "summary": "Connect Odoo 18 to PostNL: label creation, delivery options, pickup points, tracking, WBS rules.",
    "version": "18.0.1.0.0",
    "author": "You + ChatGPT",
    "website": "https://example.com",
    "category": "Inventory/Delivery",
    "license": "LGPL-3",
    "depends": ["base", "stock", "delivery", "sale_management", "website_sale"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/postnl_settings_views.xml",
        "views/postnl_wbs_views.xml",
        "views/postnl_shipment_views.xml",
        "views/delivery_carrier_views.xml",
        "views/sale_order_views.xml",
        "wizard/generate_label_wizard_views.xml",
        "views/website_checkout_templates.xml"
    ],
    "assets": {
        "web.assets_frontend": [
            "postnl_base/static/src/js/postnl_checkout.js",
            "postnl_base/static/src/xml/postnl_templates.xml"
        ]
    },
    "installable": True,
    "application": False
}
