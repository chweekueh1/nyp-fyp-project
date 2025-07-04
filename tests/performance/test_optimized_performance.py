#!/usr/bin/env python3
"""
Performance test suite for optimized data processing and backend components.
Tests all performance improvements without polluting LLM directories.
"""

import sys
import os
import time
import tempfile
from pathlib import Path
from llm.chatModel import initialize_llm_and_db

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

initialize_llm_and_db()


def test_fast_keyword_extraction():
    """Test the lightning-fast keyword extraction."""
    print("🔍 Testing Fast Keyword Extraction...")

    try:
        from llm.dataProcessing import FastYAKEMetadataTagger
        from langchain.schema import Document

        # Create test document
        test_doc = Document(
            page_content="This document discusses artificial intelligence, machine learning algorithms, neural networks, and deep learning techniques used in modern computer systems for data analysis and pattern recognition.",
            metadata={},
        )

        # Test performance
        start_time = time.time()
        result = FastYAKEMetadataTagger([test_doc])
        duration = time.time() - start_time

        # Verify results
        assert len(result) == 1, "Should return one document"
        assert "keywords" in result[0].metadata, "Should have keywords in metadata"
        keywords = result[0].metadata["keywords"]

        print(f"  ⚡ Duration: {duration:.4f}s")
        print(f"  📝 Keywords extracted: {keywords}")
        print("  ✅ Fast keyword extraction: PASSED")

        return duration < 0.1  # Should be under 0.1 seconds

    except Exception as e:
        print(f"  ❌ Fast keyword extraction: FAILED - {e}")
        return False


def test_optimized_text_extraction():
    """Test the optimized text extraction methods."""
    print("🔍 Testing Optimized Text Extraction...")

    try:
        from llm.dataProcessing import ExtractText

        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            test_content = "This is a test document for performance testing.\nIt contains multiple lines of text.\nUsed for benchmarking extraction speed."
            f.write(test_content)
            temp_file = f.name

        try:
            # Test fast extraction
            start_time = time.time()
            result = ExtractText(temp_file)
            duration = time.time() - start_time

            # Verify results
            assert len(result) >= 1, "Should return at least one document"
            assert len(result[0].page_content) > 0, "Should have content"

            print(f"  ⚡ Duration: {duration:.4f}s")
            print(f"  📄 Content length: {len(result[0].page_content)} chars")
            print(
                f"  🔧 Method: {result[0].metadata.get('extraction_method', 'unknown')}"
            )
            print("  ✅ Optimized text extraction: PASSED")

            return duration < 1.0  # Should be under 1 second

        finally:
            # Clean up
            os.unlink(temp_file)

    except Exception as e:
        print(f"  ❌ Optimized text extraction: FAILED - {e}")
        return False


def test_optimized_chunking():
    """Test the optimized chunking performance."""
    print("🔍 Testing Optimized Chunking...")

    try:
        from llm.dataProcessing import optimizedRecursiveChunker
        from langchain.schema import Document

        # Create test document with substantial content
        test_content = "This is a test document. " * 200  # Create longer content
        test_doc = Document(page_content=test_content, metadata={})

        # Test performance
        start_time = time.time()
        chunks = optimizedRecursiveChunker([test_doc])
        duration = time.time() - start_time

        # Verify results
        assert len(chunks) > 0, "Should create chunks"
        total_content = sum(len(chunk.page_content) for chunk in chunks)

        print(f"  ⚡ Duration: {duration:.4f}s")
        print(f"  📄 Chunks created: {len(chunks)}")
        print(f"  📝 Total content: {total_content} chars")
        print("  ✅ Optimized chunking: PASSED")

        return duration < 0.1  # Should be under 0.1 seconds

    except Exception as e:
        print(f"  ❌ Optimized chunking: FAILED - {e}")
        return False


