"""Unit tests for file watcher module."""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import time
from queue import Queue

from watchdog.events import FileCreatedEvent, FileModifiedEvent

from src.watcher import XMLFileHandler, XMLWatcher
from src.config import Config


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = Mock(spec=Config)
    config.watch_folder = "/test/watch"
    config.file_patterns = ["*.xml", "*.XML"]
    config.process_existing = False
    config.service_recursive = True
    config.max_concurrent_uploads = 5
    config.delete_after_upload = False
    config.processed_folder = None
    return config


@pytest.fixture
def mock_upload_callback():
    """Create a mock upload callback."""
    return Mock()


class TestXMLFileHandler:
    """Test cases for XMLFileHandler class."""
    
    def test_init(self):
        """Test handler initialization."""
        queue = Queue()
        handler = XMLFileHandler(["*.xml"], queue)
        
        assert handler.patterns == ["*.xml"]
        assert handler.queue == queue
        assert len(handler.processed_files) == 0
    
    def test_matches_pattern(self):
        """Test pattern matching."""
        handler = XMLFileHandler(["*.xml", "*.XML"], Queue())
        
        assert handler._matches_pattern("/path/to/file.xml") is True
        assert handler._matches_pattern("/path/to/file.XML") is True
        assert handler._matches_pattern("/path/to/file.txt") is False
        assert handler._matches_pattern("test.xml") is True
    
    def test_handle_file_matching(self):
        """Test handling of matching files."""
        queue = Queue()
        handler = XMLFileHandler(["*.xml"], queue)
        
        handler._handle_file("/test/file.xml")
        
        assert queue.qsize() == 1
        assert queue.get() == "/test/file.xml"
        assert "/test/file.xml" in handler.processed_files
    
    def test_handle_file_non_matching(self):
        """Test handling of non-matching files."""
        queue = Queue()
        handler = XMLFileHandler(["*.xml"], queue)
        
        handler._handle_file("/test/file.txt")
        
        assert queue.qsize() == 0
    
    def test_handle_file_duplicate(self):
        """Test handling of duplicate files."""
        queue = Queue()
        handler = XMLFileHandler(["*.xml"], queue)
        
        # Add file twice
        handler._handle_file("/test/file.xml")
        handler._handle_file("/test/file.xml")
        
        # Should only be queued once
        assert queue.qsize() == 1
    
    def test_on_created(self):
        """Test file creation event handling."""
        queue = Queue()
        handler = XMLFileHandler(["*.xml"], queue)
        
        # Create mock event
        event = Mock(spec=FileCreatedEvent)
        event.is_directory = False
        event.src_path = "/test/new_file.xml"
        
        handler.on_created(event)
        
        assert queue.qsize() == 1
        assert queue.get() == "/test/new_file.xml"
    
    def test_on_created_directory(self):
        """Test directory creation event handling."""
        queue = Queue()
        handler = XMLFileHandler(["*.xml"], queue)
        
        # Create mock event for directory
        event = Mock(spec=FileCreatedEvent)
        event.is_directory = True
        event.src_path = "/test/new_dir"
        
        handler.on_created(event)
        
        assert queue.qsize() == 0
    
    @patch('time.sleep')
    def test_on_modified(self, mock_sleep):
        """Test file modification event handling."""
        queue = Queue()
        handler = XMLFileHandler(["*.xml"], queue)
        
        # Create mock event
        event = Mock(spec=FileModifiedEvent)
        event.is_directory = False
        event.src_path = "/test/modified_file.xml"
        
        handler.on_modified(event)
        
        assert queue.qsize() == 1
        assert queue.get() == "/test/modified_file.xml"
        mock_sleep.assert_called_once_with(0.1)


