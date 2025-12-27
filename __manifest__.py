# -*- coding: utf-8 -*-
{
    'name': 'Odoo-PostNl Integration',
    'summary': 'Send confirmed sales orders to PostNL Fulfilment API',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'images': ['static/description/icon.png'],
    'author': 'Ali Hassan7',
    'depends': ['sale_management'],
    'data': [
    'security/ir.model.access.csv',

    # views first (actions)
    'views/postnl_order_log_views.xml',
    'views/postnl_config_views.xml',

    # menus LAST
    'views/postnl_menu.xml',
],

    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': ['requests'],
    },
}
