# 🏥 health-assistant-v0.1

An AI-powered health consultation system that combines web scraping, RAG (Retrieval-Augmented Generation), and a user-friendly Streamlit interface to provide intelligent health advice based on real doctor responses from Agnos Health forums.

## 🌟 Features

- **🔍 Intelligent Web Scraping**: Automatically scrapes and processes health forum data with doctor responses
- **🤖 RAG-Powered Chatbot**: Uses GPT-4 with vector search for accurate, context-aware responses
- **📊 Data Analytics Dashboard**: Visualize health trends, disease distributions, and forum activity
- **🩺 Doctor Insights**: Leverages real medical expert responses from forums
- **🔄 Incremental Updates**: Smart update system that only fetches new content
- **🌐 Bilingual Support**: Full Thai and English language support

## 📦 Key Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.11.x | Runtime environment |
| Streamlit | 1.39.0 | Web application framework |
| OpenAI | 1.99.4 | GPT-4 API client |
| LangChain | 0.2.12 | RAG orchestration |
| LangChain-OpenAI | 0.3.28 | OpenAI integration |
| FAISS | 1.8.0 | Vector similarity search |
| BeautifulSoup4 | 4.12.3 | Web scraping |
| Pandas | 2.2.2 | Data manipulation |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│                   (Streamlit Web Application)                │
├─────────────────────────────────────────────────────────────┤
│                         API Layer                            │
│                    (FastAPI - Optional)                      │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Scraper    │  │  RAG System  │  │   Analytics  │     │
│  │   Module     │  │    Module    │  │    Module    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                      Data Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Forum Data  │  │Vector Store  │  │   Metadata   │     │
│  │   (JSONL)    │  │   (FAISS)    │  │    (JSON)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
├─────────────────────────────────────────────────────────────┤
│                    External Services                         │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  OpenAI API  │  │ Agnos Health │                        │
│  │    (GPT-4)   │  │    Forums    │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Pipeline

```
1. Web Scraping Pipeline:
   Agnos Forums → Scraper → Data Processing → JSONL Storage
                              ↓
                     Doctor Comments Extraction
                              ↓
                         Metadata Generation

2. RAG Pipeline:
   User Query → Embedding → Vector Search → Context Retrieval
                                              ↓
                                     GPT-4 Generation
                                              ↓
                                     Enhanced Response
                                              ↓
                                     Forum References

3. Analytics Pipeline:
   Forum Data → Aggregation → Statistical Analysis
                                  ↓
                          Visualization Generation
                                  ↓
                            Interactive Dashboard
```

## 📁 Project Structure

```
agnos-health-assistant-v0.1/
├── streamlit_app/           # Streamlit application
│   ├── app.py              # Main chatbot interface
│   └── pages/              # Multi-page app pages
│       └── 1_📊_Data_Management.py
├── src/                    # Source code modules
│   ├── __init__.py        # Package initialization
│   ├── config.py          # Configuration settings
│   ├── scraper.py         # Web scraping module
│   └── rag_system.py      # RAG implementation
├── data/                   # Data storage
│   ├── forum_data.jsonl   # Scraped forum data
│   ├── vector_store/      # FAISS vector database
│   └── metadata/          # Additional metadata
├── scripts/               # Utility scripts
│   ├── setup.py          # Initial setup script
│   ├── update_data.py    # Data update script
│   └── test_system.py    # System test script
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # Your configuration (git-ignored)
├── .gitignore          # Git ignore file
├── LICENSE             # MIT License
├── run.sh              # Quick launch script
├── validate.py         # Validation script
└── README.md           # This file
```

## ⚡ Quick Start (5 Minutes)

For experienced developers, here's the fastest setup:

```bash
# Clone and enter directory
git clone https://github.com/yourusername/health-assistant.git && cd health-assistant-v0.1

# Setup Python 3.11 virtual environment
python3.11 -m venv venv && source venv/bin/activate

# Install dependencies
pip install --upgrade pip && pip install -r requirements.txt

# Configure API key
cp .env.example .env
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# Run the app
./venv/bin/streamlit run streamlit_app/app.py
```

## 🚀 Detailed Setup

### Prerequisites

