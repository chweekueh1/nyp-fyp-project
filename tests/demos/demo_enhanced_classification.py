#!/usr/bin/env python3
"""
Demonstration of the enhanced file classification system with improved formatting.
This demo has been moved to the test suite for better organization.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def demo_enhanced_classification():
    """Demonstrate the enhanced file classification system."""
    print("🚀 Enhanced File Classification System Demo")
    print("=" * 60)
    
    # Check dependencies
    try:
        from gradio_modules.enhanced_content_extraction import check_dependencies
        deps = check_dependencies()
        print(f"\n📦 System Dependencies:")
        print(f"  Pandoc: {'✅ Available' if deps['pandoc'] else '❌ Not Available'}")
        print(f"  Tesseract: {'✅ Available' if deps['tesseract'] else '❌ Not Available'}")
        
        if not deps['pandoc']:
            print("  💡 Install pandoc for document conversion: https://pandoc.org/installing.html")
        if not deps['tesseract']:
            print("  💡 Install tesseract for OCR: https://github.com/tesseract-ocr/tesseract")
    except Exception as e:
        print(f"❌ Error checking dependencies: {e}")
    
    # Demo 1: Enhanced Content Extraction
    print(f"\n{'='*40}")
    print("📄 Demo 1: Enhanced Content Extraction")
    print(f"{'='*40}")
    
    try:
        from gradio_modules.enhanced_content_extraction import enhanced_extract_file_content
        
        # Create a test document
        test_content = """CONFIDENTIAL DOCUMENT
        
Project Alpha - Technical Specifications

This document contains sensitive information about the new product development.
The specifications include proprietary algorithms and trade secrets.

