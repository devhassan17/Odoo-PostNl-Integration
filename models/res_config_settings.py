from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Connection / behavior
    postnl_sftp_host = fields.Char()
    postnl_sftp_port = fields.Integer(default=22)
    postnl_sftp_user = fields.Char()
    postnl_sftp_password = fields.Char()
    postnl_remote_order_path = fields.Char(default='/in/orders')
    postnl_remote_shipment_path = fields.Char(default='/out/shipments')
    postnl_remote_stock_path = fields.Char(default='/out/stock')
    postnl_batch_size = fields.Integer(default=50)
    postnl_default_shipping_code = fields.Char(default='3085')
    postnl_tnt_url_template = fields.Char(default='https://tracking.postnl.nl/#!/track/{}')
    postnl_enable_export_cron = fields.Boolean(default=True)
    postnl_enable_import_cron = fields.Boolean(default=True)
    postnl_enable_scan_cron = fields.Boolean(default=True)

    # Save / load
    def set_values(self):
        res = super().set_values()
        ICP = self.env['ir.config_parameter'].sudo()
        for f in ['postnl_sftp_host','postnl_sftp_port','postnl_sftp_user','postnl_sftp_password',
                  'postnl_remote_order_path','postnl_remote_shipment_path','postnl_remote_stock_path',
                  'postnl_batch_size','postnl_default_shipping_code','postnl_tnt_url_template',
                  'postnl_enable_export_cron','postnl_enable_import_cron','postnl_enable_scan_cron']:
            ICP.set_param(f'postnl.{f[7:]}', getattr(self, f) or '')
        return res

    @api.model
    def get_values(self):
        res = super().get_values()
        ICP = self.env['ir.config_parameter'].sudo()
        g = lambda k, d='': ICP.get_param(k, default=d)
        res.update(
            postnl_sftp_host=g('postnl.sftp_host'),
            postnl_sftp_port=int(g('postnl.sftp_port', 22) or 22),
            postnl_sftp_user=g('postnl.sftp_user'),
            postnl_sftp_password=g('postnl.sftp_password'),
            postnl_remote_order_path=g('postnl.remote_order_path','/in/orders'),
            postnl_remote_shipment_path=g('postnl.remote_shipment_path','/out/shipments'),
            postnl_remote_stock_path=g('postnl.remote_stock_path','/out/stock'),
            postnl_batch_size=int(g('postnl.batch_size', 50) or 50),
            postnl_default_shipping_code=g('postnl.default_shipping_code','3085'),
            postnl_tnt_url_template=g('postnl.tnt_url_template','https://tracking.postnl.nl/#!/track/{}'),
            postnl_enable_export_cron=(g('postnl.enable_export_cron','True') in ('True','1','true')),
            postnl_enable_import_cron=(g('postnl.enable_import_cron','True') in ('True','1','true')),
            postnl_enable_scan_cron=(g('postnl.enable_scan_cron','True') in ('True','1','true')),
        )
        return res

    # ---------- Test/Actions from Settings ----------
    def action_postnl_test_sftp(self):
        self.ensure_one()
        try:
            self.env['postnl.service']._send_file("orders", "postnl_test.txt", b"ok")
        except Exception as e:
            raise UserError(_("SFTP test failed: %s") % e)
        self.env.user.notify_success(message=_("PostNL SFTP test: OK"))
        return False

    def action_postnl_scan_now(self):
        created = self.env['postnl.order']._cron_scan_sale_orders()
        self.env.user.notify_success(message=_("Scanned Sales Orders → staged: %s") % created)
        return False

    def action_postnl_export_now(self):
        exported = self.env['postnl.order']._cron_export_orders()
        self.env.user.notify_success(message=_("Queued Orders exported: %s") % exported)
        return False

    def action_postnl_import_now(self):
        shipped = self.env['postnl.order']._cron_import_shipments()
        self.env.user.notify_success(message=_("Shipments imported (marked shipped): %s") % shipped)
        return False
