#!/usr/bin/env python3
"""
Streamlit App for Agnos Health Chatbot with Enhanced References
Main page - Chatbot Interface
"""

import streamlit as st
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import from src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the RAG system
try:
    from src.rag_system import initialize_simple_rag_system
except ImportError as e:
    st.error(f"Error importing RAG system: {e}")
    st.stop()

# Page config - Main page name
st.set_page_config(
    page_title="Agnos Health Chatbot",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'rag_system' not in st.session_state:
    st.session_state.rag_system = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'initialized' not in st.session_state:
    st.session_state.initialized = False

def initialize_system():
    """Initialize the RAG system"""
    api_key = os.getenv('OPENAI_API_KEY')
    data_path = os.getenv('DATA_PATH', '../data/forum_data.jsonl')
    
    if not api_key:
        st.error("❌ OpenAI API key not found. Please set OPENAI_API_KEY in your .env file")
        return False
    
    try:
        with st.spinner('🔄 Initializing Agnos Health RAG System...'):
            rag_system = initialize_simple_rag_system(
                data_path=data_path,
                openai_api_key=api_key,
                force_recreate=False
            )
            st.session_state.rag_system = rag_system
            st.session_state.initialized = True
            return True
    except Exception as e:
        st.error(f"❌ Failed to initialize system: {str(e)}")
        return False

def display_message(message, is_user=False):
    """Display a chat message"""
    if is_user:
        with st.chat_message("user"):
            st.write(message)
    else:
        with st.chat_message("assistant"):
            st.markdown(message)

def get_suggested_questions():
    """Get suggested questions from forum data"""
    import json
    import random
    
    suggested = []
    try:
        # Load forum data to get popular questions
        data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'forum_data.jsonl')
        with open(data_file, 'r', encoding='utf-8') as f:
            all_questions = []
            for line in f:
                try:
                    data = json.loads(line.strip())
                    # Get questions with doctor responses
                    if data.get('doctor_comments') and len(data['doctor_comments']) > 0:
                        # Extract key symptoms from content
                        content = data.get('content', '')
                        title = data.get('title', '')
                        
                        # Create suggested question based on title/content
                        if 'ซึมเศร้า' in title:
                            all_questions.append("ผมมีอาการเศร้า นอนไม่หลับ เบื่อไม่อยากทำอะไร ควรทำอย่างไร")
                        elif 'นอนไม่หลับ' in title or 'Insomnia' in title:
                            all_questions.append("นอนไม่หลับมาหลายวัน ตื่นกลางดึกบ่อย มีวิธีแก้ไขอย่างไร")
                        elif 'วิตกกังวล' in title or 'กังวล' in content:
                            all_questions.append("รู้สึกวิตกกังวล หัวใจเต้นแรง คิดมาก ควรปรึกษาหมอไหม")
                        elif 'ปวดประจำเดือน' in title:
                            all_questions.append("ปวดประจำเดือนมาก ปวดท้องน้อย มีวิธีบรรเทาอย่างไร")
                        elif 'ปัสสาวะ' in title or 'กระเพาะปัสสาวะ' in title:
                            all_questions.append("ปัสสาวะบ่อย แสบขัด อาจเป็นโรคอะไรได้บ้าง")
                        elif 'เชื้อรา' in title:
                            all_questions.append("มีตกขาวผิดปกติ คันบริเวณจุดซ่อนเร้น เป็นเชื้อราหรือไม่")
                        elif 'ตั้งครรภ์' in title:
                            all_questions.append("ประจำเดือนไม่มา กังวลว่าจะตั้งครรภ์ ควรตรวจเมื่อไหร่")
                        elif 'ปวดหัว' in title or 'ไมเกรน' in title:
                            all_questions.append("ปวดหัวข้างเดียว คลื่นไส้ อาจเป็นไมเกรนไหม")
                except:
                    continue
            
            # Get unique questions
            all_questions = list(set(all_questions))
            
            # If we have questions, randomly select 5
            if all_questions:
                suggested = random.sample(all_questions, min(5, len(all_questions)))
            else:
                # Default suggestions if no data
                suggested = [
                    "ผมมีอาการนอนไม่หลับ ตื่นกลางดึกบ่อย ควรทำอย่างไร",
                    "รู้สึกเครียด วิตกกังวล หัวใจเต้นแรง เป็นโรคอะไรหรือไม่",
                    "มีอาการปวดหัวบ่อยๆ อาจเป็นไมเกรนได้ไหม",
                    "ปวดประจำเดือนมาก มีวิธีบรรเทาอาการอย่างไร",
                    "รู้สึกเศร้า เบื่อ ไม่อยากทำอะไร อาจเป็นภาวะซึมเศร้าไหม"
                ]
    except:
        # Fallback suggestions
        suggested = [
            "ผมมีอาการนอนไม่หลับมาหลายวัน ควรทำอย่างไร",
            "รู้สึกเครียดและวิตกกังวล มีวิธีจัดการอย่างไร",
            "ปวดหัวบ่อยๆ อาจเป็นไมเกรนได้ไหม",
            "มีอาการเบื่ออาหาร น้ำหนักลด ควรตรวจอะไรบ้าง",
            "ปวดท้องประจำเดือนมาก มีวิธีบรรเทาไหม"
        ]
    
    return suggested

