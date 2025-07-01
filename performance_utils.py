#!/usr/bin/env python3
"""
Performance optimization utilities for the NYP FYP Chatbot.
"""

import asyncio
import threading
import time
import logging
from typing import Dict
from functools import lru_cache
import os
import tempfile

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and log performance metrics."""

    def __init__(self):
        self.start_times = {}
        self.metrics = {}

    def start_timer(self, operation: str):
        """Start timing an operation."""
        self.start_times[operation] = time.time()

    def end_timer(self, operation: str) -> float:
        """End timing an operation and return duration."""
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            self.metrics[operation] = duration
            logger.info(f"⏱️ {operation}: {duration:.2f}s")
            return duration
        return 0.0

    def get_metrics(self) -> Dict[str, float]:
        """Get all performance metrics."""
        return self.metrics.copy()


# Global performance monitor
perf_monitor = PerformanceMonitor()


class ConnectionPool:
    """Simple connection pool for database connections."""

    def __init__(self, max_connections: int = 5):
        self.max_connections = max_connections
        self.connections = []
        self.lock = threading.Lock()

    def get_connection(self):
        """Get a connection from the pool."""
        with self.lock:
            if self.connections:
                return self.connections.pop()
            return None

    def return_connection(self, connection):
        """Return a connection to the pool."""
        with self.lock:
            if len(self.connections) < self.max_connections:
                self.connections.append(connection)


# Global connection pool
connection_pool = ConnectionPool()


@lru_cache(maxsize=128)
def cached_file_exists(path: str) -> bool:
    """Cached file existence check."""
    return os.path.exists(path)


@lru_cache(maxsize=32)
def get_temp_dir() -> str:
    """Cached temp directory path."""
    return tempfile.gettempdir()


class LazyLoader:
    """Lazy loading utility for expensive imports."""

    def __init__(self):
        self._modules = {}
        self._lock = threading.Lock()

    def load_module(self, module_name: str, import_func):
        """Load a module lazily."""
        if module_name not in self._modules:
            with self._lock:
                if module_name not in self._modules:
                    perf_monitor.start_timer(f"import_{module_name}")
                    try:
                        self._modules[module_name] = import_func()
                        logger.info(f"✅ Lazy loaded: {module_name}")
                    except Exception as e:
                        logger.error(f"❌ Failed to lazy load {module_name}: {e}")
                        self._modules[module_name] = None
                    finally:
                        perf_monitor.end_timer(f"import_{module_name}")

        return self._modules[module_name]


# Global lazy loader
lazy_loader = LazyLoader()


class AsyncTaskManager:
    """Manage background async tasks for better performance."""

    def __init__(self):
        self.tasks = []
        self.completed_tasks = []

    async def run_task(self, coro, name: str):
        """Run a task and track its completion."""
        perf_monitor.start_timer(f"task_{name}")
        try:
            result = await coro
            self.completed_tasks.append(name)
            logger.info(f"✅ Completed task: {name}")
            return result
        except Exception as e:
            logger.error(f"❌ Task failed {name}: {e}")
            raise
        finally:
            perf_monitor.end_timer(f"task_{name}")

    async def run_parallel_tasks(self, tasks: list):
        """Run multiple tasks in parallel."""
        return await asyncio.gather(*tasks, return_exceptions=True)


# Global task manager
task_manager = AsyncTaskManager()


def optimize_gradio_performance():
    """Apply Gradio-specific performance optimizations."""
    # Set environment variables for better performance
    os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
    os.environ.setdefault("GRADIO_SERVER_PORT", "7860")

    # Disable unnecessary features for faster startup
    return {
        "show_api": False,
        "show_error": True,
        "quiet": True,
        "enable_queue": True,
        "max_threads": 4,
    }


def get_optimized_launch_config():
    """Get optimized launch configuration."""
    return {
        "debug": False,  # Disable debug mode for production
        "share": False,  # Essential: Ensures it's not a public Gradio share link
        "inbrowser": False,  # Don't auto-open browser
        "quiet": True,
        "show_error": True,
        # --- ADD THESE TWO LINES FOR DOCKER EXPOSURE ---
        "server_name": "0.0.0.0",  # Tells Gradio to listen on all available network interfaces
        "server_port": 7860,  # Tells Gradio to listen on port 7860 inside the container
    }


# And then in your main app file (e.g., app.py), you'd use it like:
# launch_config = get_optimized_launch_config()
# demo.launch(**launch_config)


class CacheManager:
    """Manage various caches for better performance."""

    def __init__(self):
        self.caches = {}
        self.cache_stats = {}

    def get_cache(self, cache_name: str, maxsize: int = 128):
        """Get or create a cache."""
        if cache_name not in self.caches:
            self.caches[cache_name] = {}
            self.cache_stats[cache_name] = {"hits": 0, "misses": 0}
        return self.caches[cache_name]

    def clear_cache(self, cache_name: str):
        """Clear a specific cache."""
        if cache_name in self.caches:
            self.caches[cache_name].clear()
            logger.info(f"🗑️ Cleared cache: {cache_name}")

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Get cache statistics."""
        return self.cache_stats.copy()


