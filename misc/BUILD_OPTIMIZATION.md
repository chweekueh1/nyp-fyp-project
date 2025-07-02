# Build Optimization and Freeze Prevention

## 🔍 **Build Freeze Diagnosis**

### **Root Causes Identified:**

1. **Heavy ML/AI Packages (229 total packages)**
   - PyTorch ecosystem: `torch==2.6.0`, `torchaudio==2.6.0`, `torchvision==0.21.0`
   - OpenCV: `opencv-python==4.11.0.86` (large binary package)
   - ML packages: `scikit-learn==1.6.1`, `sentence-transformers==4.0.2`, `transformers==4.50.3`
   - Computer Vision: `effdet==0.4.1`, `timm==1.0.15`, `pycocotools==2.0.8`
   - Heavy dependencies: `chromadb==0.6.3`, `langchain` ecosystem, `unstructured` ecosystem

2. **Excessive System Dependencies**
   - 30+ system packages in Dockerfiles
   - Many unnecessary libraries (tesseract, pandoc, poppler, etc.)
   - Heavy build tools (ninja, git, curl, etc.)

3. **No Build Caching**
   - Each build starts from scratch
   - No layer optimization
   - Redundant package installations

4. **Alpine Linux Compatibility Issues**
   - ChromaDB requires onnxruntime which doesn't have Alpine wheels
   - Limited package availability for ML/AI libraries
   - Build failures due to missing dependencies

## 🚀 **Optimizations Applied**

### **1. Requirements.txt Reduction (229 → 25 packages)**

**Kept Essential Packages:**

- Core web framework: `gradio`, `fastapi`, `uvicorn`
- Database: `chromadb`, `SQLAlchemy`, `aiosqlite`
- LangChain core: `langchain`, `langchain-chroma`, `langchain-openai`
- LangGraph: `langgraph`, `langgraph-checkpoint-sqlite`
- OpenAI: `openai`, `tiktoken`
- Security: `bcrypt`, `cryptography`
- Data handling: `numpy`, `pandas`, `pydantic`
- Document processing: `pypdf`, `pillow`
- Utilities: `python-dotenv`, `requests`, `aiofiles`

**Removed Problematic Packages:**

- PyTorch ecosystem (torch, torchaudio, torchvision)
- OpenCV (opencv-python)
- Heavy ML packages (scikit-learn, sentence-transformers, transformers)
- Computer vision packages (effdet, timm, pycocotools)
- Unstructured document processing
- Many unnecessary dependencies

### **2. Dockerfile Optimizations**

**Base Image Change:**

- **Before**: `python:3.11-alpine` (incompatible with onnxruntime)
- **After**: `python:3.11-slim` (Debian-based, better compatibility)

**System Dependencies Reduced (30+ → 8 packages):**

```dockerfile
# Essential only (Debian packages)
build-essential \
libffi-dev \
libssl-dev \
zlib1g-dev \
libjpeg-dev \
libfreetype6-dev \
libpng-dev \
cmake \
pkg-config
```

**Removed Heavy Dependencies:**

- tesseract-ocr, pandoc, poppler-utils
- ninja, git, curl, unzip
- lcms2, openjpeg, tiff, tcl, tk
- harfbuzz, fribidi, libimagequant, libxcb

### **3. Build Process Improvements**

- **Layer Optimization**: Removed redundant COPY commands
- **Dependency Caching**: Better pip caching strategy
- **Minimal Context**: Only copy necessary files
- **Debian Base**: Better compatibility with ML/AI packages
- **Package Cleanup**: `rm -rf /var/lib/apt/lists/*` to reduce image size

## 📊 **Expected Improvements**

### **Build Time:**

- **Before**: 15-30 minutes (often freezing)
- **After**: 5-10 minutes (stable)

### **Image Size:**

- **Before**: ~2-3GB
- **After**: ~1-1.5GB (slightly larger than Alpine but more compatible)

### **Memory Usage:**

- **Before**: High memory usage during build
- **After**: Reduced memory footprint

### **Stability:**

- **Before**: Frequent build freezes and compatibility issues
- **After**: Stable, predictable builds with full package compatibility

### **Compatibility:**

- **Before**: Alpine Linux limitations with ML packages
- **After**: Full compatibility with all Python packages including onnxruntime

## 🔧 **Usage**

### **Build Commands:**

```bash
# Production build
docker build -f Dockerfile -t nyp-chatbot:latest .

# Development build
docker build -f Dockerfile.dev -t nyp-chatbot:dev .

# Test build
docker build -f Dockerfile.test -t nyp-chatbot:test .
```

### **Verification:**

```bash
# Test the build
docker run --rm nyp-chatbot:test

# Check image size
docker images nyp-chatbot
```

## ⚠️ **Important Notes**

1. **ChromaDB Dependency**: Now fully compatible with onnxruntime
2. **LangChain Core**: Essential for conversation flow
3. **Document Processing**: Limited to core formats (PDF, images)
4. **ML Features**: Some advanced features may be limited but core functionality preserved
5. **Base Image**: Switched to Debian slim for better compatibility

## 🔄 **Future Optimizations**

1. **Multi-stage Builds**: Separate build and runtime stages
2. **Dependency Pinning**: Lock all dependency versions
3. **Build Caching**: Implement proper Docker layer caching
4. **Package Analysis**: Regular dependency audits
5. **Alternative Storage**: Consider lighter vector stores
6. **Alpine Optimization**: If needed, create custom Alpine builds with ML package support

## 📝 **Monitoring**

Monitor build performance:

- Build time tracking
- Memory usage during builds
- Image size monitoring
- Dependency update impact assessment
- Compatibility testing with new packages
