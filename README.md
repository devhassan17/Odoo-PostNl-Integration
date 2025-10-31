# PostNL Base (Odoo 18)

A base module that connects Odoo 18 to PostNL — label creation, delivery options, pickup points, tracking, and WBS rules.

## What works out-of-the-box
- Settings for API key, customer code/number, sender address, defaults (signature, only recipient, insured, insurance amount, package type), and checkout options.
- A **PostNL delivery provider** in `delivery.carrier` (delivery_type = postnl) that can create labels from pickings.
- A **PostNL Shipment** model that stores label PDF, barcode, options, and links to the picking. Includes **Download Label** action.
- A **wizard** to generate a label with custom options.
- **WBS Rules** model (weight & country → shipping code) and menu.
- Simple **website checkout injection** that shows PostNL delivery options (stubbed data). Replace with real Timeframe/Locations API calls.
- A tracking cron stub.

## What you need to finish
- Implement real PostNL API calls in `services/postnl_client.py` (Labelling, Locations, Timeframes, Track & Trace).
- Map `ProductCodeDelivery` and options based on your WBS rules and chosen checkout options.
- Compute real weights and prices in `delivery.carrier` `rate_shipment`.
- Optionally, integrate with your Monta module (e.g. handover scans, WMS syncs).

## How to use
1. Copy `postnl_base` to your Odoo addons path.
2. Update apps list and install.
3. Go to **Settings → General Settings → PostNL** and fill credentials.
4. Create a delivery carrier with **PostNL** type.
5. From a validated picking, open **Actions → Generate PostNL Label** (wizard) or let `send_shipping` run during delivery.
6. Download/print the label from the shipment or picking attachment.

This module ships in **test mode** and returns a **dummy PDF label** until you wire the real PostNL endpoints.
