# SRP Energy API Documentation

## Overview
The Srp Energy API allows users to access energy usage data provided by SRP Energy, a utility company. Users can retrieve information about their energy consumption, view historical data, and track trends over time. This API provides a convenient way for developers to integrate energy usage data into their applications.

## Base URL
`https://myaccount.srpnet.com/myaccountapi/api`

## Authentication
Authentication is required for most endpoints. The API uses session cookies and an XSRF token (`x-xsrf-token` header). The `SrpClient` class handling this authentication flow can be found in `src/srp/client.py`.


## API Endpoints

### Retrieve Energy Usage Data (Hourly)
**Endpoint**
`GET /usage/hourlydetail`

**Parameters**
- `billaccount` (required): The billing account number.
- `beginDate` (required): Start date of the data range (format: MM-DD-YYYY).
- `endDate` (required): End date of the data range (format: MM-DD-YYYY).

**Example**
```python
import requests

# This is a conceptual example. Real usage requires full authentication setup.
url = "https://myaccount.srpnet.com/myaccountapi/api/usage/hourlydetail"
params = {
    "billaccount": "1234567890",
    "beginDate": "01-01-2022",
    "endDate": "01-31-2022"
}

response = requests.get(url, params=params, headers=authenticated_headers)
data = response.json()
print(data)
```

### Retrieve Daily Usage Data
**Endpoint**
`GET /usage/dailyusagedetail`

**Parameters**
- `billaccount` (required): The billing account number.
- `beginDate` (required): Start date (format: MM-DD-YYYY).
- `endDate` (required): End date (format: MM-DD-YYYY).


## Other Discovered Endpoints
The following endpoints were identified but typically require no additional parameters layout or are auxiliary:
]

- `outages/lastReportedOutage`: Get last reported outage.
- `outages/userinoutage`: Check if user is in an outage.
- `usage/dailyweather`: Get daily weather.
