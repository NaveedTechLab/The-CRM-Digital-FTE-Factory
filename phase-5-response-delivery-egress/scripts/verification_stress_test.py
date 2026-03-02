#!/usr/bin/env python3
"""
Verification stress test script that triggers 10 messages across 3 channels and verifies all 10 are marked 'delivered' in the database
"""

import asyncio
import argparse
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path
import time

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.outbound_message import OutboundMessage, Base
from app.config.settings import settings
from app.utils.logger import logger


class VerificationStressTest:
    """
    Verification stress test to trigger messages across channels and verify delivery status
    """

    def __init__(self, database_url: str = None):
        """
        Initialize the verification stress test

        Args:
            database_url: Database URL for verifying messages (defaults to settings.database_url)
        """
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)

    def create_test_messages(self, num_messages: int = 10):
        """
        Create test messages across 3 channels

        Args:
            num_messages: Number of messages to create (default: 10)
        """
        session = self.Session()
        try:
            # Define test messages for each channel
            test_channels = ['gmail', 'whatsapp', 'webform']

            for i in range(num_messages):
                # Rotate between channels
                channel = test_channels[i % len(test_channels)]

                # Create a test message
                test_message = OutboundMessage(
                    message_id=f"test_msg_{i}_{int(time.time())}",
                    conversation_id=f"test_conv_{int(time.time())}",
                    content=f"This is test message {i+1} for {channel} channel.",
                    channel_destination=channel,
                    recipient_identifier=self._get_test_recipient(channel),
                    sender_identifier='test_verifier',
                    priority='normal'
                )

                session.add(test_message)
                logger.info(f"Created test message {i+1} for {channel} channel",
                           message_id=test_message.message_id, channel=channel)

            session.commit()
            logger.info(f"Created {num_messages} test messages across channels")

            return [f"test_msg_{i}_{int(time.time())}" for i in range(num_messages)]
        except Exception as e:
            logger.error(f"Error creating test messages: {str(e)}", error=str(e))
            session.rollback()
            raise
        finally:
            session.close()

    def _get_test_recipient(self, channel: str) -> str:
        """
        Get a test recipient based on the channel

        Args:
            channel: Channel type

        Returns:
            str: Test recipient identifier
        """
        if channel == 'gmail':
            return 'test@example.com'
        elif channel == 'whatsapp':
            return 'whatsapp:+1234567890'
        elif channel == 'webform':
            return 'https://test-webhook.example.com'
        else:
            return 'unknown'

    def verify_delivery_status(self, message_ids: list, timeout_seconds: int = 30):
        """
        Verify that all messages have 'delivered' status in the database

        Args:
            message_ids: List of message IDs to verify
            timeout_seconds: Timeout for verification (default: 30 seconds)

        Returns:
            tuple: (success: bool, results: dict)
        """
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            session = self.Session()
            try:
                # Query for all test messages
                messages = session.query(OutboundMessage).filter(
                    OutboundMessage.message_id.in_(message_ids)
                ).all()

                # Check delivery status
                delivered_count = 0
                status_breakdown = {}

                for msg in messages:
                    status = msg.delivery_status
                    if status not in status_breakdown:
                        status_breakdown[status] = 0
                    status_breakdown[status] += 1

                    if status == 'delivered':
                        delivered_count += 1

                logger.info(f"Delivery status check: {delivered_count}/{len(message_ids)} delivered",
                           delivered_count=delivered_count, total=len(message_ids), status_breakdown=status_breakdown)

                # If all are delivered, return success
                if delivered_count == len(message_ids):
                    logger.info(f"All {len(message_ids)} messages delivered successfully")
                    return True, {
                        'success': True,
                        'delivered_count': delivered_count,
                        'total_messages': len(message_ids),
                        'status_breakdown': status_breakdown
                    }

                # Otherwise, wait a bit before checking again
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error checking delivery status: {str(e)}", error=str(e))
                raise
            finally:
                session.close()

        # If we've reached the timeout, return failure
        session = self.Session()
        try:
            # Get final status for all messages
            messages = session.query(OutboundMessage).filter(
                OutboundMessage.message_id.in_(message_ids)
            ).all()

            status_breakdown = {}
            for msg in messages:
                status = msg.delivery_status
                if status not in status_breakdown:
                    status_breakdown[status] = 0
                status_breakdown[status] += 1

            logger.warning(f"Timeout reached. Only {status_breakdown.get('delivered', 0)}/{len(message_ids)} messages delivered",
                          delivered_count=status_breakdown.get('delivered', 0), total=len(message_ids),
                          status_breakdown=status_breakdown)

            return False, {
                'success': False,
                'delivered_count': status_breakdown.get('delivered', 0),
                'total_messages': len(message_ids),
                'status_breakdown': status_breakdown
            }
        finally:
            session.close()

    def run_verification_test(self, num_messages: int = 10, timeout_seconds: int = 60):
        """
        Run the verification stress test

        Args:
            num_messages: Number of messages to send (default: 10)
            timeout_seconds: Timeout for verification (default: 60 seconds)

        Returns:
            dict: Test results
        """
        logger.info(f"Starting verification stress test with {num_messages} messages",
                   num_messages=num_messages, timeout_seconds=timeout_seconds)

        try:
            # Create test messages
            message_ids = self.create_test_messages(num_messages)

            # Verify delivery status
            success, results = self.verify_delivery_status(message_ids, timeout_seconds)

            # Log final results
            if success:
                logger.info("VERIFICATION TEST PASSED: All messages delivered successfully")
            else:
                logger.error("VERIFICATION TEST FAILED: Not all messages were delivered")

            results['test_config'] = {
                'num_messages': num_messages,
                'timeout_seconds': timeout_seconds,
                'message_ids': message_ids
            }

            return results
        except Exception as e:
            logger.error(f"Error running verification test: {str(e)}", error=str(e))
            raise

    def print_results(self, results: dict):
        """
        Print the test results in a formatted way

        Args:
            results: Results dictionary from run_verification_test
        """
        print("\n" + "=" * 80)
        print("VERIFICATION STRESS TEST RESULTS")
        print("=" * 80)

        success = results['success']
        print(f"Test Status: {'PASSED' if success else 'FAILED'}")
        print(f"Delivered: {results['delivered_count']}/{results['total_messages']}")
        print()

        print("Status Breakdown:")
        for status, count in results['status_breakdown'].items():
            print(f"  {status.upper()}: {count}")
        print()

        print("Test Configuration:")
        config = results['test_config']
        print(f"  Messages Sent: {config['num_messages']}")
        print(f"  Timeout: {config['timeout_seconds']} seconds")
        print("=" * 80)


def main():
    """
    Main entry point for the verification stress test
    """
    parser = argparse.ArgumentParser(description="Verification Stress Test for Message Delivery")
    parser.add_argument(
        "--messages",
        type=int,
        default=10,
        help="Number of messages to send (default: 10)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout for verification in seconds (default: 60)"
    )

    args = parser.parse_args()

    # Initialize the test
    test = VerificationStressTest()

    # Run the test
    results = test.run_verification_test(args.messages, args.timeout)

    # Print results
    test.print_results(results)

    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    main()