# -*- coding: utf-8 -*-
{
    'name': 'Odoo-PostNL-Integration',
    'summary': 'Send confirmed sales orders to PostNL Fulfilment API',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': ['sale_management'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'external_dependencies': {
        'python': ['requests'],
    },
}
