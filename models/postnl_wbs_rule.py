from odoo import models, fields

class PostNLWBSRule(models.Model):
    _name = "postnl.wbs.rule"
    _description = "PostNL WBS Rule (Weight & Country -> Shipping Code)"
    _order = "weight_max asc, id asc"

    name = fields.Char(required=True, help="Friendly name for admin reference.")
    shipping_code = fields.Char(required=True, help="Carrier/contract code for PostNL.")
    weight_max = fields.Float(required=True, help="Max weight (kg) for this rule. Use 0 for 'any'.")
    country_ids = fields.Many2many("res.country", string="Countries", help="Applies to these countries. Empty = any.")
    active = fields.Boolean(default=True)

    def match_rule(self, country_code, weight_kg):
        self.ensure_one()
        ok_country = (not self.country_ids) or (country_code in self.country_ids.mapped("code"))
        ok_weight = (self.weight_max == 0) or (weight_kg <= self.weight_max + 1e-6)
        return ok_country and ok_weight
