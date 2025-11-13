# postnl_odoo_integration/services/postnl_order_builder.py
from datetime import datetime
from xml.etree import ElementTree as ET
from odoo.tools import frozendict


def _format_filename(pattern: str) -> str:
    if not pattern:
        pattern = "orders_%Y%m%d_%H%M%S.xml"
    return datetime.now().strftime(pattern)


def build_order_xml(order, filename_pattern):
    """
    Build a simple XML for PostNL ECS.
    Replace structure with your real ECS schema from Woo plugin.
    """
    order.ensure_one()
    order._compute_postnl_shipping_code()

    root = ET.Element("Orders")
    xorder = ET.SubElement(root, "Order")
    ET.SubElement(xorder, "OrderNumber").text = order.name or ""
    ET.SubElement(xorder, "CustomerName").text = order.partner_shipping_id.name or ""
    ET.SubElement(xorder, "Street").text = order.partner_shipping_id.street or ""
    ET.SubElement(xorder, "ZipCode").text = order.partner_shipping_id.zip or ""
    ET.SubElement(xorder, "City").text = order.partner_shipping_id.city or ""
    ET.SubElement(xorder, "Country").text = (
        order.partner_shipping_id.country_id.code or ""
    )
    ET.SubElement(xorder, "Email").text = order.partner_shipping_id.email or ""
    ET.SubElement(xorder, "Phone").text = order.partner_shipping_id.phone or ""
    ET.SubElement(xorder, "ShippingCode").text = order.postnl_shipping_code or ""

    lines_el = ET.SubElement(xorder, "Lines")
    for line in order.order_line:
        if line.display_type:
            continue
        xline = ET.SubElement(lines_el, "Line")
        ET.SubElement(xline, "Sku").text = line.product_id.default_code or ""
        ET.SubElement(xline, "Description").text = line.name or ""
        ET.SubElement(xline, "Quantity").text = str(line.product_uom_qty)

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    filename = _format_filename(filename_pattern)
    return xml_bytes, filename


def build_test_order_xml(env):
    """Builds a dummy XML just for configuration testing."""
    # Build a fake minimal 'order-like' object using frozendict
    Dummy = type(
        "DummyOrder",
        (),
        {
            "name": "TESTORDER001",
            "partner_shipping_id": frozendict(
                {
                    "name": "Test Customer",
                    "street": "Test Street 1",
                    "zip": "1000AA",
                    "city": "Amsterdam",
                    "country_id": frozendict({"code": "NL"}),
                    "email": "test@example.com",
                    "phone": "+3100000000",
                }
            ),
            "order_line": [],
            "postnl_shipping_code": "TEST",
            "_compute_postnl_shipping_code": lambda self: None,
            "ensure_one": lambda self: None,
        },
    )
    dummy_order = Dummy()
    xml_bytes, _ = build_order_xml(dummy_order, "test_%Y%m%d_%H%M%S.xml")
    return xml_bytes.decode("utf-8")
