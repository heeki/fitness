import json
import os
import urllib3
from urllib.parse import urlencode
from typing import List, Dict, Any, Optional

class StravaOAuth:
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None) -> None:
        self.client_id = client_id or os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('STRAVA_CLIENT_SECRET')

        # Disable SSL warnings (NOT FOR PRODUCTION USE)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Create a PoolManager that ignores SSL verification
        self.http = urllib3.PoolManager(
            cert_reqs='CERT_NONE',
            assert_hostname=False
        )

        if not all([self.client_id, self.client_secret]):
            raise ValueError("Missing required OAuth credentials")

    def get_authorization_url(self) -> str:
        """Generate the authorization URL for the OAuth flow"""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': 'http://localhost/exchange_token',
            'approval_prompt': 'force',
            'scope': 'read,activity:read_all'
        }
        return f"https://www.strava.com/oauth/authorize?{urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange the authorization code for an access token"""
        url = "https://www.strava.com/oauth/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }

        response = self.http.request('POST', url, fields=data)
        if response.status == 200:
            token_data = json.loads(response.data.decode('utf-8'))
            return token_data
        else:
            raise Exception(f"Failed to exchange code for token: {response.data.decode('utf-8')}")

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token using the refresh token"""
        url = "https://www.strava.com/oauth/token"
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }

        response = self.http.request('POST', url, fields=data)
        if response.status == 200:
            token_data = json.loads(response.data.decode('utf-8'))
            return token_data
        else:
            raise Exception(f"Failed to refresh token: {response.data.decode('utf-8')}")

    def make_authenticated_request(self, access_token: str, method: str, url: str, **kwargs: Any) -> Dict[str, Any]:
        """Make an authenticated request to the Strava API"""
        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {access_token}'
        kwargs['headers'] = headers

        try:
            response = self.http.request(method, url, **kwargs)

            # Handle response status
            if response.status == 401:  # Token expired
                raise Exception("Access token expired")
            elif response.status != 200:
                raise Exception(f"Request failed: {response.data.decode('utf-8')}")

            # Return the parsed JSON data
            return json.loads(response.data.decode('utf-8'))

        except Exception as e:
            raise Exception(f"Request failed: {str(e)}")

    def fetch_all_pages(self, access_token: str, url: str, per_page: int = 30) -> List[Dict[str, Any]]:
        """Fetch all pages of data from a paginated Strava API endpoint

        Args:
            access_token: Valid access token
            url: Base URL to fetch from
            per_page: Number of items per page (default: 30)

        Returns:
            List of all items across all pages
        """
        all_items = []
        page = 1
        while True:
            paginated_url = f"{url}?page={page}&per_page={per_page}"
            response = self.make_authenticated_request(access_token, 'GET', paginated_url)

            # if no items returned or empty list, we're done
            if not response:
                break

            # add items from this page to our collection
            all_items.extend(response)

            # if we got fewer items than requested, we've reached the end
            if len(response) < per_page:
                break

            page += 1

        return all_items
