# Dependency Installation Guide

This guide explains how to install pandoc and tesseract OCR dependencies for enhanced file classification.

## Overview

The enhanced file classification system supports:
- **Pandoc**: Document conversion (.docx, .doc, .odt, .rtf, .html, .epub, .md)
- **Tesseract OCR**: Image text extraction (.png, .jpg, .jpeg, .tiff, .bmp, .gif)

Dependencies should be installed to: `~/.nypai-chatbot/data/dependencies/`

## Directory Structure

```
~/.nypai-chatbot/
├── logs/                    # Application logs
├── data/
│   └── dependencies/        # Local dependencies
│       ├── pandoc/          # Pandoc installation
│       │   ├── pandoc.exe   # Windows
│       │   └── bin/pandoc   # Linux/macOS
│       └── tesseract/       # Tesseract installation
│           ├── tesseract.exe # Windows
│           └── bin/tesseract # Linux/macOS
├── uploads/                 # User uploaded files
└── test_uploads/           # Test files
```

## Installation Instructions

### Windows

#### Pandoc Installation
1. Download pandoc from: https://pandoc.org/installing.html
2. Extract to: `~/.nypai-chatbot/data/dependencies/pandoc/`
3. Ensure `pandoc.exe` is directly in the pandoc folder

#### Tesseract Installation
1. Download tesseract from: https://github.com/tesseract-ocr/tesseract
2. Extract to: `~/.nypai-chatbot/data/dependencies/tesseract/`
3. Ensure `tesseract.exe` is directly in the tesseract folder

### Linux/macOS

#### Pandoc Installation
1. Download pandoc from: https://pandoc.org/installing.html
2. Extract to: `~/.nypai-chatbot/data/dependencies/pandoc/`
3. Ensure binary is at: `~/.nypai-chatbot/data/dependencies/pandoc/bin/pandoc`

#### Tesseract Installation
1. Download tesseract from: https://github.com/tesseract-ocr/tesseract
2. Extract to: `~/.nypai-chatbot/data/dependencies/tesseract/`
3. Ensure binary is at: `~/.nypai-chatbot/data/dependencies/tesseract/bin/tesseract`

## Alternative: System Installation

If you prefer system-wide installation, the application will automatically detect:
- `pandoc` in system PATH
- `tesseract` in system PATH

The local dependencies take priority over system installations.

## Verification

Run the dependency test to verify installation:

```bash
python tests/performance/test_logging_and_dependency_paths.py
```

Expected output:
```
📦 Pandoc available: True
📦 Tesseract available: True
✅ Pandoc detected and working
✅ Tesseract detected and working
```

## Supported File Types

### With Pandoc
- `.docx` - Microsoft Word documents
- `.doc` - Legacy Word documents
- `.odt` - OpenDocument text
- `.rtf` - Rich Text Format
- `.html` - HTML documents
- `.htm` - HTML documents
- `.epub` - E-book format
- `.md` - Markdown documents
- `.markdown` - Markdown documents

### With Tesseract OCR
- `.png` - PNG images
- `.jpg` - JPEG images
- `.jpeg` - JPEG images
- `.tiff` - TIFF images
- `.tif` - TIFF images
- `.bmp` - Bitmap images
- `.gif` - GIF images
- `.webp` - WebP images

### Always Supported
- `.txt` - Plain text files
- `.csv` - Comma-separated values
- `.log` - Log files
- `.pdf` - PDF documents (basic extraction)

## Troubleshooting

### Dependencies Not Detected
1. Check file paths match the expected structure
2. Ensure executables have proper permissions
3. Verify file names are correct (case-sensitive on Linux/macOS)

### Permission Issues (Linux/macOS)
```bash
chmod +x ~/.nypai-chatbot/data/dependencies/pandoc/bin/pandoc
chmod +x ~/.nypai-chatbot/data/dependencies/tesseract/bin/tesseract
```

### Path Issues
- Windows: Use `pandoc.exe` and `tesseract.exe`
- Linux/macOS: Use `bin/pandoc` and `bin/tesseract`

## Performance Benefits

With dependencies installed:
- **Document Conversion**: High-quality text extraction from office documents
- **OCR Processing**: Text extraction from images and scanned documents
- **Better Classification**: More accurate classification with complete content extraction
- **Format Support**: Support for 15+ additional file formats

## Fallback Behavior

Without dependencies:
- **Graceful Degradation**: Application continues to work
- **Basic Extraction**: Text files and basic PDF extraction still supported
- **User Guidance**: Clear messages about missing dependencies
- **System PATH**: Automatic detection of system-installed tools

## Security Considerations

- Dependencies are isolated to user directory
- No system-wide modifications required
- Local installation reduces security risks
- Automatic cleanup of temporary files

## Updates

To update dependencies:
1. Replace files in the dependency directories
2. Restart the application
3. Run verification test to confirm

The application automatically detects updated dependencies on restart.
