import logging
import sys
import traceback
from typing import Optional
from datetime import datetime
import json
from ..config.settings import settings

class StructuredLogger:
    """
    Provides structured logging for the Response Delivery service with enhanced error handling
    """

    def __init__(self, name: str = "response_delivery", level: Optional[int] = None):
        """
        Initialize the structured logger

        Args:
            name: Name of the logger
            level: Logging level (defaults to DEBUG if settings.debug is True, otherwise INFO)
        """
        self.logger = logging.getLogger(name)

        # Set default level based on settings
        if level is None:
            level = logging.DEBUG if settings.debug else logging.INFO

        self.logger.setLevel(level)

        # Prevent adding multiple handlers if logger already has handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _log(self, level: int, message: str, **kwargs):
        """
        Internal method to log messages with structured data

        Args:
            level: Logging level
            message: Log message
            **kwargs: Additional structured data to log
        """
        try:
            if self.logger.isEnabledFor(level):
                # Create structured log entry
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": logging.getLevelName(level),
                    "message": message,
                    "service": settings.app_name
                }

                # Add any additional structured data
                for key, value in kwargs.items():
                    log_entry[key] = value

                # Log the structured entry as JSON
                self.logger.log(level, json.dumps(log_entry))
        except Exception as e:
            # Fallback logging if structured logging fails
            try:
                self.logger.log(level, f"Fallback log: {message} - Error in structured logging: {str(e)}")
            except Exception:
                # Ultimate fallback - print to stdout if logging completely fails
                print(f"[{datetime.utcnow().isoformat()}] {logging.getLevelName(level)} - {message}")

    def debug(self, message: str, **kwargs):
        """Log a debug message"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log an info message"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log a warning message"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log an error message"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log a critical message"""
        self._log(logging.CRITICAL, message, **kwargs)


# Global logger instance
logger = StructuredLogger()


def get_logger(name: str = "response_delivery") -> StructuredLogger:
    """
    Get a logger instance

    Args:
        name: Name of the logger (defaults to "response_delivery")

    Returns:
        StructuredLogger: Logger instance
    """
    return StructuredLogger(name=name)


def log_delivery_attempt(outbound_message_id: str, channel: str, success: bool,
                        attempt_number: int, processing_time_ms: int, **kwargs):
    """
    Log a delivery attempt with structured data

    Args:
        outbound_message_id: ID of the outbound message
        channel: Channel used for delivery
        success: Whether the delivery was successful
        attempt_number: Attempt number
        processing_time_ms: Processing time in milliseconds
        **kwargs: Additional data to log
    """
    try:
        logger.info(
            f"Delivery attempt completed for message {outbound_message_id}",
            event_type="delivery_attempt",
            outbound_message_id=outbound_message_id,
            channel=channel,
            success=success,
            attempt_number=attempt_number,
            processing_time_ms=processing_time_ms,
            **kwargs
        )
    except Exception as e:
        # Fallback if structured logging fails
        print(f"Delivery attempt log failed: {outbound_message_id}, channel: {channel}, success: {success}")


def log_rate_limit_event(channel: str, rate_limit_type: str, current_usage: int,
                        limit: int, reset_time: str, **kwargs):
    """
    Log a rate limit event

    Args:
        channel: Channel affected
        rate_limit_type: Type of rate limit event
        current_usage: Current usage count
        limit: Rate limit threshold
        reset_time: When the limit resets
        **kwargs: Additional data to log
    """
    try:
        logger.warning(
            f"Rate limit event for channel {channel}",
            event_type="rate_limit_event",
            channel=channel,
            rate_limit_type=rate_limit_type,
            current_usage=current_usage,
            limit=limit,
            reset_time=reset_time,
            **kwargs
        )
    except Exception as e:
        # Fallback if structured logging fails
        print(f"Rate limit event log failed: channel {channel}, type: {rate_limit_type}, usage: {current_usage}")


def log_retry_event(outbound_message_id: str, channel: str, attempt_number: int,
                   max_attempts: int, reason: str, **kwargs):
    """
    Log a retry event

    Args:
        outbound_message_id: ID of the outbound message
        channel: Channel for delivery
        attempt_number: Current attempt number
        max_attempts: Maximum number of attempts
        reason: Reason for retry
        **kwargs: Additional data to log
    """
    try:
        logger.info(
            f"Retry event for message {outbound_message_id}",
            event_type="retry_event",
            outbound_message_id=outbound_message_id,
            channel=channel,
            attempt_number=attempt_number,
            max_attempts=max_attempts,
            reason=reason,
            **kwargs
        )
    except Exception as e:
        # Fallback if structured logging fails
        print(f"Retry event log failed: message {outbound_message_id}, channel: {channel}, attempt: {attempt_number}")


def log_error(error: Exception, context: str = "", **kwargs):
    """
    Log an error with context

    Args:
        error: The exception that occurred
        context: Context where the error occurred
        **kwargs: Additional data to log
    """
    try:
        logger.error(
            f"Error occurred: {str(error)}",
            event_type="error",
            error_type=type(error).__name__,
            error_message=str(error),
            context=context,
            traceback=traceback.format_exc(),
            **kwargs
        )
    except Exception as e:
        # Ultimate fallback
        print(f"ERROR in {context}: {str(error)}")
        print(traceback.format_exc())


def log_performance_metric(metric_name: str, value: float, unit: str = "", **kwargs):
    """
    Log a performance metric with error handling

    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        **kwargs: Additional data to log
    """
    try:
        logger.info(
            f"Performance metric: {metric_name} = {value}{unit}",
            event_type="performance_metric",
            metric_name=metric_name,
            value=value,
            unit=unit,
            **kwargs
        )
    except Exception as e:
        # Fallback if structured logging fails
        print(f"Performance metric log failed: {metric_name} = {value}{unit}")


def log_critical_business_event(event_type: str, message: str, **kwargs):
    """
    Log a critical business event that should always be captured

    Args:
        event_type: Type of business event
        message: Event message
        **kwargs: Additional context
    """
    try:
        logger.critical(
            f"Critical business event: {event_type} - {message}",
            event_type="critical_business_event",
            business_event_type=event_type,
            message=message,
            **kwargs
        )
    except Exception as e:
        # Ultimate fallback
        print(f"CRITICAL BUSINESS EVENT: {event_type} - {message}")
        print(json.dumps(kwargs))