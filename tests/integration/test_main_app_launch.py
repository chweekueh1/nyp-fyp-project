#!/usr/bin/env python3
"""
Quick test to launch the main app and check if the chatbot UI loads.
"""

import sys
from pathlib import Path
import time
import threading

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_main_app_launch():
    """Test launching the main app."""
    print("🚀 Testing main app launch...")
    
    try:
        from gradio_modules.main_app import main_app
        
        print("✅ Main app imported successfully")
        
        # Create the app
        app = main_app()
        print("✅ Main app created successfully")
        
        # Check if the app has the expected components
        print("🔍 Checking app structure...")
        
        # The app should be a Gradio Blocks object
        import gradio as gr
        if isinstance(app, gr.Blocks):
            print("✅ App is a valid Gradio Blocks object")
        else:
            print(f"❌ App is not a Gradio Blocks object: {type(app)}")
            return False
        
        print("✅ Main app structure looks good!")
        
        # Try to launch the app briefly to see if there are any runtime errors
        print("🌐 Testing app launch (will close automatically)...")
        
        def close_app():
            time.sleep(3)  # Wait 3 seconds
            print("⏰ Auto-closing app...")
            app.close()
        
        # Start a thread to close the app after a few seconds
        close_thread = threading.Thread(target=close_app)
        close_thread.daemon = True
        close_thread.start()
        
        try:
            # Launch the app
            app.launch(
                debug=False,
                share=False,
                server_name="127.0.0.1",
                server_port=7861,  # Different port to avoid conflicts
                quiet=True,
                prevent_thread_lock=True  # Don't block the main thread
            )
            
            # Wait for the close thread to finish
            close_thread.join(timeout=5)
            
            print("✅ App launched and closed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error launching app: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Error testing main app: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_main_app_launch()
    if success:
        print("\n🎉 Main app test passed!")
        print("The main app should load the chatbot UI correctly.")
        print("You can now run: python gradio_modules/main_app.py")
    else:
        print("\n❌ Main app test failed!")
        print("There may be issues with the chatbot UI integration.")
    
    sys.exit(0 if success else 1)
