#!/usr/bin/env python3
"""
Docker Build Tracker

This module provides comprehensive Docker build tracking with:
- Local SQLite database storage
- Timezone-aware timestamps
- Image size tracking
- Build history and statistics
- Cross-Docker context access
"""

import sqlite3
import json
import subprocess
from zoneinfo import ZoneInfo
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DockerBuildTracker:
    """
    Docker build tracking with SQLite database and timezone support.

    Args:
        db_path (Optional[str]): Path to SQLite database file. If None, uses default location.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Use default location in project data directory
            project_root = Path(__file__).parent.parent.parent
            data_dir = project_root / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = data_dir / "docker_build_history.sqlite"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Create build history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS docker_builds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_name TEXT NOT NULL,
                    build_duration REAL NOT NULL,
                    image_size_mb REAL NOT NULL,
                    build_timestamp TEXT NOT NULL,
                    timezone TEXT NOT NULL,
                    dockerfile_path TEXT,
                    build_args TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create build statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS build_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_name TEXT NOT NULL,
                    avg_duration REAL NOT NULL,
                    avg_size_mb REAL NOT NULL,
            total_builds INTEGER NOT NULL,
                    last_build_timestamp TEXT NOT NULL,
                    timezone TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(image_name)
                )
            """)

            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_image_name
                ON docker_builds(image_name)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_build_timestamp
                ON docker_builds(build_timestamp)
            """)

            conn.commit()
            conn.close()
            logger.info(f"Database initialized at {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def get_current_timestamp(self, timezone_name: str = "Asia/Singapore") -> str:
        """
        Get current timestamp in specified timezone.

        Args:
            timezone_name (str): Timezone name (default: Asia/Singapore)

        Returns:
            str: ISO format timestamp string
        """
        try:
            tz = ZoneInfo(timezone_name)
            current_time = datetime.now(tz)
            return current_time.isoformat()
        except Exception as e:
            logger.warning(f"Failed to get timezone-aware timestamp: {e}")
            # Fallback to UTC
            return datetime.now(timezone.utc).isoformat()

    def get_image_size(self, image_name: str) -> float:
        """
        Get Docker image size in MB.

        Args:
            image_name (str): Name of the Docker image

        Returns:
            float: Image size in MB
        """
        try:
            result = subprocess.run(
                ["docker", "images", "--format", "{{.Size}}", image_name],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0 and result.stdout.strip():
                size_str = result.stdout.strip()
                # Parse size (e.g., "1.23GB", "456MB", "789KB")
                if size_str.endswith("GB"):
                    return float(size_str[:-2]) * 1024
                elif size_str.endswith("MB"):
                    return float(size_str[:-2])
                elif size_str.endswith("KB"):
                    return float(size_str[:-2]) / 1024
                else:
                    return float(size_str) / (1024 * 1024)  # Assume bytes
            else:
                logger.warning(f"Could not get size for image {image_name}")
                return 0.0

        except Exception as e:
            logger.error(f"Failed to get image size for {image_name}: {e}")
            return 0.0

    def record_build(
        self,
        image_name: str,
        build_duration: float,
        dockerfile_path: Optional[str] = None,
        build_args: Optional[Dict[str, str]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        timezone_name: str = "Asia/Singapore",
    ):
        """
        Record a Docker build in the database.

        Args:
            image_name (str): Name of the Docker image
            build_duration (float): Build duration in seconds
            dockerfile_path (Optional[str]): Path to Dockerfile used
            build_args (Optional[Dict[str, str]]): Build arguments used
            success (bool): Whether the build was successful
            error_message (Optional[str]): Error message if build failed
            timezone_name (str): Timezone for timestamp
        """
        try:
            # Get image size if build was successful
            image_size_mb = self.get_image_size(image_name) if success else 0.0

            # Get timezone-aware timestamp
            build_timestamp = self.get_current_timestamp(timezone_name)

            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO docker_builds
                (image_name, build_duration, image_size_mb, build_timestamp, timezone,
                 dockerfile_path, build_args, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    image_name,
                    build_duration,
                    image_size_mb,
                    build_timestamp,
                    timezone_name,
                    dockerfile_path,
                    json.dumps(build_args) if build_args else None,
                    success,
                    error_message,
                ),
            )

            # Update statistics
            self._update_statistics(
                image_name,
                build_duration,
                image_size_mb,
                build_timestamp,
                timezone_name,
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Recorded build for {image_name}: {build_duration:.2f}s, {image_size_mb:.2f}MB"
            )

        except Exception as e:
            logger.error(f"Failed to record build for {image_name}: {e}")

    def _update_statistics(
        self,
        image_name: str,
        duration: float,
        size_mb: float,
        timestamp: str,
        timezone_name: str,
    ):
        """
        Update build statistics for an image.

        Args:
            image_name (str): Name of the Docker image
            duration (float): Build duration in seconds
            size_mb (float): Image size in MB
            timestamp (str): Timestamp of the build
            timezone_name (str): Timezone for timestamp
        """
        try:
            # Use a separate connection for statistics to avoid locking issues
            stats_conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            stats_cursor = stats_conn.cursor()

            # Get current statistics
            stats_cursor.execute(
                """
                SELECT avg_duration, avg_size_mb, total_builds
                FROM build_statistics
                WHERE image_name = ?
            """,
                (image_name,),
            )

            result = stats_cursor.fetchone()

            if result:
                # Update existing statistics
                current_avg_duration, current_avg_size, current_total = result
                new_total = current_total + 1
                new_avg_duration = (
                    current_avg_duration * current_total + duration
                ) / new_total
                new_avg_size = (current_avg_size * current_total + size_mb) / new_total

                stats_cursor.execute(
                    """
                    UPDATE build_statistics
                    SET avg_duration = ?, avg_size_mb = ?, total_builds = ?,
                        last_build_timestamp = ?, timezone = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE image_name = ?
                """,
                    (
                        new_avg_duration,
                        new_avg_size,
                        new_total,
                        timestamp,
                        timezone_name,
                        image_name,
                    ),
                )
            else:
                # Create new statistics
                stats_cursor.execute(
                    """
                    INSERT INTO build_statistics
                    (image_name, avg_duration, avg_size_mb, total_builds, last_build_timestamp, timezone)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (image_name, duration, size_mb, 1, timestamp, timezone_name),
                )

            stats_conn.commit()
            stats_conn.close()

        except Exception as e:
            logger.error(f"Failed to update statistics for {image_name}: {e}")

    def get_build_history(
        self, image_name: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get build history from database.

        Args:
            image_name (Optional[str]): Filter by image name (optional)
            limit (int): Maximum number of records to return

        Returns:
            List[Dict[str, Any]]: List of build records
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            if image_name:
                cursor.execute(
                    """
                    SELECT image_name, build_duration, image_size_mb, build_timestamp, timezone,
                           dockerfile_path, build_args, success, error_message
                    FROM docker_builds
                    WHERE image_name = ?
                    ORDER BY build_timestamp DESC
                    LIMIT ?
                """,
                    (image_name, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT image_name, build_duration, image_size_mb, build_timestamp, timezone,
                           dockerfile_path, build_args, success, error_message
                    FROM docker_builds
                    ORDER BY build_timestamp DESC
                    LIMIT ?
                """,
                    (limit,),
                )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "image_name": row[0],
                        "build_duration": row[1],
                        "image_size_mb": row[2],
                        "build_timestamp": row[3],
                        "timezone": row[4],
                        "dockerfile_path": row[5],
                        "build_args": json.loads(row[6]) if row[6] else None,
                        "success": row[7],
                        "error_message": row[8],
                    }
                )

            conn.close()
            return results

        except Exception as e:
            logger.error(f"Failed to get build history: {e}")
            return []

    def get_build_statistics(self) -> Dict[str, Any]:
        """
        Get build statistics for all images.

        Returns:
            Dict[str, Any]: Dictionary with build statistics
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                SELECT image_name, avg_duration, avg_size_mb, total_builds,
                       last_build_timestamp, timezone
                FROM build_statistics
                ORDER BY last_build_timestamp DESC
            """)

            statistics = {}
            for row in cursor.fetchall():
                statistics[row[0]] = {
                    "avg_duration": row[1],
                    "avg_size_mb": row[2],
                    "total_builds": row[3],
                    "last_build_timestamp": row[4],
                    "timezone": row[5],
                }

            conn.close()
            return statistics

        except Exception as e:
            logger.error(f"Failed to get build statistics: {e}")
            return {}

    def export_to_json(self, output_path: Optional[str] = None) -> str:
        """
        Export build data to JSON format (for backward compatibility).

        Args:
            output_path (Optional[str]): Output file path (optional)

        Returns:
            str: Path to exported JSON file
        """
        try:
            if output_path is None:
                data_dir = Path(__file__).parent.parent / "data"
                data_dir.mkdir(exist_ok=True)
                output_path = data_dir / "docker_build_times.json"

            output_path = Path(output_path)

            # Get build history and statistics
            history = self.get_build_history(limit=1000)
            statistics = self.get_build_statistics()

            # Format for backward compatibility
            export_data = {
                "history": [
                    {
                        "timestamp": record["build_timestamp"],
                        "image": record["image_name"],
                        "duration": record["build_duration"],
                        "size_mb": record["image_size_mb"],
                        "timezone": record["timezone"],
                    }
                    for record in history
                ],
                "averages": {
                    image: {
                        "duration": stats["avg_duration"],
                        "size_mb": stats["avg_size_mb"],
                        "total_builds": stats["total_builds"],
                    }
                    for image, stats in statistics.items()
                },
                "last_build_time": self.get_current_timestamp(),
                "database_path": str(self.db_path),
            }

            with open(output_path, "w") as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported build data to {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to export to JSON: {e}")
            return ""

    def copy_to_docker_context(self, docker_context_path: str):
        """
        Copy database to Docker context for access in containers.

        Args:
            docker_context_path (str): Path to Docker context directory
        """
        try:
            docker_context = Path(docker_context_path)
            target_path = docker_context / "docker_build_history.db"

            # Copy database file
            import shutil

            shutil.copy2(self.db_path, target_path)

            logger.info(f"Copied database to Docker context: {target_path}")

        except Exception as e:
            logger.error(f"Failed to copy database to Docker context: {e}")


def track_docker_build(
    image_name: str,
    build_duration: float,
    dockerfile_path: Optional[str] = None,
    build_args: Optional[Dict[str, str]] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    timezone_name: str = "Asia/Singapore",
):
    """
    Convenience function to track a Docker build.

    Args:
        image_name (str): Name of the Docker image
        build_duration (float): Build duration in seconds
        dockerfile_path (Optional[str]): Path to Dockerfile used
        build_args (Optional[Dict[str, str]]): Build arguments used
        success (bool): Whether the build was successful
        error_message (Optional[str]): Error message if build failed
        timezone_name (str): Timezone for timestamp
    """
    tracker = DockerBuildTracker()
    tracker.record_build(
        image_name=image_name,
        build_duration=build_duration,
        dockerfile_path=dockerfile_path,
        build_args=build_args,
        success=success,
        error_message=error_message,
        timezone_name=timezone_name,
    )


if __name__ == "__main__":
    # Example usage
    tracker = DockerBuildTracker()

    # Record a sample build
    tracker.record_build(
        image_name="test-image",
        build_duration=120.5,
        dockerfile_path="docker/Dockerfile.test",
        build_args={"BUILD_ENV": "production"},
    )

    # Export to JSON
    tracker.export_to_json()

    # Print statistics
    stats = tracker.get_build_statistics()
    print("Build Statistics:")
    for image, data in stats.items():
        print(
            f"  {image}: {data['avg_duration']:.2f}s avg, {data['avg_size_mb']:.2f}MB avg, {data['total_builds']} builds"
        )
