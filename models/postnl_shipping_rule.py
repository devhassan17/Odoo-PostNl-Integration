# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class PostnlShippingRule(models.Model):
    _name = "postnl.shipping.rule"
    _description = "PostNL Shipping Code Rule"
    _order = "sequence, max_weight"

    name = fields.Char(required=True, default=lambda self: _("Rule"))
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    shipping_code = fields.Char(required=True, help="PostNL (agent) code to use if rule matches.")
    max_weight = fields.Float(string="Max Weight (kg)", required=True, digits=(12, 3))
    country_ids = fields.Many2many("res.country", string="Countries", required=True)

    @api.model
    def _match(self, country, weight):
        if not country or not weight:
            return False
        rules = self.search([
            ("active", "=", True),
            ("country_ids", "in", [country.id]),
            ("max_weight", ">=", weight),
        ], order="sequence asc, max_weight asc", limit=1)
        return rules[:1] or False