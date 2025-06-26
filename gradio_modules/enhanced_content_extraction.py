#!/usr/bin/env python3
"""
Enhanced content extraction using pandoc and tesseract OCR for better file processing.
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Set up logging
logger = logging.getLogger(__name__)

def get_dependency_paths() -> Dict[str, Optional[str]]:
    """Get paths to dependencies in ~/.nypai-chatbot/data/dependencies/"""
    try:
        from utils import get_chatbot_dir
        deps_dir = os.path.join(get_chatbot_dir(), 'data', 'dependencies')

        paths: Dict[str, Optional[str]] = {
            'pandoc': None,
            'tesseract': None
        }

        # Check for pandoc
        if os.name == 'nt':  # Windows
            pandoc_path = os.path.join(deps_dir, 'pandoc', 'pandoc.exe')
        else:  # Linux/macOS
            pandoc_path = os.path.join(deps_dir, 'pandoc', 'bin', 'pandoc')

        if os.path.exists(pandoc_path):
            paths['pandoc'] = pandoc_path

        # Check for tesseract
        if os.name == 'nt':  # Windows
            tesseract_path = os.path.join(deps_dir, 'tesseract', 'tesseract.exe')
        else:  # Linux/macOS
            tesseract_path = os.path.join(deps_dir, 'tesseract', 'bin', 'tesseract')

        if os.path.exists(tesseract_path):
            paths['tesseract'] = tesseract_path

        return paths
    except Exception as e:
        logger.error(f"Error getting dependency paths: {e}")
        return {'pandoc': None, 'tesseract': None}

def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are available."""
    dependencies = {
        'pandoc': False,
        'tesseract': False
    }

    # Get dependency paths
    dep_paths = get_dependency_paths()

    # Check pandoc (try local path first, then system PATH)
    pandoc_cmd = dep_paths['pandoc'] or 'pandoc'
    try:
        result = subprocess.run([pandoc_cmd, '--version'],
                              capture_output=True, text=True, timeout=10)
        dependencies['pandoc'] = result.returncode == 0
        if dependencies['pandoc']:
            logger.info(f"Pandoc found: {pandoc_cmd}")
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        dependencies['pandoc'] = False

    # Check tesseract (try local path first, then system PATH)
    tesseract_cmd = dep_paths['tesseract'] or 'tesseract'
    try:
        result = subprocess.run([tesseract_cmd, '--version'],
                              capture_output=True, text=True, timeout=10)
        dependencies['tesseract'] = result.returncode == 0
        if dependencies['tesseract']:
            logger.info(f"Tesseract found: {tesseract_cmd}")
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        dependencies['tesseract'] = False

    return dependencies

def extract_with_pandoc(file_path: str) -> Optional[str]:
    """Extract text content using pandoc."""
    try:
        file_ext = Path(file_path).suffix.lower()

        # Pandoc supported formats
        pandoc_formats = {
            '.docx': 'docx',
            '.doc': 'doc',
            '.odt': 'odt',
            '.rtf': 'rtf',
            '.html': 'html',
            '.htm': 'html',
            '.epub': 'epub',
            '.md': 'markdown',
            '.markdown': 'markdown'
        }

        if file_ext not in pandoc_formats:
            return None

        input_format = pandoc_formats[file_ext]

        # Get pandoc command (try local path first, then system PATH)
        dep_paths = get_dependency_paths()
        pandoc_cmd = dep_paths['pandoc'] or 'pandoc'

        # Use pandoc to convert to plain text
        cmd = [pandoc_cmd, '-f', input_format, '-t', 'plain', '--wrap=none', file_path]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            content = result.stdout.strip()
            if content:
                logger.info(f"Successfully extracted content using pandoc from {file_path}")
                return content
        else:
            logger.warning(f"Pandoc extraction failed for {file_path}: {result.stderr}")

    except Exception as e:
        logger.error(f"Error in pandoc extraction for {file_path}: {e}")

    return None

