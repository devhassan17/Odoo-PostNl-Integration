from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # SFTP and integration fields
    postnl_enabled = fields.Boolean(string="Enable PostNL Integration")
    postnl_customer_number = fields.Char(string="PostNL Customer Number")
    postnl_contract_number = fields.Char(string="PostNL Contract Number")
    postnl_default_warehouse_id = fields.Many2one("stock.warehouse", string="Default Warehouse")
    postnl_delivery_product_id = fields.Many2one("product.product", string="PostNL Delivery Product")

    postnl_sftp_host = fields.Char(string="SFTP Host")
    postnl_sftp_port = fields.Integer(string="SFTP Port", default=22)
    postnl_sftp_username = fields.Char(string="SFTP Username")
    postnl_sftp_private_key = fields.Text(string="SFTP Private Key")
    postnl_sftp_path_orders = fields.Char(string="Orders Export Path")
    postnl_sftp_path_shipments = fields.Char(string="Shipments Import Path")

    postnl_export_auto = fields.Boolean(string="Export Orders Automatically")
    postnl_export_trigger_state = fields.Selection([
        ("sale", "On Sale Order Confirmation"),
        ("done", "On Delivery Done"),
    ], string="Order Export Trigger", default="sale")
    postnl_export_filename_pattern = fields.Char(string="Order Export Filename Pattern", default="orders_%Y%m%d_%H%M%S.xml")

    postnl_import_auto = fields.Boolean(string="Import Shipments Automatically")
    postnl_import_auto_done = fields.Boolean(string="Auto-complete Deliveries from Shipments")

    postnl_weight_line_ids = fields.One2many(
        comodel_name='postnl.weight.rule',
        inverse_name='config_id',
        string='PostNL Weight Settings'
    )

    def set_values(self):
        super().set_values()
        params = self.env["ir.config_parameter"].sudo()
        params.set_param("postnl_odoo_integration.enabled", self.postnl_enabled)
        params.set_param("postnl_odoo_integration.customer_number", self.postnl_customer_number or "")
        params.set_param("postnl_odoo_integration.contract_number", self.postnl_contract_number or "")
        params.set_param("postnl_odoo_integration.default_warehouse_id", self.postnl_default_warehouse_id.id or False)
        params.set_param("postnl_odoo_integration.delivery_product_id", self.postnl_delivery_product_id.id or False)
        params.set_param("postnl_odoo_integration.sftp_host", self.postnl_sftp_host or "")
        params.set_param("postnl_odoo_integration.sftp_port", self.postnl_sftp_port or 22)
        params.set_param("postnl_odoo_integration.sftp_username", self.postnl_sftp_username or "")
        params.set_param("postnl_odoo_integration.sftp_private_key", self.postnl_sftp_private_key or "")
        params.set_param("postnl_odoo_integration.sftp_path_orders", self.postnl_sftp_path_orders or "")
        params.set_param("postnl_odoo_integration.sftp_path_shipments", self.postnl_sftp_path_shipments or "")
        params.set_param("postnl_odoo_integration.export_auto", self.postnl_export_auto)
        params.set_param("postnl_odoo_integration.export_trigger_state", self.postnl_export_trigger_state or "sale")
        params.set_param("postnl_odoo_integration.export_filename_pattern", self.postnl_export_filename_pattern or "")
        params.set_param("postnl_odoo_integration.import_auto", self.postnl_import_auto)
        params.set_param("postnl_odoo_integration.import_auto_done", self.postnl_import_auto_done)

    @api.model
    def get_values(self):
        res = super().get_values()
        params = self.env["ir.config_parameter"].sudo()
        res.update(
            postnl_enabled=params.get_param("postnl_odoo_integration.enabled", "False") == "True",
            postnl_customer_number=params.get_param("postnl_odoo_integration.customer_number"),
            postnl_contract_number=params.get_param("postnl_odoo_integration.contract_number"),
            postnl_default_warehouse_id=int(params.get_param("postnl_odoo_integration.default_warehouse_id", 0)) or False,
            postnl_delivery_product_id=int(params.get_param("postnl_odoo_integration.delivery_product_id", 0)) or False,
            postnl_sftp_host=params.get_param("postnl_odoo_integration.sftp_host"),
            postnl_sftp_port=int(params.get_param("postnl_odoo_integration.sftp_port", 22)),
            postnl_sftp_username=params.get_param("postnl_odoo_integration.sftp_username"),
            postnl_sftp_private_key=params.get_param("postnl_odoo_integration.sftp_private_key", ""),
            postnl_sftp_path_orders=params.get_param("postnl_odoo_integration.sftp_path_orders"),
            postnl_sftp_path_shipments=params.get_param("postnl_odoo_integration.sftp_path_shipments"),
            postnl_export_auto=params.get_param("postnl_odoo_integration.export_auto", "False") == "True",
            postnl_export_trigger_state=params.get_param("postnl_odoo_integration.export_trigger_state", "sale"),
            postnl_export_filename_pattern=params.get_param("postnl_odoo_integration.export_filename_pattern"),
            postnl_import_auto=params.get_param("postnl_odoo_integration.import_auto", "False") == "True",
            postnl_import_auto_done=params.get_param("postnl_odoo_integration.import_auto_done", "False") == "True",
        )
        return res


class PostnlWeightRule(models.Model):
    _name = 'postnl.weight.rule'
    _description = 'PostNL Weight Rule'

    shipping_code = fields.Char(string='Shipping Code', required=True)
    min_weight = fields.Float(string='Min Weight', required=True)
    max_weight = fields.Float(string='Max Weight', required=True)
    country_ids = fields.Many2many('res.country', string='Countries')