# Global cache manager
cache_manager = CacheManager()


class StartupTimer:
    """Comprehensive startup time tracking."""

    def __init__(self):
        self.startup_start_time = None
        self.startup_phases = {}
        self.startup_completed = False
        self.total_startup_time = 0

    def start_startup_tracking(self):
        """Start tracking the complete app startup process."""
        import time

        self.startup_start_time = time.time()
        logger.info("🚀 Starting app startup time tracking...")

    def mark_startup_phase(self, phase_name: str):
        """Mark a specific startup phase completion."""
        if self.startup_start_time is None:
            logger.warning(
                "⚠️ Startup tracking not started, call start_startup_tracking() first"
            )
            return

        import time

        current_time = time.time()
        phase_duration = current_time - self.startup_start_time
        self.startup_phases[phase_name] = phase_duration
        logger.info(f"📍 Startup phase '{phase_name}' reached at {phase_duration:.2f}s")

    def complete_startup_tracking(self):
        """Complete startup tracking and log comprehensive results."""
        if self.startup_start_time is None:
            logger.warning("⚠️ Startup tracking not started")
            return

        import time

        self.total_startup_time = time.time() - self.startup_start_time
        self.startup_completed = True

        self._log_comprehensive_startup_metrics()
        return self.total_startup_time

    def _log_comprehensive_startup_metrics(self):
        """Log detailed startup performance metrics."""
        logger.info("=" * 80)
        logger.info("🎯 COMPLETE APP STARTUP PERFORMANCE REPORT")
        logger.info("=" * 80)

        # Total startup time (most important metric)
        logger.info(f"⏱️  TOTAL APP STARTUP TIME: {self.total_startup_time:.2f}s")
        logger.info("=" * 80)

        # Startup phases
        if self.startup_phases:
            logger.info("📊 Startup Phase Timeline:")
            for phase, duration in self.startup_phases.items():
                logger.info(f"  📍 {phase}: {duration:.2f}s")
            logger.info("-" * 40)

        # Performance metrics from perf_monitor
        metrics = perf_monitor.get_metrics()
        if metrics:
            logger.info("🔧 Component Performance Breakdown:")

            # Group metrics by category
            startup_metrics = {
                k: v
                for k, v in metrics.items()
                if "startup" in k.lower() or "init" in k.lower()
            }
            import_metrics = {
                k: v
                for k, v in metrics.items()
                if "import" in k.lower() or "load" in k.lower()
            }
            other_metrics = {
                k: v
                for k, v in metrics.items()
                if k not in startup_metrics and k not in import_metrics
            }

            if startup_metrics:
                logger.info("  🚀 Startup Operations:")
                for operation, duration in startup_metrics.items():
                    logger.info(f"    • {operation}: {duration:.2f}s")

            if import_metrics:
                logger.info("  📦 Import/Loading Operations:")
                for operation, duration in import_metrics.items():
                    logger.info(f"    • {operation}: {duration:.2f}s")

            if other_metrics:
                logger.info("  ⚙️  Other Operations:")
                for operation, duration in other_metrics.items():
                    logger.info(f"    • {operation}: {duration:.2f}s")

            total_measured = sum(metrics.values())
            logger.info(f"  📊 Total measured operations: {total_measured:.2f}s")
            logger.info("-" * 40)

        # Performance analysis
        self._analyze_startup_performance()

        logger.info("=" * 80)
        logger.info(f"🎉 App startup completed in {self.total_startup_time:.2f}s")
        logger.info("=" * 80)

    def _analyze_startup_performance(self):
        """Analyze and provide insights on startup performance."""
        logger.info("🔍 Performance Analysis:")

        # Calculate actual startup time (exclude app_launch which includes runtime)
        metrics = perf_monitor.get_metrics()
        actual_startup_time = self.total_startup_time

        # If app_launch is in metrics and seems to be the bulk of time, exclude it
        if metrics and "app_launch" in metrics:
            app_launch_time = metrics["app_launch"]
            if app_launch_time > 10 and app_launch_time > (
                self.total_startup_time * 0.8
            ):
                # app_launch includes runtime, calculate actual startup without it
                actual_startup_time = self.total_startup_time - app_launch_time
                logger.info(
                    f"  📊 Actual startup time (excluding runtime): {actual_startup_time:.2f}s"
                )
                logger.info(f"  📊 App launch + runtime: {app_launch_time:.2f}s")

        # Analyze actual startup performance
        if actual_startup_time < 5:
            logger.info("  🟢 EXCELLENT: Very fast startup time!")
        elif actual_startup_time < 15:
            logger.info("  🟡 GOOD: Reasonable startup time")
        elif actual_startup_time < 30:
            logger.info("  🟠 MODERATE: Startup time could be improved")
        else:
            logger.info("  🔴 SLOW: Startup time needs optimization")

        # Identify bottlenecks (exclude app_launch from analysis)
        if metrics:
            startup_metrics = {k: v for k, v in metrics.items() if k != "app_launch"}
            if startup_metrics:
                slowest_operations = sorted(
                    startup_metrics.items(), key=lambda x: x[1], reverse=True
                )[:3]
                if slowest_operations:
                    logger.info("  🐌 Slowest startup operations:")
                    for operation, duration in slowest_operations:
                        percentage = (
                            (duration / actual_startup_time) * 100
                            if actual_startup_time > 0
                            else 0
                        )
                        logger.info(
                            f"    • {operation}: {duration:.2f}s ({percentage:.1f}% of startup)"
                        )