def extract_with_tesseract(file_path: str) -> Optional[str]:
    """Extract text from images using tesseract OCR."""
    try:
        file_ext = Path(file_path).suffix.lower()

        # Image formats supported by tesseract
        image_formats = {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif', '.webp'}

        if file_ext not in image_formats:
            return None

        # Get tesseract command (try local path first, then system PATH)
        dep_paths = get_dependency_paths()
        tesseract_cmd = dep_paths['tesseract'] or 'tesseract'

        # Use tesseract to extract text
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmp_output:
            output_path = tmp_output.name

        try:
            # Remove the .txt extension as tesseract adds it automatically
            output_base = output_path[:-4]

            cmd = [tesseract_cmd, file_path, output_base, '-l', 'eng']

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                # Read the output file
                if os.path.exists(output_path):
                    with open(output_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()

                    if content:
                        logger.info(f"Successfully extracted text using tesseract from {file_path}")
                        return content
            else:
                logger.warning(f"Tesseract OCR failed for {file_path}: {result.stderr}")

        finally:
            # Clean up temporary file
            if os.path.exists(output_path):
                os.unlink(output_path)

    except Exception as e:
        logger.error(f"Error in tesseract OCR for {file_path}: {e}")

    return None

def extract_pdf_content(file_path: str) -> Optional[str]:
    """Extract content from PDF files using multiple methods."""
    try:
        # Try pandoc first for PDF
        content = extract_with_pandoc(file_path)
        if content:
            return content
        
        # Fallback to existing PDF extraction methods
        try:
            from llm.dataProcessing import ExtractText
            documents = ExtractText(file_path)
            if documents:
                content = "\n\n".join([doc.page_content for doc in documents])
                if content.strip():
                    logger.info(f"Successfully extracted PDF content using fallback method from {file_path}")
                    return content
        except Exception as e:
            logger.warning(f"Fallback PDF extraction failed for {file_path}: {e}")
        
    except Exception as e:
        logger.error(f"Error in PDF content extraction for {file_path}: {e}")
    
    return None

def extract_text_file_content(file_path: str) -> Optional[str]:
    """Extract content from plain text files."""
    try:
        file_ext = Path(file_path).suffix.lower()
        text_formats = {'.txt', '.csv', '.log', '.md', '.markdown'}
        
        if file_ext not in text_formats:
            return None
        
        # Try different encodings
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read().strip()
                if content:
                    logger.info(f"Successfully read text file {file_path} with encoding {encoding}")
                    return content
            except UnicodeDecodeError:
                continue
        
        logger.warning(f"Could not decode text file {file_path} with any supported encoding")
        
    except Exception as e:
        logger.error(f"Error reading text file {file_path}: {e}")
    
    return None

def enhanced_extract_file_content(file_path: str) -> Dict[str, Any]:
    """
    Enhanced file content extraction with multiple methods and detailed results.
    
    Returns:
        Dict containing extracted content, method used, and metadata
    """
    if not os.path.exists(file_path):
        return {
            'content': '',
            'method': 'error',
            'error': f'File not found: {file_path}',
            'file_size': 0,
            'file_type': 'unknown'
        }
    
    file_ext = Path(file_path).suffix.lower()
    file_size = os.path.getsize(file_path)
    
    result = {
        'content': '',
        'method': 'none',
        'error': None,
        'file_size': file_size,
        'file_type': file_ext,
        'extraction_methods_tried': []
    }
    
    # Check dependencies
    deps = check_dependencies()
    
    # Try different extraction methods based on file type
    extraction_methods = []
    
    # PDF files
    if file_ext == '.pdf':
        extraction_methods.append(('pdf_extraction', extract_pdf_content))
    
    # Image files (OCR)
    elif file_ext in {'.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif', '.webp'}:
        if deps['tesseract']:
            extraction_methods.append(('tesseract_ocr', extract_with_tesseract))
        else:
            result['error'] = 'Tesseract OCR not available for image processing'
    
    # Document files
    elif file_ext in {'.docx', '.doc', '.odt', '.rtf', '.html', '.htm', '.epub', '.md', '.markdown'}:
        if deps['pandoc']:
            extraction_methods.append(('pandoc', extract_with_pandoc))
        else:
            result['error'] = 'Pandoc not available for document processing'
    
    # Text files
    elif file_ext in {'.txt', '.csv', '.log'}:
        extraction_methods.append(('text_file', extract_text_file_content))
    
    # Excel files
    elif file_ext in {'.xlsx', '.xls'}:
        extraction_methods.append(('excel_fallback', lambda _: None))  # Placeholder
    
    # PowerPoint files
    elif file_ext in {'.pptx', '.ppt'}:
        if deps['pandoc']:
            extraction_methods.append(('pandoc', extract_with_pandoc))
    
    # Try extraction methods
    for method_name, method_func in extraction_methods:
        result['extraction_methods_tried'].append(method_name)
        try:
            content = method_func(file_path)
            if content and content.strip():
                result['content'] = content.strip()
                result['method'] = method_name
                break
        except Exception as e:
            logger.warning(f"Extraction method {method_name} failed for {file_path}: {e}")
            continue
    
    # Fallback to original method if nothing worked
    if not result['content'] and file_ext != '.pdf':  # Avoid double PDF processing
        result['extraction_methods_tried'].append('fallback_original')
        try:
            from llm.dataProcessing import ExtractText
            documents = ExtractText(file_path)
            if documents:
                content = "\n\n".join([doc.page_content for doc in documents])
                if content.strip():
                    result['content'] = content.strip()
                    result['method'] = 'fallback_original'
        except Exception as e:
            result['error'] = f"All extraction methods failed. Last error: {str(e)}"
    
    if not result['content']:
        result['error'] = result['error'] or "No content could be extracted from the file"
    
    return result
