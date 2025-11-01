from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    postnl_delivery_date = fields.Date(string="PostNL Delivery Date")
    postnl_timeslot = fields.Selection([
        ("morning","Morning"),
        ("day","Day"),
        ("evening","Evening"),
    ], string="Delivery Timeslot")
    postnl_only_recipient = fields.Boolean(string="Only Recipient")
    postnl_home_only = fields.Boolean(string="Home Address Only")
    postnl_mailbox_parcel = fields.Boolean(string="Mailbox Parcel")
    postnl_age_check = fields.Boolean(string="Age Check (18+)")

    def postnl_evening(self):
        return self.postnl_timeslot == "evening"

    def _postnl_pick_shipping_code_fallback(self, country):
        NL = country and country.code == "NL"
        if self.postnl_mailbox_parcel and NL:
            return "03533"
        if NL:
            if self.postnl_evening():
                return "3087"  # example: evening
            return "3085"
        if country and country.code == "BE":
            return "04946"
        if country and country.code in ("AT","DE","FR","ES","IT","LU","DK","SE","FI","PT","IE","CZ","PL","HU"):
            return "04952"
        return "04945"

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"
    postnl_gift_message = fields.Char(string="Gift Message (per line)", size=140)
