from ..models.channel_config import ChannelConfig
from typing import Dict, Optional
import json

class ChannelConfigurationManager:
    """
    Manages default channel configurations for each communication channel
    """

    def __init__(self):
        """
        Initialize the channel configuration manager with default values
        """
        self._default_configs = self._create_default_configs()

    def _create_default_configs(self) -> Dict[str, dict]:
        """
        Create default configurations for all supported channels

        Returns:
            Dict[str, dict]: Default configurations for each channel
        """
        return {
            'gmail': {
                'api_endpoint': 'https://www.googleapis.com/gmail/v1/users',
                'rate_limit_requests': 250,  # Per minute
                'rate_limit_window_seconds': 60,
                'burst_limit': 500,
                'retry_attempts': 3,
                'retry_delay_base': 5,  # seconds
                'timeout_seconds': 30,
                'enabled': True
            },
            'whatsapp': {
                'api_endpoint': 'https://api.twilio.com/2010-04-01/Accounts',
                'rate_limit_requests': 100,  # Per minute (Twilio limits)
                'rate_limit_window_seconds': 60,
                'burst_limit': 200,
                'retry_attempts': 3,
                'retry_delay_base': 5,  # seconds
                'timeout_seconds': 30,
                'enabled': True
            },
            'webform': {
                'api_endpoint': None,  # Will be set dynamically based on webhook URL
                'rate_limit_requests': 1000,  # Higher limit for webhooks
                'rate_limit_window_seconds': 60,
                'burst_limit': 2000,
                'retry_attempts': 5,
                'retry_delay_base': 10,  # seconds (longer for webhooks)
                'timeout_seconds': 60,
                'enabled': True
            }
        }

    def get_default_config(self, channel_type: str) -> Optional[dict]:
        """
        Get the default configuration for a specific channel type

        Args:
            channel_type: The channel type ('gmail', 'whatsapp', 'webform')

        Returns:
            dict: Default configuration for the channel, or None if not found
        """
        return self._default_configs.get(channel_type)

    def create_channel_config(self, channel_type: str, **overrides) -> ChannelConfig:
        """
        Create a ChannelConfig instance with default values, allowing overrides

        Args:
            channel_type: The channel type ('gmail', 'whatsapp', 'webform')
            **overrides: Configuration values to override defaults

        Returns:
            ChannelConfig: A ChannelConfig instance with the specified configuration
        """
        if channel_type not in self._default_configs:
            raise ValueError(f"Unsupported channel type: {channel_type}")

        # Start with defaults
        config_data = self._default_configs[channel_type].copy()

        # Apply overrides
        for key, value in overrides.items():
            if key in config_data:
                config_data[key] = value

        # Create and return the ChannelConfig instance
        return ChannelConfig(channel_type=channel_type, **config_data)

    def get_all_default_configs(self) -> Dict[str, dict]:
        """
        Get all default configurations

        Returns:
            Dict[str, dict]: All default configurations
        """
        return self._default_configs.copy()

    def update_default_config(self, channel_type: str, **updates):
        """
        Update the default configuration for a specific channel type

        Args:
            channel_type: The channel type to update
            **updates: Configuration values to update
        """
        if channel_type not in self._default_configs:
            raise ValueError(f"Unsupported channel type: {channel_type}")

        for key, value in updates.items():
            if key in self._default_configs[channel_type]:
                self._default_configs[channel_type][key] = value

    def get_rate_limit_config(self, channel_type: str) -> Dict[str, int]:
        """
        Get rate limiting configuration for a specific channel

        Args:
            channel_type: The channel type

        Returns:
            Dict[str, int]: Rate limiting configuration
        """
        config = self.get_default_config(channel_type)
        if not config:
            raise ValueError(f"Unsupported channel type: {channel_type}")

        return {
            'requests_per_window': config['rate_limit_requests'],
            'window_seconds': config['rate_limit_window_seconds'],
            'burst_limit': config['burst_limit']
        }

    def get_retry_config(self, channel_type: str) -> Dict[str, int]:
        """
        Get retry configuration for a specific channel

        Args:
            channel_type: The channel type

        Returns:
            Dict[str, int]: Retry configuration
        """
        config = self.get_default_config(channel_type)
        if not config:
            raise ValueError(f"Unsupported channel type: {channel_type}")

        return {
            'max_attempts': config['retry_attempts'],
            'delay_base': config['retry_delay_base']
        }

    def is_channel_enabled(self, channel_type: str) -> bool:
        """
        Check if a specific channel is enabled

        Args:
            channel_type: The channel type

        Returns:
            bool: True if enabled, False otherwise
        """
        config = self.get_default_config(channel_type)
        if not config:
            raise ValueError(f"Unsupported channel type: {channel_type}")

        return config['enabled']

# Global instance
channel_config_manager = ChannelConfigurationManager()

def get_channel_config_manager():
    """
    Get the global channel configuration manager instance

    Returns:
        ChannelConfigurationManager: The global instance
    """
    return channel_config_manager