class TestXMLWatcher:
    """Test cases for XMLWatcher class."""
    
    def test_init(self, mock_config, mock_upload_callback):
        """Test watcher initialization."""
        watcher = XMLWatcher(mock_config, mock_upload_callback)
        
        assert watcher.config == mock_config
        assert watcher.upload_callback == mock_upload_callback
        assert isinstance(watcher.file_queue, Queue)
        assert watcher.observer is not None
        assert watcher.worker_thread is None
    
    @patch('src.watcher.Observer')
    @patch('src.watcher.Thread')
    def test_start_without_existing(self, mock_thread, mock_observer, mock_config, mock_upload_callback):
        """Test starting watcher without processing existing files."""
        mock_config.process_existing = False
        
        watcher = XMLWatcher(mock_config, mock_upload_callback)
        watcher.start()
        
        # Verify observer was started
        watcher.observer.schedule.assert_called_once()
        watcher.observer.start.assert_called_once()
        
        # Verify worker thread was started
        mock_thread.assert_called_once()
        mock_thread.return_value.start.assert_called_once()
    
    @patch('src.watcher.Observer')
    @patch('src.watcher.Thread')
    @patch('src.watcher.Path')
    def test_start_with_existing(self, mock_path_class, mock_thread, mock_observer, 
                                mock_config, mock_upload_callback):
        """Test starting watcher with processing existing files."""
        mock_config.process_existing = True
        
        # Mock existing files
        mock_path = MagicMock()
        mock_path_class.return_value = mock_path
        
        mock_file1 = MagicMock()
        mock_file1.stat.return_value.st_mtime = 100
        mock_file2 = MagicMock()
        mock_file2.stat.return_value.st_mtime = 200
        
        mock_path.rglob.return_value = [mock_file1, mock_file2]
        
        watcher = XMLWatcher(mock_config, mock_upload_callback)
        watcher.start()
        
        # Verify existing files were queued
        assert watcher.file_queue.qsize() == 4  # 2 files x 2 patterns
    
    @patch('src.watcher.Observer')
    def test_stop(self, mock_observer, mock_config, mock_upload_callback):
        """Test stopping the watcher."""
        watcher = XMLWatcher(mock_config, mock_upload_callback)
        watcher.worker_thread = Mock()
        
        watcher.stop()
        
        assert watcher.stop_event.is_set()
        watcher.observer.stop.assert_called_once()
        watcher.observer.join.assert_called_once()
        watcher.worker_thread.join.assert_called_once()
        watcher.executor.shutdown.assert_called_once_with(wait=True)
    
    @patch('time.sleep')
    def test_process_file_success(self, mock_sleep, mock_config, mock_upload_callback, tmp_path):
        """Test successful file processing."""
        # Create test file
        test_file = tmp_path / "test.xml"
        test_file.write_text("<test>data</test>")
        
        watcher = XMLWatcher(mock_config, mock_upload_callback)
        watcher._process_file(str(test_file))
        
        # Verify upload callback was called
        mock_upload_callback.assert_called_once_with(test_file)
        mock_sleep.assert_called_once_with(0.5)
    
    @patch('time.sleep')
    def test_process_file_not_exists(self, mock_sleep, mock_config, mock_upload_callback):
        """Test processing non-existent file."""
        watcher = XMLWatcher(mock_config, mock_upload_callback)
        watcher._process_file("/non/existent/file.xml")
        
        # Upload callback should not be called
        mock_upload_callback.assert_not_called()
    
    @patch('time.sleep')
    def test_process_file_with_delete(self, mock_sleep, mock_config, mock_upload_callback, tmp_path):
        """Test file processing with delete after upload."""
        mock_config.delete_after_upload = True
        
        # Create test file
        test_file = tmp_path / "test.xml"
        test_file.write_text("<test>data</test>")
        
        watcher = XMLWatcher(mock_config, mock_upload_callback)
        watcher._process_file(str(test_file))
        
        # Verify file was deleted
        assert not test_file.exists()
    
    @patch('time.sleep')
    def test_process_file_with_move(self, mock_sleep, mock_config, mock_upload_callback, tmp_path):
        """Test file processing with move after upload."""
        processed_folder = tmp_path / "processed"
        mock_config.processed_folder = str(processed_folder)
        
        # Create test file
        test_file = tmp_path / "test.xml"
        test_file.write_text("<test>data</test>")
        
        watcher = XMLWatcher(mock_config, mock_upload_callback)
        watcher._process_file(str(test_file))
        
        # Verify file was moved
        assert not test_file.exists()
        assert (processed_folder / "test.xml").exists()
    
    def test_get_queue_size(self, mock_config, mock_upload_callback):
        """Test getting queue size."""
        watcher = XMLWatcher(mock_config, mock_upload_callback)
        
        # Add items to queue
        watcher.file_queue.put("file1.xml")
        watcher.file_queue.put("file2.xml")
        
        assert watcher.get_queue_size() == 2
