# postnl_odoo_integration/services/postnl_shipment_parser.py
from xml.etree import ElementTree as ET


def parse_shipments(content: bytes):
    """
    Parse shipment XML content into a list of dicts:
    {
        'order_ref': 'SO001',
        'tracking_number': '3SABC123456',
        'status': 'DELIVERED',
        'delivered': True/False,
    }
    Adapt this to your PostNL ECS shipment schema.
    """
    res = []
    if not content:
        return res
    root = ET.fromstring(content)
    # assume <Shipments><Shipment>...</Shipment></Shipments>
    for xshipment in root.findall(".//Shipment"):
        order_ref = (xshipment.findtext("OrderNumber") or "").strip()
        tracking = (xshipment.findtext("TrackingNumber") or "").strip()
        status = (xshipment.findtext("Status") or "").strip().upper()
        delivered = status in {"DELIVERED", "DEL", "BEZORGD"}
        res.append(
            {
                "order_ref": order_ref,
                "tracking_number": tracking,
                "status": status,
                "delivered": delivered,
            }
        )
    return res


def validate_sample_file(content: bytes):
    """Lightweight validation used by 'Test Shipment Import'."""
    # will raise if XML is invalid
    parse_shipments(content)
