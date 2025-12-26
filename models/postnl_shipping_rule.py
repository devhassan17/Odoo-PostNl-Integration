# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PostNLShippingRule(models.Model):
    """Weight based rules to determine PostNL productCode by destination country."""

    _name = 'postnl.shipping.rule'
    _description = 'PostNL Weight Based Shipping Rule'
    _order = 'max_weight_kg asc, id asc'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    product_code = fields.Char(string='Product Code', required=True)
    max_weight_kg = fields.Float(string='Max Weight (kg)', required=True, digits=(16, 3))
    country_ids = fields.Many2many('res.country', string='Countries')
    active = fields.Boolean(default=True)
    config_id = fields.Many2one('postnl.config', string='Configuration', ondelete='cascade')

    @api.depends('product_code', 'max_weight_kg')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.product_code} <= {rec.max_weight_kg}kg"