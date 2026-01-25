import httpx
from typing import Optional, Dict, List, Any
from urllib.parse import unquote

class SrpClient:
    """
    Client for interacting with the SRP Energy API.
    """
    BASE_URL = "https://myaccount.srpnet.com/myaccountapi/api"

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        
        # Use headers that mimic a real browser/client as found in debugging
        headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Mobile Safari/537.36",
            "srp-client": "redesign",
            "Accept": "application/json, text/plain, */*"
        }
        
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers)
        self.xsrf_token: Optional[str] = None
        # self.cookies is managed by the client.cookies automatically

    async def login(self) -> None:
        """
        Authenticates with the SRP API.
        1. Posts credentials to authorize.
        2. Fetches the XSRF token from the antiforgery endpoint.
        """
        # Step 0: Prime cookies (optional but good practice based on debugging)
        try:
            await self.client.get("https://myaccount.srpnet.com/")
        except Exception:
            pass # Ignore failures here

        # Step 1: Login to get session cookies
        login_url = f"{self.BASE_URL}/login/authorize"
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        # Initial login request
        response = await self.client.post(
            login_url, 
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        
        # Step 2: Get XSRF token from the specific endpoint
        antiforgery_url = f"{self.BASE_URL}/login/antiforgerytoken"
        response = await self.client.get(antiforgery_url)
        response.raise_for_status()
        
        # Extract XSRF token from cookies in the response
        # It comes in as URL-encoded (e.g. including %7C instead of |)
        raw_xsrf = response.cookies.get("xsrf-token") or response.cookies.get("XSRF-TOKEN")
        
        if raw_xsrf:
            self.xsrf_token = unquote(raw_xsrf)
        else:
             # Fallback check client cookies just in case
             raw_xsrf = self.client.cookies.get("xsrf-token") or self.client.cookies.get("XSRF-TOKEN")
             if raw_xsrf:
                 self.xsrf_token = unquote(raw_xsrf)

    async def get_usage(self, account_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Fetches hourly usage data.
        
        Args:
            account_id: The billing account number.
            start_date: Start date in format MM-DD-YYYY.
            end_date: End date in format MM-DD-YYYY.
        """
        if not self.xsrf_token:
            await self.login()

        url = f"{self.BASE_URL}/usage/hourlydetail"
        
        params = {
            "billaccount": account_id,
            "beginDate": start_date,
            "endDate": end_date
        }
        
        headers = {}
        if self.xsrf_token:
            headers["x-xsrf-token"] = self.xsrf_token
        
        response = await self.client.get(
            url, 
            params=params, 
            headers=headers
        )
        response.raise_for_status()
        
        return response.json()

    async def get_daily_usage(self, account_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Fetches daily usage data.
        """
        params = {
            "billaccount": account_id,
            "beginDate": start_date,
            "endDate": end_date
        }
        return await self._get("/usage/dailyusagedetail", params=params)

    async def get_profile(self) -> Dict[str, Any]:
        """
        Fetches the user profile information.
        """
        return await self._get("/login/profile")

    async def get_landlord_list(self) -> List[Any]:
        """
        Fetches the list of landlord accounts.
        """
        return await self._get("/landlord/list")

    # --- Billing & Payments ---

    async def get_current_bill_info(self, account_id: str) -> Dict[str, Any]:
        """
        Fetches current bill info.
        """
        return await self._get("/accounts/getcurrentbillinfo", params={"billAccount": account_id})

    async def get_bill_projection(self, account_id: str) -> Dict[str, Any]:
        """
        Fetches bill projection for the current cycle.
        """
        return await self._get("/payments/billprojection", params={"billaccount": account_id})

    async def get_payment_history(self, account_id: str) -> List[Any]:
        """
        Fetches payment history for the account.
        """
        return await self._get("/payments/historybyacct", params={"billAccount": account_id})

    async def get_scheduled_payments(self, account_id: str) -> List[Any]:
        """
        Fetches scheduled payments.
        """
        return await self._get("/payments/getscheduledbyacct", params={"billAccount": account_id})

    # --- Account ---

    async def get_all_accounts(self) -> List[Any]:
        """
        Fetches all accounts linked to the user.
        """
        return await self._get("/accounts/all")
        
    async def get_billing_address(self, account_id: str) -> Dict[str, Any]:
        """
        Fetches billing address.
        """
        return await self._get("/accounts/billingaddress", params={"can": account_id})

    # --- Outages ---

    async def get_outages(self) -> Dict[str, Any]:
        """
        Fetches active outages and outage history.
        """
        # Based on HAR, there are multiple outage endpoints. 
        # 'getall' seems to be the main one for active status?
        return await self._get("/outages/getall")

    # --- Documents ---

    async def get_ebill_list(self, account_id: str) -> List[Any]:
        """
        Fetches list of available eBill documents.
        """
        return await self._get("/documents/eBillList", params={"id": account_id})

    # --- Helper ---

    async def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Internal helper for GET requests with automatic auth and error handling.
        """
        if not self.xsrf_token:
            await self.login()

        url = f"{self.BASE_URL}{endpoint}"
        
        headers = {}
        if self.xsrf_token:
            headers["x-xsrf-token"] = self.xsrf_token

        response = await self.client.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    ENDPOINTS = {
        "accounts/all": "Get all accounts linked to the user.",
        "accounts/billingaddress": "Get billing address.",
        "accounts/getaccounthistory": "Get account history.",
        "accounts/getaccountmanager": "Get account manager details.",
        "accounts/getaddress": "Get account address.",
        "accounts/getcurrentbillinfo": "Get current bill info (balance, due date).",
        "accounts/getmpowerdata": "Get MPower data (prepaid).",
        "accounts/getphone": "Get phone number.",
        "accounts/getratecode": "Get rate code (price plan).",
        "accounts/getratemetadata": "Get rate metadata.",
        "accounts/gettransferredaccountstatus": "Check transfer status.",
        "accounts/hashaccount": "Get account hash.",
        "autopay/getautopayinfo": "Get AutoPay settings.",
        "autopay/getiseligible": "Check AutoPay eligibility.",
        "autopay/getisenrolled": "Check AutoPay enrollment.",
        "bankaccount/getlist": "List saved bank accounts.",
        "contact/getcontacts": "Get contact information.",
        "documents/communitysolarlink": "Community solar link.",
        "documents/eBillDocument.pdf": "Download eBill PDF (requires params).",
        "documents/eBillList": "List available eBills.",
        "documents/energyscorecardlinks": "Energy scorecard links.",
        "landlord/list": "List landlord accounts.",
        "myaccount/dashboardmessages": "Get dashboard messages.",
        "notification/getnotifications": "Get notification settings.",
        "outages/getMedicalSupportOption": "Get medical support options.",
        "outages/getall": "Get all active outages.",
        "outages/history": "Get outage history.",
        "outages/icereimbursementinfo": "Get ice reimbursement info.",
        "outages/isIneligibleToReport": "Check outage reporting eligibility.",
        "outages/lastReportedOutage": "Get last reported outage.",
        "outages/userinoutage": "Check if user is in an outage.",
        "payments/accountpayment": "Get account payment info.",
        "payments/billingoptionsdetails": "Get billing option details.",
        "payments/billprojection": "Get bill projection.",
        "payments/creditextensioncheck": "Check for credit extension.",
        "payments/getscheduledbyacct": "Get scheduled payments.",
        "payments/historybyacct": "Get payment history.",
        "payments/iscustomduedateeligible": "Check custom due date eligibility.",
        "primarycontacts/getprimarycontactinfostatus": "Get primary contact status.",
        "usage/dailyusagedetail": "Get daily usage (requires params).",
        "usage/dailyweather": "Get daily weather.",
        "usage/hourlydetail": "Get hourly usage (requires params).",
        "wattplan/hasenoughhistory": "Check WattPlan history."
    }

    async def list_available_endpoints(self) -> Dict[str, str]:
        """
        Returns a dictionary of available endpoints and their descriptions.
        """
        return self.ENDPOINTS

    async def generic_request(self, endpoint: str, method: str = "GET", params: Dict[str, Any] = None, data: Dict[str, Any] = None) -> Any:
        """
        Performs a generic request to any SRP endpoint.
        """
        if not self.xsrf_token:
            await self.login()

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        headers = {}
        if self.xsrf_token:
            headers["x-xsrf-token"] = self.xsrf_token

        if method.upper() == "GET":
            response = await self.client.get(url, params=params, headers=headers)
        elif method.upper() == "POST":
            # SRP typically uses form-urlencoded for login but JSON for some valid APIs? 
            # Sticking to standard usage here, but might need adjustment if some APIs want JSON body.
            # Most internal APIs appearing in HAR were GETs.
            response = await self.client.post(url, json=data, params=params, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()
