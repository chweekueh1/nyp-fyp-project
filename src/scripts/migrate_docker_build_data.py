#!/usr/bin/env python3
"""
Docker Build Data Migration Script

This script migrates existing Docker build times from JSON format to the new SQLite database
with timezone-aware timestamps and image size tracking.
"""

import json
import sys
from pathlib import Path

# Add the scripts directory to the path so we can import docker_build_tracker
sys.path.insert(0, str(Path(__file__).parent))

from docker_build_tracker import DockerBuildTracker


def migrate_json_to_sqlite():
    """Migrate existing JSON data to SQLite database."""
    try:
        # Find the JSON file
        data_dir = Path(__file__).parent.parent.parent / "data"
        json_path = data_dir / "docker_build_times.json"

        if not json_path.exists():
            print(f"❌ JSON file not found: {json_path}")
            return False

        print(f"📁 Found JSON file: {json_path}")

        # Load JSON data
        with open(json_path, "r") as f:
            data = json.load(f)

        print(f"📊 Loaded {len(data.get('history', []))} build records")

        # Initialize tracker
        tracker = DockerBuildTracker()

        # Migrate build history
        migrated_count = 0
        for build in data.get("history", []):
            try:
                # Extract data from JSON format
                image_name = build.get("image", "unknown")
                duration = build.get("duration", 0.0)
                timestamp = build.get("timestamp", "")
                timezone = build.get("timezone", "Asia/Singapore")

                # Record in SQLite database
                tracker.record_build(
                    image_name=image_name,
                    build_duration=duration,
                    build_timestamp=timestamp,
                    timezone_name=timezone,
                )

                migrated_count += 1
                print(f"  ✅ Migrated: {image_name} ({duration:.2f}s)")

            except Exception as e:
                print(f"  ❌ Failed to migrate build {build}: {e}")

        print(f"\n🎯 Migration completed: {migrated_count} records migrated")

        # Export updated data back to JSON for backward compatibility
        tracker.export_to_json(json_path)
        print(f"📄 Updated JSON file: {json_path}")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def show_migration_stats():
    """Show statistics about the migration."""
    try:
        tracker = DockerBuildTracker()

        # Get build history
        history = tracker.get_build_history(limit=1000)
        statistics = tracker.get_build_statistics()

        print("\n📈 Migration Statistics:")
        print(f"  Total builds: {len(history)}")
        print(f"  Unique images: {len(statistics)}")

        if statistics:
            print("\n  Image Statistics:")
            for image, stats in statistics.items():
                print(f"    {image}:")
                print(f"      Average duration: {stats['avg_duration']:.2f}s")
                print(f"      Average size: {stats['avg_size_mb']:.2f}MB")
                print(f"      Total builds: {stats['total_builds']}")
                print(f"      Last build: {stats['last_build_timestamp']}")
                print(f"      Timezone: {stats['timezone']}")

        return True

    except Exception as e:
        print(f"❌ Failed to show statistics: {e}")
        return False


def main():
    """Main migration function."""
    print("🚀 Docker Build Data Migration")
    print("=" * 40)

    # Check if migration is needed
    tracker = DockerBuildTracker()
    existing_history = tracker.get_build_history(limit=1)

    if existing_history:
        print("⚠️  SQLite database already contains data")
        response = input("Do you want to proceed with migration? (y/N): ")
        if response.lower() != "y":
            print("Migration cancelled.")
            return

    # Perform migration
    success = migrate_json_to_sqlite()

    if success:
        print("\n✅ Migration successful!")
        show_migration_stats()
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
