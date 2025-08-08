#!/usr/bin/env python3
"""
System test script for Agnos Health Assistant
Tests all major components
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from src.config import Config
        print("  ✅ Config module")
    except ImportError as e:
        print(f"  ❌ Config module: {e}")
        return False
    
    try:
        from src.scraper import AgnosForumScraper
        print("  ✅ Scraper module")
    except ImportError as e:
        print(f"  ❌ Scraper module: {e}")
        return False
    
    try:
        from src.rag_system import SimpleAgnosHealthRAG, initialize_simple_rag_system
        print("  ✅ RAG system module")
    except ImportError as e:
        print(f"  ❌ RAG system module: {e}")
        return False
    
    return True

def test_configuration():
    """Test configuration"""
    print("\n🧪 Testing configuration...")
    
    from src.config import Config
    
    tests = [
        ('OpenAI API Key', Config.OPENAI_API_KEY and Config.OPENAI_API_KEY != 'sk-your-api-key-here'),
        ('Data directory', Path(Config.DATA_DIR).exists()),
        ('Vector store directory', Path(Config.VECTOR_STORE_PATH).exists()),
    ]
    
    all_passed = True
    for test_name, result in tests:
        if result:
            print(f"  ✅ {test_name}")
        else:
            print(f"  ❌ {test_name}")
            all_passed = False
    
    return all_passed

def test_data_files():
    """Test data files"""
    print("\n🧪 Testing data files...")
    
    from src.config import Config
    
    data_file = Path(Config.DATA_PATH)
    if data_file.exists():
        # Count lines in data file
        with open(data_file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        print(f"  ✅ Forum data file exists ({line_count} threads)")
    else:
        print(f"  ⚠️  Forum data file not found")
        print(f"     Run 'python scripts/update_data.py' to scrape data")
        return False
    
    # Check vector store
    vector_files = list(Path(Config.VECTOR_STORE_PATH).glob('*.faiss'))
    if vector_files:
        print(f"  ✅ Vector store exists ({len(vector_files)} index files)")
    else:
        print(f"  ⚠️  Vector store not initialized")
        print(f"     Will be created when you first run the chatbot")
    
    return True

def test_rag_system():
    """Test RAG system"""
    print("\n🧪 Testing RAG system...")
    
    from src.config import Config
    
    if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == 'sk-your-api-key-here':
        print("  ⏭️  Skipping RAG test (no API key configured)")
        return True
    
    if not Path(Config.DATA_PATH).exists():
        print("  ⏭️  Skipping RAG test (no data available)")
        return True
    
    try:
        from src.rag_system import initialize_simple_rag_system
        
        print("  🔄 Initializing RAG system...")
        rag_system = initialize_simple_rag_system(
            data_path=Config.DATA_PATH,
            openai_api_key=Config.OPENAI_API_KEY,
            force_recreate=False
        )
        
        print("  🔄 Running test query...")
        response = rag_system.query("อาการปวดหัว")
        
        if response['success']:
            print("  ✅ RAG system working")
            print(f"     Response length: {len(response['answer'])} characters")
            if response.get('sources'):
                print(f"     Sources found: {len(response['sources'])}")
        else:
            print(f"  ❌ RAG system error: {response.get('error')}")
            return False
            
    except Exception as e:
        print(f"  ❌ RAG system error: {e}")
        return False
    
    return True

def test_streamlit():
    """Test Streamlit installation"""
    print("\n🧪 Testing Streamlit...")
    
    try:
        import streamlit
        version = streamlit.__version__
        print(f"  ✅ Streamlit installed (v{version})")
    except ImportError:
        print("  ❌ Streamlit not installed")
        print("     Run: pip install streamlit")
        return False
    
    # Check if app file exists
    app_file = Path("streamlit_app/app.py")
    if app_file.exists():
        print(f"  ✅ Streamlit app file exists")
    else:
        print(f"  ❌ Streamlit app file not found")
        return False
    
    return True

def main():
    """Main test function"""
    print("""
    ╔═══════════════════════════════════════════════╗
    ║     🏥 Agnos Health Assistant Tests          ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Data Files", test_data_files),
        ("RAG System", test_rag_system),
        ("Streamlit", test_streamlit),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("📊 Test Summary:")
    print("-"*50)
    
    passed = 0
    failed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-"*50)
    print(f"Total: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\nRun the application with:")
        print("  streamlit run streamlit_app/app.py")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)