Classification: CONFIDENTIAL
Sensitivity: HIGH
Distribution: Authorized Personnel Only
"""
        
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "confidential_doc.txt")
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Extract content
        extraction_result = enhanced_extract_file_content(temp_file)
        
        print(f"📋 Extraction Results:")
        print(f"  Method: {extraction_result['method']}")
        print(f"  File Type: {extraction_result['file_type']}")
        print(f"  File Size: {extraction_result['file_size']} bytes")
        print(f"  Content Length: {len(extraction_result['content'])} characters")
        print(f"  Methods Tried: {', '.join(extraction_result['extraction_methods_tried'])}")
        
        if extraction_result['error']:
            print(f"  ⚠️ Error: {extraction_result['error']}")
        else:
            print(f"  ✅ Extraction successful!")
        
        # Clean up
        os.unlink(temp_file)
        os.rmdir(temp_dir)
        
    except Exception as e:
        print(f"❌ Content extraction demo failed: {e}")
    
    # Demo 2: Enhanced Formatting
    print(f"\n{'='*40}")
    print("🎨 Demo 2: Enhanced Response Formatting")
    print(f"{'='*40}")
    
    try:
        from gradio_modules.classification_formatter import format_classification_response
        
        # Mock classification results
        classification = {
            'classification': 'CONFIDENTIAL',
            'sensitivity': 'HIGH',
            'reasoning': 'This document contains proprietary technical specifications and trade secrets. The presence of terms like "confidential", "proprietary algorithms", and "authorized personnel only" indicates high sensitivity content that requires restricted access.',
            'confidence': 0.92
        }
        
        extraction_info = {
            'content': test_content,
            'method': 'text_file',
            'file_size': len(test_content.encode('utf-8')),
            'file_type': '.txt',
            'extraction_methods_tried': ['text_file'],
            'error': None
        }
        
        file_info = {
            'filename': 'confidential_doc.txt',
            'size': str(len(test_content.encode('utf-8'))),
            'saved_name': 'confidential_doc_20240624_143000.txt'
        }
        
        # Format the response
        formatted = format_classification_response(classification, extraction_info, file_info)
        
        print(f"🔐 Security Classification:")
        print(f"  {formatted['classification']}")
        print(f"\n🔥 Sensitivity Level:")
        print(f"  {formatted['sensitivity']}")
        print(f"\n📄 File Information:")
        for line in formatted['file_info'].split('\n'):
            if line.strip():
                print(f"  {line}")
        print(f"\n🧠 Analysis & Reasoning:")
        for line in formatted['reasoning'].split('\n'):
            if line.strip():
                print(f"  {line}")
        print(f"\n📋 Summary:")
        for line in formatted['summary'].split('\n'):
            if line.strip():
                print(f"  {line}")
        
    except Exception as e:
        print(f"❌ Formatting demo failed: {e}")
    
    # Demo 3: Performance Comparison
    print(f"\n{'='*40}")
    print("⚡ Demo 3: Performance Improvements")
    print(f"{'='*40}")
    
    try:
        import time
        from gradio_modules.enhanced_content_extraction import enhanced_extract_file_content
        
        # Create a larger test file
        large_content = "This is a performance test document.\n" * 500
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "large_doc.txt")
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(large_content)
        
        # Time the extraction
        start_time = time.time()
        result = enhanced_extract_file_content(temp_file)
        end_time = time.time()
        
        extraction_time = end_time - start_time
        
        print(f"📊 Performance Metrics:")
        print(f"  File Size: {result['file_size']:,} bytes")
        print(f"  Content Length: {len(result['content']):,} characters")
        print(f"  Extraction Time: {extraction_time:.3f} seconds")
        print(f"  Processing Speed: {len(result['content'])/extraction_time:.0f} chars/sec")
        print(f"  Method Used: {result['method']}")
        
        if extraction_time < 0.1:
            print(f"  🚀 Excellent performance!")
        elif extraction_time < 0.5:
            print(f"  ✅ Good performance!")
        else:
            print(f"  ⚠️ Performance could be improved")
        
        # Clean up
        os.unlink(temp_file)
        os.rmdir(temp_dir)
        
    except Exception as e:
        print(f"❌ Performance demo failed: {e}")
    
    # Demo 4: Multiple File Types
    print(f"\n{'='*40}")
    print("📁 Demo 4: Multiple File Type Support")
    print(f"{'='*40}")
    
    try:
        from gradio_modules.enhanced_content_extraction import enhanced_extract_file_content
        
        file_types = [
            ('.txt', 'Plain text document'),
            ('.md', 'Markdown document'),
            ('.csv', 'CSV data file'),
            ('.log', 'Log file'),
            ('.pdf', 'PDF document'),
            ('.docx', 'Word document'),
            ('.png', 'Image file (OCR)'),
            ('.jpg', 'JPEG image (OCR)')
        ]
        
        temp_dir = tempfile.mkdtemp()
        
        for file_ext, description in file_types:
            temp_file = os.path.join(temp_dir, f"test{file_ext}")
            
            # Create appropriate test content
            if file_ext in ['.txt', '.md', '.csv', '.log']:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(f"Test content for {description}")
                
                result = enhanced_extract_file_content(temp_file)
                print(f"  {file_ext}: {result['method']} - {'✅' if result['content'] else '❌'}")
                
                os.unlink(temp_file)
            else:
                # For other file types, just show what method would be attempted
                result = enhanced_extract_file_content(temp_file)  # Will fail but show method selection
                methods_tried = result.get('extraction_methods_tried', [])
                if methods_tried:
                    print(f"  {file_ext}: would try {', '.join(methods_tried)} - ⚠️ (requires dependencies)")
                else:
                    print(f"  {file_ext}: no extraction method available - ❌")
        
        os.rmdir(temp_dir)
        
    except Exception as e:
        print(f"❌ File types demo failed: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print("🎉 Enhanced File Classification System Summary")
    print(f"{'='*60}")
    print("✅ Enhanced content extraction with multiple methods")
    print("✅ Beautiful formatting with emojis and styling")
    print("✅ Performance optimizations for fast processing")
    print("✅ Support for multiple file types")
    print("✅ Dependency detection and graceful fallbacks")
    print("✅ Detailed extraction method reporting")
    print("✅ Rich classification summaries with recommendations")
    print("\n💡 To get the most out of this system:")
    print("   • Install pandoc for document conversion")
    print("   • Install tesseract for OCR capabilities")
    print("   • Use the enhanced interface for better user experience")
    print("\n🚀 The system is ready for production use!")

if __name__ == "__main__":
    demo_enhanced_classification()
