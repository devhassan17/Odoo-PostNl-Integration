# postnl_odoo_integration/models/postnl_shipping_rule.py
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PostNLShippingRule(models.Model):
    _name = "postnl.shipping.rule"
    _description = "PostNL Shipping Rule"
    _order = "sequence, id"

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(default=10)

    shipping_code = fields.Char(string="PostNL Shipping Code", required=True)

    weight_min = fields.Float(string="Min Weight (kg)", default=0.0)
    weight_max = fields.Float(string="Max Weight (kg)")
    no_max_weight = fields.Boolean(string="No Max Limit")

    country_ids = fields.Many2many(
        "res.country",
        "postnl_shipping_rule_country_rel",
        "rule_id",
        "country_id",
        string="Countries",
    )

    active = fields.Boolean(default=True)

    @api.constrains("weight_min", "weight_max", "no_max_weight")
    def _check_weights(self):
        for rule in self:
            if (
                not rule.no_max_weight
                and rule.weight_max
                and rule.weight_max < rule.weight_min
            ):
                raise ValidationError(_("Max weight must be greater than min weight."))

    @api.model
    def get_shipping_code(self, country, weight_kg):
        """Return best matching shipping_code for country + weight."""
        domain = [("active", "=", True)]
        if country:
            domain.append(("country_ids", "in", country.id))
        rules = self.search(domain, order="sequence, id")
        for rule in rules:
            if weight_kg < rule.weight_min:
                continue
            if (
                not rule.no_max_weight
                and rule.weight_max
                and weight_kg > rule.weight_max
            ):
                continue
            return rule.shipping_code
        return False
