from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

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
        if not country or weight is None:
            _logger.info("POSTNL RULE: no match (country=%s, weight=%s)", country and country.code, weight)
            return False
        rules = self.search([
            ("active","=",True),
            ("country_ids","in",[country.id]),
            ("max_weight",">=",weight),
        ], order="sequence asc, max_weight asc", limit=1)
        rule = rules[:1] or False
        _logger.info("POSTNL RULE: country=%s weight=%.3f -> %s",
                     country.code, weight, rule and f"{rule.name}({rule.shipping_code})")
        return rule
