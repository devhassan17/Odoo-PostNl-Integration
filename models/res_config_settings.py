from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    postnl_sftp_host = fields.Char(string="SFTP Host")
    postnl_sftp_port = fields.Integer(string="SFTP Port", default=22)
    postnl_sftp_username = fields.Char(string="SFTP Username")
    postnl_sftp_password = fields.Char(string="SFTP Password")
    postnl_sftp_private_key = fields.Text(string="SFTP Private Key")  # Optional, if you need key auth
    postnl_remote_order_path = fields.Char(string="Remote Order Path")
    postnl_remote_shipment_path = fields.Char(string="Remote Shipment Path")
    postnl_remote_stock_path = fields.Char(string="Remote Stock Path")

    postnl_batch_size = fields.Integer(string="Batch Size", default=50)
    postnl_default_shipping_code = fields.Char(string="Default Shipping Code")
    postnl_tnt_url_template = fields.Char(string="T&T URL Template")

    postnl_enable_scan_cron = fields.Boolean(string="Enable Scan Scheduler")
    postnl_enable_export_cron = fields.Boolean(string="Enable Export Scheduler")
    postnl_enable_import_cron = fields.Boolean(string="Enable Import Scheduler")

    @api.model
    def get_values(self):
        res = super().get_values()
        IrConfig = self.env['ir.config_parameter'].sudo()
        res.update(
            postnl_sftp_host=IrConfig.get_param('postnl_sftp_host', default=''),
            postnl_sftp_port=int(IrConfig.get_param('postnl_sftp_port', default=22)),
            postnl_sftp_username=IrConfig.get_param('postnl_sftp_username', default=''),
            postnl_sftp_password=IrConfig.get_param('postnl_sftp_password', default=''),
            postnl_sftp_private_key=IrConfig.get_param('postnl_sftp_private_key', default=''),
            postnl_remote_order_path=IrConfig.get_param('postnl_remote_order_path', default=''),
            postnl_remote_shipment_path=IrConfig.get_param('postnl_remote_shipment_path', default=''),
            postnl_remote_stock_path=IrConfig.get_param('postnl_remote_stock_path', default=''),
            postnl_batch_size=int(IrConfig.get_param('postnl_batch_size', default=50)),
            postnl_default_shipping_code=IrConfig.get_param('postnl_default_shipping_code', default=''),
            postnl_tnt_url_template=IrConfig.get_param('postnl_tnt_url_template', default=''),
            postnl_enable_scan_cron=IrConfig.get_param('postnl_enable_scan_cron') == 'True',
            postnl_enable_export_cron=IrConfig.get_param('postnl_enable_export_cron') == 'True',
            postnl_enable_import_cron=IrConfig.get_param('postnl_enable_import_cron') == 'True',
        )
        return res

    def set_values(self):
        super().set_values()
        IrConfig = self.env['ir.config_parameter'].sudo()
        IrConfig.set_param('postnl_sftp_host', self.postnl_sftp_host or '')
        IrConfig.set_param('postnl_sftp_port', self.postnl_sftp_port or 22)
        IrConfig.set_param('postnl_sftp_username', self.postnl_sftp_username or '')
        IrConfig.set_param('postnl_sftp_password', self.postnl_sftp_password or '')
        IrConfig.set_param('postnl_sftp_private_key', self.postnl_sftp_private_key or '')
        IrConfig.set_param('postnl_remote_order_path', self.postnl_remote_order_path or '')
        IrConfig.set_param('postnl_remote_shipment_path', self.postnl_remote_shipment_path or '')
        IrConfig.set_param('postnl_remote_stock_path', self.postnl_remote_stock_path or '')
        IrConfig.set_param('postnl_batch_size', self.postnl_batch_size or 50)
        IrConfig.set_param('postnl_default_shipping_code', self.postnl_default_shipping_code or '')
        IrConfig.set_param('postnl_tnt_url_template', self.postnl_tnt_url_template or '')
        IrConfig.set_param('postnl_enable_scan_cron', self.postnl_enable_scan_cron)
        IrConfig.set_param('postnl_enable_export_cron', self.postnl_enable_export_cron)
        IrConfig.set_param('postnl_enable_import_cron', self.postnl_enable_import_cron)

    def action_postnl_test_sftp(self):
        try:
            from ..services.sftp_client import PostNLSFTPClient
            client = PostNLSFTPClient(self)
            client.test_connection()
        except Exception as e:
            raise UserError(_('SFTP test failed: %s') % str(e))

    def action_postnl_scan_now(self):
        self.env['postnl.shipment.export']._scan_orders_for_export()

    def action_postnl_export_now(self):
        self.env['postnl.shipment.export'].cron_export_orders()

    def action_postnl_import_now(self):
        self.env['postnl.shipment.import'].cron_import_shipments()
