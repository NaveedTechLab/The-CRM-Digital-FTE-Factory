"""
Performance optimization utilities for high-volume message processing
"""

import asyncio
import time
from typing import Any, Callable, Dict, List
from functools import wraps
from contextlib import contextmanager
import cProfile
import pstats
from io import StringIO
from ..utils.logger import log_performance_metric, logger


class PerformanceMonitor:
    """
    Monitor and optimize performance for high-volume message processing
    """

    def __init__(self):
        self.metrics = {}
        self.profile_stats = {}

    def measure_execution_time(self, func: Callable) -> Callable:
        """
        Decorator to measure execution time of functions

        Args:
            func: Function to measure

        Returns:
            Callable: Wrapped function with timing
        """
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
            finally:
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                log_performance_metric(
                    metric_name=f"{func.__name__}_execution_time",
                    value=execution_time * 1000,  # Convert to milliseconds
                    unit="ms",
                    function=func.__name__
                )
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
            finally:
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                log_performance_metric(
                    metric_name=f"{func.__name__}_execution_time",
                    value=execution_time * 1000,  # Convert to milliseconds
                    unit="ms",
                    function=func.__name__
                )
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    @contextmanager
    def performance_timer(self, operation_name: str):
        """
        Context manager to measure execution time of code blocks

        Args:
            operation_name: Name of the operation being measured
        """
        start_time = time.perf_counter()
        try:
            yield
        finally:
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            log_performance_metric(
                metric_name=f"{operation_name}_execution_time",
                value=execution_time * 1000,  # Convert to milliseconds
                unit="ms",
                operation=operation_name
            )

    def profile_function(self, func: Callable) -> Callable:
        """
        Decorator to profile function execution

        Args:
            func: Function to profile

        Returns:
            Callable: Wrapped function with profiling
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()
            try:
                result = func(*args, **kwargs)
            finally:
                profiler.disable()

                # Get profiling stats
                s = StringIO()
                ps = pstats.Stats(profiler, stream=s)
                ps.sort_stats('cumulative')
                ps.print_stats(10)  # Top 10 functions

                # Store profile stats
                self.profile_stats[func.__name__] = s.getvalue()

                log_performance_metric(
                    metric_name=f"{func.__name__}_profile",
                    value=len(s.getvalue()),
                    unit="chars",
                    function=func.__name__
                )
            return result

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            profiler = cProfile.Profile()
            profiler.enable()
            try:
                result = await func(*args, **kwargs)
            finally:
                profiler.disable()

                # Get profiling stats
                s = StringIO()
                ps = pstats.Stats(profiler, stream=s)
                ps.sort_stats('cumulative')
                ps.print_stats(10)  # Top 10 functions

                # Store profile stats
                self.profile_stats[func.__name__] = s.getvalue()

                log_performance_metric(
                    metric_name=f"{func.__name__}_profile",
                    value=len(s.getvalue()),
                    unit="chars",
                    function=func.__name__
                )
            return result

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper

    def batch_process(self, items: List[Any], process_func: Callable, batch_size: int = 10) -> List[Any]:
        """
        Process items in batches for better performance

        Args:
            items: List of items to process
            process_func: Function to process each item
            batch_size: Size of each batch

        Returns:
            List[Any]: Processed results
        """
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            with self.performance_timer(f"batch_process_{i//batch_size}"):
                batch_results = [process_func(item) for item in batch]
                results.extend(batch_results)

        return results

    async def async_batch_process(self, items: List[Any], process_func: Callable, batch_size: int = 10) -> List[Any]:
        """
        Process items in batches asynchronously for better performance

        Args:
            items: List of items to process
            process_func: Async function to process each item
            batch_size: Size of each batch

        Returns:
            List[Any]: Processed results
        """
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]

            with self.performance_timer(f"async_batch_process_{i//batch_size}"):
                # Process batch concurrently
                batch_tasks = [process_func(item) for item in batch]
                batch_results = await asyncio.gather(*batch_tasks)
                results.extend(batch_results)

        return results

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get a performance report with all collected metrics

        Returns:
            Dict[str, Any]: Performance report
        """
        return {
            "metrics": self.metrics,
            "profile_stats": self.profile_stats,
            "summary": {
                "total_metrics_collected": len(self.metrics),
                "functions_profiled": len(self.profile_stats)
            }
        }