# Global startup timer
startup_timer = StartupTimer()


def log_startup_performance():
    """Log startup performance metrics (legacy function for compatibility)."""
    metrics = perf_monitor.get_metrics()
    if metrics:
        logger.info("📊 Startup Performance Metrics:")
        for operation, duration in metrics.items():
            logger.info(f"  {operation}: {duration:.2f}s")

        total_time = sum(metrics.values())
        logger.info(f"  Total measured time: {total_time:.2f}s")


def start_app_startup_tracking():
    """Start comprehensive app startup tracking."""
    startup_timer.start_startup_tracking()


def mark_startup_milestone(milestone_name: str):
    """Mark a startup milestone."""
    startup_timer.mark_startup_phase(milestone_name)


def complete_app_startup_tracking():
    """Complete app startup tracking and return total time."""
    return startup_timer.complete_startup_tracking()


def get_total_startup_time():
    """Get the total app startup time."""
    return startup_timer.total_startup_time if startup_timer.startup_completed else None


# Advanced performance optimizations
class MemoryOptimizer:
    """Memory optimization utilities."""

    @staticmethod
    def clear_import_cache():
        """Clear Python import cache to free memory."""
        import sys
        import gc

        # Clear module cache for modules we don't need anymore
        modules_to_clear = [
            "keybert",
            "sentence_transformers",
            "transformers",
            "torch",
            "tensorflow",
            "sklearn",
        ]

        for module_name in modules_to_clear:
            if module_name in sys.modules:
                del sys.modules[module_name]

        gc.collect()
        logger.debug("🗑️ Cleared import cache and ran garbage collection")

    @staticmethod
    def optimize_gc():
        """Optimize garbage collection settings."""
        import gc

        # Set more aggressive garbage collection
        gc.set_threshold(700, 10, 10)  # More frequent collection
        gc.collect()
        logger.debug("🔧 Optimized garbage collection settings")


class ProcessOptimizer:
    """Process-level optimizations."""

    @staticmethod
    def set_process_priority():
        """Set process priority for better performance."""
        try:
            import psutil
            import os
            import sys

            # Set high priority on Windows, nice value on Unix
            if sys.platform == "win32":  # Windows
                psutil.Process().nice(psutil.HIGH_PRIORITY_CLASS)
            else:  # Unix/Linux
                os.nice(-5)  # Higher priority

            logger.debug("⚡ Set high process priority")
        except ImportError:
            logger.debug(
                "⚠️ psutil not available, skipping process priority optimization"
            )
        except Exception as e:
            logger.debug(f"⚠️ Could not set process priority: {e}")

    @staticmethod
    def optimize_thread_pool():
        """Optimize thread pool settings."""
        import os

        # Set optimal thread pool size based on CPU cores
        cpu_count = os.cpu_count() or 4
        optimal_workers = min(cpu_count * 2, 8)  # Cap at 8 workers

        # Store in environment for other modules to use
        os.environ["OPTIMAL_WORKERS"] = str(optimal_workers)
        logger.debug(f"🔧 Set optimal worker count: {optimal_workers}")


# Global optimizers
memory_optimizer = MemoryOptimizer()
process_optimizer = ProcessOptimizer()


def apply_all_optimizations():
    """Apply all available performance optimizations."""
    perf_monitor.start_timer("optimization_setup")

    try:
        # Process optimizations
        process_optimizer.set_process_priority()
        process_optimizer.optimize_thread_pool()

        # Memory optimizations
        memory_optimizer.optimize_gc()

        # Environment optimizations
        optimize_environment_variables()

        logger.info("⚡ Applied all performance optimizations")
    except Exception as e:
        logger.warning(f"⚠️ Some optimizations failed: {e}")
    finally:
        perf_monitor.end_timer("optimization_setup")


def optimize_environment_variables():
    """Set environment variables for optimal performance."""
    import os

    # Python optimizations
    os.environ.setdefault("PYTHONOPTIMIZE", "1")  # Enable optimizations
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")  # Skip .pyc files

    # Threading optimizations
    os.environ.setdefault("OMP_NUM_THREADS", "4")  # Limit OpenMP threads
    os.environ.setdefault("MKL_NUM_THREADS", "4")  # Limit MKL threads

    # Disable unnecessary features
    os.environ.setdefault(
        "TOKENIZERS_PARALLELISM", "false"
    )  # Disable tokenizer warnings
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")  # Prefer local models

    logger.debug("🔧 Optimized environment variables")
