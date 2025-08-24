#!/usr/bin/env python3
"""Main entry point for XML Watcher Service."""

import os
import sys
import signal
import logging
import argparse
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Add parent directory to path for imports when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config, ConfigError
from src.api_client import APIClient, APIError
from src.watcher import XMLWatcher
import logging as logging_module  # Avoid conflict with logger variable


# Try to import colorlog for colored output
try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


class XMLWatcherService:
    """Main service class for XML Watcher."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the service.
        
        Args:
            config_path: Path to configuration file
        """
        self.config: Optional[Config] = None
        self.api_client: Optional[APIClient] = None
        self.watcher: Optional[XMLWatcher] = None
        self.logger: Optional[logging_module.Logger] = None
        self.running = False
        
        # Load configuration
        try:
            self.config = Config(config_path)
        except ConfigError as e:
            print(f"Configuration error: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Set up logging
        self._setup_logging()
        
        # Initialize components
        self._initialize_components()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        # Create logger
        self.logger = logging.getLogger()
        self.logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        
        if self.config.log_colored_output and COLORLOG_AVAILABLE:
            # Colored console output
            console_formatter = colorlog.ColoredFormatter(
                '%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
        else:
            # Standard console output
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if configured)
        if self.config.log_file:
            log_path = Path(self.config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                self.config.log_file,
                maxBytes=self.config.log_max_size * 1024 * 1024,  # MB to bytes
                backupCount=self.config.log_backup_count
            )
            
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def _initialize_components(self):
        """Initialize service components."""
        self.logger.info(f"Initializing {self.config.service_name} service...")
        
        # Initialize API client
        try:
            self.api_client = APIClient(self.config)
            
            # Test API connection
            self.logger.info("Testing API connection...")
            if self.api_client.test_connection():
                self.logger.info("API connection successful")
            else:
                self.logger.warning("API connection test failed - will retry during uploads")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize API client: {e}")
            sys.exit(1)
        
        # Initialize watcher
        try:
            self.watcher = XMLWatcher(self.config, self._upload_file)
        except Exception as e:
            self.logger.error(f"Failed to initialize file watcher: {e}")
            sys.exit(1)
    
    def _upload_file(self, file_path: Path):
        """Upload a file to the API.
        
        Args:
            file_path: Path to the file to upload
        """
        assert self.logger is not None, "Logger not initialized"
        assert self.api_client is not None, "API client not initialized"
        
        self.logger.info(f"Processing file: {file_path}")
        
        try:
            response = self.api_client.upload_file(file_path)
            self.logger.info(f"Successfully uploaded {file_path.name}: {response}")
        except APIError as e:
            self.logger.error(f"Failed to upload {file_path.name}: {e}")
            # Could implement a dead letter queue here for failed uploads
        except Exception as e:
            self.logger.error(f"Unexpected error uploading {file_path.name}: {e}")
    
    def start(self):
        """Start the service."""
        assert self.logger is not None, "Logger not initialized"
        assert self.config is not None, "Config not initialized"
        assert self.watcher is not None, "Watcher not initialized"
        
        self.logger.info(f"Starting {self.config.service_name} service...")
        self.logger.info(f"Watching folder: {self.config.watch_folder}")
        self.logger.info(f"API endpoint: {self.config.api_endpoint}")
        self.logger.info(f"File patterns: {', '.join(self.config.file_patterns)}")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            # Start watcher
            self.watcher.start()
            self.running = True
            
            self.logger.info("Service started successfully. Press Ctrl+C to stop.")
            
            # Keep the main thread alive
            while self.running:
                # Log queue size periodically
                queue_size = self.watcher.get_queue_size()
                if queue_size > 0:
                    self.logger.info(f"Files in queue: {queue_size}")
                
                # Sleep for check interval
                signal.pause() if hasattr(signal, 'pause') else time.sleep(30)
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Service error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the service."""
        if not self.running:
            return
        
        self.running = False
        assert self.logger is not None, "Logger not initialized"
        
        self.logger.info("Stopping service...")
        
        # Stop watcher
        if self.watcher:
            self.watcher.stop()
        
        # Close API client
        if self.api_client:
            self.api_client.close()
        
        self.logger.info("Service stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals."""
        assert self.logger is not None, "Logger not initialized"
        self.logger.info(f"Received signal {signum}")
        self.running = False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="XML Watcher Service - Monitors a folder for XML files and uploads them to an API"
    )
    parser.add_argument(
        "-c", "--config",
        help="Path to configuration file (default: config/config.yaml)",
        default="config/config.yaml"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="XML Watcher Service 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Create and start service
    service = XMLWatcherService(args.config)
    service.start()


if __name__ == "__main__":
    import time  # Import here for signal.pause fallback
    main()
