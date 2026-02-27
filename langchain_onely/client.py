"""HTTP client for OneLy API."""

import time
from typing import Any, Dict, Optional

import requests

from .constants import (
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    ONELY_API_BASE,
    PACKAGE_VERSION,
    RETRY_BACKOFF,
)


class OneLyClient:
    """HTTP client for interacting with OneLy API."""

    def __init__(self, api_key: Optional[str] = None, base_url: str = ONELY_API_BASE):
        """Initialize OneLy client.

        Args:
            api_key: Optional API key for seller actions
            base_url: Base URL for API (default: https://1ly.store)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()

    def _get_headers(self, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get headers for API request.

        Args:
            additional_headers: Optional additional headers

        Returns:
            Dict of headers
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"langchain-onely/{PACKAGE_VERSION}",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        if additional_headers:
            headers.update(additional_headers)

        return headers

    @staticmethod
    def _safe_json(response: requests.Response) -> Optional[Any]:
        """Safely parse JSON from a response."""
        try:
            return response.json()
        except ValueError:
            return None

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body data
            headers: Additional headers

        Returns:
            Response JSON

        Raises:
            requests.HTTPError: On HTTP error
        """
        url = f"{self.base_url}{endpoint}"
        request_headers = self._get_headers(headers)

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    headers=request_headers,
                    timeout=DEFAULT_TIMEOUT,
                )

                # Handle rate limiting with retry
                if response.status_code == 429:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_BACKOFF**attempt
                        time.sleep(wait_time)
                        continue
                    else:
                        return {
                            "error": True,
                            "message": "Rate limit exceeded. Please try again later.",
                            "details": {
                                "code": "RATE_LIMIT_EXCEEDED",
                                "status": 429,
                            },
                        }

                # Check for errors
                if not response.ok:
                    error_data = self._safe_json(response)
                    if error_data is None:
                        error_data = {"raw": response.text} if response.text else {}
                    return {
                        "error": True,
                        "message": f"API request failed: {response.status_code}",
                        "details": {
                            "code": "API_ERROR",
                            "status": response.status_code,
                            "response": error_data,
                        },
                    }

                # Success
                if not response.text:
                    return {}
                data = self._safe_json(response)
                if data is None:
                    return {
                        "error": True,
                        "message": "API returned non-JSON response.",
                        "details": {
                            "code": "NON_JSON_RESPONSE",
                            "status": response.status_code,
                            "response": response.text,
                        },
                    }
                return data

            except requests.Timeout:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF**attempt)
                    continue
                return {
                    "error": True,
                    "message": "Request timed out. Please try again.",
                    "details": {
                        "code": "TIMEOUT",
                        "timeout": DEFAULT_TIMEOUT,
                    },
                }

            except requests.RequestException as e:
                return {
                    "error": True,
                    "message": f"Request failed: {str(e)}",
                    "details": {
                        "code": "REQUEST_FAILED",
                        "exception": str(e),
                    },
                }

        return {
            "error": True,
            "message": "Max retries exceeded.",
            "details": {"code": "MAX_RETRIES_EXCEEDED"},
        }

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make GET request."""
        return self._make_request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make POST request."""
        return self._make_request("POST", endpoint, json_data=json_data, headers=headers)

    def put(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make PUT request."""
        return self._make_request("PUT", endpoint, json_data=json_data, headers=headers)

    def delete(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make DELETE request."""
        return self._make_request("DELETE", endpoint, headers=headers)
