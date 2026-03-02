import asyncio
import random
from datetime import datetime, timedelta
from typing import Callable, Any, Optional, Union
from ..utils.logger import logger


class RetryMechanism:
    """
    Implements exponential backoff with jitter for retry logic
    """

    def __init__(self, base_delay: int = 5, max_delay: int = 300, max_attempts: int = 3, jitter_factor: float = 0.1):
        """
        Initialize the retry mechanism

        Args:
            base_delay: Base delay in seconds for the first retry (default 5)
            max_delay: Maximum delay in seconds between retries (default 300, 5 minutes)
            max_attempts: Maximum number of retry attempts (default 3)
            jitter_factor: Factor for adding randomness to delays (default 0.1 = 10%)
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_attempts = max_attempts
        self.jitter_factor = jitter_factor

    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic

        Args:
            func: The function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function

        Returns:
            Result of the function if successful

        Raises:
            Exception: If all retry attempts fail, raises the last exception
        """
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                logger.info(
                    f"Function executed successfully on attempt {attempt}",
                    function_name=func.__name__ if hasattr(func, '__name__') else str(func),
                    attempt=attempt
                )
                return result
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Attempt {attempt} failed: {str(e)}",
                    function_name=func.__name__ if hasattr(func, '__name__') else str(func),
                    attempt=attempt,
                    max_attempts=self.max_attempts
                )

                if attempt < self.max_attempts:
                    delay = self.calculate_delay(attempt)
                    logger.info(
                        f"Waiting {delay:.2f}s before retry",
                        attempt=attempt + 1,
                        delay=delay
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_attempts} attempts failed",
                        function_name=func.__name__ if hasattr(func, '__name__') else str(func),
                        error=str(last_exception)
                    )

        # If we get here, all attempts failed
        raise last_exception

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate the delay for a specific attempt using exponential backoff with jitter

        Args:
            attempt: The attempt number (1-indexed)

        Returns:
            float: Delay in seconds
        """
        # Exponential backoff: base_delay * (2 ^ (attempt - 1))
        base_delay = self.base_delay * (2 ** (attempt - 1))

        # Cap the delay at max_delay
        capped_delay = min(base_delay, self.max_delay)

        # Add jitter: add/subtract up to jitter_factor percentage of the delay
        jitter_range = capped_delay * self.jitter_factor
        jitter = random.uniform(-jitter_range, jitter_range)

        final_delay = max(0, capped_delay + jitter)

        return final_delay

    def calculate_next_retry_time(self, attempt: int, base_time: Optional[datetime] = None) -> datetime:
        """
        Calculate the next retry time based on the attempt number

        Args:
            attempt: The attempt number (1-indexed)
            base_time: Base time to calculate from (default: current time)

        Returns:
            datetime: When the next retry should occur
        """
        if base_time is None:
            base_time = datetime.utcnow()

        delay = self.calculate_delay(attempt)
        return base_time + timedelta(seconds=delay)

    def is_retry_exhausted(self, attempt: int) -> bool:
        """
        Check if the retry attempts are exhausted

        Args:
            attempt: Current attempt number

        Returns:
            bool: True if retry is exhausted, False otherwise
        """
        return attempt >= self.max_attempts

    def get_remaining_attempts(self, current_attempt: int) -> int:
        """
        Get the number of remaining retry attempts

        Args:
            current_attempt: Current attempt number

        Returns:
            int: Number of remaining attempts
        """
        return max(0, self.max_attempts - current_attempt)


class DeliveryRetryMechanism(RetryMechanism):
    """
    Specialized retry mechanism for delivery operations with additional delivery-specific logic
    """

    def __init__(self, base_delay: int = 5, max_delay: int = 300, max_attempts: int = 3, jitter_factor: float = 0.1):
        """
        Initialize the delivery retry mechanism

        Args:
            base_delay: Base delay in seconds for the first retry
            max_delay: Maximum delay in seconds between retries
            max_attempts: Maximum number of retry attempts
            jitter_factor: Factor for adding randomness to delays
        """
        super().__init__(base_delay, max_delay, max_attempts, jitter_factor)

    async def execute_delivery_with_retry(self, delivery_func: Callable, message_id: str,
                                       channel: str, *args, **kwargs) -> Any:
        """
        Execute a delivery function with retry logic and delivery-specific logging

        Args:
            delivery_func: The delivery function to execute
            message_id: ID of the message being delivered
            channel: Channel being used for delivery
            *args: Arguments to pass to the delivery function
            **kwargs: Keyword arguments to pass to the delivery function

        Returns:
            Result of the delivery function if successful

        Raises:
            Exception: If all retry attempts fail, raises the last exception
        """
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.info(
                    f"Attempting delivery for message {message_id}",
                    message_id=message_id,
                    channel=channel,
                    attempt=attempt,
                    max_attempts=self.max_attempts
                )

                result = await delivery_func(*args, **kwargs) if asyncio.iscoroutinefunction(delivery_func) else delivery_func(*args, **kwargs)

                logger.info(
                    f"Delivery successful for message {message_id}",
                    message_id=message_id,
                    channel=channel,
                    attempt=attempt
                )
                return result
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"Delivery attempt {attempt} failed for message {message_id}: {str(e)}",
                    message_id=message_id,
                    channel=channel,
                    attempt=attempt,
                    max_attempts=self.max_attempts,
                    error_type=type(e).__name__
                )

                if attempt < self.max_attempts:
                    delay = self.calculate_delay(attempt)
                    logger.info(
                        f"Scheduling retry for message {message_id} in {delay:.2f}s",
                        message_id=message_id,
                        channel=channel,
                        attempt=attempt + 1,
                        delay=delay
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_attempts} delivery attempts failed for message {message_id}",
                        message_id=message_id,
                        channel=channel,
                        error=str(last_exception)
                    )

        # If we get here, all attempts failed
        raise last_exception

    def categorize_failure(self, exception: Exception) -> str:
        """
        Categorize a failure as temporary or permanent

        Args:
            exception: The exception that occurred

        Returns:
            str: 'temporary' or 'permanent' based on the exception type
        """
        temp_failures = [
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
            "rate limit",
            "throttled",
            "temporarily unavailable"
        ]

        exc_str = str(type(exception).__name__).lower() + " " + str(exception).lower()

        for temp_failure in temp_failures:
            if isinstance(temp_failure, str):
                if temp_failure in exc_str:
                    return "temporary"
            else:
                if isinstance(exception, temp_failure):
                    return "temporary"

        return "permanent"


# Global retry mechanism instance
retry_mechanism = DeliveryRetryMechanism()


def get_retry_mechanism() -> DeliveryRetryMechanism:
    """
    Get the global retry mechanism instance

    Returns:
        DeliveryRetryMechanism: The global retry mechanism instance
    """
    return retry_mechanism


def calculate_delay(attempt: int) -> float:
    """
    Calculate delay for a given attempt using the global retry mechanism

    Args:
        attempt: The attempt number (1-indexed)

    Returns:
        float: Delay in seconds
    """
    return retry_mechanism.calculate_delay(attempt)


def calculate_next_retry_time(attempt: int, base_time: Optional[datetime] = None) -> datetime:
    """
    Calculate the next retry time for a given attempt

    Args:
        attempt: The attempt number (1-indexed)
        base_time: Base time to calculate from (default: current time)

    Returns:
        datetime: When the next retry should occur
    """
    return retry_mechanism.calculate_next_retry_time(attempt, base_time)