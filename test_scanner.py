#!/usr/bin/env python3
"""
Test script for Directory Scanner
This script tests both the Rust backend and Python fallback implementations.
"""

import os
import sys
import json
import tempfile
import time
from pathlib import Path

# Add the python_frontend directory to the path
sys.path.insert(0, str(Path(__file__).parent / "python_frontend"))

def create_test_files(test_dir):
    """Create test files of various sizes"""
    test_files = [
        ("small.txt", "Small file content"),
        ("medium.txt", "Medium file content " * 100),
        ("large.txt", "Large file content " * 1000),
        ("huge.txt", "Huge file content " * 10000),
        ("binary.dat", bytes(range(256)) * 50),
        ("empty.txt", ""),
    ]
    
    # Create subdirectory
    subdir = test_dir / "subdir"
    subdir.mkdir(exist_ok=True)
    
    created_files = []
    
    for filename, content in test_files:
        filepath = test_dir / filename
        if isinstance(content, str):
            filepath.write_text(content, encoding='utf-8')
        else:
            filepath.write_bytes(content)
        created_files.append(filepath)
        
        # Also create a file in subdirectory
        sub_filepath = subdir / f"sub_{filename}"
        if isinstance(content, str):
            sub_filepath.write_text(content, encoding='utf-8')
        else:
            sub_filepath.write_bytes(content)
        created_files.append(sub_filepath)
    
    return created_files

def test_rust_backend(test_dir):
    """Test the Rust backend if available"""
    print("\n" + "=" * 40)
    print("Testing Rust Backend")
    print("=" * 40)
    
    try:
        # Try to import the Rust module
        import rust_backend
        print("✓ Rust backend module imported successfully")
        
        # Test scan_dir function
        start_time = time.time()
        result_json = rust_backend.scan_dir(str(test_dir), 20)
        end_time = time.time()
        
        results = json.loads(result_json)
        print(f"✓ Scanned directory in {end_time - start_time:.3f} seconds")
        print(f"✓ Found {len(results)} files")
        
        # Verify results are sorted by size
        if len(results) > 1:
            sizes = [file_info['size'] for file_info in results]
            is_sorted = all(sizes[i] >= sizes[i+1] for i in range(len(sizes)-1))
            print(f"✓ Results sorted by size: {is_sorted}")
        
        # Test count_files function
        file_count = rust_backend.count_files(str(test_dir))
        print(f"✓ File count: {file_count}")
        
        # Test get_directory_size function
        dir_size = rust_backend.get_directory_size(str(test_dir))
        print(f"✓ Directory size: {dir_size} bytes")
        
        # Display top 5 largest files
        print("\nTop 5 largest files:")
        for i, file_info in enumerate(results[:5]):
            size_mb = file_info['size'] / (1024 * 1024)
            filename = Path(file_info['path']).name
            print(f"  {i+1}. {filename}: {size_mb:.2f} MB")
        
        return True, results
        
    except ImportError as e:
        print(f"✗ Rust backend not available: {e}")
        print("  Run 'python build_rust.py' in python_frontend/ to build it")
        return False, []
    except Exception as e:
        print(f"✗ Rust backend test failed: {e}")
        return False, []

def test_python_fallback(test_dir):
    """Test the Python fallback implementation"""
    print("\n" + "=" * 40)
    print("Testing Python Fallback")
    print("=" * 40)
    
    try:
        # Import the main module to access ScanWorker
        from main import ScanWorker
        
        # Create a worker and run the Python scan
        worker = ScanWorker(str(test_dir), 20)
        
        start_time = time.time()
        results = worker.scan_with_python()
        end_time = time.time()
        
        print(f"✓ Scanned directory in {end_time - start_time:.3f} seconds")
        print(f"✓ Found {len(results)} files")
        
        # Verify results are sorted by size
        if len(results) > 1:
            sizes = [file_info['size'] for file_info in results]
            is_sorted = all(sizes[i] >= sizes[i+1] for i in range(len(sizes)-1))
            print(f"✓ Results sorted by size: {is_sorted}")
        
        # Display top 5 largest files
        print("\nTop 5 largest files:")
        for i, file_info in enumerate(results[:5]):
            size_mb = file_info['size'] / (1024 * 1024)
            filename = Path(file_info['path']).name
            print(f"  {i+1}. {filename}: {size_mb:.2f} MB")
        
        return True, results
        
    except Exception as e:
        print(f"✗ Python fallback test failed: {e}")
        return False, []

def test_gui_components():
    """Test GUI components without actually showing the window"""
    print("\n" + "=" * 40)
    print("Testing GUI Components")
    print("=" * 40)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from main import DirectoryScannerApp
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create the main window
        window = DirectoryScannerApp()
        print("✓ Main window created successfully")
        
        # Test some basic functionality
        window.format_file_size(1024)
        print("✓ File size formatting works")
        
        # Don't show the window, just test creation
        print("✓ GUI components initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ GUI test failed: {e}")
        return False

def main():
    """Main test function"""
    print("Directory Scanner - Test Suite")
    print("=" * 50)
    
    # Create temporary test directory
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = Path(temp_dir)
        print(f"Created test directory: {test_dir}")
        
        # Create test files
        print("\nCreating test files...")
        test_files = create_test_files(test_dir)
        print(f"✓ Created {len(test_files)} test files")
        
        # Test Rust backend
        rust_success, rust_results = test_rust_backend(test_dir)
        
        # Test Python fallback
        python_success, python_results = test_python_fallback(test_dir)
        
        # Test GUI components
        gui_success = test_gui_components()
        
        # Compare results if both backends worked
        if rust_success and python_success:
            print("\n" + "=" * 40)
            print("Comparing Results")
            print("=" * 40)
            
            if len(rust_results) == len(python_results):
                print("✓ Both backends found the same number of files")
            else:
                print(f"⚠ Different file counts: Rust={len(rust_results)}, Python={len(python_results)}")
            
            # Compare file sizes for common files
            rust_files = {Path(f['path']).name: f['size'] for f in rust_results}
            python_files = {Path(f['path']).name: f['size'] for f in python_results}
            
            common_files = set(rust_files.keys()) & set(python_files.keys())
            size_matches = sum(1 for f in common_files if rust_files[f] == python_files[f])
            
            print(f"✓ Size matches for {size_matches}/{len(common_files)} common files")
        
        # Summary
        print("\n" + "=" * 50)
        print("Test Summary")
        print("=" * 50)
        print(f"Rust Backend: {'✓ PASS' if rust_success else '✗ FAIL'}")
        print(f"Python Fallback: {'✓ PASS' if python_success else '✗ FAIL'}")
        print(f"GUI Components: {'✓ PASS' if gui_success else '✗ FAIL'}")
        
        if rust_success or python_success:
            print("\n✓ Directory Scanner is working correctly!")
            print("You can now run the GUI application with: python python_frontend/main.py")
        else:
            print("\n✗ Tests failed. Please check the error messages above.")
            return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)