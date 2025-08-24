"""File system watcher for XML files."""

import os
import time
import logging
import fnmatch
from pathlib import Path
from typing import Set, Callable, Optional, List
from queue import Queue, Empty
from threading import Thread, Event
from concurrent.futures import ThreadPoolExecutor, as_completed

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent


logger = logging.getLogger(__name__)


class XMLFileHandler(FileSystemEventHandler):
    """Handler for XML file system events."""
    
    def __init__(self, patterns: List[str], queue: Queue):
        """Initialize the handler.
        
        Args:
            patterns: List of file patterns to match (e.g., ["*.xml", "*.XML"])
            queue: Queue to put detected files
        """
        self.patterns = patterns
        self.queue = queue
        self.processed_files: Set[str] = set()
    
    def _matches_pattern(self, file_path: str) -> bool:
        """Check if file matches any of the patterns."""
        file_name = os.path.basename(file_path)
        return any(fnmatch.fnmatch(file_name, pattern) for pattern in self.patterns)
    
    def _handle_file(self, file_path: str) -> None:
        """Handle a detected file."""
        # Check if file matches patterns
        if not self._matches_pattern(file_path):
            return
        
        # Avoid processing the same file multiple times in quick succession
        if file_path in self.processed_files:
            return
        
        # Add to processed files with cleanup after 60 seconds
        self.processed_files.add(file_path)
        
        # Clean up old entries (simple approach - in production, use time-based cleanup)
        if len(self.processed_files) > 1000:
            self.processed_files.clear()
        
        logger.debug(f"Detected XML file: {file_path}")
        self.queue.put(file_path)
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            self._handle_file(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            # Wait a bit to ensure file write is complete
            time.sleep(0.1)
            self._handle_file(event.src_path)


class XMLWatcher:
    """Watches a folder for XML files and processes them."""
    
    def __init__(self, config, upload_callback: Callable[[Path], None]):
        """Initialize the watcher.
        
        Args:
            config: Configuration object
            upload_callback: Function to call for each detected file
        """
        self.config = config
        self.upload_callback = upload_callback
        self.file_queue: Queue = Queue()
        self.observer = Observer()
        self.stop_event = Event()
        self.worker_thread: Optional[Thread] = None
        self.executor = ThreadPoolExecutor(
            max_workers=self.config.max_concurrent_uploads
        )
    
    def start(self):
        """Start watching for files."""
        logger.info(f"Starting XML watcher on: {self.config.watch_folder}")
        
        # Process existing files if configured
        if self.config.process_existing:
            self._process_existing_files()
        
        # Set up file system observer
        event_handler = XMLFileHandler(self.config.file_patterns, self.file_queue)
        self.observer.schedule(
            event_handler,
            self.config.watch_folder,
            recursive=self.config.service_recursive
        )
        
        # Start worker thread for processing files
        self.worker_thread = Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        
        # Start observer
        self.observer.start()
        logger.info("XML watcher started successfully")
    
    def stop(self):
        """Stop watching for files."""
        logger.info("Stopping XML watcher...")
        
        # Signal stop
        self.stop_event.set()
        
        # Stop observer
        self.observer.stop()
        self.observer.join()
        
        # Wait for worker thread
        if self.worker_thread:
            self.worker_thread.join(timeout=30)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("XML watcher stopped")
    
    def _process_existing_files(self):
        """Process existing XML files in the watch folder."""
        logger.info("Processing existing XML files...")
        
        watch_path = Path(self.config.watch_folder)
        pattern_files = []
        
        for pattern in self.config.file_patterns:
            if self.config.service_recursive:
                files = list(watch_path.rglob(pattern))
            else:
                files = list(watch_path.glob(pattern))
            pattern_files.extend(files)
        
        # Remove duplicates and sort by modification time
        unique_files = list(set(pattern_files))
        unique_files.sort(key=lambda f: f.stat().st_mtime)
        
        logger.info(f"Found {len(unique_files)} existing XML files")
        
        for file_path in unique_files:
            self.file_queue.put(str(file_path))
    
    def _process_queue(self):
        """Process files from the queue."""
        futures = []
        
        while not self.stop_event.is_set():
            try:
                # Get file from queue with timeout
                file_path = self.file_queue.get(timeout=1)
                
                # Submit to executor
                future = self.executor.submit(self._process_file, file_path)
                futures.append(future)
                
                # Clean up completed futures
                futures = [f for f in futures if not f.done()]
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
    
    def _process_file(self, file_path: str):
        """Process a single file."""
        path = Path(file_path)
        
        # Verify file still exists
        if not path.exists():
            logger.warning(f"File no longer exists: {file_path}")
            return
        
        # Wait a moment to ensure file is fully written
        time.sleep(0.5)
        
        try:
            # Call upload callback
            self.upload_callback(path)
            
            # Handle post-processing
            if self.config.delete_after_upload:
                self._delete_file(path)
            elif self.config.processed_folder:
                self._move_file(path, self.config.processed_folder)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    def _delete_file(self, file_path: Path):
        """Delete a file after processing."""
        try:
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
    
    def _move_file(self, file_path: Path, target_folder: str):
        """Move a file to the processed folder."""
        try:
            target_dir = Path(target_folder)
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate unique target path if file exists
            target_path = target_dir / file_path.name
            counter = 1
            while target_path.exists():
                stem = file_path.stem
                suffix = file_path.suffix
                target_path = target_dir / f"{stem}_{counter}{suffix}"
                counter += 1
            
            file_path.rename(target_path)
            logger.info(f"Moved file to: {target_path}")
            
        except Exception as e:
            logger.error(f"Failed to move file {file_path}: {e}")
    
    def get_queue_size(self) -> int:
        """Get the current queue size."""
        return self.file_queue.qsize()