def main():
    """Main Streamlit app"""
    
    # Header
    st.title("🩺 Agnos Health Chatbot")
    st.markdown("### AI-Powered Health Consultation with Forum References")
    
    # Sidebar
    with st.sidebar:
        st.header("Information")
        st.markdown("""
        **Features:**
        - 🔍 Symptom-based disease prediction
        - 📚 Forum reference matching
        - 👨‍⚕️ Doctor expertise integration
        - 🔗 Actual forum URLs
        - 🇹🇭 Thai language support
        """)
        
        st.markdown("---")
        
        if st.button("🔄 Reset Chat"):
            st.session_state.chat_history = []
            if st.session_state.rag_system:
                st.session_state.rag_system.clear_memory()
            st.rerun()
        
        if st.button("⚙️ Reinitialize System"):
            st.session_state.initialized = False
            st.session_state.rag_system = None
            st.rerun()
    
    # Initialize system if needed
    if not st.session_state.initialized:
        if not initialize_system():
            return
        st.success("✅ System initialized successfully!")
    
    # Display chat history
    for message in st.session_state.chat_history:
        display_message(message['content'], message['is_user'])
    
    # Show suggested questions if no chat history
    if len(st.session_state.chat_history) == 0:
        st.markdown("💡 คำถามแนะนำ")
        
        suggested_questions = get_suggested_questions()
        
        # Create columns for better layout
        cols = st.columns(2)
        for i, question in enumerate(suggested_questions):
            col_idx = i % 2
            with cols[col_idx]:
                if st.button(f"💬 {question}", key=f"suggest_{i}", use_container_width=True):
                    st.session_state.suggested_question = question
                    st.rerun()
    
    # Check if a suggested question was clicked
    if 'suggested_question' in st.session_state:
        prompt = st.session_state.suggested_question
        del st.session_state.suggested_question
    else:
        prompt = st.chat_input("พิมพ์อาการหรือคำถามเกี่ยวกับสุขภาพ...")
    
    # Process the prompt
    if prompt:
        # Add user message to history
        st.session_state.chat_history.append({
            'content': prompt,
            'is_user': True
        })
        display_message(prompt, is_user=True)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("🤔 กำลังวิเคราะห์อาการและค้นหาข้อมูล..."):
                try:
                    response = st.session_state.rag_system.query(prompt)
                    
                    if response['success']:
                        # Display the response
                        st.markdown(response['answer'])
                        
                        # Show additional information in expandable sections
                        if response.get('disease_predictions'):
                            with st.expander(f"🏥 Disease Predictions ({len(response['disease_predictions'])})"):
                                for i, disease in enumerate(response['disease_predictions'], 1):
                                    st.write(f"**{i}. {disease['disease_name']}**")
                                    st.write(f"📋 From case: {disease['forum_title']}")
                                    if disease.get('forum_url'):
                                        st.write(f"🔗 [View Forum Discussion]({disease['forum_url']})")
                                    st.write("---")
                        
                        if response.get('doctor_history'):
                            with st.expander(f"👨‍⚕️ Expert Insights ({len(response['doctor_history'])})"):
                                for i, history in enumerate(response['doctor_history'], 1):
                                    st.write(f"**{i}. {history.get('doctor_name', 'แพทย์')}**")
                                    st.write(f"💬 {history['response'][:200]}...")
                                    st.write(f"📋 From case: {history['forum_title']}")
                                    if history.get('forum_url'):
                                        st.write(f"🔗 [View Forum Discussion]({history['forum_url']})")
                                    if history.get('likes', 0) > 0:
                                        st.write(f"👍 {history['likes']} likes")
                                    st.write("---")
                        
                        if response.get('sources'):
                            with st.expander(f"📚 Forum Sources ({len(response['sources'])})"):
                                for i, source in enumerate(response['sources'], 1):
                                    st.write(f"**{i}. {source['title']}**")
                                    if source.get('url'):
                                        st.write(f"🔗 [View Discussion]({source['url']})")
                                    st.write(f"📅 Date: {source.get('date', 'N/A')}")
                                    st.write(f"📁 Type: {source.get('content_type', 'question')}")
                                    st.write("---")
                        
                        # Add to chat history
                        st.session_state.chat_history.append({
                            'content': response['answer'],
                            'is_user': False
                        })
                        
                    else:
                        error_msg = f"❌ Error: {response.get('error', 'Unknown error')}"
                        st.error(error_msg)
                        st.session_state.chat_history.append({
                            'content': error_msg,
                            'is_user': False
                        })
                        
                except Exception as e:
                    error_msg = f"❌ An error occurred: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({
                        'content': error_msg,
                        'is_user': False
                    })

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center'>
    <small>🩺 Agnos Health Chatbot | Powered by OpenAI GPT-4 | Enhanced with Forum References</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()