"""Configuration management for XML Watcher Service."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from dotenv import load_dotenv


class ConfigError(Exception):
    """Configuration related errors."""
    pass


class Config:
    """Configuration manager for the XML Watcher Service."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_path: Path to configuration file. If not provided,
                        looks for CONFIG_FILE env var or config/config.yaml
        """
        load_dotenv()  # Load environment variables from .env file
        
        if config_path is None:
            config_path = os.getenv("CONFIG_FILE", "config/config.yaml")
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
        self._validate_config()
        self._apply_env_overrides()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise ConfigError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ConfigError(f"Error reading config file: {e}")
    
    def _validate_config(self) -> None:
        """Validate configuration values."""
        # Required fields
        required_fields = [
            "watch_folder",
            "api.endpoint",
        ]
        
        for field in required_fields:
            if not self._get_nested(field):
                raise ConfigError(f"Required configuration field missing: {field}")
        
        # Validate watch folder exists
        watch_folder = Path(self.watch_folder)
        if not watch_folder.exists():
            raise ConfigError(f"Watch folder does not exist: {watch_folder}")
        if not watch_folder.is_dir():
            raise ConfigError(f"Watch folder is not a directory: {watch_folder}")
        
        # Validate numeric values
        if self.service_check_interval <= 0:
            raise ConfigError("service.check_interval must be positive")
        
        if self.api_timeout <= 0:
            raise ConfigError("api.timeout must be positive")
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        # Map of env vars to config paths
        env_mapping = {
            "WATCH_FOLDER": "watch_folder",
            "API_ENDPOINT": "api.endpoint",
            "API_TOKEN": "api.auth.token",
            "LOG_LEVEL": "logging.level",
        }
        
        for env_var, config_path in env_mapping.items():
            value = os.getenv(env_var)
            if value:
                self._set_nested(config_path, value)
    
    def _get_nested(self, path: str, default: Any = None) -> Any:
        """Get nested configuration value using dot notation."""
        keys = path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def _set_nested(self, path: str, value: Any) -> None:
        """Set nested configuration value using dot notation."""
        keys = path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    @property
    def watch_folder(self) -> str:
        """Get watch folder path."""
        return self._get_nested("watch_folder", "")
    
    @property
    def api_endpoint(self) -> str:
        """Get API endpoint URL."""
        return self._get_nested("api.endpoint", "")
    
    @property
    def api_auth_type(self) -> str:
        """Get API authentication type."""
        return self._get_nested("api.auth.type", "none")
    
    @property
    def api_auth_token(self) -> Optional[str]:
        """Get API bearer token."""
        return self._get_nested("api.auth.token")
    
    @property
    def api_auth_username(self) -> Optional[str]:
        """Get API basic auth username."""
        return self._get_nested("api.auth.username")
    
    @property
    def api_auth_password(self) -> Optional[str]:
        """Get API basic auth password."""
        return self._get_nested("api.auth.password")
    
    @property
    def api_timeout(self) -> int:
        """Get API request timeout."""
        return int(self._get_nested("api.timeout", 30))
    
    @property
    def api_retry_attempts(self) -> int:
        """Get number of API retry attempts."""
        return int(self._get_nested("api.retry_attempts", 3))
    
    @property
    def api_retry_delay(self) -> int:
        """Get delay between API retries."""
        return int(self._get_nested("api.retry_delay", 5))
    
    @property
    def file_patterns(self) -> list:
        """Get file patterns to watch."""
        return self._get_nested("processing.patterns", ["*.xml", "*.XML"])
    
    @property
    def process_existing(self) -> bool:
        """Whether to process existing files on startup."""
        return bool(self._get_nested("processing.process_existing", False))
    
    @property
    def delete_after_upload(self) -> bool:
        """Whether to delete files after successful upload."""
        return bool(self._get_nested("processing.delete_after_upload", False))
    
    @property
    def processed_folder(self) -> Optional[str]:
        """Get folder to move processed files to."""
        folder = self._get_nested("processing.processed_folder", "")
        return folder if folder else None
    
    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self._get_nested("logging.level", "INFO")
    
    @property
    def log_file(self) -> Optional[str]:
        """Get log file path."""
        file_path = self._get_nested("logging.file", "")
        return file_path if file_path else None
    
    @property
    def log_max_size(self) -> int:
        """Get maximum log file size in MB."""
        return int(self._get_nested("logging.max_size", 10))
    
    @property
    def log_backup_count(self) -> int:
        """Get number of log backup files."""
        return int(self._get_nested("logging.backup_count", 5))
    
    @property
    def log_colored_output(self) -> bool:
        """Whether to use colored console output."""
        return bool(self._get_nested("logging.colored_output", True))
    
    @property
    def service_name(self) -> str:
        """Get service name."""
        return self._get_nested("service.name", "xml-watcher")
    
    @property
    def service_check_interval(self) -> float:
        """Get check interval in seconds."""
        return float(self._get_nested("service.check_interval", 1.0))
    
    @property
    def service_recursive(self) -> bool:
        """Whether to watch subdirectories recursively."""
        return bool(self._get_nested("service.recursive", True))
    
    @property
    def max_concurrent_uploads(self) -> int:
        """Get maximum number of concurrent uploads."""
        return int(self._get_nested("service.max_concurrent_uploads", 5))
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        headers = {}
        
        if self.api_auth_type == "bearer" and self.api_auth_token:
            headers["Authorization"] = f"Bearer {self.api_auth_token}"
        elif self.api_auth_type == "basic" and self.api_auth_username and self.api_auth_password:
            import base64
            credentials = base64.b64encode(
                f"{self.api_auth_username}:{self.api_auth_password}".encode()
            ).decode()
            headers["Authorization"] = f"Basic {credentials}"
        
        return headers
