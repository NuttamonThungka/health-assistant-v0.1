"""
Configuration settings for Agnos Health Assistant
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # OpenAI Settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4-turbo-preview')
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '2000'))
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
    
    # Scraping Settings
    BASE_URL = os.getenv('BASE_URL', 'https://www.agnoshealth.com/forums')
    MAX_THREADS = int(os.getenv('MAX_THREADS', '50'))
    SCRAPE_DELAY = float(os.getenv('SCRAPE_DELAY', '1.0'))
    
    # RAG Settings
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000'))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '100'))
    TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', '5'))
    
    # Data Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    DATA_PATH = os.path.join(DATA_DIR, 'forum_data.jsonl')
    VECTOR_STORE_PATH = os.path.join(DATA_DIR, 'vector_store')
    METADATA_PATH = os.path.join(DATA_DIR, 'metadata')
    
    # Streamlit Settings
    STREAMLIT_SERVER_PORT = int(os.getenv('STREAMLIT_SERVER_PORT', '8501'))
    STREAMLIT_SERVER_ADDRESS = os.getenv('STREAMLIT_SERVER_ADDRESS', 'localhost')
    
    # Feature Flags
    ENABLE_ANALYTICS = os.getenv('ENABLE_ANALYTICS', 'true').lower() == 'true'
    ENABLE_UPDATES = os.getenv('ENABLE_UPDATES', 'true').lower() == 'true'
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required. Please set it in your .env file")
        
        # Create directories if they don't exist
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.VECTOR_STORE_PATH, exist_ok=True)
        os.makedirs(cls.METADATA_PATH, exist_ok=True)
        
        return True

# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")