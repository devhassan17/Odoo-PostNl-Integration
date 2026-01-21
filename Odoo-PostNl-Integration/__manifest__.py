# -*- coding: utf-8 -*-
{
    'name': 'Odoo-PostNl Integration',
    'summary': 'Send confirmed sales orders to PostNL Fulfilment API',
    'version': '1.0.0',
    'category': 'Sales',
    'images': ['static/description/icon.png'],
    "author": "Managemyweb.co",
    "website": "https://fairchain.org/Odoo-PostNl-Integration/",
    "category": "Warehouse",
    "license": "LGPL-3",
    "images": ["static/description/banner.png"],

    'depends': [
        'sale_management',
        'stock',   # IMPORTANT: picking / carrier_tracking_ref
        'base',
    ],

    'data': [
        # 🔐 Security
        'security/ir.model.access.csv',

        # ⏱️ Cron
        'data/ir_cron.xml',

        # 👁️ Views (actions first)
        'views/postnl_order_log_views.xml',
        'views/postnl_config_views.xml',
        'views/postnl_replenishment_views.xml',

        # 📂 Menus LAST
        'views/postnl_menu.xml',
    ],

    'installable': True,
    'application': True,
    'auto_install': False,
    "support": "programmer.alihassan@gmail.com",
    "price": 199.99,
    "currency": "USD",
    'external_dependencies': {
        'python': ['requests'],
    },
}
