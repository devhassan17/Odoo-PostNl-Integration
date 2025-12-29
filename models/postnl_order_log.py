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

    # -------------------------------------------------------------------------
    # Fulfilment / Shipment details (Related from Sale Order)
    # -------------------------------------------------------------------------
    so_postnl_fulfilment_status = fields.Selection(
        related='sale_order_id.postnl_fulfilment_status',
        string='Fulfilment Status',
        store=False,
        readonly=True,
    )
    so_postnl_fulfilment_order_no = fields.Char(
        related='sale_order_id.postnl_fulfilment_order_no',
        string='Fulfilment Order No',
        store=False,
        readonly=True,
    )
    so_postnl_message_no = fields.Char(
        related='sale_order_id.postnl_message_no',
        string='Shipment Message No',
        store=False,
        readonly=True,
    )
    so_postnl_ship_date = fields.Date(
        related='sale_order_id.postnl_ship_date',
        string='Ship Date',
        store=False,
        readonly=True,
    )
    so_postnl_ship_time = fields.Char(
        related='sale_order_id.postnl_ship_time',
        string='Ship Time',
        store=False,
        readonly=True,
    )
    so_postnl_track_trace_code = fields.Char(
        related='sale_order_id.postnl_track_trace_code',
        string='Barcode / Track&Trace',
        store=False,
        readonly=True,
    )
    so_postnl_track_trace_url = fields.Char(
        related='sale_order_id.postnl_track_trace_url',
        string='Track&Trace URL',
        store=False,
        readonly=True,
    )
    so_postnl_last_webhook_at = fields.Datetime(
        related='sale_order_id.postnl_last_webhook_at',
        string='Last Webhook At',
        store=False,
        readonly=True,
    )
    so_postnl_last_payload = fields.Text(
        related='sale_order_id.postnl_last_payload',
        string='Last Shipment Payload',
        store=False,
        readonly=True,
    )
