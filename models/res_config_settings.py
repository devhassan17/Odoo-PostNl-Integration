# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    postnl_api_url = fields.Char(string="PostNL API URL", config_parameter="postnl.api_url")
    postnl_api_key = fields.Char(string="PostNL API Key", config_parameter="postnl.api_key")
    postnl_customer_number = fields.Char(string="Customer Number", config_parameter="postnl.customer_number")
    postnl_merchant_code = fields.Char(string="Merchant Code", config_parameter="postnl.merchant_code")
    postnl_fulfilment_location = fields.Char(string="Fulfilment Location", config_parameter="postnl.fulfilment_location")
    postnl_channel = fields.Char(string="Channel", config_parameter="postnl.channel")
    postnl_default_product_code = fields.Char(string="Default Product Code", config_parameter="postnl.default_product_code")

    # ✅ NEW FIELD
    postnl_inbound_url = fields.Char(string="PostNL Inbound URL", config_parameter="postnl.inbound_url")
