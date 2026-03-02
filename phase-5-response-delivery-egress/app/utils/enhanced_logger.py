import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
import traceback


class EnhancedLogger:
    """
    Enhanced structured logging with improved error handling and context tracking
    """

    def __init__(self, name: str = "response_delivery", level: str = "INFO"):
        """
        Initialize the enhanced logger

        Args:
            name: Name of the logger
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_json_formatter()
            self._setup_error_handling()

    def _setup_json_formatter(self):
        """
        Set up JSON formatter for structured logging
        """
        json_formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s %(module)s %(function)s %(line)s",
            rename_fields={
                'timestamp': '@timestamp',
                'level': 'level',
                'name': 'logger',
            }
        )

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(json_formatter)
        self.logger.addHandler(handler)

    def _setup_error_handling(self):
        """
        Set up error handling for the logger
        """
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            self.logger.critical(
                "Uncaught exception",
                exc_info=(exc_type, exc_value, exc_traceback)
            )

        sys.excepthook = handle_exception

    def _log_with_context(self, level: int, message: str, **kwargs):
        """
        Log a message with additional context

        Args:
            level: Logging level
            message: Log message
            **kwargs: Additional context to include in the log
        """
        extra_fields = {
            "timestamp": datetime.utcnow().isoformat(),
            "context": kwargs
        }

        # Add caller information
        frame = sys._getframe(2)  # Get the caller's frame
        extra_fields["module"] = frame.f_globals.get("__name__", "")
        extra_fields["function"] = frame.f_code.co_name
        extra_fields["line"] = frame.f_lineno

        self.logger.log(level, message, extra=extra_fields)

    def debug(self, message: str, **kwargs):
        """Log a debug message"""
        self._log_with_context(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log an info message"""
        self._log_with_context(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log a warning message"""
        self._log_with_context(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log an error message"""
        self._log_with_context(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log a critical message"""
        self._log_with_context(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs):
        """
        Log an exception with traceback

        Args:
            message: Log message
            **kwargs: Additional context to include in the log
        """
        extra_fields = {
            "timestamp": datetime.utcnow().isoformat(),
            "context": kwargs,
            "traceback": traceback.format_exc()
        }

        # Add caller information
        frame = sys._getframe(1)  # Get the caller's frame
        extra_fields["module"] = frame.f_globals.get("__name__", "")
        extra_fields["function"] = frame.f_code.co_name
        extra_fields["line"] = frame.f_lineno

        self.logger.error(message, extra=extra_fields, exc_info=True)

    def log_delivery_attempt(self, channel: str, message_id: str, success: bool,
                           processing_time_ms: float, **kwargs):
        """
        Log a delivery attempt with specific delivery-related fields

        Args:
            channel: Delivery channel (gmail, whatsapp, webform)
            message_id: ID of the message being delivered
            success: Whether the delivery was successful
            processing_time_ms: Processing time in milliseconds
            **kwargs: Additional context
        """
        self.info(
            f"Delivery attempt completed for message {message_id}",
            channel=channel,
            message_id=message_id,
            success=success,
            processing_time_ms=processing_time_ms,
            **kwargs
        )

    def log_rate_limit_event(self, channel: str, client_id: str, remaining_calls: int,
                           reset_time: str, **kwargs):
        """
        Log a rate limit event

        Args:
            channel: Channel where rate limit occurred
            client_id: Client that triggered rate limit
            remaining_calls: Number of remaining calls
            reset_time: When the rate limit resets
            **kwargs: Additional context
        """
        self.warning(
            f"Rate limit event for channel {channel}",
            event_type="rate_limit",
            channel=channel,
            client_id=client_id,
            remaining_calls=remaining_calls,
            reset_time=reset_time,
            **kwargs
        )

    def log_retry_event(self, message_id: str, channel: str, attempt_number: int,
                       max_attempts: int, reason: str, **kwargs):
        """
        Log a retry event

        Args:
            message_id: ID of the message being retried
            channel: Channel for the retry
            attempt_number: Current attempt number
            max_attempts: Maximum number of attempts
            reason: Reason for the retry
            **kwargs: Additional context
        """
        self.info(
            f"Retry attempt {attempt_number} for message {message_id}",
            event_type="retry",
            message_id=message_id,
            channel=channel,
            attempt_number=attempt_number,
            max_attempts=max_attempts,
            reason=reason,
            **kwargs
        )


# Global logger instance
enhanced_logger = EnhancedLogger()


def get_enhanced_logger(name: str = "response_delivery") -> EnhancedLogger:
    """
    Get the global enhanced logger instance

    Args:
        name: Name for the logger (default: response_delivery)

    Returns:
        EnhancedLogger: The enhanced logger instance
    """
    return EnhancedLogger(name)


# Convenience functions for common logging
def log_delivery_attempt(channel: str, message_id: str, success: bool,
                       processing_time_ms: float, **kwargs):
    """Convenience function to log delivery attempts"""
    enhanced_logger.log_delivery_attempt(channel, message_id, success, processing_time_ms, **kwargs)


def log_rate_limit_event(channel: str, client_id: str, remaining_calls: int,
                        reset_time: str, **kwargs):
    """Convenience function to log rate limit events"""
    enhanced_logger.log_rate_limit_event(channel, client_id, remaining_calls, reset_time, **kwargs)


def log_retry_event(message_id: str, channel: str, attempt_number: int,
                   max_attempts: int, reason: str, **kwargs):
    """Convenience function to log retry events"""
    enhanced_logger.log_retry_event(message_id, channel, attempt_number, max_attempts, reason, **kwargs)


def log_exception(message: str, **kwargs):
    """Convenience function to log exceptions"""
    enhanced_logger.exception(message, **kwargs)


def log_error(message: str, **kwargs):
    """Convenience function to log errors"""
    enhanced_logger.error(message, **kwargs)


def log_info(message: str, **kwargs):
    """Convenience function to log info"""
    enhanced_logger.info(message, **kwargs)


def log_warning(message: str, **kwargs):
    """Convenience function to log warnings"""
    enhanced_logger.warning(message, **kwargs)


def log_debug(message: str, **kwargs):
    """Convenience function to log debug"""
    enhanced_logger.debug(message, **kwargs)