"""Unit tests for API client module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import requests

from src.api_client import APIClient, APIError
from src.config import Config


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = Mock(spec=Config)
    config.api_endpoint = "https://api.example.com/upload"
    config.api_auth_type = "bearer"
    config.api_auth_token = "test-token"
    config.api_timeout = 30
    config.api_retry_attempts = 3
    config.api_retry_delay = 1
    config.service_name = "test-service"
    config.get_auth_headers.return_value = {"Authorization": "Bearer test-token"}
    return config


@pytest.fixture
def api_client(mock_config):
    """Create an API client instance."""
    with patch('src.api_client.requests.Session'):
        return APIClient(mock_config)


class TestAPIClient:
    """Test cases for APIClient class."""
    
    def test_init(self, mock_config):
        """Test API client initialization."""
        with patch('src.api_client.requests.Session') as mock_session:
            client = APIClient(mock_config)
            
            assert client.config == mock_config
            assert mock_session.called
    
    def test_create_session(self, api_client, mock_config):
        """Test session creation with retry configuration."""
        # Access the session to trigger creation
        session = api_client.session
        
        # Verify headers were set
        session.headers.update.assert_called()
    
    def test_upload_file_success(self, api_client, tmp_path):
        """Test successful file upload."""
        # Create a test XML file
        test_file = tmp_path / "test.xml"
        test_file.write_text("<test>data</test>")
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "id": "123"}
        
        api_client.session.post.return_value = mock_response
        
        # Perform upload
        result = api_client.upload_file(test_file)
        
        # Verify
        assert result == {"status": "success", "id": "123"}
        api_client.session.post.assert_called_once()
        
        # Check call arguments
        call_args = api_client.session.post.call_args
        assert call_args[0][0] == api_client.config.api_endpoint
        assert "files" in call_args[1]
        assert "data" in call_args[1]
        assert "timeout" in call_args[1]
    
    def test_upload_file_not_found(self, api_client, tmp_path):
        """Test upload with non-existent file."""
        non_existent_file = tmp_path / "does_not_exist.xml"
        
        with pytest.raises(APIError, match="File not found"):
            api_client.upload_file(non_existent_file)
    
    def test_upload_file_not_a_file(self, api_client, tmp_path):
        """Test upload with directory instead of file."""
        directory = tmp_path / "testdir"
        directory.mkdir()
        
        with pytest.raises(APIError, match="Not a file"):
            api_client.upload_file(directory)
    
    def test_upload_file_http_error(self, api_client, tmp_path):
        """Test upload with HTTP error response."""
        # Create a test file
        test_file = tmp_path / "test.xml"
        test_file.write_text("<test>data</test>")
        
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Server error")
        
        api_client.session.post.return_value = mock_response
        
        # Perform upload - should retry and then fail
        with pytest.raises(APIError, match="Failed to upload.*after 3 attempts"):
            api_client.upload_file(test_file)
        
        # Verify retries
        assert api_client.session.post.call_count == 3
    
    def test_upload_file_timeout(self, api_client, tmp_path):
        """Test upload with timeout error."""
        # Create a test file
        test_file = tmp_path / "test.xml"
        test_file.write_text("<test>data</test>")
        
        # Mock timeout
        api_client.session.post.side_effect = requests.exceptions.Timeout()
        
        with pytest.raises(APIError, match="Request timed out"):
            api_client.upload_file(test_file)
    
    def test_upload_file_connection_error(self, api_client, tmp_path):
        """Test upload with connection error."""
        # Create a test file
        test_file = tmp_path / "test.xml"
        test_file.write_text("<test>data</test>")
        
        # Mock connection error
        api_client.session.post.side_effect = requests.exceptions.ConnectionError()
        
        with pytest.raises(APIError, match="Failed to connect"):
            api_client.upload_file(test_file)
    
    def test_upload_file_auth_error(self, api_client, tmp_path):
        """Test upload with authentication error."""
        # Create a test file
        test_file = tmp_path / "test.xml"
        test_file.write_text("<test>data</test>")
        
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
        
        api_client.session.post.return_value = mock_response
        
        with pytest.raises(APIError, match="Authentication failed"):
            api_client.upload_file(test_file)
    
    def test_test_connection_success(self, api_client):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        api_client.session.head.return_value = mock_response
        
        assert api_client.test_connection() is True
    
    def test_test_connection_method_not_allowed(self, api_client):
        """Test connection test with HEAD not allowed."""
        # Mock HEAD returning 405
        mock_head_response = Mock()
        mock_head_response.status_code = 405
        
        # Mock GET returning 200
        mock_get_response = Mock()
        mock_get_response.status_code = 200
        
        api_client.session.head.return_value = mock_head_response
        api_client.session.get.return_value = mock_get_response
        
        assert api_client.test_connection() is True
        
        # Verify GET was called after HEAD failed
        api_client.session.get.assert_called_once()
    
    def test_test_connection_failure(self, api_client):
        """Test failed connection test."""
        api_client.session.head.side_effect = Exception("Network error")
        
        assert api_client.test_connection() is False
    
    def test_close(self, api_client):
        """Test closing the client."""
        api_client.close()
        api_client.session.close.assert_called_once()
