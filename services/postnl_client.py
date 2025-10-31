import logging
import base64
from odoo import models, api

_logger = logging.getLogger(__name__)

POSTNL_ENDPOINTS = {
    "sandbox": "https://api-sandbox.postnl.nl",
    "production": "https://api.postnl.nl",
}

class PostNLClient(models.AbstractModel):
    _name = "postnl.client"
    _description = "PostNL API Client"

    @api.model
    def is_configured(self):
        icp = self.env["ir.config_parameter"].sudo()
        return bool(icp.get_param("postnl_base.api_key"))

    @api.model
    def _base_url(self):
        icp = self.env["ir.config_parameter"].sudo()
        test_mode = icp.get_param("postnl_base.test_mode") in ("True", True, "1", 1)
        return POSTNL_ENDPOINTS["sandbox" if test_mode else "production"]

    @api.model
    def _auth_headers(self):
        icp = self.env["ir.config_parameter"].sudo()
        api_key = icp.get_param("postnl_base.api_key")
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "apikey": api_key or "",
        }

    # -- Public helpers --
    @api.model
    def build_track_trace_url(self, barcode, partner):
        # Generic T&T link pattern; PostNL also offers localized pages.
        country_code = (partner.country_id and partner.country_id.code) or "NL"
        postcode = (partner.zip or "").replace(" ", "")
        return f"https://tracktrace.postnl.nl/?B={barcode}&P={postcode}&D={country_code}"

    # -- Core operations --
    @api.model
    def create_label_from_picking(self, picking, shipment_record=None):
        """Create a shipping label via PostNL APIs.
        This is a minimal working stub that returns a fake PDF in test mode,
        and is structured so you can plug in real endpoints (Labelling API).
        """
        icp = self.env["ir.config_parameter"].sudo()
        test_mode = icp.get_param("postnl_base.test_mode") in ("True", True, "1", 1)

        # Build shipment payload from picking
        payload = self._build_labelling_payload(picking, shipment_record)

        if test_mode:
            # Return a dummy PDF and barcode for fast validation
            dummy_pdf = self._dummy_label_pdf(picking.name)
            dummy_barcode = f"3S{picking.id:08d}NL"
            tnt = self.build_track_trace_url(dummy_barcode, picking.partner_id)
            return {"barcode": dummy_barcode, "label_pdf": dummy_pdf, "track_trace_url": tnt}

        # TODO: integrate with real PostNL Labelling endpoint using 'requests'
        # Example (pseudo):
        # import requests, json
        # url = self._base_url() + "/shipment/v2_2/label"  # Example path; verify in docs
        # resp = requests.post(url, headers=self._auth_headers(), data=json.dumps(payload), timeout=30)
        # resp.raise_for_status()
        # data = resp.json()
        # pdf_b64 = data["ResponseShipments"][0]["Labels"][0]["Content"]
        # barcode = data["ResponseShipments"][0]["Barcodes"][0]["Value"]
        # return {"barcode": barcode, "label_pdf": base64.b64decode(pdf_b64), "track_trace_url": self.build_track_trace_url(barcode, picking.partner_id)}
        raise NotImplementedError("Please implement the real PostNL API call (Labelling)")

    @api.model
    def _build_labelling_payload(self, picking, shipment_record=None):
        icp = self.env["ir.config_parameter"].sudo()
        return {
            "Customer": {
                "CustomerCode": icp.get_param("postnl_base.customer_code") or "",
                "CustomerNumber": icp.get_param("postnl_base.customer_number") or "",
                "Address": {
                    "AddressType": "02",
                    "City": icp.get_param("postnl_base.sender_city") or "",
                    "CompanyName": icp.get_param("postnl_base.sender_name") or "",
                    "Countrycode": icp.get_param("postnl_base.sender_country_code") or "NL",
                    "HouseNr": icp.get_param("postnl_base.sender_house_no") or "",
                    "Street": icp.get_param("postnl_base.sender_street") or "",
                    "Zipcode": icp.get_param("postnl_base.sender_postcode") or "",
                }
            },
            "Shipments": [{
                "Addresses": [
                    {
                        "AddressType": "01",  # Receiver
                        "FirstName": picking.partner_id.name or "",
                        "Name": picking.partner_id.name or "",
                        "CompanyName": picking.partner_id.commercial_company_name or "",
                        "Street": picking.partner_id.street or "",
                        "HouseNr": picking.partner_id.street2 or "",
                        "Zipcode": (picking.partner_id.zip or "").replace(" ", ""),
                        "City": picking.partner_id.city or "",
                        "Countrycode": (picking.partner_id.country_id and picking.partner_id.country_id.code) or "NL",
                        "Email": picking.partner_id.email or "",
                        "MobileNumber": picking.partner_id.mobile or picking.partner_id.phone or "",
                    }
                ],
                "Barcode": "",
                "Dimension": {"Weight": int((picking.weight or 0.5) * 1000)},  # grams
                "ProductCodeDelivery": "3085",  # placeholder: NL domestic parcel
                "Reference": picking.name,
                "Remark": getattr(shipment_record, "label_description", "") if shipment_record else "",
                "Options": self._build_options(shipment_record),
            }]
        }

    @api.model
    def _build_options(self, shipment_record):
        opts = []
        if shipment_record:
            if shipment_record.signature:
                opts.append({"OptionType": "Signature"})
            if shipment_record.only_recipient:
                opts.append({"OptionType": "OnlyRecipent"})
            if shipment_record.insured and shipment_record.insured_amount:
                opts.append({"OptionType": "Insured", "Characteristics": [{"Characteristic": "Amount", "Value": int(shipment_record.insured_amount)}]})
        return opts

    @api.model
    def _dummy_label_pdf(self, ref):
        # super tiny PDF placeholder (valid minimal PDF)
        pdf = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>
endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>
endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>> >>
endobj
4 0 obj<</Length 55>>
stream
BT /F1 12 Tf 50 150 Td (PostNL Label: {ref}) Tj ET
endstream
endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>
endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000060 00000 n 
0000000112 00000 n 
0000000269 00000 n 
0000000380 00000 n 
trailer<</Size 6/Root 1 0 R>>
startxref
457
%%EOF"""
        return pdf.encode("utf-8")


    @api.model
    def _cron_update_tracking(self):
        # TODO: Call PostNL Track & Trace API for recent shipments and update states/log notes
        _logger.info("PostNL tracking cron stub executed.")
