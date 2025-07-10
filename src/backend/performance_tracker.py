#!/usr/bin/env python3
"""
Performance Tracking module for the NYP FYP CNC Chatbot backend.

This module provides comprehensive performance tracking including:

- Docker build time tracking
- API call time tracking
- App startup time tracking
- Performance metrics collection
- Input sanitization and security
- Per-user performance analytics

The module integrates with the consolidated SQLite database for persistent
performance data storage.
"""

import time
import uuid
import logging
import threading
from typing import Dict, Any, Optional
from contextlib import contextmanager
from .consolidated_database import get_performance_database, InputSanitizer
import json

# Set up logging
logger = logging.getLogger(__name__)

# Thread-local storage for tracking context
_thread_local = threading.local()


class PerformanceTracker:
    """
    Tracks performance metrics for the application.

    Initializes the PerformanceTracker instance.
    """

    def __init__(self):
        self.db = get_performance_database()
        self._active_timers = {}

    def start_docker_build(self, username: str, build_id: Optional[str] = None) -> str:
        """Start tracking a Docker build.

        :param username: Username performing the build
        :type username: str
        :param build_id: Optional build ID, will generate if not provided
        :type build_id: Optional[str]
        :return: Build ID for tracking
        :rtype: str
        """
        try:
            # Sanitize inputs
            username = InputSanitizer.sanitize_username(username)
            build_id = build_id or str(uuid.uuid4())

            start_time = time.time()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(start_time))

            # Store build start in thread-local storage
            if not hasattr(_thread_local, "docker_builds"):
                _thread_local.docker_builds = {}

            _thread_local.docker_builds[build_id] = {
                "username": username,
                "start_time": start_time,
                "timestamp": timestamp,
            }

            # Record build start in database
            query = """
                INSERT INTO docker_builds
                (username, build_id, build_start_time, build_status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """
            self.db.execute_update(
                query, (username, build_id, timestamp, "started", timestamp)
            )

            logger.info(
                f"Started Docker build tracking for user {username}, build_id: {build_id}"
            )
            return build_id

        except Exception as e:
            logger.error(f"Failed to start Docker build tracking: {e}")
            return str(uuid.uuid4())  # Return fallback ID

    def end_docker_build(
        self,
        build_id: str,
        status: str = "completed",
        image_size: Optional[float] = None,
        build_logs: Optional[str] = None,
    ) -> bool:
        """End tracking a Docker build.

        :param build_id: Build ID to end tracking
        :type build_id: str
        :param status: Build status (completed, failed, cancelled)
        :type status: str
        :param image_size: Final image size in MB
        :type image_size: Optional[float]
        :param build_logs: Build logs (truncated if too long)
        :type build_logs: Optional[str]
        :return: True if successful, False otherwise
        :rtype: bool
        """
        try:
            # Get build info from thread-local storage
            if (
                not hasattr(_thread_local, "docker_builds")
                or build_id not in _thread_local.docker_builds
            ):
                logger.warning(f"No active Docker build found for build_id: {build_id}")
                return False

            build_info = _thread_local.docker_builds[build_id]
            end_time = time.time()
            duration = end_time - build_info["start_time"]
            end_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(end_time))

            # Sanitize inputs
            status = InputSanitizer.sanitize_string(status, max_length=20)
            if build_logs:
                build_logs = InputSanitizer.sanitize_string(
                    build_logs, max_length=10000
                )

            # Update database
            query = """
                UPDATE docker_builds
                SET build_end_time = ?, build_duration = ?, build_status = ?,
                    image_size = ?, build_logs = ?
                WHERE build_id = ?
            """
            success = self.db.execute_update(
                query,
                (end_timestamp, duration, status, image_size, build_logs, build_id),
            )

            # Clean up thread-local storage
            del _thread_local.docker_builds[build_id]

            if success:
                logger.info(
                    f"Completed Docker build tracking for build_id: {build_id}, duration: {duration:.2f}s"
                )
            return success

        except Exception as e:
            logger.error(f"Failed to end Docker build tracking: {e}")
            return False

    def track_api_call(
        self,
        username: str,
        endpoint: str,
        method: str,
        start_time: Optional[float] = None,
    ) -> str:
        """Start tracking an API call.

        :param username: Username making the API call
        :type username: str
        :param endpoint: API endpoint being called
        :type endpoint: str
        :param method: HTTP method (GET, POST, etc.)
        :type method: str
        :param start_time: Optional start time, uses current time if not provided
        :type start_time: Optional[float]
        :return: Call ID for tracking
        :rtype: str
        """
        try:
            # Sanitize inputs
            username = InputSanitizer.sanitize_username(username)
            endpoint = InputSanitizer.sanitize_string(endpoint, max_length=200)
            method = InputSanitizer.sanitize_string(method.upper(), max_length=10)

            start_time = start_time or time.time()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(start_time))
            call_id = str(uuid.uuid4())

            # Store call info in thread-local storage
            if not hasattr(_thread_local, "api_calls"):
                _thread_local.api_calls = {}

            _thread_local.api_calls[call_id] = {
                "username": username,
                "endpoint": endpoint,
                "method": method,
                "start_time": start_time,
                "timestamp": timestamp,
            }

            # Record call start in database
            query = """
                INSERT INTO api_calls
                (username, endpoint, method, start_time, created_at)
                VALUES (?, ?, ?, ?, ?)
            """
            self.db.execute_update(
                query, (username, endpoint, method, timestamp, timestamp)
            )

            logger.debug(
                f"Started API call tracking for user {username}, endpoint: {endpoint}"
            )
            return call_id

        except Exception as e:
            logger.error(f"Failed to start API call tracking: {e}")
            return str(uuid.uuid4())  # Return fallback ID

    def end_api_call(
        self,
        call_id: str,
        status_code: int = 200,
        response_size: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """End tracking an API call.

        :param call_id: Call ID to end tracking
        :type call_id: str
        :param status_code: HTTP status code
        :type status_code: int
        :param response_size: Response size in bytes
        :type response_size: Optional[int]
        :param error_message: Error message if call failed
        :type error_message: Optional[str]
        :return: True if successful, False otherwise
        :rtype: bool
        """
        try:
            # Get call info from thread-local storage
            if (
                not hasattr(_thread_local, "api_calls")
                or call_id not in _thread_local.api_calls
            ):
                logger.warning(f"No active API call found for call_id: {call_id}")
                return False

            call_info = _thread_local.api_calls[call_id]
            end_time = time.time()
            duration = end_time - call_info["start_time"]
            end_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(end_time))

            # Sanitize error message
            if error_message:
                error_message = InputSanitizer.sanitize_string(
                    error_message, max_length=1000
                )

            # Update database
            query = """
                UPDATE api_calls
                SET end_time = ?, duration = ?, status_code = ?,
                    response_size = ?, error_message = ?
                WHERE username = ? AND endpoint = ? AND method = ? AND start_time = ?
            """
            success = self.db.execute_update(
                query,
                (
                    end_timestamp,
                    duration,
                    status_code,
                    response_size,
                    error_message,
                    call_info["username"],
                    call_info["endpoint"],
                    call_info["method"],
                    call_info["timestamp"],
                ),
            )

            # Clean up thread-local storage
            del _thread_local.api_calls[call_id]

            if success:
                logger.debug(
                    f"Completed API call tracking for call_id: {call_id}, duration: {duration:.3f}s"
                )
            return success

        except Exception as e:
            logger.error(f"Failed to end API call tracking: {e}")
            return False

    def start_app_startup(self, username: str, startup_id: Optional[str] = None) -> str:
        """Start tracking app startup.

        :param username: Username starting the app
        :type username: str
        :param startup_id: Optional startup ID, will generate if not provided
        :type startup_id: Optional[str]
        :return: Startup ID for tracking
        :rtype: str
        """
        try:
            # Sanitize inputs
            username = InputSanitizer.sanitize_username(username)
            startup_id = startup_id or str(uuid.uuid4())

            start_time = time.time()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(start_time))

            # Store startup info in thread-local storage
            if not hasattr(_thread_local, "app_startups"):
                _thread_local.app_startups = {}

            _thread_local.app_startups[startup_id] = {
                "username": username,
                "start_time": start_time,
                "timestamp": timestamp,
                "component_times": {},
            }

            # Record startup start in database
            query = """
                INSERT INTO app_startups
                (username, startup_id, startup_start_time, startup_status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """
            self.db.execute_update(
                query, (username, startup_id, timestamp, "started", timestamp)
            )

            logger.info(
                f"Started app startup tracking for user {username}, startup_id: {startup_id}"
            )
            return startup_id

        except Exception as e:
            logger.error(f"Failed to start app startup tracking: {e}")
            return str(uuid.uuid4())  # Return fallback ID

    def track_component_startup(
        self, startup_id: str, component_name: str, start_time: Optional[float] = None
    ) -> str:
        """Track individual component startup time.

        :param startup_id: Startup ID to track component for
        :type startup_id: str
        :param component_name: Name of the component
        :type component_name: str
        :param start_time: Optional start time, uses current time if not provided
        :type start_time: Optional[float]
        :return: Component tracking ID
        :rtype: str
        """
        try:
            if (
                not hasattr(_thread_local, "app_startups")
                or startup_id not in _thread_local.app_startups
            ):
                logger.warning(
                    f"No active app startup found for startup_id: {startup_id}"
                )
                return str(uuid.uuid4())

            component_name = InputSanitizer.sanitize_string(
                component_name, max_length=100
            )
            start_time = start_time or time.time()
            component_id = str(uuid.uuid4())

            _thread_local.app_startups[startup_id]["component_times"][component_id] = {
                "name": component_name,
                "start_time": start_time,
            }

            return component_id

        except Exception as e:
            logger.error(f"Failed to track component startup: {e}")
            return str(uuid.uuid4())

    def end_component_startup(self, startup_id: str, component_id: str) -> bool:
        """End tracking a component startup.

        :param startup_id: Startup ID
        :type startup_id: str
        :param component_id: Component ID to end tracking
        :type component_id: str
        :return: True if successful, False otherwise
        :rtype: bool
        """
        try:
            if (
                not hasattr(_thread_local, "app_startups")
                or startup_id not in _thread_local.app_startups
            ):
                return False

            if (
                component_id
                not in _thread_local.app_startups[startup_id]["component_times"]
            ):
                return False

            component_info = _thread_local.app_startups[startup_id]["component_times"][
                component_id
            ]
            end_time = time.time()
            duration = end_time - component_info["start_time"]

            # Store component duration
            component_info["duration"] = duration
            component_info["end_time"] = end_time

            logger.debug(
                f"Component {component_info['name']} startup completed in {duration:.3f}s"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to end component startup tracking: {e}")
            return False

    def end_app_startup(
        self,
        startup_id: str,
        status: str = "completed",
        memory_usage: Optional[float] = None,
    ) -> bool:
        """End tracking app startup.

        :param startup_id: Startup ID to end tracking
        :type startup_id: str
        :param status: Startup status (completed, failed, timeout)
        :type status: str
        :param memory_usage: Memory usage in MB
        :type memory_usage: Optional[float]
        :return: True if successful, False otherwise
        :rtype: bool
        """
        try:
            # Get startup info from thread-local storage
            if (
                not hasattr(_thread_local, "app_startups")
                or startup_id not in _thread_local.app_startups
            ):
                logger.warning(
                    f"No active app startup found for startup_id: {startup_id}"
                )
                return False

            startup_info = _thread_local.app_startups[startup_id]
            end_time = time.time()
            duration = end_time - startup_info["start_time"]
            end_timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(end_time))

            # Prepare component load times JSON
            component_times = {}
            for comp_id, comp_info in startup_info["component_times"].items():
                if "duration" in comp_info:
                    component_times[comp_info["name"]] = comp_info["duration"]

            component_times_json = (
                json.dumps(component_times) if component_times else None
            )

            # Sanitize status
            status = InputSanitizer.sanitize_string(status, max_length=20)

            # Update database
            query = """
                UPDATE app_startups
                SET startup_end_time = ?, startup_duration = ?, startup_status = ?,
                    component_load_times = ?, memory_usage = ?
                WHERE startup_id = ?
            """
            success = self.db.execute_update(
                query,
                (
                    end_timestamp,
                    duration,
                    status,
                    component_times_json,
                    memory_usage,
                    startup_id,
                ),
            )

            # Clean up thread-local storage
            del _thread_local.app_startups[startup_id]

            if success:
                logger.info(
                    f"Completed app startup tracking for startup_id: {startup_id}, duration: {duration:.2f}s"
                )
            return success

        except Exception as e:
            logger.error(f"Failed to end app startup tracking: {e}")
            return False

    def record_performance_metric(
        self,
        username: str,
        metric_type: str,
        metric_name: str,
        metric_value: float,
        metric_unit: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Record a performance metric.

        :param username: Username associated with the metric
        :type username: str
        :param metric_type: Type of metric (memory, cpu, network, etc.)
        :type metric_type: str
        :param metric_name: Name of the metric
        :type metric_name: str
        :param metric_value: Metric value
        :type metric_value: float
        :param metric_unit: Unit of measurement
        :type metric_unit: Optional[str]
        :param metadata: Additional metadata
        :type metadata: Optional[Dict[str, Any]]
        :return: True if successful, False otherwise
        :rtype: bool
        """
        try:
            # Sanitize inputs
            username = InputSanitizer.sanitize_username(username)
            metric_type = InputSanitizer.sanitize_string(metric_type, max_length=50)
            metric_name = InputSanitizer.sanitize_string(metric_name, max_length=100)
            if metric_unit:
                metric_unit = InputSanitizer.sanitize_string(metric_unit, max_length=20)

            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
            metadata_json = json.dumps(metadata) if metadata else None

            # Insert metric into database
            query = """
                INSERT INTO performance_metrics
                (username, metric_type, metric_name, metric_value, metric_unit, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            success = self.db.execute_update(
                query,
                (
                    username,
                    metric_type,
                    metric_name,
                    metric_value,
                    metric_unit,
                    timestamp,
                    metadata_json,
                ),
            )

            if success:
                logger.debug(
                    f"Recorded performance metric: {metric_type}.{metric_name} = {metric_value}"
                )
            return success

        except Exception as e:
            logger.error(f"Failed to record performance metric: {e}")
            return False

    def get_user_performance_summary(
        self, username: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get performance summary for a user.

        :param username: Username to get summary for
        :type username: str
        :param days: Number of days to look back
        :type days: int
        :return: Performance summary dictionary
        :rtype: Dict[str, Any]
        """
        try:
            username = InputSanitizer.sanitize_username(username)

            # Get Docker build stats
            query = """
                SELECT COUNT(*) as total_builds,
                       AVG(build_duration) as avg_build_time,
                       MIN(build_duration) as min_build_time,
                       MAX(build_duration) as max_build_time,
                       COUNT(CASE WHEN build_status = 'completed' THEN 1 END) as successful_builds
                FROM docker_builds
                WHERE username = ? AND created_at >= datetime('now', '-{} days')
            """.format(days)

            build_stats = self.db.execute_query(query, (username,))

            # Get API call stats
            query = """
                SELECT COUNT(*) as total_calls,
                       AVG(duration) as avg_call_time,
                       MIN(duration) as min_call_time,
                       MAX(duration) as max_call_time,
                       COUNT(CASE WHEN status_code < 400 THEN 1 END) as successful_calls
                FROM api_calls
                WHERE username = ? AND created_at >= datetime('now', '-{} days')
            """.format(days)

            api_stats = self.db.execute_query(query, (username,))

            # Get app startup stats
            query = """
                SELECT COUNT(*) as total_startups,
                       AVG(startup_duration) as avg_startup_time,
                       MIN(startup_duration) as min_startup_time,
                       MAX(startup_duration) as max_startup_time,
                       COUNT(CASE WHEN startup_status = 'completed' THEN 1 END) as successful_startups
                FROM app_startups
                WHERE username = ? AND created_at >= datetime('now', '-{} days')
            """.format(days)

            startup_stats = self.db.execute_query(query, (username,))

            return {
                "username": username,
                "period_days": days,
                "docker_builds": {
                    "total": build_stats[0][0] if build_stats else 0,
                    "avg_time": build_stats[0][1]
                    if build_stats and build_stats[0][1]
                    else 0,
                    "min_time": build_stats[0][2]
                    if build_stats and build_stats[0][2]
                    else 0,
                    "max_time": build_stats[0][3]
                    if build_stats and build_stats[0][3]
                    else 0,
                    "successful": build_stats[0][4] if build_stats else 0,
                },
                "api_calls": {
                    "total": api_stats[0][0] if api_stats else 0,
                    "avg_time": api_stats[0][1] if api_stats and api_stats[0][1] else 0,
                    "min_time": api_stats[0][2] if api_stats and api_stats[0][2] else 0,
                    "max_time": api_stats[0][3] if api_stats and api_stats[0][3] else 0,
                    "successful": api_stats[0][4] if api_stats else 0,
                },
                "app_startups": {
                    "total": startup_stats[0][0] if startup_stats else 0,
                    "avg_time": startup_stats[0][1]
                    if startup_stats and startup_stats[0][1]
                    else 0,
                    "min_time": startup_stats[0][2]
                    if startup_stats and startup_stats[0][2]
                    else 0,
                    "max_time": startup_stats[0][3]
                    if startup_stats and startup_stats[0][3]
                    else 0,
                    "successful": startup_stats[0][4] if startup_stats else 0,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get performance summary for user {username}: {e}")
            return {}


# Global performance tracker instance
_performance_tracker = None


def get_performance_tracker() -> PerformanceTracker:
    """Get the global performance tracker instance."""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker


# Context managers for easy tracking
@contextmanager
def track_docker_build(username: str, build_id: Optional[str] = None):
    """
    Tracks the time taken to build the Docker image.

    Raises:
        Exception: If the build fails.
    """
    tracker = get_performance_tracker()
    bid = tracker.start_docker_build(username, build_id)
    try:
        yield bid
        tracker.end_docker_build(bid, "completed")
    except Exception as e:
        tracker.end_docker_build(bid, "failed", build_logs=str(e))
        raise


@contextmanager
def track_api_call(username: str, endpoint: str, method: str):
    """
    Tracks the time taken for an API call.

    Raises:
        Exception: If the API call fails.
    """
    tracker = get_performance_tracker()
    call_id = tracker.track_api_call(username, endpoint, method)
    try:
        yield call_id
        tracker.end_api_call(call_id, 200)
    except Exception as e:
        tracker.end_api_call(call_id, 500, error_message=str(e))
        raise


@contextmanager
def track_app_startup(username: str, startup_id: Optional[str] = None):
    """
    Tracks the time taken for the application to start up.

    Raises:
        Exception: If startup fails.
    """
    tracker = get_performance_tracker()
    sid = tracker.start_app_startup(username, startup_id)
    try:
        yield sid
        tracker.end_app_startup(sid, "completed")
    except Exception:
        tracker.end_app_startup(sid, "failed")
        raise
