# -*- coding: utf-8 -*-

from odoo import fields, models


class PostNLOrderLog(models.Model):
    """Technical log of all PostNL API attempts."""

    _name = 'postnl.order.log'
    _description = 'PostNL Order Log'
    _order = 'sent_at desc, id desc'

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='set null', index=True)
    order_name = fields.Char(string='Order', index=True)
    destination_country_id = fields.Many2one('res.country', string='Destination Country', ondelete='set null')
    total_weight_kg = fields.Float(string='Total Weight (kg)', digits=(16, 3))
    product_code = fields.Char(string='PostNL Product Code')
    endpoint_url = fields.Char(string='Endpoint URL')

    http_status = fields.Integer(string='HTTP Status')
    success = fields.Boolean(string='Success', default=False, index=True)
    error_message = fields.Char(string='Error')

    request_payload = fields.Text(string='Request Payload')
    response_body = fields.Text(string='Response Body')
    sent_at = fields.Datetime(string='Sent At', default=fields.Datetime.now, index=True)
