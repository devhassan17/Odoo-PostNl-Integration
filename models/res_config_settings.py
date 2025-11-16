from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # 1) GENERAL CONFIGURATION
    postnl_enabled = fields.Boolean(string="Enable PostNL Integration")
    postnl_customer_number = fields.Char(string="PostNL Customer Number")
    postnl_contract_number = fields.Char(string="PostNL Contract Number")
    postnl_default_warehouse_id = fields.Many2one(
        'stock.warehouse', string="Default Warehouse"
    )
    postnl_delivery_product_id = fields.Many2one(
        'product.product', string="PostNL Delivery Product"
    )

    # 2) SFTP CONFIGURATION
    postnl_sftp_host = fields.Char(string="SFTP Host")
    postnl_sftp_port = fields.Integer(string="SFTP Port", default=22)
    postnl_sftp_username = fields.Char(string="SFTP Username")
    postnl_sftp_password = fields.Char(string="SFTP Password")
    postnl_sftp_path_orders = fields.Char(string="Orders Export Path")
    postnl_sftp_path_shipments = fields.Char(string="Shipments Import Path")

    # 3) ORDER EXPORT CONFIG
    postnl_export_auto = fields.Boolean(string="Export Orders Automatically")
    postnl_export_trigger_state = fields.Selection(
        [
            ('sale', 'On Sale Order Confirmation'),
            ('done', 'On Delivery Done'),
        ],
        string="Order Export Trigger",
        default='sale'
    )
    postnl_export_filename_pattern = fields.Char(
        string="Order Export Filename Pattern",
        default="orders_%Y%m%d_%H%M%S.xml"
    )

    # 4) SHIPMENT IMPORT CONFIG
    postnl_import_auto = fields.Boolean(string="Import Shipments Automatically")
    postnl_import_auto_done = fields.Boolean(
        string="Auto-complete Deliveries from Shipments"
    )

    # -------------------------------------------------------------------------
    # GET / SET VALUES
    # -------------------------------------------------------------------------

    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('postnl_odoo_integration.enabled', self.postnl_enabled)
        params.set_param('postnl_odoo_integration.customer_number', self.postnl_customer_number or '')
        params.set_param('postnl_odoo_integration.contract_number', self.postnl_contract_number or '')
        params.set_param('postnl_odoo_integration.default_warehouse_id', self.postnl_default_warehouse_id.id or False)
        params.set_param('postnl_odoo_integration.delivery_product_id', self.postnl_delivery_product_id.id or False)

        params.set_param('postnl_odoo_integration.sftp_host', self.postnl_sftp_host or '')
        params.set_param('postnl_odoo_integration.sftp_port', self.postnl_sftp_port or 22)
        params.set_param('postnl_odoo_integration.sftp_username', self.postnl_sftp_username or '')
        params.set_param('postnl_odoo_integration.sftp_password', self.postnl_sftp_password or '')
        params.set_param('postnl_odoo_integration.sftp_path_orders', self.postnl_sftp_path_orders or '')
        params.set_param('postnl_odoo_integration.sftp_path_shipments', self.postnl_sftp_path_shipments or '')

        params.set_param('postnl_odoo_integration.export_auto', self.postnl_export_auto)
        params.set_param('postnl_odoo_integration.export_trigger_state', self.postnl_export_trigger_state or 'sale')
        params.set_param('postnl_odoo_integration.export_filename_pattern', self.postnl_export_filename_pattern or '')

        params.set_param('postnl_odoo_integration.import_auto', self.postnl_import_auto)
        params.set_param('postnl_odoo_integration.import_auto_done', self.postnl_import_auto_done)

    @api.model
    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()

        res.update(
            postnl_enabled = params.get_param('postnl_odoo_integration.enabled', 'False') == 'True',
            postnl_customer_number = params.get_param('postnl_odoo_integration.customer_number'),
            postnl_contract_number = params.get_param('postnl_odoo_integration.contract_number'),
            postnl_default_warehouse_id = int(params.get_param('postnl_odoo_integration.default_warehouse_id', 0)) or False,
            postnl_delivery_product_id = int(params.get_param('postnl_odoo_integration.delivery_product_id', 0)) or False,

            postnl_sftp_host = params.get_param('postnl_odoo_integration.sftp_host'),
            postnl_sftp_port = int(params.get_param('postnl_odoo_integration.sftp_port', 22)),
            postnl_sftp_username = params.get_param('postnl_odoo_integration.sftp_username'),
            postnl_sftp_password = params.get_param('postnl_odoo_integration.sftp_password'),
            postnl_sftp_path_orders = params.get_param('postnl_odoo_integration.sftp_path_orders'),
            postnl_sftp_path_shipments = params.get_param('postnl_odoo_integration.sftp_path_shipments'),

            postnl_export_auto = params.get_param('postnl_odoo_integration.export_auto', 'False') == 'True',
            postnl_export_trigger_state = params.get_param('postnl_odoo_integration.export_trigger_state', 'sale'),
            postnl_export_filename_pattern = params.get_param('postnl_odoo_integration.export_filename_pattern'),

            postnl_import_auto = params.get_param('postnl_odoo_integration.import_auto', 'False') == 'True',
            postnl_import_auto_done = params.get_param('postnl_odoo_integration.import_auto_done', 'False') == 'True',
        )
        return res

    # -------------------------------------------------------------------------
    # TEST BUTTON METHODS
    # -------------------------------------------------------------------------

    def action_test_general_config(self):
        if not self.postnl_enabled:
            raise UserError(_("PostNL Integration is not enabled."))
        if not self.postnl_customer_number or not self.postnl_contract_number:
            raise UserError(_("Please set customer and contract numbers."))
        if not self.postnl_default_warehouse_id:
            raise UserError(_("Please set a default warehouse."))
        # More validation as needed...
        raise UserError(_("General configuration looks valid."))

    def action_test_sftp_connection(self):
        self.ensure_one()
        from ..services.sftp_client import PostNLSFTPClient

        client = PostNLSFTPClient(
            host=self.postnl_sftp_host,
            port=self.postnl_sftp_port,
            username=self.postnl_sftp_username,
            password=self.postnl_sftp_password,
        )
        try:
            client.test_connection()
        except Exception as e:
            _logger.exception("PostNL SFTP test failed")
            raise UserError(_("SFTP test failed: %s") % e)
        raise UserError(_("SFTP connection successful."))

    def action_test_order_export(self):
        # You can implement a dry-run builder that doesn't write to SFTP
        from ..services.postnl_order_builder import build_test_order_xml
        try:
            xml_string = build_test_order_xml(self.env)
            _logger.info("Test order XML built: %s", xml_string[:500])
        except Exception as e:
            _logger.exception("PostNL Order export test failed")
            raise UserError(_("Order export test failed: %s") % e)
        raise UserError(_("Order export test passed (XML built successfully)."))

    def action_test_shipment_import(self):
        from ..services.sftp_client import PostNLSFTPClient
        from ..services.postnl_shipment_parser import validate_sample_file

        client = PostNLSFTPClient(
            host=self.postnl_sftp_host,
            port=self.postnl_sftp_port,
            username=self.postnl_sftp_username,
            password=self.postnl_sftp_password,
        )
        try:
            filenames = client.list_files(self.postnl_sftp_path_shipments or '.')
            # Optionally read first file and validate XML structure
            if filenames:
                content = client.read_file(self.postnl_sftp_path_shipments, filenames[0])
                validate_sample_file(content)
        except Exception as e:
            _logger.exception("PostNL Shipment import test failed")
            raise UserError(_("Shipment import test failed: %s") % e)

        raise UserError(_("Shipment import configuration looks OK."))
