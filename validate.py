#!/usr/bin/env python3
"""
Final validation script for Agnos Health Assistant v0.1
Ensures the project is complete and self-contained
"""

import os
import sys
import json
from pathlib import Path

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def check_mark(passed):
    return f"{GREEN}✅{RESET}" if passed else f"{RED}❌{RESET}"

def validate_structure():
    """Validate project structure"""
    print("\n🔍 Validating Project Structure...")
    
    required_dirs = [
        "streamlit_app",
        "streamlit_app/pages",
        "src",
        "scripts",
        "data",
        "data/vector_store",
        "data/metadata"
    ]
    
    required_files = [
        "README.md",
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "LICENSE",
        "run.sh",
        "streamlit_app/app.py",
        "streamlit_app/pages/1_📊_Data_Management.py",
        "src/__init__.py",
        "src/config.py",
        "src/scraper.py",
        "src/rag_system.py",
        "scripts/setup.py",
        "scripts/update_data.py",
        "scripts/test_system.py"
    ]
    
    all_good = True
    
    print("\n📁 Required Directories:")
    for dir_path in required_dirs:
        exists = Path(dir_path).exists()
        print(f"  {check_mark(exists)} {dir_path}")
        if not exists:
            all_good = False
    
    print("\n📄 Required Files:")
    for file_path in required_files:
        exists = Path(file_path).exists()
        print(f"  {check_mark(exists)} {file_path}")
        if not exists:
            all_good = False
    
    return all_good

def validate_data():
    """Validate data files"""
    print("\n🔍 Validating Data Files...")
    
    data_file = Path("data/forum_data.jsonl")
    vector_store = Path("data/vector_store/index.faiss")
    
    checks = []
    
    if data_file.exists():
        # Count threads
        with open(data_file, 'r', encoding='utf-8') as f:
            thread_count = sum(1 for _ in f)
        print(f"  {check_mark(True)} Forum data: {thread_count} threads")
        checks.append(True)
    else:
        print(f"  {check_mark(False)} Forum data: Not found")
        checks.append(False)
    
    if vector_store.exists():
        size_kb = vector_store.stat().st_size / 1024
        print(f"  {check_mark(True)} Vector store: {size_kb:.1f} KB")
        checks.append(True)
    else:
        print(f"  {check_mark(False)} Vector store: Not found")
        checks.append(False)
    
    return all(checks)

def validate_imports():
    """Validate Python imports"""
    print("\n🔍 Validating Python Imports...")
    
    imports_to_test = [
        ("streamlit", "Streamlit"),
        ("pandas", "Pandas"),
        ("plotly", "Plotly"),
        ("openai", "OpenAI"),
        ("langchain", "LangChain"),
        ("faiss", "FAISS"),
        ("dotenv", "Python-dotenv"),
        ("bs4", "BeautifulSoup"),
        ("requests", "Requests")
    ]
    
    all_good = True
    for module, name in imports_to_test:
        try:
            __import__(module)
            print(f"  {check_mark(True)} {name}")
        except ImportError:
            print(f"  {check_mark(False)} {name} - Run: pip install -r requirements.txt")
            all_good = False
    
    return all_good

def validate_modules():
    """Validate project modules"""
    print("\n🔍 Validating Project Modules...")
    
    sys.path.insert(0, os.getcwd())
    
    modules_to_test = [
        ("src.config", "Config"),
        ("src.scraper", "Scraper"),
        ("src.rag_system", "RAG System")
    ]
    
    all_good = True
    for module, name in modules_to_test:
        try:
            __import__(module)
            print(f"  {check_mark(True)} {name}")
        except Exception as e:
            print(f"  {check_mark(False)} {name}: {e}")
            all_good = False
    
    return all_good

def validate_env():
    """Validate environment configuration"""
    print("\n🔍 Validating Environment...")
    
    env_exists = Path(".env").exists()
    env_example_exists = Path(".env.example").exists()
    
    print(f"  {check_mark(env_example_exists)} .env.example template")
    
    if env_exists:
        # Check for API key
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key and api_key != 'sk-your-api-key-here':
            print(f"  {check_mark(True)} .env file configured")
            print(f"  {check_mark(True)} OpenAI API key set")
            return True
        else:
            print(f"  {check_mark(True)} .env file exists")
            print(f"  {YELLOW}⚠️{RESET}  OpenAI API key not configured")
            return False
    else:
        print(f"  {YELLOW}⚠️{RESET}  .env file not found (copy from .env.example)")
        return False

def main():
    """Main validation"""
    print("""
╔═══════════════════════════════════════════════════╗
║   🏥 Agnos Health Assistant v0.1 Validation      ║
╚═══════════════════════════════════════════════════╝
    """)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    results = {
        "Structure": validate_structure(),
        "Data Files": validate_data(),
        "Python Imports": validate_imports(),
        "Project Modules": validate_modules(),
        "Environment": validate_env()
    }
    
    # Summary
    print("\n" + "="*50)
    print("📊 VALIDATION SUMMARY")
    print("="*50)
    
    for check, passed in results.items():
        status = f"{GREEN}PASSED{RESET}" if passed else f"{RED}FAILED{RESET}"
        print(f"{check:20} {status}")
    
    all_passed = all(results.values())
    
    print("="*50)
    
    if all_passed:
        print(f"\n{GREEN}🎉 SUCCESS! Project is complete and self-contained.{RESET}")
        print("\nYou can now:")
        print("1. Run the app: ./run.sh")
        print("2. Or: streamlit run streamlit_app/app.py")
        print("3. Commit to GitHub: git init && git add . && git commit")
    else:
        print(f"\n{YELLOW}⚠️  Some checks failed. Please review the issues above.{RESET}")
        print("\nQuick fixes:")
        if not results["Python Imports"]:
            print("  - Install dependencies: pip install -r requirements.txt")
        if not results["Environment"]:
            print("  - Configure API key: cp .env.example .env && edit .env")
        if not results["Data Files"]:
            print("  - Initialize data: python scripts/setup.py")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())