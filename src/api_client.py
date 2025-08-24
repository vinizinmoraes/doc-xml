"""API client for uploading XML files."""

import os
import time
from pathlib import Path
from typing import Optional, Dict, Any
import logging
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class APIError(Exception):
    """API related errors."""
    pass


class APIClient:
    """Client for uploading XML files to the API."""
    
    def __init__(self, config):
        """Initialize API client.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        
        # Configure retries
        retry_strategy = Retry(
            total=self.config.api_retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "User-Agent": f"{self.config.service_name}/1.0",
        })
        
        # Add authentication headers
        auth_headers = self.config.get_auth_headers()
        if auth_headers:
            session.headers.update(auth_headers)
        
        return session
    
    def upload_file(self, file_path: Path) -> Dict[str, Any]:
        """Upload an XML file to the API.
        
        Args:
            file_path: Path to the XML file to upload
            
        Returns:
            Response data from the API
            
        Raises:
            APIError: If upload fails after all retries
        """
        if not file_path.exists():
            raise APIError(f"File not found: {file_path}")
        
        if not file_path.is_file():
            raise APIError(f"Not a file: {file_path}")
        
        logger.info(f"Uploading file: {file_path}")
        
        # Read file content
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
        except Exception as e:
            raise APIError(f"Error reading file {file_path}: {e}")
        
        # Prepare the request
        files = {
            'file': (file_path.name, file_content, 'application/xml')
        }
        
        # Additional metadata
        data = {
            'filename': file_path.name,
            'size': len(file_content),
            'path': str(file_path.absolute()),
        }
        
        # Attempt upload with retries
        last_error = None
        for attempt in range(self.config.api_retry_attempts):
            try:
                response = self._make_request(files, data)
                logger.info(f"Successfully uploaded {file_path.name}")
                return response
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Upload attempt {attempt + 1} failed for {file_path.name}: {e}"
                )
                
                if attempt < self.config.api_retry_attempts - 1:
                    time.sleep(self.config.api_retry_delay)
        
        # All attempts failed
        raise APIError(
            f"Failed to upload {file_path.name} after "
            f"{self.config.api_retry_attempts} attempts: {last_error}"
        )
    
    def _make_request(self, files: Dict, data: Dict) -> Dict[str, Any]:
        """Make the actual API request.
        
        Args:
            files: Files to upload
            data: Additional form data
            
        Returns:
            Response data
            
        Raises:
            APIError: If request fails
        """
        try:
            response = self.session.post(
                self.config.api_endpoint,
                files=files,
                data=data,
                timeout=self.config.api_timeout
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Try to parse JSON response
            try:
                return response.json()
            except ValueError:
                # If response is not JSON, return text
                return {"response": response.text, "status_code": response.status_code}
            
        except requests.exceptions.Timeout:
            raise APIError(f"Request timed out after {self.config.api_timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise APIError("Failed to connect to API endpoint")
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                raise APIError("Authentication failed - check your API credentials")
            elif response.status_code == 404:
                raise APIError(f"API endpoint not found: {self.config.api_endpoint}")
            elif response.status_code == 413:
                raise APIError("File too large for API")
            else:
                raise APIError(f"HTTP error {response.status_code}: {e}")
        except Exception as e:
            raise APIError(f"Unexpected error: {e}")
    
    def test_connection(self) -> bool:
        """Test the API connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try a HEAD request first, fall back to GET if not supported
            response = self.session.head(
                self.config.api_endpoint,
                timeout=10
            )
            
            if response.status_code == 405:  # Method not allowed
                response = self.session.get(
                    self.config.api_endpoint,
                    timeout=10
                )
            
            return response.status_code < 500
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False
    
    def close(self):
        """Close the session."""
        self.session.close()
