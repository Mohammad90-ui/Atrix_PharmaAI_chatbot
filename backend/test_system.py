"""
System Test Script
Verifies all components are working correctly.
"""
import sys
import importlib
from pathlib import Path


def print_status(check_name, passed, message=""):
    """Print colored status message."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} - {check_name}")
    if message:
        print(f"    {message}")


def check_python_version():
    """Check Python version >= 3.8"""
    version = sys.version_info
    passed = version.major == 3 and version.minor >= 8
    msg = f"Python {version.major}.{version.minor}.{version.micro}"
    print_status("Python Version", passed, msg)
    return passed


def check_dependencies():
    """Check if all required packages are installed."""
    required = [
        'fastapi', 'uvicorn', 'pandas', 'openpyxl', 'docx',
        'sentence_transformers', 'faiss', 'pydantic', 'gradio',
        'loguru', 'numpy'
    ]
    
    all_installed = True
    for package in required:
        package_name = 'faiss' if package == 'faiss' else package
        package_name = 'python-docx' if package == 'docx' else package_name
        
        try:
            if package == 'docx':
                importlib.import_module('docx')
            elif package == 'faiss':
                importlib.import_module('faiss')
            else:
                importlib.import_module(package)
            print_status(f"Package: {package}", True)
        except ImportError:
            print_status(f"Package: {package}", False, "Not installed")
            all_installed = False
    
    return all_installed


def check_data_files():
    """Check if source data files exist."""
    base_path = Path(__file__).parent
    files = [
        'Pharma_Clinical_Trial_AllDrugs.xlsx',
        'Pharma_Clinical_Trial_Notes.docx'
    ]
    
    all_exist = True
    for file in files:
        file_path = base_path / file
        exists = file_path.exists()
        print_status(f"Data File: {file}", exists)
        if not exists:
            all_exist = False
    
    return all_exist


def check_modules():
    """Check if all custom modules can be imported."""
    modules = [
        'data_loader', 'retriever', 'chatbot_engine', 'logger'
    ]
    
    all_imported = True
    for module in modules:
        try:
            importlib.import_module(module)
            print_status(f"Module: {module}", True)
        except Exception as e:
            print_status(f"Module: {module}", False, str(e))
            all_imported = False
    
    return all_imported


def test_data_loading():
    """Test if data can be loaded."""
    try:
        from data_loader import DataLoader
        base_path = Path(__file__).parent
        
        loader = DataLoader(
            str(base_path / 'Pharma_Clinical_Trial_AllDrugs.xlsx'),
            str(base_path / 'Pharma_Clinical_Trial_Notes.docx')
        )
        
        excel_df, doc_chunks, excel_chunks = loader.load_all()
        
        passed = len(excel_df) > 0 and len(doc_chunks) > 0 and len(excel_chunks) > 0
        msg = f"Loaded {len(excel_chunks)} Excel rows, {len(doc_chunks)} Doc chunks"
        print_status("Data Loading", passed, msg)
        return passed
    except Exception as e:
        print_status("Data Loading", False, str(e))
        return False


def test_retrieval():
    """Test if retrieval system works."""
    try:
        from data_loader import DataLoader
        from retriever import Retriever
        base_path = Path(__file__).parent
        
        # Load data
        loader = DataLoader(
            str(base_path / 'Pharma_Clinical_Trial_AllDrugs.xlsx'),
            str(base_path / 'Pharma_Clinical_Trial_Notes.docx')
        )
        excel_df, doc_chunks, excel_chunks = loader.load_all()
        
        # Build index
        retriever = Retriever()
        retriever.build_index(doc_chunks, excel_chunks)
        
        # Test search
        doc_results, excel_results = retriever.search("What's the dose for Metformin?")
        
        passed = len(doc_results) > 0 or len(excel_results) > 0
        msg = f"Retrieved {len(doc_results)} doc results, {len(excel_results)} excel results"
        print_status("Retrieval System", passed, msg)
        return passed
    except Exception as e:
        print_status("Retrieval System", False, str(e))
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Clinical Trial Query Chatbot - System Test")
    print("=" * 60)
    print()
    
    print("1. Checking Python Environment...")
    print("-" * 60)
    python_ok = check_python_version()
    print()
    
    print("2. Checking Dependencies...")
    print("-" * 60)
    deps_ok = check_dependencies()
    print()
    
    print("3. Checking Data Files...")
    print("-" * 60)
    data_ok = check_data_files()
    print()
    
    print("4. Checking Custom Modules...")
    print("-" * 60)
    modules_ok = check_modules()
    print()
    
    if python_ok and deps_ok and data_ok and modules_ok:
        print("5. Testing Data Loading...")
        print("-" * 60)
        loading_ok = test_data_loading()
        print()
        
        print("6. Testing Retrieval System...")
        print("-" * 60)
        retrieval_ok = test_retrieval()
        print()
    else:
        loading_ok = False
        retrieval_ok = False
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_tests = [
        ("Python Version", python_ok),
        ("Dependencies", deps_ok),
        ("Data Files", data_ok),
        ("Custom Modules", modules_ok),
        ("Data Loading", loading_ok),
        ("Retrieval System", retrieval_ok)
    ]
    
    passed = sum(1 for _, ok in all_tests if ok)
    total = len(all_tests)
    
    for name, ok in all_tests:
        status = "✅" if ok else "❌"
        print(f"{status} {name}")
    
    print()
    print(f"TOTAL: {passed}/{total} tests passed")
    print()
    
    if passed == total:
        print("🎉 All systems operational! You're ready to launch the chatbot.")
        print("   Run: python app.py (backend) and python ui.py (frontend)")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above before launching.")
        print("   Tip: Run 'pip install -r requirements.txt' to install dependencies")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
