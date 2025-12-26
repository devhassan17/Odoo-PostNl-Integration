# -*- coding: utf-8 -*-
{
    'name': 'Odoo-PostNL-Integration',
    'summary': 'Send confirmed sales orders to PostNL Fulfilment API',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'images': ['static/description/icon.png'],
    'author': 'Ali Hassan1',
    'depends': ['sale_management'],
    "data": [
    "security/ir.model.access.csv",
    "views/postnl_menu.xml",
    "views/postnl_order_log_views.xml",
    "views/postnl_config_views.xml",
],
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['requests'],
    },
}
