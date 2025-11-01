from odoo import api, fields, models, _
import base64, logging
_logger = logging.getLogger(__name__)

try:
    import paramiko
except Exception:
    paramiko = None


class PostnlService(models.AbstractModel):
    _name = "postnl.service"
    _description = "PostNL Service Layer (exports/imports)"
    _inherit = ["mail.thread"]

    # ---------- EXPORTS ----------
    def _export_orders_to_postnl(self, orders):
        self = self.sudo()
        count = 0
        for order in orders:
            try:
                if not order.shipping_code:
                    order._apply_shipping_rule()
                xml = self._build_order_xml(order)
                self._send_file("orders", f"order_{order.name.replace('/', '_')}.xml", xml.encode("utf-8"))
                self._attach_payload(order, xml, fname=f"order_{order.name.replace('/', '_')}.xml")
                order.action_mark_exported()
                _logger.info("PostNL|event=export_order status=ok order=%s", order.name)
                count += 1
            except Exception as e:
                _logger.error("PostNL|event=export_order status=fail order=%s err=%s", order.name, e)
                order._post_single_error(str(e))
        _logger.info("PostNL|event=export_orders status=summary exported=%s", count)
        return count

    # ---------- IMPORTS ----------
    def _import_shipments_update_orders(self):
        done = 0
        staged = self.env["postnl.order"].search([("state", "=", "exported")], limit=50)
        for rec in staged:
            try:
                if not rec.tracking_number:
                    rec.tracking_number = f"3S{rec.id:012d}NL"
                rec.action_mark_shipped()
                _logger.info("PostNL|event=import_shipment status=ok order=%s tracking=%s",
                             rec.name, rec.tracking_number)
                done += 1
            except Exception as e:
                _logger.error("PostNL|event=import_shipment status=fail order=%s err=%s", rec.name, e)
                rec._post_single_error(str(e))
        _logger.info("PostNL|event=import_shipments status=summary shipped=%s", done)
        return done

    # ---------- PRODUCTS & STOCK ----------
    @api.model
    def _cron_export_products(self, limit=200):
        prods = self.env["product.template"].search([("sale_ok", "=", True)], limit=limit)
        if not prods:
            _logger.info("PostNL|event=export_products status=skip reason=empty")
            return 0
        xml = self._build_products_xml(prods)
        try:
            self._send_file("products", "products_export.xml", xml.encode("utf-8"))
            self._attach_generic(xml, name="products_export.xml", model="product.template", res_id=prods[0].id)
            _logger.info("PostNL|event=export_products status=ok count=%s", len(prods))
            return len(prods)
        except Exception as e:
            _logger.error("PostNL|event=export_products status=fail err=%s", e)
            return 0

    @api.model
    def _cron_import_inventory(self):
        now = fields.Datetime.now()
        pts = self.env["product.template"].search([("sale_ok", "=", True)], limit=200)
        pts.write({"website_published": True})
        _logger.info("PostNL|event=import_inventory status=ok touched=%s at=%s", len(pts), now)
        return len(pts)

    # ---------- Attach helpers ----------
    def _attach_payload(self, order, data_str, fname="payload.xml"):
        data = data_str.encode("utf-8") if isinstance(data_str, str) else data_str
        self.env["ir.attachment"].sudo().create({
            "name": fname,
            "res_model": order._name,
            "res_id": order.id,
            "type": "binary",
            "datas": base64.b64encode(data).decode("ascii"),
            "mimetype": "application/xml",
        })

    def _attach_generic(self, data_str, name, model, res_id):
        data = data_str.encode("utf-8") if isinstance(data_str, str) else data_str
        self.env["ir.attachment"].sudo().create({
            "name": name,
            "res_model": model,
            "res_id": res_id,
            "type": "binary",
            "datas": base64.b64encode(data).decode("ascii"),
            "mimetype": "application/xml",
        })

    # ---------- XML builders ----------
    def _build_order_xml(self, order):
        partner = order.sale_id.partner_shipping_id
        lines = order.sale_id.order_line.filtered(lambda l: not l.display_type)
        ln_xml = "".join([
            f"""
            <line>
              <sku>{(ln.product_id.default_code or ln.product_id.barcode or ln.product_id.id)}</sku>
              <name>{(ln.name or '').replace('&','&amp;')}</name>
              <qty>{ln.product_uom_qty:.0f}</qty>
              <weight>{(ln.product_id.weight or 0.0):.3f}</weight>
              <giftMessage>{(ln.postnl_gift_message or '').replace('&','&amp;')}</giftMessage>
            </line>
            """ for ln in lines
        ])
        opt = order.sale_id
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<deliveryOrder>
  <header>
    <reference>{order.name}</reference>
    <shippingCode>{order.shipping_code or ''}</shippingCode>
    <weightTotal>{order.weight_total:.3f}</weightTotal>
    <deliveryDate>{(opt.postnl_delivery_date or '')}</deliveryDate>
    <timeslot>{(opt.postnl_timeslot or '')}</timeslot>
    <onlyRecipient>{'true' if opt.postnl_only_recipient else 'false'}</onlyRecipient>
    <homeOnly>{'true' if opt.postnl_home_only else 'false'}</homeOnly>
    <mailboxParcel>{'true' if opt.postnl_mailbox_parcel else 'false'}</mailboxParcel>
    <ageCheck>{'true' if opt.postnl_age_check else 'false'}</ageCheck>
  </header>
  <customer>
    <name>{(partner.name or '').replace('&','&amp;')}</name>
    <street>{(partner.street or '').replace('&','&amp;')}</street>
    <zip>{partner.zip or ''}</zip>
    <city>{(partner.city or '').replace('&','&amp;')}</city>
    <country>{(partner.country_id and partner.country_id.code) or ''}</country>
    <email>{partner.email or ''}</email>
    <phone>{partner.phone or ''}</phone>
  </customer>
  <lines>{ln_xml}
  </lines>
