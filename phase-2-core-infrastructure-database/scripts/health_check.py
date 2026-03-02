#!/usr/bin/env python3
"""
Health check script to verify database and Kafka connectivity.
Provides clear 'PASS/FAIL' output for both DB and Kafka connectivity.
"""
import sys
import subprocess
import time
from app.database_manager import DatabaseManager
from app.stream_manager import StreamManager
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_postgres_connectivity():
    """
    Check if PostgreSQL is accessible and tables exist.

    Returns:
        tuple: (status: bool, message: str)
    """
    logger.info("Checking PostgreSQL connectivity...")

    try:
        # Initialize database manager
        db_manager = DatabaseManager()

        # Perform health check
        is_healthy = db_manager.health_check()

        if is_healthy:
            # Verify that required tables exist
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="internal_crm",
                user="postgres",
                password="postgres"
            )

            cursor = conn.cursor()

            # Check if key tables exist
            required_tables = ['customers', 'tickets', 'messages', 'vector_embeddings']
            existing_tables = []

            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)

            tables = [row[0] for row in cursor.fetchall()]

            for table in required_tables:
                if table in tables:
                    existing_tables.append(table)

            cursor.close()
            conn.close()

            if len(existing_tables) == len(required_tables):
                logger.info("✓ PostgreSQL connectivity: PASS")
                logger.info(f"✓ Required tables exist: {existing_tables}")
                return True, "PostgreSQL connection OK and all required tables exist"
            else:
                missing_tables = set(required_tables) - set(existing_tables)
                logger.error(f"✗ PostgreSQL connectivity: FAIL - Missing tables: {missing_tables}")
                return False, f"PostgreSQL connection OK but missing tables: {missing_tables}"
        else:
            logger.error("✗ PostgreSQL connectivity: FAIL")
            return False, "PostgreSQL connection failed"

    except Exception as e:
        logger.error(f"✗ PostgreSQL connectivity: FAIL - {str(e)}")
        return False, f"PostgreSQL connection failed: {str(e)}"


async def check_kafka_connectivity():
    """
    Check if Kafka broker is accessible and topics are available.

    Returns:
        tuple: (status: bool, message: str)
    """
    logger.info("Checking Kafka connectivity...")

    try:
        # Initialize stream manager
        stream_manager = StreamManager()

        # Perform health check
        is_healthy = await stream_manager.health_check()

        if is_healthy:
            logger.info("✓ Kafka connectivity: PASS")
            return True, "Kafka broker connection OK"
        else:
            logger.error("✗ Kafka connectivity: FAIL")
            return False, "Kafka broker connection failed"

    except Exception as e:
        logger.error(f"✗ Kafka connectivity: FAIL - {str(e)}")
        return False, f"Kafka connection failed: {str(e)}"


def run_health_checks():
    """
    Run all health checks and return overall status.

    Returns:
        bool: True if all checks pass, False otherwise
    """
    print("="*60)
    print("CUSTOMER SUCCESS DIGITAL FTE - INFRASTRUCTURE HEALTH CHECK")
    print("="*60)

    # Check PostgreSQL
    db_status, db_message = check_postgres_connectivity()
    print(f"PostgreSQL: {'PASS' if db_status else 'FAIL'} - {db_message}")

    # Check Kafka
    kafka_status, kafka_message = asyncio.run(check_kafka_connectivity())
    print(f"Kafka: {'PASS' if kafka_status else 'FAIL'} - {kafka_message}")

    print("-"*60)

    # Overall status
    all_pass = db_status and kafka_status

    if all_pass:
        print("OVERALL STATUS: PASS - All infrastructure components are READY")
        print("✓ Database connectivity established")
        print("✓ Kafka broker accessible")
        print("✓ All required tables exist")
        print("✓ Topics accessible")
    else:
        print("OVERALL STATUS: FAIL - Some infrastructure components are NOT READY")
        if not db_status:
            print("✗ Database connectivity issues")
        if not kafka_status:
            print("✗ Kafka connectivity issues")

    print("="*60)

    return all_pass


def check_docker_containers():
    """
    Check if required Docker containers are running.

    Returns:
        tuple: (status: bool, message: str)
    """
    logger.info("Checking Docker containers...")

    try:
        # Check if docker is available
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return False, "Docker not available or not running"

        # Check for required containers
        running_containers = result.stdout

        postgres_running = 'crm-postgres' in running_containers
        kafka_running = 'crm-kafka' in running_containers

        if postgres_running and kafka_running:
            logger.info("✓ Docker containers: PASS")
            return True, "Both PostgreSQL and Kafka containers are running"
        else:
            missing_containers = []
            if not postgres_running:
                missing_containers.append("PostgreSQL")
            if not kafka_running:
                missing_containers.append("Kafka")

            logger.error(f"✗ Docker containers: FAIL - Missing containers: {missing_containers}")
            return False, f"Docker containers not running: {missing_containers}"

    except subprocess.TimeoutExpired:
        logger.error("✗ Docker containers: FAIL - Docker command timed out")
        return False, "Docker command timed out"
    except FileNotFoundError:
        logger.error("✗ Docker containers: FAIL - Docker not found")
        return False, "Docker not installed or not in PATH"
    except Exception as e:
        logger.error(f"✗ Docker containers: FAIL - {str(e)}")
        return False, f"Docker check failed: {str(e)}"


def main():
    """
    Main function to run health checks.
    """
    print("Running infrastructure health check...\n")

    # Check if Docker containers are running first
    docker_status, docker_message = check_docker_containers()
    print(f"Docker: {'PASS' if docker_status else 'FAIL'} - {docker_message}")

    if not docker_status:
        print("\n✗ Docker containers are not running. Please start them using:")
        print("  docker-compose up -d")
        sys.exit(1)

    # Wait a moment for services to be ready
    print("\nWaiting for services to be ready...")
    time.sleep(5)

    # Run the main health checks
    overall_status = run_health_checks()

    # Exit with appropriate code
    sys.exit(0 if overall_status else 1)


if __name__ == "__main__":
    main()