import json
import base64
import datetime

# App active profile (test, qa, pre-prod, prod)
PROFILE = "test"

# Frontend build version
WEB_VERSION = "1.0.0-SNAPSHOT"

# Backend build version
API_VERSION = "1.0.0-SNAPSHOT"

# Location (country/tz)
LOCATION_INFO = "AR/UTC-3"

# The Cave website information
WEBSITE_INFO = {
    "Name": "cave",
    "Description": "The Cave/AR website",
    "Web-Version": WEB_VERSION,
    "Api-Version": API_VERSION,
    "Release-Date": datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%s"),
    "Location": LOCATION_INFO
}

# Website signature based on WEBSITE_INFO (base64 encoded)
SIGNATURE = str(base64.b64encode(bytes(json.dumps(WEBSITE_INFO), 'utf-8')))