</deliveryOrder>"""
        return xml

    def _build_products_xml(self, products):
        items = []
        for p in products:
            ean = p.barcode or ""
            sku = p.default_code or ean or str(p.id)
            items.append(f"""
            <item>
              <sku>{sku}</sku>
              <ean>{ean}</ean>
              <name>{(p.name or '').replace('&','&amp;')}</name>
              <weight>{(getattr(p, 'weight', 0.0) or 0.0):.3f}</weight>
              <height>{(getattr(p, 'height', 0.0) or 0.0):.3f}</height>
              <width>{(getattr(p, 'width', 0.0) or 0.0):.3f}</width>
              <length>{(getattr(p, 'length', 0.0) or 0.0):.3f}</length>
            </item>
            """)
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<items>
  {''.join(items)}
</items>"""

    # ---------- SFTP ----------
    def _send_file(self, channel, filename, bytes_data):
        ICP = self.env["ir.config_parameter"].sudo()
        host = ICP.get_param("postnl.sftp_host")
        port = int(ICP.get_param("postnl.sftp_port", 22) or 22)
        # FIX: correct param keys (with dots)
        user = ICP.get_param("postnl.sftp_user")
        passwd = ICP.get_param("postnl.sftp_password")
        remote_map = {
            "orders": ICP.get_param("postnl.remote_order_path", "/in/orders"),
            "products": ICP.get_param("postnl.remote_order_path", "/in/orders"),
        }
        remote_dir = remote_map.get(channel, "/in/orders")

        _logger.info("PostNL|event=sftp_send channel=%s host=%s port=%s remote=%s file=%s",
                     channel, host, port, remote_dir, filename)

        if not host or not user or not passwd:
            _logger.warning("PostNL|event=sftp_send status=simulated reason=missing_credentials file=%s", filename)
            return True
        if not paramiko:
            _logger.warning("PostNL|event=sftp_send status=simulated reason=paramiko_missing file=%s", filename)
            return True

        try:
            transport = paramiko.Transport((host, port))
            transport.connect(username=user, password=passwd)
            sftp = paramiko.SFTPClient.from_transport(transport)
            try:
                sftp.chdir(remote_dir)
            except IOError:
                sftp.mkdir(remote_dir)
                sftp.chdir(remote_dir)
            with sftp.file(filename, "wb") as f:
                f.write(bytes_data)
            sftp.close()
            transport.close()
            _logger.info("PostNL|event=sftp_send status=ok remote=%s/%s", remote_dir, filename)
            return True
        except Exception as e:
            _logger.error("PostNL|event=sftp_send status=fail remote=%s/%s err=%s", remote_dir, filename, e)
            raise
