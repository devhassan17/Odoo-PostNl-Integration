# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PostNLConfig(models.Model):
    """Single-page configuration for PostNL integration.

    Values are stored in ir.config_parameter so they are system-wide.
    """

    _name = 'postnl.config'
    _description = 'PostNL Configuration'

    name = fields.Char(default='PostNL Configuration', readonly=True)

    api_url = fields.Char(string='API URL', compute='_compute_params', inverse='_inverse_api_url')
    api_key = fields.Char(string='API Key', compute='_compute_params', inverse='_inverse_api_key')
    customer_number = fields.Char(string='Customer Number', compute='_compute_params', inverse='_inverse_customer_number')
    merchant_code = fields.Char(string='Merchant Code', compute='_compute_params', inverse='_inverse_merchant_code')
    fulfilment_location = fields.Char(string='Fulfilment Location', compute='_compute_params', inverse='_inverse_fulfilment_location')
    channel = fields.Char(string='Channel', compute='_compute_params', inverse='_inverse_channel')
    default_product_code = fields.Char(string='Default Product Code', compute='_compute_params', inverse='_inverse_default_product_code')

    rule_ids = fields.One2many('postnl.shipping.rule', 'config_id', string='Weight Rules')

    @api.model
    def get_singleton(self):
        rec = self.search([], limit=1)
        if not rec:
            rec = self.create({})
        return rec

    def _compute_params(self):
        icp = self.env['ir.config_parameter'].sudo()
        for rec in self:
            rec.api_url = icp.get_param('postnl.api_url', '')
            rec.api_key = icp.get_param('postnl.api_key', '')
            rec.customer_number = icp.get_param('postnl.customer_number', '')
            rec.merchant_code = icp.get_param('postnl.merchant_code', '')
            rec.fulfilment_location = icp.get_param('postnl.fulfilment_location', '')
            rec.channel = icp.get_param('postnl.channel', '')
            rec.default_product_code = icp.get_param('postnl.default_product_code', '')

    def _set_param(self, key, value):
        self.env['ir.config_parameter'].sudo().set_param(key, value or '')

    def _inverse_api_url(self):
        for rec in self:
            rec._set_param('postnl.api_url', rec.api_url)

    def _inverse_api_key(self):
        for rec in self:
            rec._set_param('postnl.api_key', rec.api_key)

    def _inverse_customer_number(self):
        for rec in self:
            rec._set_param('postnl.customer_number', rec.customer_number)

    def _inverse_merchant_code(self):
        for rec in self:
            rec._set_param('postnl.merchant_code', rec.merchant_code)

    def _inverse_fulfilment_location(self):
        for rec in self:
            rec._set_param('postnl.fulfilment_location', rec.fulfilment_location)

    def _inverse_channel(self):
        for rec in self:
            rec._set_param('postnl.channel', rec.channel)

    def _inverse_default_product_code(self):
        for rec in self:
            rec._set_param('postnl.default_product_code', rec.default_product_code)
