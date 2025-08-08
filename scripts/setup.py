#!/usr/bin/env python3
"""
Setup script for Agnos Health Assistant
Initializes the system and downloads required data
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_environment():
    """Set up the environment"""
    print("🔧 Setting up Agnos Health Assistant v0.1...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file from template...")
        env_example = Path(".env.example")
        if env_example.exists():
            env_file.write_text(env_example.read_text())
            print("⚠️  Please edit .env and add your OpenAI API key")
        else:
            print("❌ .env.example not found")
            sys.exit(1)
    else:
        print("✅ .env file exists")
    
    # Create data directories
    print("📁 Creating data directories...")
    directories = [
        "data",
        "data/vector_store",
        "data/metadata",
        "logs",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created {directory}/")
    
    # Check OpenAI API key
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'sk-your-api-key-here':
        print("\n⚠️  WARNING: OpenAI API key not configured!")
        print("Please edit .env and add your actual API key")
        print("Get your API key from: https://platform.openai.com/api-keys")
    else:
        print("✅ OpenAI API key configured")
    
    return True

def initial_scrape():
    """Run initial data scraping"""
    from src.scraper import AgnosForumScraper
    from src.config import Config
    
    response = input("\n🌐 Do you want to scrape initial forum data? (y/n): ")
    if response.lower() != 'y':
        print("⏭️  Skipping initial scrape")
        return
    
    print("\n🕷️ Starting initial forum scrape...")
    print("This may take 5-10 minutes...")
    
    try:
        scraper = AgnosForumScraper(
            base_url=Config.BASE_URL,
            output_file=Config.DATA_PATH,
            max_threads=20  # Start with fewer threads for initial setup
        )
        
        scraper.run(mode='full')
        print("✅ Initial scraping completed!")
        
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        print("You can run the scraper later with: python scripts/update_data.py")

def initialize_rag():
    """Initialize the RAG system"""
    from src.config import Config
    
    if not Path(Config.DATA_PATH).exists():
        print("\n⚠️  No forum data found. Skipping RAG initialization.")
        print("Run 'python scripts/update_data.py' to scrape data first.")
        return
    
    print("\n🤖 Initializing RAG system...")
    
    try:
        from src.rag_system import initialize_simple_rag_system
        
        rag_system = initialize_simple_rag_system(
            data_path=Config.DATA_PATH,
            openai_api_key=Config.OPENAI_API_KEY,
            force_recreate=True
        )
        
        print("✅ RAG system initialized successfully!")
        
        # Test the system
        print("\n🧪 Testing the system...")
        response = rag_system.query("สวัสดี")
        if response['success']:
            print("✅ System test passed!")
        else:
            print(f"⚠️  System test failed: {response.get('error')}")
            
    except Exception as e:
        print(f"❌ RAG initialization failed: {e}")
        print("Please check your OpenAI API key and try again.")

def main():
    """Main setup function"""
    print("""
    ╔═══════════════════════════════════════════════╗
    ║     🏥 Agnos Health Assistant Setup v0.1      ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Run initial scrape
    initial_scrape()
    
    # Initialize RAG system
    initialize_rag()
    
    print("\n" + "="*50)
    print("✅ Setup completed successfully!")
    print("\n📚 Next steps:")
    print("1. Edit .env file if you haven't added your OpenAI API key")
    print("2. Run the application: streamlit run streamlit_app/app.py")
    print("3. Access the app at: http://localhost:8501")
    print("\n💡 Useful commands:")
    print("  - Update data: python scripts/update_data.py")
    print("  - Run tests: python scripts/test_system.py")
    print("  - View help: python scripts/setup.py --help")
    print("="*50)

if __name__ == "__main__":
    main()