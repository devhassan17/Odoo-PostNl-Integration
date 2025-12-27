# # -*- coding: utf-8 -*-

# """PostNL Fulfilment API configuration.

# For now these values are hardcoded as requested.
# Later you can move them to ir.config_parameter / settings UI.
# """

# # Sandbox endpoint (Production: https://api.postnl.nl/v2/fulfilment/order)
# API_URL = "https://api-sandbox.postnl.nl/v2/fulfilment/order"

# # Required headers (PostNL docs: Content-type, customerNumber, apikey)
# CUSTOMER_NUMBER = "10586117"
# API_KEY = "d9fc5fac-91d1-498b-80b2-d95efcbcc389"

# # Payload defaults
# MERCHANT_CODE = "mc"
# FULFILMENT_LOCATION = "AstroHouten"
# CHANNEL = "NL"        # Packing slip language
# DEFAULT_PRODUCT_CODE = "03085" # PostNL product code fallback

# # HTTP timeout (seconds)
# TIMEOUT = 30

# # Optional: only send for these countries (empty = allow all)
# ALLOWED_COUNTRY_CODES = []