- **Python 3.11** (Specifically tested with Python 3.11.11)
- OpenAI API key (Get one at https://platform.openai.com/api-keys)
- 2GB free disk space
- Internet connection
- macOS, Linux, or Windows with WSL2

> ⚠️ **Important**: This project requires Python 3.11. Using other versions may cause compatibility issues with LangChain and OpenAI packages.

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/health-assistant.git
cd health-assistant-v0.1
```

2. **Check Python version**
```bash
python3 --version
# If not 3.11, install it:
# macOS: brew install python@3.11
# Ubuntu/Debian: sudo apt install python3.11
# Windows: Download from python.org
```

3. **Create virtual environment with Python 3.11**
```bash
# Ensure you're using Python 3.11
python3.11 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

4. **Verify Python version in venv**
```bash
python --version
# Should show: Python 3.11.x
```

5. **Install dependencies**
```bash
# Upgrade pip first (IMPORTANT)
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# Note: If you get errors, try installing packages individually:
# pip install openai==1.99.4
# pip install langchain-openai==0.3.28
# pip install langchain-core==0.3.74
```

6. **Set up environment variables**
```bash
# Copy the example file
cp .env.example .env

# Edit .env file with your favorite editor
nano .env  # or vim, code, etc.

# Add your OpenAI API key:
# OPENAI_API_KEY=sk-your-actual-api-key-here
```

7. **Initialize the system**
```bash
# Run setup script
./venv/bin/python scripts/setup.py

# This will:
# - Verify all dependencies
# - Create necessary directories
# - Initialize the vector database
# - Load sample data
```

8. **Run the application**
```bash
# Method 1: Direct execution (RECOMMENDED)
./venv/bin/streamlit run streamlit_app/Agnos_Health_Chatbot.py

# Method 2: Using Python module
python -m streamlit run streamlit_app/Agnos_Health_Chatbot.py

# Method 3: Using the run script (auto-setup)
chmod +x run.sh
./run.sh
```

The application will open automatically in your browser at `http://localhost:8501`

> 📝 **Important Notes**: 
> - Always use `./venv/bin/streamlit` to avoid system Python conflicts
> - The first run may take a few minutes to initialize the vector database
> - Ensure your OpenAI API key has sufficient credits

## 💻 Usage

### Chatbot Interface

1. Navigate to the main page
2. Type your health-related question in Thai or English
3. View AI-generated response with:
   - Medical insights
   - Forum references
   - Doctor recommendations
4. Click suggested questions for quick queries

### Data Management

1. Navigate to the Data Management page
2. **Overview Tab**: View system statistics
3. **Visualizations Tab**: Explore data insights
4. **Dataset Tab**: Browse and search forum data
5. **Update Tab**: Fetch new forum content

### Updating Forum Data

```bash
# Update with new threads only
./venv/bin/python scripts/update_data.py --mode update

# Full refresh
./venv/bin/python scripts/update_data.py --mode full
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following settings:

```env
# Required - Get your API key from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-actual-api-key-here

# Optional Configuration
MAX_THREADS=50                          # Max forum threads to scrape
CHUNK_SIZE=1000                        # Text chunk size for embeddings
CHUNK_OVERLAP=100                      # Overlap between chunks
EMBEDDING_MODEL=text-embedding-3-small # OpenAI embedding model
LLM_MODEL=gpt-4o-mini                  # Language model (gpt-4o-mini is cost-effective)
```

> 💡 **Tips for API Key**:
> - Never commit your `.env` file to git (it's in .gitignore)
> - Use environment-specific keys for dev/prod
> - Monitor usage at https://platform.openai.com/usage

### Customization

Edit `src/config.py` to modify:
- Scraping parameters
- Model settings
- UI configurations
- Language preferences

## 📊 API Documentation

### Scraper Module

```python
from src.scraper import AgnosForumScraper

# Initialize scraper
scraper = AgnosForumScraper(
    base_url="https://www.agnoshealth.com/forums",
    max_threads=50
)

# Run scraping
scraper.run(mode='update')  # or 'full'
```

### RAG System

```python
from src.rag_system import SimpleRAGSystem

# Initialize RAG
rag = SimpleRAGSystem(
    data_path="data/forum_data.jsonl",
    openai_api_key="your-key"
)

# Query
response = rag.query("อาการปวดหัวบ่อยๆ")
```

## 🧪 Testing

Run tests with:

```bash
# All tests
pytest tests/

# Specific module
pytest tests/test_scraper.py

# With coverage
pytest --cov=src tests/
```

## 📈 Performance

- **Scraping Speed**: ~20 threads/minute
- **Query Response**: < 3 seconds
- **Vector Search**: < 500ms
- **Memory Usage**: ~500MB
- **Storage**: ~100MB for 1000 threads

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. ModuleNotFoundError: No module named 'dotenv' or other modules
**Problem**: Streamlit runs but can't find installed packages.

**Solution**: You're likely using system Python instead of venv Python.
```bash
# Always use one of these methods:
./venv/bin/streamlit run streamlit_app/app.py  # RECOMMENDED
# OR
python -m streamlit run streamlit_app/app.py    # If venv is activated
```

#### 2. Port 8501 is already in use
**Problem**: Another Streamlit instance is running.

**Solution**: Kill the existing process or use a different port.
```bash
# Kill existing process
lsof -ti:8501 | xargs kill -9

# Or use a different port
./venv/bin/streamlit run streamlit_app/app.py --server.port 8502
```

#### 3. Python version issues
**Problem**: Wrong Python version being used.

**Solution**: Ensure Python 3.11 is installed and used for venv.
```bash
# Check Python version
python3.11 --version

# Recreate venv with correct Python
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. OpenAI API key not found
**Problem**: Application can't find the API key.

**Solution**: Ensure .env file exists and contains the key.
```bash
# Check if .env exists
ls -la .env

# Create from template if missing
cp .env.example .env

# Add your API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

#### 5. Virtual environment not activated
**Problem**: Commands use system Python instead of venv.

**Solution**: Always activate venv or use full paths.
```bash
# Activate venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Or use full paths (no activation needed)
./venv/bin/python scripts/setup.py
./venv/bin/streamlit run streamlit_app/app.py
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This system is for informational purposes only and should not replace professional medical advice. Always consult with qualified healthcare providers for medical concerns.


## 🔄 Version History

- **v0.1.0** (2024-01-08)
  - Initial release
  - Core scraping functionality
  - RAG-powered chatbot
  - Data management interface
  - Thai/English support

---

Built with ❤️ for better health information access