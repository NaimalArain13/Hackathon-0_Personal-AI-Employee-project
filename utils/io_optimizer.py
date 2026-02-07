"""
I/O Optimizer Module for the Personal AI Employee system.
Optimizes file I/O operations for better performance.
"""

import asyncio
import logging
import os
import threading
from pathlib import Path
from typing import List, Union, Callable
from functools import wraps
import time
from utils.setup_logger import setup_logger


class IOOptimizer:
    """
    Class to optimize file I/O operations for better performance.
    """

    def __init__(self):
        """Initialize the I/O optimizer."""
        self.logger = setup_logger("IOOptimizer", level=logging.INFO)
        self.cache = {}
        self.lock = threading.RLock()  # Reentrant lock for thread safety
        self.max_cache_size = 100  # Maximum number of files to cache

    def read_file_optimized(self, file_path: str, use_cache: bool = True) -> str:
        """
        Optimized file reading with caching.

        Args:
            file_path: Path to the file to read
            use_cache: Whether to use caching for frequently accessed files

        Returns:
            Content of the file as a string
        """
        path = Path(file_path)

        # Use cache if enabled and file is in cache
        if use_cache:
            with self.lock:
                if str(path) in self.cache:
                    cached_data, cached_time, file_stat = self.cache[str(path)]

                    # Check if file has been modified since caching
                    try:
                        current_stat = path.stat()
                        if current_stat.st_mtime <= cached_time:
                            self.logger.debug(f"Cache hit for {file_path}")
                            return cached_data
                        else:
                            # File has been modified, remove from cache
                            del self.cache[str(path)]
                    except FileNotFoundError:
                        # File no longer exists, remove from cache
                        del self.cache[str(path)]

        # Read the file
        start_time = time.time()
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        read_time = time.time() - start_time

        if read_time > 0.1:  # Log if reading takes more than 100ms
            self.logger.warning(f"Slow file read for {file_path}: {read_time:.3f}s")

        # Cache the file if cache is enabled
        if use_cache:
            with self.lock:
                # Remove oldest entries if cache is full
                if len(self.cache) >= self.max_cache_size:
                    # Remove oldest entry (by modification time)
                    oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                    del self.cache[oldest_key]

                try:
                    file_stat = path.stat()
                    self.cache[str(path)] = (content, file_stat.st_mtime, file_stat)
                except FileNotFoundError:
                    pass  # File was deleted, don't cache

        return content

    def write_file_optimized(self, file_path: str, content: str, append: bool = False) -> bool:
        """
        Optimized file writing with batching and buffering.

        Args:
            file_path: Path to the file to write
            content: Content to write to the file
            append: Whether to append to the file or overwrite

        Returns:
            True if successful, False otherwise
        """
        path = Path(file_path)

        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        try:
            mode = 'a' if append else 'w'
            with open(path, mode, encoding='utf-8', buffering=8192) as f:  # 8KB buffer
                f.write(content)

            write_time = time.time() - start_time

            if write_time > 0.1:  # Log if writing takes more than 100ms
                self.logger.warning(f"Slow file write for {file_path}: {write_time:.3f}s")

            # Invalidate cache if file was modified
            with self.lock:
                if str(path) in self.cache:
                    del self.cache[str(path)]

            return True
        except Exception as e:
            self.logger.error(f"Error writing file {file_path}: {e}")
            return False

    def batch_read_files(self, file_paths: List[str]) -> List[tuple]:
        """
        Batch read multiple files efficiently.

        Args:
            file_paths: List of file paths to read

        Returns:
            List of tuples (file_path, content, success)
        """
        results = []

        # Sort files by size to optimize I/O (smaller files first)
        size_sorted_paths = sorted(file_paths, key=lambda p: self._get_file_size(p))

        for file_path in size_sorted_paths:
            try:
                content = self.read_file_optimized(file_path)
                results.append((file_path, content, True))
            except Exception as e:
                self.logger.error(f"Error reading {file_path}: {e}")
                results.append((file_path, "", False))

        return results

    def batch_write_files(self, file_data: List[tuple]) -> List[tuple]:
        """
        Batch write multiple files efficiently.

        Args:
            file_data: List of tuples (file_path, content) to write

        Returns:
            List of tuples (file_path, success)
        """
        results = []

        for file_path, content in file_data:
            success = self.write_file_optimized(file_path, content)
            results.append((file_path, success))

        return results

    def _get_file_size(self, file_path: str) -> int:
        """
        Get file size with error handling.

        Args:
            file_path: Path to the file

        Returns:
            Size of the file in bytes, or infinity if file doesn't exist
        """
        try:
            return Path(file_path).stat().st_size
        except FileNotFoundError:
            return float('inf')  # Put missing files at the end

    def clear_cache(self):
        """Clear the file cache."""
        with self.lock:
            self.cache.clear()
            self.logger.info("File cache cleared")

    def get_cache_stats(self) -> dict:
        """
        Get statistics about the file cache.

        Returns:
            Dictionary with cache statistics
        """
        with self.lock:
            return {
                'cached_files': len(self.cache),
                'cache_size_limit': self.max_cache_size,
                'cache_keys': list(self.cache.keys())
            }

    def atomic_write(self, file_path: str, content: str) -> bool:
        """
        Perform an atomic write operation (write to temp file then rename).

        Args:
            file_path: Path to the file to write
            content: Content to write

        Returns:
            True if successful, False otherwise
        """
        path = Path(file_path)
        temp_path = path.with_suffix(path.suffix + '.tmp')

        try:
            # Write to temporary file
            self.write_file_optimized(str(temp_path), content)

            # Atomically replace the original file
            temp_path.replace(path)

            # Invalidate cache
            with self.lock:
                if str(path) in self.cache:
                    del self.cache[str(path)]

            return True
        except Exception as e:
            self.logger.error(f"Atomic write failed for {file_path}: {e}")

            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()

            return False

    async def async_read_file(self, file_path: str) -> str:
        """
        Asynchronously read a file using thread pool.

        Args:
            file_path: Path to the file to read

        Returns:
            Content of the file as a string
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.read_file_optimized, file_path, True)

    async def async_write_file(self, file_path: str, content: str) -> bool:
        """
        Asynchronously write a file using thread pool.

        Args:
            file_path: Path to the file to write
            content: Content to write

        Returns:
            True if successful, False otherwise
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.write_file_optimized, file_path, content, False)


