#!/usr/bin/env python3
"""
Demo script for the integrated main app with enhanced chatbot features.

This demonstrates the fully integrated main application that includes:
1. Enhanced chatbot interface with chat history loading
2. Message persistence to chat session files
3. Chat session management (create, select, rename)
4. File upload functionality
5. Audio input functionality
6. Search functionality
7. User authentication (login/register)

Run this script to see the complete integrated application.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Run the integrated main application."""
    print("🚀 Starting Integrated Main App with Enhanced Chatbot Features...")
    print()
    print("📋 Features included:")
    print("   ✅ Enhanced chatbot interface with chat history loading")
    print("   ✅ Automatic message persistence to chat session files")
    print("   ✅ Chat session management (create, select, rename)")
    print("   ✅ File upload and analysis")
    print("   ✅ Audio input processing")
    print("   ✅ Chat history search")
    print("   ✅ User authentication (login/register)")
    print("   ✅ Tabbed interface for different functionalities")
    print()
    print("🔧 Integration improvements:")
    print("   • Replaced basic chat interface with enhanced chatbot_ui")
    print("   • Added proper chat history loading on login")
    print("   • Integrated message persistence with backend")
    print("   • Maintained compatibility with existing features")
    print()
    print("📝 How to use:")
    print("   1. Register a new account or login with existing credentials")
    print("   2. Your existing chats will automatically load")
    print("   3. Use the chat selector to switch between conversations")
    print("   4. Send messages - they'll be automatically saved")
    print("   5. Create new chats using the 'New Chat' button")
    print("   6. Use other tabs for file upload, audio, search, and management")
    print()
    
    try:
        from gradio_modules.main_app import main_app
        
        print("🔄 Loading main application...")
        app = main_app()
        
        print("✅ Main application loaded successfully!")
        print("🌐 Starting web interface...")
        print()
        print("🎯 The application will open in your browser.")
        print("   If it doesn't open automatically, go to: http://127.0.0.1:7860")
        print()
        
        # Launch the app
        app.launch(
            debug=False,
            share=False,
            server_name="127.0.0.1",
            server_port=7860,
            quiet=False
        )
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        print("\n🔍 Troubleshooting tips:")
        print("   • Make sure all dependencies are installed")
        print("   • Check that the backend is properly configured")
        print("   • Verify that the database is accessible")
        print("   • Try running the test scripts first")
        sys.exit(1)

if __name__ == "__main__":
    main()