class ConnectionPoolOptimizer:
    """
    Optimize database and API connection pools for high-volume processing
    """

    def __init__(self, max_connections: int = 20, min_connections: int = 5):
        """
        Initialize connection pool optimizer

        Args:
            max_connections: Maximum number of connections
            min_connections: Minimum number of connections to maintain
        """
        self.max_connections = max_connections
        self.min_connections = min_connections
        self.active_connections = 0
        self.connection_pool = []

    async def get_connection(self):
        """
        Get a connection from the pool

        Returns:
            Connection object
        """
        if self.connection_pool:
            # Return existing connection
            return self.connection_pool.pop()
        elif self.active_connections < self.max_connections:
            # Create new connection if under limit
            self.active_connections += 1
            return await self._create_new_connection()
        else:
            # Wait for available connection (implementing a simple queue)
            # In a real implementation, you might want to implement a proper queue
            await asyncio.sleep(0.01)  # Small delay before retrying
            return await self.get_connection()

    async def return_connection(self, connection):
        """
        Return a connection to the pool

        Args:
            connection: Connection object to return
        """
        if len(self.connection_pool) < self.max_connections:
            self.connection_pool.append(connection)
        else:
            # Close connection if pool is full
            await self._close_connection(connection)
            self.active_connections -= 1

    async def _create_new_connection(self):
        """
        Create a new connection

        Returns:
            Connection object
        """
        # This is a placeholder - implement based on your connection type
        # For example, if using SQLAlchemy:
        # return engine.connect()
        pass

    async def _close_connection(self, connection):
        """
        Close a connection

        Args:
            connection: Connection object to close
        """
        # This is a placeholder - implement based on your connection type
        # For example, if using SQLAlchemy:
        # connection.close()
        pass

    def optimize_for_concurrent_load(self, expected_concurrent_requests: int):
        """
        Adjust connection pool size based on expected concurrent load

        Args:
            expected_concurrent_requests: Expected number of concurrent requests
        """
        optimal_size = max(self.min_connections, min(expected_concurrent_requests * 2, self.max_connections))
        self.max_connections = optimal_size
        logger.info(
            f"Adjusted connection pool size for concurrent load",
            expected_concurrent_requests=expected_concurrent_requests,
            new_pool_size=optimal_size
        )


class CacheOptimizer:
    """
    Optimize caching for frequently accessed data
    """

    def __init__(self, max_size: int = 1000):
        """
        Initialize cache optimizer

        Args:
            max_size: Maximum number of items in cache
        """
        self.max_size = max_size
        self.cache = {}
        self.access_order = []  # For LRU implementation

    def get(self, key: str):
        """
        Get item from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if key in self.cache:
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None

    def set(self, key: str, value: Any):
        """
        Set item in cache

        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            # Update existing key
            self.cache[key] = value
            # Move to end (most recently used)
            self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # Add new key
            if len(self.cache) >= self.max_size:
                # Remove least recently used item
                lru_key = self.access_order.pop(0)
                del self.cache[lru_key]

            self.cache[key] = value
            self.access_order.append(key)

    def invalidate(self, key: str):
        """
        Invalidate a cache entry

        Args:
            key: Cache key to invalidate
        """
        if key in self.cache:
            del self.cache[key]
            self.access_order.remove(key)

    def clear(self):
        """
        Clear all cache entries
        """
        self.cache.clear()
        self.access_order.clear()


# Global performance optimization instances
performance_monitor = PerformanceMonitor()
connection_optimizer = ConnectionPoolOptimizer()
cache_optimizer = CacheOptimizer()


def optimize_message_processing():
    """
    Apply performance optimizations for message processing
    """
    logger.info("Applying performance optimizations for message processing")

    # Optimize for expected concurrent load
    # This would be adjusted based on system capacity
    connection_optimizer.optimize_for_concurrent_load(50)

    logger.info("Performance optimizations applied successfully")


def get_optimization_recommendations() -> List[str]:
    """
    Get performance optimization recommendations

    Returns:
        List[str]: Optimization recommendations
    """
    return [
        "Implement connection pooling for database connections",
        "Use batching for bulk operations",
        "Cache frequently accessed data",
        "Monitor and profile performance bottlenecks",
        "Optimize queries with proper indexing",
        "Implement efficient serialization/deserialization",
        "Use asynchronous processing where possible",
        "Implement circuit breaker pattern for external APIs",
        "Monitor memory usage and implement garbage collection",
        "Optimize for concurrent load based on expected volume"
    ]


# Apply optimizations on module import
optimize_message_processing()