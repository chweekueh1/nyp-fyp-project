#!/usr/bin/env python3
"""
Docker Build Tracking Setup Script

This script sets up the Docker build tracking system by:
1. Initializing the SQLite database
2. Migrating existing JSON data if available
3. Setting up the tracking system for future builds
"""

import sys
from pathlib import Path

# Add the scripts directory to the path so we can import docker_build_tracker
sys.path.insert(0, str(Path(__file__).parent))

from docker_build_tracker import DockerBuildTracker
from migrate_docker_build_data import migrate_json_to_sqlite, show_migration_stats


def setup_docker_build_tracking():
    """Set up the Docker build tracking system."""
    print("🚀 Setting up Docker Build Tracking System")
    print("=" * 50)

    try:
        # Initialize the tracker (this creates the database)
        tracker = DockerBuildTracker()
        print("✅ SQLite database initialized")

        # Check if there's existing JSON data to migrate
        data_dir = Path(__file__).parent.parent.parent / "data"
        json_path = data_dir / "docker_build_times.json"

        if json_path.exists():
            print(f"📁 Found existing JSON data: {json_path}")
            print("🔄 Starting migration...")

            success = migrate_json_to_sqlite()
            if success:
                print("✅ Migration completed successfully")
                show_migration_stats()
            else:
                print("⚠️  Migration failed, but database is still functional")
        else:
            print("📝 No existing JSON data found - starting fresh")

        # Test the system
        print("\n🧪 Testing the tracking system...")

        # Record a test build
        tracker.record_build(
            image_name="test-setup-image",
            build_duration=10.5,
            dockerfile_path="docker/Dockerfile",
            build_args={"TEST": "true"},
            timezone_name="Asia/Singapore",
        )

        # Get statistics
        stats = tracker.get_build_statistics()
        if "test-setup-image" in stats:
            print("✅ Test build recorded successfully")

        # Export to JSON for backward compatibility
        tracker.export_to_json()
        print("✅ JSON export completed")

        print("\n🎯 Docker Build Tracking System Setup Complete!")
        print(f"📊 Database location: {tracker.db_path}")
        print("📝 You can now use the tracking system in your Docker builds")

        return True

    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


def main():
    """Main setup function."""
    success = setup_docker_build_tracking()

    if success:
        print("\n✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. The database is ready for use")
        print("2. Docker builds can now track timing and image sizes")
        print("3. Benchmarks will automatically use the new tracking system")
        print("4. Use the migration script if you have existing JSON data")
    else:
        print("\n❌ Setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
