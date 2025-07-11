# Docker Build Tracking System

This document describes the comprehensive Docker build tracking system that provides timezone-aware timestamps, image size tracking, and SQLite database storage for build history and statistics.

## Overview

The Docker build tracking system consists of:

1. **SQLite Database**: Stores build history with timezone-aware timestamps
2. **Image Size Tracking**: Automatically captures Docker image sizes
3. **Build Statistics**: Calculates averages and trends
4. **Backward Compatibility**: Exports to JSON format for existing tools
5. **Cross-Context Access**: Database can be copied to different Docker contexts

## Components

### Core Files

- `src/scripts/docker_build_tracker.py` - Main tracking system
- `src/scripts/migrate_docker_build_data.py` - Migration from JSON to SQLite
- `src/scripts/setup_docker_build_tracking.py` - Initial setup script
- `docker_build_history.db` - SQLite database (created automatically)
- `src/docker_build_times.json` - JSON export for backward compatibility

### Database Schema

#### docker_builds Table

- `id` - Primary key
- `image_name` - Docker image name
- `build_duration` - Build time in seconds
- `image_size_mb` - Image size in MB
- `build_timestamp` - ISO format timestamp
- `timezone` - Timezone used for timestamp
- `dockerfile_path` - Path to Dockerfile used
- `build_args` - JSON string of build arguments
- `success` - Boolean indicating build success
- `error_message` - Error message if build failed
- `created_at` - Database record creation time

#### build_statistics Table

- `id` - Primary key
- `image_name` - Docker image name (unique)
- `avg_duration` - Average build duration
- `avg_size_mb` - Average image size
- `total_builds` - Total number of builds
- `last_build_timestamp` - Timestamp of last build
- `timezone` - Timezone used
- `updated_at` - Last statistics update time

## Setup

### Initial Setup

```bash
# Run the setup script to initialize the system
python src/scripts/setup_docker_build_tracking.py
```

This will:

1. Create the SQLite database
2. Migrate existing JSON data if available
3. Test the system with a sample build
4. Export data to JSON for backward compatibility

### Migration from JSON

If you have existing `docker_build_times.json` data:

```bash
# Run the migration script
python src/scripts/migrate_docker_build_data.py
```

## Usage

### Recording Builds

```python
from src.scripts.docker_build_tracker import track_docker_build

# Record a build
track_docker_build(
    image_name="my-app",
    build_duration=120.5,
    dockerfile_path="docker/Dockerfile",
    build_args={"ENV": "production"},
    timezone_name="Asia/Singapore"
)
```

### Using the Tracker Class

```python
from src.scripts.docker_build_tracker import DockerBuildTracker

tracker = DockerBuildTracker()

# Record a build
tracker.record_build(
    image_name="my-app",
    build_duration=120.5,
    dockerfile_path="docker/Dockerfile",
    build_args={"ENV": "production"},
    timezone_name="Asia/Singapore"
)

# Get build history
history = tracker.get_build_history(limit=50)

# Get statistics
stats = tracker.get_build_statistics()

# Export to JSON
tracker.export_to_json("build_times.json")
```

### Integration with Benchmarks

The benchmark system automatically uses the new tracking system:

```bash
# Run benchmarks (will use SQLite database)
python src/scripts/run_benchmarks.py
```

The benchmarks will:

1. Load Docker build times from SQLite database
2. Include image sizes in results
3. Store comprehensive statistics
4. Export updated JSON for backward compatibility

## Docker Integration

### Dockerfile Updates

All Dockerfiles now include:

```dockerfile
# Copy Docker build tracking database (if exists)
COPY --chown=appuser:appgroup docker_build_history.db* ./
```

This ensures the database is available in all Docker contexts.

### Environment Variables

- `BENCHMARK_MODE=1` - Enables benchmark mode in containers
- `TZ=Asia/Singapore` - Sets timezone for timestamps

## Requirements

### Core Dependencies

- `pytz>=2025.2` - Timezone support
- `psutil>=6.1.0` - System monitoring
- `sqlite3` - Built into Python

### Benchmark Dependencies

See `requirements/requirements-benchmark.txt` for complete list.

## File Organization

### Requirements Files

- `requirements/requirements-app.txt` - Main application dependencies
- `requirements/requirements-benchmark.txt` - Benchmark-specific dependencies
- `requirements/requirements-dev.txt` - Development dependencies
- `requirements/requirements-test.txt` - Testing dependencies
- `requirements/requirements-docs.txt` - Documentation dependencies
- `requirements/requirements-precommit.txt` - Pre-commit hooks

### Dockerfiles

- `docker/Dockerfile` - Production build
- `docker/Dockerfile.dev` - Development build
- `docker/Dockerfile.test` - Testing build
- `docker/Dockerfile.bench` - Benchmark build
- `docker/Dockerfile.benchmark` - Alternative benchmark build
- `docker/Dockerfile.docs` - Documentation build

## Timezone Support

The system uses timezone-aware timestamps with the following features:

- Default timezone: `Asia/Singapore`
- ISO format timestamps
- Automatic timezone conversion
- Fallback to UTC if timezone unavailable

## Performance Features

### Comprehensive Benchmarking

The benchmark system now includes:

1. **File Classification Benchmarks**
   - Text file classification
   - PDF file classification
   - Office document classification

2. **Audio Transcription Benchmarks**
   - Short audio files
   - Long audio files

3. **Search Benchmarks**
   - Simple queries
   - Complex queries
   - Fuzzy matching

4. **System Benchmarks**
   - Memory allocation
   - Thread pool operations
   - Async operations
   - Database operations
   - Network latency simulation

5. **Security Benchmarks**
   - Password hashing
   - Rate limiting (single and multiple users)

### Async and Multi-threaded Execution

- Concurrent benchmark execution
- Performance monitoring decorators
- Memory usage tracking
- System information reporting

## Database Management

### Backup and Restore

```bash
# Backup database
cp docker_build_history.db docker_build_history.db.backup

# Restore database
cp docker_build_history.db.backup docker_build_history.db
```

### Cleanup

```bash
# Remove old database (will be recreated)
rm docker_build_history.db
```

## Troubleshooting

### Common Issues

1. **Database Locked Error**
   - The system now uses connection timeouts
   - Separate connections for statistics updates

2. **Image Size Not Available**
   - Occurs when Docker image doesn't exist
   - System gracefully handles this with 0.0 MB size

3. **Timezone Issues**
   - System falls back to UTC if timezone unavailable
   - Check `pytz` installation

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Migration from Old System

If you're migrating from the old JSON-only system:

1. Run the setup script: `python src/scripts/setup_docker_build_tracking.py`
2. The system will automatically migrate existing data
3. Both SQLite and JSON formats will be maintained
4. Benchmarks will use the new system automatically

## Future Enhancements

- Web interface for build statistics
- Automated build performance alerts
- Integration with CI/CD pipelines
- Export to other formats (CSV, Excel)
- Real-time build monitoring