# Global instance for easy access
_io_optimizer = IOOptimizer()


def get_io_optimizer() -> IOOptimizer:
    """
    Get the global I/O optimizer instance.

    Returns:
        IOOptimizer instance
    """
    return _io_optimizer


def optimized_file_operation(func: Callable) -> Callable:
    """
    Decorator to optimize file operations.

    Args:
        func: Function to decorate

    Returns:
        Decorated function with optimized I/O
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # This could be expanded to add additional optimizations
        # For now, it just calls the original function
        return func(*args, **kwargs)

    return wrapper


if __name__ == "__main__":
    # Example usage
    import logging

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create an I/O optimizer
    optimizer = IOOptimizer()

    print("I/O Optimizer initialized")
    print(f"Cache stats: {optimizer.get_cache_stats()}")

    # Example: Create a test file and read it
    test_file = "test_optimized_read.md"
    test_content = "# Test File\n\nThis is a test file for optimized I/O operations."

    # Write the file
    success = optimizer.write_file_optimized(test_file, test_content)
    print(f"Write success: {success}")

    # Read the file (this will cache it)
    content = optimizer.read_file_optimized(test_file)
    print(f"Read success: {len(content)} characters read")

    # Read again (this should use cache)
    content_cached = optimizer.read_file_optimized(test_file)
    print(f"Cached read success: {len(content_cached)} characters read")

    # Clean up
    import os
    if os.path.exists(test_file):
        os.remove(test_file)