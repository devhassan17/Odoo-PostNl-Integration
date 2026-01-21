# -*- coding: utf-8 -*-
import json
from odoo import api, fields, models
from odoo.tools import html_escape

class SaleOrder(models.Model):
    _inherit = "sale.order"

    postnl_fulfilment_order_no = fields.Char(string="PostNL Fulfilment Order No", copy=False, index=True)
    postnl_message_no = fields.Char(string="PostNL Message No", copy=False)
    postnl_ship_date = fields.Date(string="PostNL Ship Date", copy=False)
    postnl_ship_time = fields.Char(string="PostNL Ship Time", copy=False)

    postnl_track_trace_code = fields.Char(string="PostNL Barcode / Track&Trace", copy=False)
    postnl_track_trace_url = fields.Char(string="PostNL Track&Trace URL", compute="_compute_postnl_tnt_url", store=True)

    postnl_last_webhook_at = fields.Datetime(string="PostNL Last Webhook At", copy=False)
    postnl_fulfilment_status = fields.Selection([
        ("pending", "Pending"),
        ("shipped", "Shipped"),
        ("partial", "Partially Shipped"),
        ("error", "Error"),
    ], default="pending", copy=False)
    postnl_last_payload = fields.Text(string="PostNL Last Payload (Debug)", copy=False)

    @api.depends("postnl_track_trace_code", "partner_shipping_id.zip")
    def _compute_postnl_tnt_url(self):
        for order in self:
            barcode = (order.postnl_track_trace_code or "").strip()
            postcode = (order.partner_shipping_id.zip or "").replace(" ", "").strip()
            if barcode and postcode:
                # ✅ Must build ourselves (as you required)
                order.postnl_track_trace_url = f"https://www.postnl.nl/tracktrace/?B={barcode}&P={postcode}"
            else:
                order.postnl_track_trace_url = False

    def _postnl_apply_shipment(self, meta: dict, order_status: dict):
        """Apply 1 orderStatus item to sale.order"""
        self.ensure_one()

        order_no = order_status.get("orderNo")
        barcode = (order_status.get("trackAndTraceCode") or "").strip()
        ship_date = order_status.get("shipDate")
        ship_time = order_status.get("shipTime")

        if order_no and not self.postnl_fulfilment_order_no:
            self.postnl_fulfilment_order_no = order_no

        # multi shipments => append barcode
        if barcode:
            existing = (self.postnl_track_trace_code or "").strip()
            if existing and barcode not in existing.split(","):
                self.postnl_track_trace_code = f"{existing},{barcode}"
                self.postnl_fulfilment_status = "partial"
            else:
                self.postnl_track_trace_code = barcode
                self.postnl_fulfilment_status = "shipped"

        if ship_date:
            self.postnl_ship_date = ship_date
        if ship_time:
            self.postnl_ship_time = ship_time

        self.postnl_message_no = meta.get("messageNo") or self.postnl_message_no
        self.postnl_last_webhook_at = fields.Datetime.now()
        self.postnl_last_payload = json.dumps({"meta": meta, "orderStatus": order_status}, indent=2)

        # Update picking tracking too (optional but useful)
        picking = self.picking_ids.filtered(lambda p: p.state not in ("done", "cancel"))[:1]
        if picking and barcode:
            picking.carrier_tracking_ref = barcode

        if barcode:
            msg = (
                f"<b>PostNL Shipment</b><br/>"
                f"OrderNo: {html_escape(order_no or '')}<br/>"
                f"Barcode: {html_escape(barcode)}<br/>"
                f"Ship: {html_escape(ship_date or '')} {html_escape(ship_time or '')}<br/>"
                f"<a href='{html_escape(self.postnl_track_trace_url or '')}' target='_blank'>Track & Trace</a>"
            )
            self.message_post(body=msg)
