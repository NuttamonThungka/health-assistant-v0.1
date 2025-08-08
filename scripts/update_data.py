#!/usr/bin/env python3
"""
Data update script for Agnos Health Assistant
Updates forum data with new threads
"""

import os
import sys
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.scraper import AgnosForumScraper
from src.config import Config

def update_forum_data(mode='update', max_threads=None):
    """Update forum data"""
    print(f"\n🔄 Starting data {mode}...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    try:
        # Initialize scraper
        scraper = AgnosForumScraper(
            base_url=Config.BASE_URL,
            output_file=Config.DATA_PATH,
            max_threads=max_threads or Config.MAX_THREADS,
            delay=Config.SCRAPE_DELAY
        )
        
        # Run scraping
        scraper.run(mode=mode)
        
        print("\n✅ Data update completed successfully!")
        
        # Update vector store
        response = input("\n🤖 Do you want to update the vector store? (y/n): ")
        if response.lower() == 'y':
            update_vector_store()
            
    except Exception as e:
        print(f"\n❌ Error updating data: {e}")
        sys.exit(1)

def update_vector_store():
    """Update the vector store with new data"""
    print("\n🔄 Updating vector store...")
    
    try:
        from src.rag_system import initialize_simple_rag_system
        
        # Recreate vector store with updated data
        rag_system = initialize_simple_rag_system(
            data_path=Config.DATA_PATH,
            openai_api_key=Config.OPENAI_API_KEY,
            force_recreate=True
        )
        
        print("✅ Vector store updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating vector store: {e}")
        print("You can update it later from the Streamlit app")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Update Agnos Health forum data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update with new threads only
  python scripts/update_data.py
  
  # Full refresh of all data
  python scripts/update_data.py --mode full
  
  # Update with custom thread limit
  python scripts/update_data.py --max-threads 100
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['update', 'full'],
        default='update',
        help='Update mode: update (new threads only) or full (all threads)'
    )
    
    parser.add_argument(
        '--max-threads',
        type=int,
        help='Maximum number of threads to scrape'
    )
    
    parser.add_argument(
        '--no-vector-update',
        action='store_true',
        help='Skip vector store update'
    )
    
    args = parser.parse_args()
    
    print("""
    ╔═══════════════════════════════════════════════╗
    ║     🏥 Agnos Health Data Updater             ║
    ╚═══════════════════════════════════════════════╝
    """)
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Run update
    update_forum_data(mode=args.mode, max_threads=args.max_threads)
    
    print("\n✨ All done!")

if __name__ == "__main__":
    main()