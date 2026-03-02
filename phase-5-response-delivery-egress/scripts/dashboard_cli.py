#!/usr/bin/env python3
"""
Unified Dashboard CLI script to query the database and show the count of Inbound vs. Outbound messages across all channels
"""

import asyncio
import argparse
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.models.outbound_message import OutboundMessage, Base
from app.config.settings import settings
from app.utils.logger import logger


class DashboardCLI:
    """
    Unified Dashboard CLI utility to provide real-time stats (Inbound vs. Outbound) during test runs
    """

    def __init__(self, database_url: str = None):
        """
        Initialize the dashboard CLI

        Args:
            database_url: Database URL for querying messages (defaults to settings.database_url)
        """
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url)
        self.Session = sessionmaker(bind=self.engine)

    def get_message_counts(self, days: int = 7):
        """
        Get message counts for inbound and outbound messages across all channels

        Args:
            days: Number of days to look back (default: 7)

        Returns:
            Dict with message counts by channel and direction
        """
        session = self.Session()
        try:
            # Calculate the date threshold
            threshold_date = datetime.utcnow() - timedelta(days=days)

            # Query for outbound messages by channel
            outbound_counts = session.query(
                OutboundMessage.channel_destination,
                func.count(OutboundMessage.id).label('count')
            ).filter(
                OutboundMessage.created_at >= threshold_date
            ).group_by(
                OutboundMessage.channel_destination
            ).all()

            # Convert to dict
            outbound_dict = {row[0]: row[1] for row in outbound_counts}

            # Calculate total outbound
            total_outbound = sum(outbound_dict.values())

            # For inbound messages, we'd normally query the messages table from Phase 2
            # Since we don't have access to that here, we'll just show outbound stats
            # In a real implementation, you'd join with the Phase 2 messages table
            inbound_dict = {}  # Placeholder - would come from Phase 2 DB
            total_inbound = 0  # Placeholder - would come from Phase 2 DB

            return {
                "period_days": days,
                "start_date": threshold_date.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "inbound": {
                    "total": total_inbound,
                    "by_channel": inbound_dict
                },
                "outbound": {
                    "total": total_outbound,
                    "by_channel": outbound_dict
                },
                "totals": {
                    "inbound": total_inbound,
                    "outbound": total_outbound,
                    "all": total_inbound + total_outbound
                }
            }
        finally:
            session.close()

    def print_dashboard(self, stats):
        """
        Print the dashboard in a formatted way

        Args:
            stats: Statistics dictionary from get_message_counts
        """
        print("=" * 80)
        print("UNIFIED MESSAGE DASHBOARD")
        print("=" * 80)
        print(f"Reporting Period: {stats['start_date']} to {stats['end_date']} ({stats['period_days']} days)")
        print()

        print("INBOUND MESSAGES:")
        print(f"  Total: {stats['inbound']['total']}")
        print("  By Channel: N/A (would come from Phase 2 DB)")
        print()

        print("OUTBOUND MESSAGES:")
        print(f"  Total: {stats['outbound']['total']}")
        for channel, count in stats['outbound']['by_channel'].items():
            print(f"  {channel.upper()}: {count}")
        print()

        print("SUMMARY:")
        print(f"  Total Messages: {stats['totals']['all']}")
        print(f"  Inbound: {stats['totals']['inbound']}")
        print(f"  Outbound: {stats['totals']['outbound']}")
        print("=" * 80)

    def run_dashboard(self, days: int = 7):
        """
        Run the dashboard and display results

        Args:
            days: Number of days to look back
        """
        logger.info(f"Generating dashboard for last {days} days")

        try:
            stats = self.get_message_counts(days=days)
            self.print_dashboard(stats)

            logger.info("Dashboard generated successfully")
        except Exception as e:
            logger.error(f"Error generating dashboard: {str(e)}", error=str(e))
            raise


def main():
    """
    Main entry point for the dashboard CLI
    """
    parser = argparse.ArgumentParser(description="Unified Dashboard for Message Stats")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back (default: 7)"
    )

    args = parser.parse_args()

    dashboard = DashboardCLI()
    dashboard.run_dashboard(days=args.days)


if __name__ == "__main__":
    main()