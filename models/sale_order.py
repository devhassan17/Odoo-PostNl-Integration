from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Store PostNL-specific checkout choices (mirrors Woo plugin behavior)
    postnl_delivery_option = fields.Selection([
        ("standard", "Standard"),
        ("morning", "Morning"),
        ("evening", "Evening"),
        ("pickup", "Pickup Point"),
    ], string="PostNL Delivery Option", copy=False)

    postnl_pickup_location_code = fields.Char(copy=False)
    postnl_pickup_location_name = fields.Char(copy=False)
    postnl_pickup_address = fields.Char(copy=False)
    postnl_pickup_postcode = fields.Char(copy=False)
    postnl_pickup_city = fields.Char(copy=False)