def test_memory_conscious_batching():
    """Test the memory-conscious batching system."""
    print("🔍 Testing Memory-Conscious Batching...")

    try:
        from llm.dataProcessing import optimized_batching
        from langchain.schema import Document

        # Create test chunks
        test_chunks = []
        for i in range(50):
            content = f"Test chunk {i} with some content. " * 10
            test_chunks.append(Document(page_content=content, metadata={"chunk_id": i}))

        # Test performance
        start_time = time.time()
        batches = list(optimized_batching(test_chunks, batch_size=10, max_memory_mb=1))
        duration = time.time() - start_time

        # Verify results
        assert len(batches) > 0, "Should create batches"
        total_chunks = sum(len(batch) for batch in batches)
        assert total_chunks == len(test_chunks), "Should preserve all chunks"

        print(f"  ⚡ Duration: {duration:.4f}s")
        print(f"  📦 Batches created: {len(batches)}")
        print(f"  📄 Total chunks: {total_chunks}")
        print("  ✅ Memory-conscious batching: PASSED")

        return duration < 0.1  # Should be under 0.1 seconds

    except Exception as e:
        print(f"  ❌ Memory-conscious batching: FAILED - {e}")
        return False


def test_performance_monitoring():
    """Test the performance monitoring system."""
    print("🔍 Testing Performance Monitoring...")

    try:
        from performance_utils import perf_monitor

        # Test timer functionality
        perf_monitor.start_timer("test_operation")
        time.sleep(0.01)  # Small delay
        duration = perf_monitor.end_timer("test_operation")

        # Verify results
        assert duration > 0, "Should measure positive duration"
        assert duration < 1.0, "Should be reasonable duration"

        metrics = perf_monitor.get_metrics()
        assert "test_operation" in metrics, "Should store metrics"

        print(f"  ⚡ Measured duration: {duration:.4f}s")
        print(f"  📊 Metrics stored: {len(metrics)} operations")
        print("  ✅ Performance monitoring: PASSED")

        return True

    except Exception as e:
        print(f"  ❌ Performance monitoring: FAILED - {e}")
        return False


def test_complete_pipeline_performance():
    """Test the complete optimized data processing pipeline."""
    print("🔍 Testing Complete Pipeline Performance...")

    try:
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            test_content = """
            This is a comprehensive test document for performance testing.
            It contains artificial intelligence concepts, machine learning algorithms,
            neural networks, and deep learning techniques.
            The document is designed to test keyword extraction, chunking, and processing speed.
            Performance optimization is crucial for real-time applications.
            """
            f.write(test_content)
            temp_file = f.name

        try:
            # Test complete pipeline (without database insertion to avoid pollution)
            start_time = time.time()

            # We'll test individual components instead of full pipeline
            # to avoid database pollution
            from llm.dataProcessing import (
                ExtractText,
                FastYAKEMetadataTagger,
                optimizedRecursiveChunker,
            )

            # Step 1: Extract text
            documents = ExtractText(temp_file)

            # Step 2: Extract keywords
            documents = FastYAKEMetadataTagger(documents)

            # Step 3: Chunk documents
            chunks = optimizedRecursiveChunker(documents)

            duration = time.time() - start_time

            # Verify results
            assert len(documents) > 0, "Should extract documents"
            assert len(chunks) > 0, "Should create chunks"

            print(f"  ⚡ Total duration: {duration:.4f}s")
            print(f"  📄 Documents: {len(documents)}")
            print(f"  📝 Chunks: {len(chunks)}")
            print(f"  🔧 Keywords: {documents[0].metadata.get('keywords', [])}")
            print("  ✅ Complete pipeline: PASSED")

            return duration < 2.0  # Should be under 2 seconds

        finally:
            # Clean up
            os.unlink(temp_file)

    except Exception as e:
        print(f"  ❌ Complete pipeline: FAILED - {e}")
        return False


def run_performance_tests():
    """Run all performance tests."""
    print("🚀 Running Optimized Performance Tests")
    print("=" * 60)

    tests = [
        test_fast_keyword_extraction,
        test_optimized_text_extraction,
        test_optimized_chunking,
        test_memory_conscious_batching,
        test_performance_monitoring,
        test_complete_pipeline_performance,
    ]

    results = []
    total_start = time.time()

    for test_func in tests:
        print(f"\n{'=' * 40}")
        try:
            success = test_func()
            results.append((test_func.__name__, success))
        except Exception as e:
            print(f"❌ {test_func.__name__}: FAILED - {e}")
            results.append((test_func.__name__, False))

    total_duration = time.time() - total_start

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 Performance Test Results:")
    print(f"{'=' * 60}")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status} {test_name}")

    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    print(f"⏱️ Total test time: {total_duration:.2f}s")

    if passed == total:
        print("🎉 All performance optimizations working correctly!")
        return True
    else:
        print("⚠️ Some performance tests failed")
        return False


if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)
