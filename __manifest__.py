# -*- coding: utf-8 -*-
{
    'name': 'Odoo-PostNL-Integration',
    'summary': 'Send confirmed sales orders to PostNL Fulfilment API',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'author': 'Custom4',
    'license': 'LGPL-3',
    'depends': ['sale_management'],
    "data": [
    "views/postnl_menu.xml",
    "views/postnl_order_views.xml",
    "views/postnl_config_views.xml",
],
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['requests'],
    },
}
