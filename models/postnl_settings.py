from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    postnl_api_key = fields.Char(string="PostNL API Key", config_parameter="postnl_base.api_key")
    postnl_customer_code = fields.Char(string="Customer Code", config_parameter="postnl_base.customer_code")
    postnl_customer_number = fields.Char(string="Customer Number", config_parameter="postnl_base.customer_number")
    postnl_sender_name = fields.Char(string="Sender Name", config_parameter="postnl_base.sender_name")
    postnl_sender_street = fields.Char(string="Sender Street", config_parameter="postnl_base.sender_street")
    postnl_sender_house_no = fields.Char(string="Sender House No.", config_parameter="postnl_base.sender_house_no")
    postnl_sender_postcode = fields.Char(string="Sender Postcode", config_parameter="postnl_base.sender_postcode")
    postnl_sender_city = fields.Char(string="Sender City", config_parameter="postnl_base.sender_city")
    postnl_sender_country_code = fields.Char(string="Sender Country Code", default="NL", config_parameter="postnl_base.sender_country_code")

    # Defaults / Options mirroring Woo plugins
    postnl_default_signature = fields.Boolean(string="Default: Signature Required", config_parameter="postnl_base.default_signature")
    postnl_default_only_recipient = fields.Boolean(string="Default: Only Recipient", config_parameter="postnl_base.default_only_recipient")
    postnl_default_insured = fields.Boolean(string="Default: Insured", config_parameter="postnl_base.default_insured")
    postnl_default_insured_amount = fields.Float(string="Default: Insurance Amount", config_parameter="postnl_base.default_insured_amount")
    postnl_default_package_type = fields.Selection([
        ("package", "Package"),
        ("mailbox", "Mailbox"),
        ("letter", "Unpaid Letter"),
    ], string="Default Package Type", default="package", config_parameter="postnl_base.default_package_type")

    postnl_evening_delivery = fields.Boolean(string="Enable Evening Delivery", config_parameter="postnl_base.evening_delivery")
    postnl_morning_delivery = fields.Boolean(string="Enable Morning Delivery", config_parameter="postnl_base.morning_delivery")
    postnl_saturday_delivery = fields.Boolean(string="Enable Saturday Delivery", config_parameter="postnl_base.saturday_delivery")
    postnl_cutoff_hour = fields.Integer(string="Cut-off Hour (0-23)", default=17, config_parameter="postnl_base.cutoff_hour")

    postnl_test_mode = fields.Boolean(string="Test Mode (sandbox)", default=True, config_parameter="postnl_base.test_mode")
