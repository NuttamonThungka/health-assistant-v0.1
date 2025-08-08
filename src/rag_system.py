"""
Simple RAG Pipeline for Agnos Health Forum Chatbot
Simplified version to avoid Pydantic compatibility issues
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    from langchain_openai import OpenAIEmbeddings, ChatOpenAI
    from langchain_community.vectorstores import FAISS
    from langchain.schema import Document
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError as e:
    raise ImportError(f"Required LangChain libraries not found: {e}")

class SimpleAgnosHealthRAG:
    def __init__(self, data_path: str = "../forum_data.jsonl", openai_api_key: Optional[str] = None):
        """Simple RAG initialization"""
        self.data_path = data_path
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        self.vector_store = None
        self.chat_history = []
        
        # Initialize components with proper configuration
        # Set API key as environment variable to avoid proxy issues
        os.environ["OPENAI_API_KEY"] = self.openai_api_key
        
        # Get model configuration from environment or use defaults
        model_name = os.getenv('LLM_MODEL', 'gpt-4o-mini')
        temperature = float(os.getenv('TEMPERATURE', '0.7'))
        
        # Initialize without passing api_key directly to avoid proxy parameter issues
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(
            temperature=temperature,
            model_name=model_name  # Using GPT-4 Turbo for better performance and cost efficiency
        )
        
    def load_documents(self) -> List[Document]:
        """Load forum data from JSONL file"""
        documents = []
        
        if not os.path.exists(self.data_path):
            print(f"⚠️ Data file not found: {self.data_path}")
            return documents
            
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if data.get('content') and data.get('title'):
                            # Create main document for patient question
                            doc = Document(
                                page_content=f"Title: {data['title']}\\n\\nContent: {data['content']}",
                                metadata={
                                    'title': data.get('title', ''),
                                    'url': data.get('url', ''),
                                    'date': data.get('date', ''),
                                    'tags': data.get('tags', ''),
                                    'source': 'agnos_health_forum',
                                    'content_type': 'question'
                                }
                            )
                            documents.append(doc)
                            
                            # Process doctor comments as separate expert documents
                            doctor_comments = data.get('doctor_comments', [])
                            for i, comment in enumerate(doctor_comments):
                                # Handle both old format (dict) and new format (string)
                                if isinstance(comment, dict):
                                    # Old format with full metadata
                                    content_text = comment.get('content_text', '')
                                    doctor_user = comment.get('user', {})
                                    doctor_name = f"{doctor_user.get('prefix_name', '')} {doctor_user.get('firstname', '')} {doctor_user.get('lastname', '')}".strip()
                                    pub_date = comment.get('pub_date', '')
                                    likes = comment.get('sum_likes', 0)
                                elif isinstance(comment, str):
                                    # New simplified format (just content_text string)
                                    content_text = comment
                                    doctor_name = "แพทย์ผู้เชี่ยวชาญ"  # Generic doctor name
                                    pub_date = ''
                                    likes = 0
                                else:
                                    continue
                                
                                if content_text and len(content_text.strip()) > 10:
                                    doctor_doc = Document(
                                        page_content=f"Patient Question: {data['title']}\\n\\nDoctor's Expert Answer ({doctor_name}): {content_text}",
                                        metadata={
                                            'title': data.get('title', ''),
                                            'url': data.get('url', ''),
                                            'date': pub_date,
                                            'doctor_name': doctor_name,
                                            'doctor_prefix': doctor_name.split()[0] if doctor_name else '',
                                            'likes': likes,
                                            'source': 'agnos_health_forum',
                                            'content_type': 'doctor_answer'
                                        }
                                    )
                                    documents.append(doctor_doc)
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            print(f"Error loading documents: {e}")
            
        return documents
    
    def create_vector_store(self, force_recreate: bool = False):
        """Create or load vector store"""
        vector_store_path = "./data/vector_store"
        
        if os.path.exists(vector_store_path) and not force_recreate:
            try:
                self.vector_store = FAISS.load_local(
                    vector_store_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
                print("✅ Vector store loaded successfully")
                return
            except Exception as e:
                print(f"Failed to load existing vector store: {e}")
        
        # Create new vector store
        documents = self.load_documents()
        if not documents:
            print("⚠️ No documents found, creating empty vector store")
            # Create a dummy document to initialize the vector store
            dummy_doc = Document(page_content="Placeholder", metadata={})
            self.vector_store = FAISS.from_documents([dummy_doc], self.embeddings)
        else:
            # Split documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\\n\\n", "\\n", " ", ""]
            )
            split_docs = text_splitter.split_documents(documents)
            
            # Create vector store
            self.vector_store = FAISS.from_documents(split_docs, self.embeddings)
        
        # Save vector store
        Path(vector_store_path).parent.mkdir(parents=True, exist_ok=True)
        self.vector_store.save_local(vector_store_path)
        print("✅ Vector store created successfully")
    
    def get_symptom_based_matches(self, question: str, k: int = 15) -> List[Document]:
        """Enhanced symptom-based matching for disease prediction"""
        # Get more initial matches for better symptom relevance
        retriever = self.vector_store.as_retriever(search_kwargs={"k": k})
        initial_docs = retriever.get_relevant_documents(question)
        
        # Separate and prioritize based on content type and relevance
        doctor_answers = []
        patient_cases = []
        
        # Extract key symptoms from user question for relevance scoring
        symptom_keywords = self._extract_symptom_keywords(question)
        
        for doc in initial_docs:
            # Calculate relevance score based on symptom matching
            relevance_score = self._calculate_symptom_relevance(doc, symptom_keywords)
            
            if doc.metadata.get('content_type') == 'doctor_answer':
                doctor_answers.append((doc, relevance_score))
            else:
                patient_cases.append((doc, relevance_score))
        
        # Sort by relevance score (higher is better)
        doctor_answers.sort(key=lambda x: x[1], reverse=True)
        patient_cases.sort(key=lambda x: x[1], reverse=True)
        
        # Return most relevant matches
        result_docs = []
        result_docs.extend([doc for doc, score in doctor_answers[:6]])
        result_docs.extend([doc for doc, score in patient_cases[:4]])
        
        return result_docs
    
    def _extract_symptom_keywords(self, question: str) -> List[str]:
        """Extract symptom-related keywords from user question"""
        # Common Thai symptom keywords
        symptom_patterns = [
            'ปวด', 'เจ็บ', 'นอนไม่หลับ', 'นอนหลับยาก', 'เครียด', 'วิตก', 'กังวล',
            'ซึมเศร้า', 'เศร้า', 'เบื่อ', 'อ่อนเพลีย', 'เหนื่อย', 'คลื่นไส้', 'อาเจียน',
            'ท้องเสียถ่ายเป็นเลือด', 'ท้องผูก', 'ปวดหัว', 'ไข้', 'ไอ', 'จาม',
            'ผื่น', 'คัน', 'บวม', 'ปวดประจำเดือน', 'ประจำเดือนไม่มา', 'หัวใจเต้นแรง',
            'หายใจลำบาก', 'เจ็บหน้าอก', 'มึนงง', 'วิงเวียน', 'ตาพร่ามัว'
        ]
        
        found_symptoms = []
        question_lower = question.lower()
        
        for symptom in symptom_patterns:
            if symptom in question_lower:
                found_symptoms.append(symptom)
        
        return found_symptoms
    
    def _calculate_symptom_relevance(self, doc: Document, user_symptoms: List[str]) -> float:
        """Calculate relevance score based on symptom matching"""
        if not user_symptoms:
            return 0.5  # Default relevance
        
        doc_content = doc.page_content.lower()
        doc_title = doc.metadata.get('title', '').lower()
        
        # Count symptom matches in content and title
        content_matches = sum(1 for symptom in user_symptoms if symptom in doc_content)
        title_matches = sum(1 for symptom in user_symptoms if symptom in doc_title)
        
        # Title matches are weighted more heavily
        relevance_score = (content_matches * 1.0) + (title_matches * 2.0)
        
        # Normalize by number of user symptoms
        if len(user_symptoms) > 0:
            relevance_score = relevance_score / len(user_symptoms)
        
        # Bonus for doctor answers
        if doc.metadata.get('content_type') == 'doctor_answer':
            relevance_score += 0.3
        
        # Bonus for high engagement (likes)
        likes = doc.metadata.get('likes', 0)
        if likes > 0:
            relevance_score += min(likes * 0.1, 0.5)  # Max bonus of 0.5
        
        return min(relevance_score, 3.0)  # Cap at 3.0

    def extract_disease_predictions(self, relevant_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract disease predictions from matched forum cases"""
        diseases = []
        seen_diseases = set()
        
        for doc in relevant_docs:
            title = doc.metadata.get('title', '')
            url = doc.metadata.get('url', '')
            
            # Skip if no title or URL
            if not title or not url:
                continue
            
            # Extract disease from title - use the exact title if it contains disease info
            disease_name = None
            title_lower = title.lower()
            
            # Direct title matching (prefer using the actual title)
            if 'ซึมเศร้า' in title_lower or 'depression' in title_lower:
                disease_name = title  # Use full title for better context
            elif 'วิตกกังวล' in title_lower or 'anxiety' in title_lower:
                disease_name = title
            elif 'นอนไม่หลับ' in title_lower or 'insomnia' in title_lower:
                disease_name = title
            elif 'ปวดประจำเดือน' in title_lower or 'menstrual' in title_lower or 'dysmenorrhea' in title_lower:
                disease_name = title
            elif 'เครียด' in title_lower or 'stress' in title_lower:
                disease_name = title
            elif 'ปรับตัว' in title_lower or 'adjustment' in title_lower:
                disease_name = title
            elif 'โรค' in title:
                disease_name = title  # Any disease-related title
            
            if disease_name and disease_name not in seen_diseases:
                diseases.append({
                    'disease_name': disease_name,  # Use full title as disease name
                    'forum_title': title,
                    'forum_url': url,
                    'relevance_score': 1.0
                })
                seen_diseases.add(disease_name)
        
        return diseases[:3]  # Top 3 disease predictions

    def get_historical_doctor_comments(self, relevant_docs: List[Document]) -> List[Dict[str, Any]]:
        """Extract historical doctor comments from similar cases"""
        doctor_history = []
        
        for doc in relevant_docs:
            if doc.metadata.get('content_type') == 'doctor_answer':
                doctor_name = doc.metadata.get('doctor_name', 'แพทย์ผู้เชี่ยวชาญ')
                doctor_prefix = doc.metadata.get('doctor_prefix', 'นพ.')
                content = doc.page_content
                
                # Extract just the doctor's response
                if "Doctor's Expert Answer" in content:
                    doctor_response = content.split("Doctor's Expert Answer")[1].strip()
                    if doctor_response.startswith("(") and "):" in doctor_response:
                        doctor_response = doctor_response.split("):", 1)[1].strip()
                else:
                    doctor_response = content
                
                # Clean up the response
                doctor_response = doctor_response.replace("\\n", " ").strip()
                
                if len(doctor_response) > 20:  # Filter out very short responses
                    doctor_history.append({
                        'doctor_name': doctor_name,
                        'doctor_prefix': doctor_prefix,
                        'response': doctor_response[:300],  # Limit length
                        'forum_title': doc.metadata.get('title', ''),
                        'forum_url': doc.metadata.get('url', ''),
                        'likes': doc.metadata.get('likes', 0)
                    })
        
        # Sort by likes (most helpful first)
        doctor_history.sort(key=lambda x: x['likes'], reverse=True)
        return doctor_history[:3]  # Top 3 doctor responses

    def query(self, question: str) -> Dict[str, Any]:
        """Enhanced query with symptom-based disease prediction"""
        try:
            if not self.vector_store:
                return {
                    'success': False,
                    'error': 'Vector store not initialized'
                }
            
            # Get symptom-based matches
            relevant_docs = self.get_symptom_based_matches(question, k=10)
            
            # Extract disease predictions
            disease_predictions = self.extract_disease_predictions(relevant_docs)
            
            # Get historical doctor comments
            doctor_history = self.get_historical_doctor_comments(relevant_docs)
            
            # Separate current context
            current_doctor_insights = []
            similar_cases = []
            
            for doc in relevant_docs[:5]:
                if doc.metadata.get('content_type') == 'doctor_answer':
                    doctor_name = doc.metadata.get('doctor_name', 'แพทย์')
                    content = doc.page_content.split("Doctor's Expert Answer")[1] if "Doctor's Expert Answer" in doc.page_content else doc.page_content
                    current_doctor_insights.append(f"🩺 {doctor_name}: {content[:200]}...")
                else:
                    similar_cases.append(doc.page_content[:300])
            
            # Prepare enhanced context for disease prediction
            disease_context = ""
            if disease_predictions:
                disease_context = "โรคที่อาจเป็นได้จากอาการที่คล้ายกัน:\\n"
                for i, disease in enumerate(disease_predictions, 1):
                    disease_context += f"{i}. {disease['disease_name']} (จากกรณี: {disease['forum_title']})\\n"
            
            historical_context = ""
            if doctor_history:
                historical_context = "ประสบการณ์แพทย์จากกรณีคล้ายกัน:\\n"
                for i, history in enumerate(doctor_history, 1):
                    historical_context += f"{i}. {history['doctor_prefix']} {history['doctor_name']}: {history['response'][:150]}...\\n"
            
            # Prepare chat history
            chat_history_text = "\\n".join([
                f"User: {msg['user']}\\nAssistant: {msg['assistant']}" 
                for msg in self.chat_history[-3:]  # Last 3 exchanges
            ])
            
            # Prepare forum references with URLs
            forum_references = ""
            if disease_predictions or doctor_history:
                forum_references = "\nแหล่งอ้างอิงจากฟอรั่ม Agnos Health:\n"
                
                # Add disease prediction references
                ref_count = 1
                seen_urls = set()
                
                for disease in disease_predictions:
                    if disease.get('forum_url') and disease['forum_url'] not in seen_urls:
                        forum_references += f"{ref_count}. {disease['forum_title']}\n"
                        forum_references += f"   🔗 {disease['forum_url']}\n"
                        seen_urls.add(disease['forum_url'])
                        ref_count += 1
                
                # Add doctor history references
                for history in doctor_history:
                    if history.get('forum_url') and history['forum_url'] not in seen_urls:
                        forum_references += f"{ref_count}. {history['forum_title']}\n"
                        forum_references += f"   🔗 {history['forum_url']}\n"
                        seen_urls.add(history['forum_url'])
                        ref_count += 1
                        if ref_count > 5:  # Limit references
                            break

            # Prepare components for the prompt (avoiding backslashes in f-strings)
            newline = "\n"
            current_insights_text = newline.join(current_doctor_insights[:2]) if current_doctor_insights else ""
            similar_cases_text = newline.join(similar_cases[:2]) if similar_cases else ""

            # Create enhanced prompt for symptom-based prediction
            prompt = f"""คุณเป็นผู้ช่วยให้คำปรึกษาสุขภาพที่มีความเชี่ยวชาญจากฟอรั่ม Agnos Health

เมื่อผู้ใช้บอกอาการ ให้:
1. วิเคราะห์อาการและคาดการณ์โรคที่อาจเป็น
2. อ้างอิงจากกรณีในฐานข้อมูลและคำตอบแพทย์
3. แนะนำการดูแลเบื้องต้นและการหาหมอ
4. ห้ามสร้างแหล่งอ้างอิงเอง - จะเพิ่มให้ภายหลัง

{disease_context}

{historical_context}

คำแนะนำปัจจุบัน:
{current_insights_text}

กรณีคล้ายกัน:
{similar_cases_text}

ประวัติการสนทนา:
{chat_history_text}

คำถาม: {question}

ตอบแบบเป็นมิตรและให้ข้อมูลครบถ้วน อย่าสร้างส่วนแหล่งอ้างอิงเอง:"""
            
            # Get response
            response = self.llm.invoke(prompt)
            answer = response.content if hasattr(response, 'content') else str(response)
            
            # Add to chat history
            self.chat_history.append({
                'user': question,
                'assistant': answer
            })
            
            # Keep only last 10 exchanges
            if len(self.chat_history) > 10:
                self.chat_history = self.chat_history[-10:]
            
            # Prepare enhanced sources with disease predictions
            sources = []
            for doc in relevant_docs[:5]:
                if doc.metadata:
                    sources.append({
                        'title': doc.metadata.get('title', 'ไม่ระบุ'),
                        'url': doc.metadata.get('url', ''),
                        'date': doc.metadata.get('date', ''),
                        'tags': doc.metadata.get('tags', ''),
                        'content_type': doc.metadata.get('content_type', 'question')
                    })
            
            # Always add forum references (replace any existing ones)
            if disease_predictions or doctor_history:
                # Remove any existing reference sections that might be incomplete
                if "แหล่งอ้างอิง" in answer:
                    # Split at the reference section and take only the content before it
                    parts = answer.split("แหล่งอ้างอิง")
                    answer = parts[0].rstrip()
                
                # Always add our properly formatted references
                reference_text = "\n\n📚 **แหล่งอ้างอิงจากฟอรั่ม Agnos Health:**\n"
                
                ref_count = 1
                seen_urls = set()
                
                # Add disease prediction references
                for disease in disease_predictions:
                    if disease.get('forum_url') and disease['forum_url'] not in seen_urls:
                        reference_text += f"{ref_count}. {disease['forum_title']}\n"
                        reference_text += f"   🔗 {disease['forum_url']}\n\n"
                        seen_urls.add(disease['forum_url'])
                        ref_count += 1
                
                # Add doctor history references  
                for history in doctor_history:
                    if history.get('forum_url') and history['forum_url'] not in seen_urls and ref_count <= 5:
                        reference_text += f"{ref_count}. {history['forum_title']}\n"
                        reference_text += f"   🔗 {history['forum_url']}\n\n"
                        seen_urls.add(history['forum_url'])
                        ref_count += 1
                
                answer += reference_text

            return {
                'success': True,
                'answer': answer,
                'sources': sources,
                'disease_predictions': disease_predictions,
                'doctor_history': doctor_history,
                'matched_cases': len(relevant_docs),
                'symptom_relevance_used': True
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def clear_memory(self):
        """Clear chat history"""
        self.chat_history = []
        
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            'total_documents': self.vector_store.index.ntotal if self.vector_store else 0,
            'total_threads': 0,
            'unique_conditions': 0,
            'date_range': {'earliest': 'N/A', 'latest': 'N/A'}
        }

def initialize_simple_rag_system(data_path: str = "../forum_data.jsonl", 
                                openai_api_key: Optional[str] = None,
                                force_recreate: bool = False) -> SimpleAgnosHealthRAG:
    """Initialize the simple RAG system"""
    try:
        print("🚀 Initializing Simple Agnos Health RAG System...")
        print("=" * 50)
        
        # Create RAG instance
        rag_system = SimpleAgnosHealthRAG(
            data_path=data_path,
            openai_api_key=openai_api_key
        )
        
        # Create vector store
        rag_system.create_vector_store(force_recreate=force_recreate)
        
        # Get statistics
        stats = rag_system.get_statistics()
        print(f"📊 Data Statistics:")
        print(f"  • Total documents: {stats.get('total_documents', 0)}")
        print(f"  • Unique threads: {stats.get('total_threads', 0)}")
        print(f"  • Medical conditions: {stats.get('unique_conditions', 0)}")
        
        print("✅ Simple RAG System Ready!")
        print("=" * 50)
        
        return rag_system
        
    except Exception as e:
        print(f"❌ Failed to initialize RAG system: {str(e)}")
        raise