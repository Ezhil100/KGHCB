# main.py - Complete Corrected Version
import re
import os
import tempfile
import time
from datetime import datetime
from typing import List, Dict, Optional

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, storage
try:
    from firebase_admin import firestore as _firestore
except Exception:
    _firestore = None

# Optional admin API import (works when running as script)
try:
    import admin_api as _admin_api  # type: ignore
    admin_router = getattr(_admin_api, 'router', None)
    save_chat_history = getattr(_admin_api, 'save_chat_history', None)
    detect_appointment_intent = getattr(_admin_api, 'detect_appointment_intent', None)
    extract_appointment_details = getattr(_admin_api, 'extract_appointment_details', None)
    save_appointment_request = getattr(_admin_api, 'save_appointment_request', None)
except Exception:
    try:
        from . import admin_api as _admin_api  # type: ignore
        admin_router = getattr(_admin_api, 'router', None)
        save_chat_history = getattr(_admin_api, 'save_chat_history', None)
        detect_appointment_intent = getattr(_admin_api, 'detect_appointment_intent', None)
        extract_appointment_details = getattr(_admin_api, 'extract_appointment_details', None)
        save_appointment_request = getattr(_admin_api, 'save_appointment_request', None)
    except Exception:
        admin_router = None
        def save_chat_history(*args, **kwargs):
            return False
        def detect_appointment_intent(*args, **kwargs):
            return False
        def extract_appointment_details(*args, **kwargs):
            return {"date": None, "time": None, "reason": None}
        def save_appointment_request(*args, **kwargs):
            return None

# LangChain imports
from langchain_community.document_loaders import UnstructuredPDFLoader, PyPDFLoader, CSVLoader, UnstructuredExcelLoader
from langchain_text_splitters.character import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import pandas as pd  # For Excel/CSV processing

# =============================================================================
# CONFIGURATION & INITIALIZATION
# =============================================================================

app = FastAPI(
    title="KG Hospital AI Chatbot API",
    version="1.0.0",
    description="AI-powered chatbot system for KG Hospital"
)

# Mount admin router without altering existing endpoints
if admin_router is not None:
    app.include_router(admin_router)

PORT = int(os.getenv("PORT", 8000))

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hospital-chat-bot.vercel.app",
        "https://hospital-chat-bot-frontend-9ds2.vercel.app",
        "http://localhost:3000",
        "http://localhost:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Firebase Admin SDK
try:
    if not firebase_admin._apps:
        firebase_config = {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }

        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred, {
            'storageBucket': f"{firebase_config['project_id']}.firebasestorage.app"
        })

    bucket = storage.bucket()
    FIREBASE_INITIALIZED = True
    # If admin_api module is available, wire Firestore client for DB operations
    try:
        if _admin_api is not None and _firestore is not None:
            setattr(_admin_api, 'FIREBASE_INITIALIZED', True)
            setattr(_admin_api, 'db', _firestore.client())
    except Exception:
        pass
    print("Firebase initialized successfully")
except Exception as e:
    print(f"Firebase initialization failed: {e}")
    FIREBASE_INITIALIZED = False

vectorstore = None
conversation_chain = None
loaded_documents = []

# =============================================================================
# IMPROVED SESSION MANAGEMENT WITH BETTER NUMBER TRACKING
# =============================================================================
user_sessions = {}

class UserSession:
    def __init__(self):
        self.last_doctor_list = []  # Store [{number: 1, name: "Dr. X", specialty: "Y", info: "..."}]
        self.last_department_list = []  # Store [{number: 1, name: "Dept X", info: "..."}]
        self.last_query_time = datetime.now()
        self.context_type = None  # 'doctors', 'departments', or None
        self.last_raw_doctor_list = ""  # Store the raw displayed list for validation
    
    def is_session_valid(self, timeout_minutes=30):
        """Check if session is still valid (not expired)"""
        elapsed = (datetime.now() - self.last_query_time).total_seconds() / 60
        return elapsed < timeout_minutes
    
    def update_timestamp(self):
        self.last_query_time = datetime.now()
    
    def set_doctor_list(self, doctors: List[Dict], raw_list: str = ""):
        """Store numbered doctor list with raw text for validation"""
        self.last_doctor_list = doctors
        self.last_raw_doctor_list = raw_list
        self.context_type = 'doctors'
        self.update_timestamp()
    
    def set_department_list(self, departments: List[Dict]):
        """Store numbered department list"""
        self.last_department_list = departments
        self.context_type = 'departments'
        self.update_timestamp()
    
    def get_doctor_by_number(self, number: int) -> Optional[Dict]:
        """Retrieve doctor info by number with improved validation"""
        if not self.is_session_valid():
            return None
        
        # First try structured data
        for doc in self.last_doctor_list:
            if doc['number'] == number:
                return doc
        
        # Fallback: parse from raw list if structured data fails
        if self.last_raw_doctor_list:
            lines = self.last_raw_doctor_list.split('\n')
            for line in lines:
                line = line.strip()
                # Match pattern: "1. Dr. Name, Specialty" or "1. Dr. Name - Specialty"
                match = re.match(r'^(\d+)\.\s+(Dr\.\s+.+?)(?:,\s+|\s+-\s+)(.+)$', line)
                if match:
                    try:
                        line_number = int(match.group(1))
                        if line_number == number:
                            return {
                                'number': number,
                                'name': match.group(2).strip(),
                                'specialty': match.group(3).strip(),
                                'info': "",
                                'full_text': line
                            }
                    except (ValueError, IndexError):
                        continue
        
        return None
    
    def get_department_by_number(self, number: int) -> Optional[Dict]:
        """Retrieve department info by number"""
        if not self.is_session_valid():
            return None
        for dept in self.last_department_list:
            if dept['number'] == number:
                return dept
        return None
    
    def clear_context(self):
        """Clear stored context"""
        self.last_doctor_list = []
        self.last_department_list = []
        self.last_raw_doctor_list = ""
        self.context_type = None

def get_user_session(user_id: str) -> UserSession:
    """Get or create user session"""
    if user_id not in user_sessions:
        user_sessions[user_id] = UserSession()
    return user_sessions[user_id]

def cleanup_expired_sessions():
    """Remove expired sessions to save memory"""
    expired_users = []
    for user_id, session in user_sessions.items():
        if not session.is_session_valid():
            expired_users.append(user_id)
    
    for user_id in expired_users:
        del user_sessions[user_id]

# =============================================================================
# PYDANTIC MODELS
# =============================================================================
class ChatMessage(BaseModel):
    message: str
    user_role: str = "visitor"
    user_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    is_appointment_request: bool = False
    appointment_id: str | None = None
    show_appointment_button: bool = False
    suggested_reason: str | None = None
    context_type: str | None = None  # 'doctors', 'departments', or None

# =============================================================================
# DOCUMENT PROCESSING FUNCTIONS
# =============================================================================
def load_document(file_path: str):
    """Load documents from PDF, Excel (.xlsx, .xls), or CSV files."""
    documents = []
    file_name = os.path.basename(file_path)
    file_ext = os.path.splitext(file_name)[1].lower()

    # Handle CSV files
    if file_ext == '.csv':
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded CSV with {len(df)} rows and columns: {list(df.columns)}")
            
            from langchain.schema import Document
            documents = []
            for idx, row in df.iterrows():
                row_text = " | ".join([f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])])
                documents.append(Document(
                    page_content=row_text,
                    metadata={"source": file_name, "row": idx + 1, "type": "csv"}
                ))
            
            print(f"Loaded {file_name} as CSV with {len(documents)} records")
            return documents
        except Exception as e:
            print(f"CSV loading failed for {file_name}: {e}")
            raise Exception(f"CSV processing failed for {file_name}: {e}")
    
    # Handle Excel files (.xlsx, .xls)
    elif file_ext in ['.xlsx', '.xls']:
        try:
            df = pd.read_excel(file_path)
            print(f"Loaded Excel with {len(df)} rows and columns: {list(df.columns)}")
            
            from langchain.schema import Document
            documents = []
            for idx, row in df.iterrows():
                row_text = " | ".join([f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])])
                documents.append(Document(
                    page_content=row_text,
                    metadata={"source": file_name, "row": idx + 1, "type": "excel"}
                ))
            
            print(f"Loaded {file_name} as Excel with {len(documents)} records")
            return documents
        except Exception as e:
            print(f"Excel loading failed for {file_name}: {e}")
            raise Exception(f"Excel processing failed for {file_name}: {e}")
    
    # Handle PDF files
    elif file_ext == '.pdf':
        try:
            loader = UnstructuredPDFLoader(file_path)
            documents = loader.load()
            if documents:
                print(f"Loaded {file_name} using UnstructuredPDFLoader")
                return documents
        except Exception as e:
            print(f"UnstructuredPDFLoader failed for {file_name}: {e}")

        try:
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            if documents:
                print(f"Loaded {file_name} using PyPDFLoader")
                return documents
        except Exception as e:
            print(f"PyPDFLoader failed for {file_name}: {e}")

        raise Exception(f"All PDF processing methods failed for {file_name}")
    
    else:
        raise Exception(f"Unsupported file format: {file_ext}. Supported formats: .pdf, .csv, .xlsx, .xls")

def setup_vectorstore(documents):
    if not documents:
        raise ValueError("No documents provided for vectorstore creation")

    print(f"Processing {len(documents)} document pages...")

    text_splitter = CharacterTextSplitter(
        separator='\n',
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )

    doc_chunks = text_splitter.split_documents(documents)
    print(f"Created {len(doc_chunks)} text chunks")

    if len(doc_chunks) > 2000:
        print("Large document detected. Limiting to 2000 chunks for performance.")
        doc_chunks = doc_chunks[:2000]

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    print("Creating vector store...")
    vectorstore = FAISS.from_documents(doc_chunks, embeddings)
    print("Vector store created successfully!")

    return vectorstore

def create_chain(vectorstore):
    from langchain.prompts import PromptTemplate
    
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 15,  # Increased from 10 to 15 for better context
            "fetch_k": 30,  # Increased from 25 to 30
            "lambda_mult": 0.5
        }
    )

    memory = ConversationBufferMemory(
        llm=llm,
        output_key='answer',
        memory_key='chat_history',
        return_messages=True
    )

    # IMPROVED PROMPT TEMPLATE - Less restrictive, more intelligent
    qa_prompt_template = """You are an AI assistant for KG Hospital. Your role is to provide helpful information to hospital visitors, staff, and administrators.

IMPORTANT GUIDELINES:
1. Use the information provided in the Context below as your primary knowledge source
2. If the Context contains relevant information, provide a comprehensive answer based on it
3. If the Context doesn't contain specific details but you can provide general medical/hospital guidance, do so while being clear about limitations
4. For medical advice: Always recommend consulting with healthcare professionals
5. Be helpful, accurate, and professional in all responses

Context (Retrieved Information):
{context}

Previous Conversation:
{chat_history}

Current Question: {question}

RESPONSE GUIDELINES:
- For doctors: Provide names, specialties, and available information. If listing multiple doctors, use numbered format.
- For departments: Include services, locations, and available details
- For medical queries: Provide general information but emphasize consulting doctors
- For appointments: Explain the process based on available information
- For symptoms: Provide general guidance but recommend medical consultation
- Always be helpful and avoid saying "I don't know" unless absolutely necessary

Answer in a helpful, informative tone:"""

    qa_prompt = PromptTemplate(
        template=qa_prompt_template,
        input_variables=["context", "chat_history", "question"]
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        verbose=False,
        return_source_documents=False,
        combine_docs_chain_kwargs={"prompt": qa_prompt}
    )

    return chain

# =============================================================================
# FIREBASE FUNCTIONS
# =============================================================================
def upload_file_to_firebase(file_path: str, file_name: str):
    if not FIREBASE_INITIALIZED:
        return False, "Firebase not initialized"

    try:
        blob = bucket.blob(f"documents/{file_name}")
        blob.upload_from_filename(file_path)
        print(f"Uploaded {file_name} to Firebase Storage")
        return True, f"File '{file_name}' uploaded successfully"
    except Exception as e:
        print(f"Upload failed for {file_name}: {e}")
        return False, f"Upload failed: {str(e)}"

def list_firebase_files():
    if not FIREBASE_INITIALIZED:
        return []

    try:
        blobs = bucket.list_blobs(prefix="documents/")
        files_info = []
        
        supported_extensions = ('.pdf', '.csv', '.xlsx', '.xls')

        for blob in blobs:
            if blob.name.lower().endswith(supported_extensions):
                files_info.append({
                    'name': blob.name.replace('documents/', ''),
                    'size': blob.size or 0,
                    'created': blob.time_created.isoformat() if blob.time_created else '',
                    'status': 'loaded'
                })

        return files_info
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

def download_firebase_file(file_name: str):
    if not FIREBASE_INITIALIZED:
        return None

    try:
        blob = bucket.blob(f"documents/{file_name}")
        if not blob.exists():
            return None

        file_ext = os.path.splitext(file_name)[1] or '.tmp'
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        temp_file_path = temp_file.name
        temp_file.close()

        blob.download_to_filename(temp_file_path)
        return temp_file_path
    except Exception as e:
        print(f"Download failed for {file_name}: {e}")
        return None

def reload_all_documents():
    global vectorstore, conversation_chain, loaded_documents

    print("Reloading all documents from Firebase...")
    firebase_files = list_firebase_files()
    if not firebase_files:
        return False, "No documents found in Firebase"

    all_documents = []
    successful_loads = 0

    for file_info in firebase_files:
        file_name = file_info['name']
        print(f"Processing {file_name}...")

        temp_file_path = download_firebase_file(file_name)
        if temp_file_path:
            try:
                documents = load_document(temp_file_path)
                all_documents.extend(documents)
                successful_loads += 1
                print(f"✓ Successfully loaded {file_name} with {len(documents)} document(s)")
                os.remove(temp_file_path)
            except Exception as e:
                print(f"✗ Failed to process {file_name}: {str(e)}")
                import traceback
                traceback.print_exc()
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        else:
            print(f"✗ Failed to download {file_name} from Firebase")

    if all_documents:
        print(f"Total documents loaded: {len(all_documents)}")
        vectorstore = setup_vectorstore(all_documents)
        conversation_chain = create_chain(vectorstore)
        loaded_documents = all_documents
        return True, f"Successfully loaded {successful_loads} out of {len(firebase_files)} documents"

    return False, "No documents could be processed"

# =============================================================================
# IMPROVED NUMBER REFERENCE DETECTION
# =============================================================================
def detect_number_reference(message: str) -> Optional[int]:
    """Enhanced number detection with better patterns"""
    message_lower = message.lower().strip()
    
    # Remove any extra spaces and normalize
    message_clean = re.sub(r'\s+', ' ', message_lower)
    
    # Enhanced patterns for number references:
    patterns = [
        r'^\s*(\d+)\s*$',  # Just a number: "1", " 2 ", "3"
        r'^(?:number|no\.?|#)\s*(\d+)\s*$',  # "number 1", "no 1", "#1"
        r'^(?:doctor|dr\.?|option|choice)\s*(?:number|no\.?|#)?\s*(\d+)\s*$',  # "doctor 1", "option 1"
        r'^tell me (?:about|more about)?\s*(?:number|no\.?|#)?\s*(\d+)\s*$',  # "tell me about 1"
        r'^(?:show|give|select|choose)\s+(?:me\s+)?(?:number|no\.?|#)?\s*(\d+)\s*$',  # "show me 1", "select 2"
        r'^(\d+)\s*(?:please|pls|details|info)?\s*$',  # "1 please", "2 details"
        r'^i choose\s*(\d+)\s*$',  # "i choose 1"
        r'^want\s+(?:number|no\.?|#)?\s*(\d+)\s*$',  # "want 1"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message_clean)
        if match:
            try:
                number = int(match.group(1))
                # Validate it's a reasonable number (1-50 for doctors)
                if 1 <= number <= 50:
                    return number
            except (ValueError, IndexError):
                continue
    
    return None

# =============================================================================
# IMPROVED DOCTOR LIST EXTRACTION AND FORMATTING
# =============================================================================
def extract_structured_doctor_info(context: str) -> List[Dict]:
    """Enhanced doctor extraction with better formatting"""
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    
    prompt = f"""Extract ALL doctor information from the context and format as a structured numbered list.

CRITICAL INSTRUCTIONS:
1. Extract EVERY doctor mentioned in the context
2. For each doctor, include: Name and Specialty/Department
3. Format EXACTLY as: Number. Dr. Name, Specialty
4. If specialty is not specified, try to infer from context or leave as "General Medicine"
5. Ensure ALL numbers are sequential starting from 1
6. Do NOT skip any numbers
7. Do NOT add any introductory text, notes, or disclaimers
8. Do NOT include IDs, employee numbers, or extensions

Context:
{context}

Format your response EXACTLY like this:
1. Dr. Name1, Specialty1
2. Dr. Name2, Specialty2
3. Dr. Name3, Specialty3"""

    response = llm.invoke(prompt)
    raw_text = response.content.strip()
    
    # Parse the numbered list into structured data
    doctors = []
    lines = raw_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Enhanced pattern matching for various formats
        patterns = [
            r'^(\d+)\.\s+(Dr\.\s+.+?),\s+(.+)$',  # "1. Dr. Name, Specialty"
            r'^(\d+)\.\s+(Dr\.\s+.+?)\s+-\s+(.+)$',  # "1. Dr. Name - Specialty"
            r'^(\d+)\.\s+(Dr\.\s+.+?)\s*:\s*(.+)$',  # "1. Dr. Name: Specialty"
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                try:
                    number = int(match.group(1))
                    name = match.group(2).strip()
                    specialty = match.group(3).strip()
                    
                    # Clean up specialty - remove trailing periods, extra spaces
                    specialty = re.sub(r'\.$', '', specialty).strip()
                    if not specialty or specialty.lower() in ['none', 'not specified', 'unknown']:
                        specialty = "General Medicine"
                    
                    doctors.append({
                        'number': number,
                        'name': name,
                        'specialty': specialty,
                        'info': "",
                        'full_text': line
                    })
                    break  # Stop after first successful match
                except (ValueError, IndexError):
                    continue
    
    return doctors

def get_doctor_detailed_info(doctor_name: str, specialty: str) -> str:
    """Get detailed information about a specific doctor with better error handling"""
    if not conversation_chain or not vectorstore:
        return None
    
    try:
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 8, 'fetch_k': 20, 'lambda_mult': 0.5}
        )
        
        # Clean the doctor name for better search
        clean_name = re.sub(r'Dr\.?\s*', '', doctor_name).strip()
        
        # Multiple search strategies
        search_queries = [
            f"{clean_name} {specialty} doctor information",
            f"Dr. {clean_name} {specialty}",
            f"{clean_name} qualifications experience contact",
            f"doctor {clean_name} hospital staff"
        ]
        
        all_docs = []
        for query in search_queries:
            try:
                docs = retriever.invoke(query)
                all_docs.extend(docs)
            except Exception as e:
                print(f"Search query failed '{query}': {e}")
        
        # Remove duplicates
        unique_docs = []
        seen_content = set()
        for doc in all_docs:
            content_hash = hash(doc.page_content[:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_docs.append(doc)
        
        context = "\n\n".join([doc.page_content for doc in unique_docs[:10]])
        
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        prompt = f"""Based on the context, provide detailed information about Dr. {clean_name}.

If specific information is not available, provide general information about {specialty} department at KG Hospital.

Include whatever information is available:
- Full name and title
- Specialty/Department  
- Qualifications (if available)
- Experience (if available)
- Contact information (if available)
- Consultation hours (if available)
- Any other relevant details

If detailed information is not found, provide helpful guidance about consulting {specialty} department.

Context:
{context}

Doctor Information:"""
        
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"Error getting doctor details: {e}")
        return None

# =============================================================================
# IMPROVED QUERY HANDLING FUNCTIONS
# =============================================================================
def detect_information_query(message: str) -> bool:
    """Detect if user is asking for information about symptoms, doctors, or treatment."""
    message_lower = message.lower().strip()
    
    info_keywords = [
        'who should i consult', 'which doctor', 'what doctor', 'who to consult',
        'who can i see', 'who do i see', 'which specialist',
        'fever', 'headache', 'pain', 'cold', 'cough', 'symptom',
        'treatment for', 'cure for', 'specialist for', 'doctor for',
        'suffering from', 'have', 'got', 'experiencing',
        'diabetes', 'blood pressure', 'heart', 'stomach', 'back pain',
        'chest pain', 'throat', 'skin', 'allergy', 'cancer', 'asthma',
        'arthritis', 'migraine', 'infection', 'virus', 'bacterial',
        'what is', 'what are', 'how to treat', 'how to prevent',
        'symptoms of', 'causes of', 'diagnosis for'
    ]
    
    return any(keyword in message_lower for keyword in info_keywords)

def detect_query_type(message: str):
    """Improved query type detection"""
    message_lower = message.lower().strip()
    
    # Doctor list queries
    doctor_queries = [
        'list doctors', 'all doctors', 'doctors list', 'show doctors',
        'available doctors', 'doctors available', 'list of doctors',
        'doctor list', 'docs list', 'list doc', 'list dr',
        'which doctors are there', 'what doctors do you have'
    ]
    
    # Department list queries  
    dept_queries = [
        'list departments', 'all departments', 'departments list', 
        'show departments', 'available departments', 'list of departments',
        'department list', 'depts list', 'list dept',
        'which departments are there', 'what departments do you have'
    ]
    
    # Check for exact matches first
    if any(query == message_lower for query in doctor_queries):
        return 'doctors'
    elif any(query == message_lower for query in dept_queries):
        return 'departments'
    
    # Check for partial matches
    if any(query in message_lower for query in doctor_queries):
        return 'doctors'
    elif any(query in message_lower for query in dept_queries):
        return 'departments'
    
    # Check for simple keywords (only if message is short)
    if len(message_lower) < 50:
        if any(word in message_lower for word in ['doctors', 'doctor', 'docs', 'doc']) and \
           not any(word in message_lower for word in ['appointment', 'book', 'schedule', 'availability']):
            return 'doctors'
        elif any(word in message_lower for word in ['departments', 'department', 'depts', 'dept']):
            return 'departments'
    
    return None

def get_doctors_list():
    """Improved doctors list retrieval with better formatting"""
    if not conversation_chain or not vectorstore:
        return None
    
    try:
        # Try multiple search queries to get comprehensive results
        search_queries = [
            "list all doctors and their specialties departments",
            "doctors names specialties departments cardiology surgery",
            "medical staff doctors physicians specialists",
            "consulting doctors cardiologists surgeons physicians"
        ]
        
        all_docs = []
        for query in search_queries:
            try:
                retriever = vectorstore.as_retriever(
                    search_type="mmr",
                    search_kwargs={'k': 10, 'fetch_k': 25, 'lambda_mult': 0.5}
                )
                docs = retriever.invoke(query)
                all_docs.extend(docs)
            except Exception as e:
                print(f"Error in query '{query}': {e}")
        
        # Remove duplicates
        unique_docs = []
        seen_content = set()
        for doc in all_docs:
            content_hash = hash(doc.page_content[:100])  # Hash first 100 chars for deduplication
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_docs.append(doc)
        
        context = "\n\n".join([doc.page_content for doc in unique_docs[:20]])
        
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        prompt = f"""Based on the context, extract ALL doctors with their specialties.

CRITICAL FORMATTING RULES:
- Format EXACTLY as: Number. Dr. Full Name, Specialty
- Ensure ALL numbers are sequential starting from 1
- Do NOT skip any numbers
- If specialty is not clear, use "General Medicine"
- Include ALL doctors mentioned in the context
- Do not add any introductory text, notes, or explanations
- Each doctor on a separate line

Context:
{context}

Doctors List:"""
        
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"Error getting doctors list: {e}")
        return None

def get_departments_list():
    """Improved departments list retrieval"""
    if not conversation_chain or not vectorstore:
        return None
    
    try:
        # Try multiple search queries
        search_queries = [
            "list all hospital departments",
            "medical departments specialties",
            "clinical departments services",
            "hospital departments list"
        ]
        
        all_docs = []
        for query in search_queries:
            try:
                retriever = vectorstore.as_retriever(
                    search_type="mmr",
                    search_kwargs={'k': 6, 'fetch_k': 15, 'lambda_mult': 0.5}
                )
                docs = retriever.invoke(query)
                all_docs.extend(docs)
            except Exception as e:
                print(f"Error in query '{query}': {e}")
        
        # Remove duplicates
        unique_docs = []
        seen_content = set()
        for doc in all_docs:
            if doc.page_content not in seen_content:
                seen_content.add(doc.page_content)
                unique_docs.append(doc)
        
        context = "\n\n".join([doc.page_content for doc in unique_docs[:10]])
        
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        prompt = f"""Based on the context, extract ALL hospital departments.

Format each entry as: Number. Department Name

Important rules:
- List EVERY department mentioned in the context
- Each department on a separate line with number
- Format: "1. Department Name"
- Include ALL available departments
- Do not skip any departments mentioned
- Do not add any introductory text or notes

Context:
{context}

Departments List:"""
        
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"Error getting departments list: {e}")
        return None

# =============================================================================
# IMPROVED MEDICAL QUERY HANDLER
# =============================================================================
def handle_medical_query(message: str, user_role: str) -> str:
    """Handle medical queries intelligently using RAG with fallback knowledge"""
    if not conversation_chain or not vectorstore:
        return get_fallback_medical_response(message)
    
    try:
        # Use broader search for medical queries
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 12, 'fetch_k': 25, 'lambda_mult': 0.4}
        )
        
        # Expand search terms for better context retrieval
        expanded_query = f"{message} hospital medical treatment symptoms diagnosis"
        docs = retriever.invoke(expanded_query)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        
        prompt = f"""You are a helpful AI assistant for KG Hospital. A user is asking a medical-related question.

User Question: {message}

Available Hospital Context:
{context}

IMPORTANT GUIDELINES:
1. Use the hospital context above to provide relevant information
2. If the context contains specific information about the hospital's services, doctors, or departments related to this query, share that information
3. You can provide general medical information that would be helpful, but always clarify this is general knowledge
4. EMPHASIZE that for proper medical advice, they should consult with healthcare professionals
5. Be helpful and informative while maintaining medical accuracy
6. If the context doesn't have specific information, still try to be helpful by guiding them to the right department or suggesting they contact the hospital

Provide a comprehensive, helpful response:"""
        
        response = llm.invoke(prompt)
        return response.content
        
    except Exception as e:
        print(f"Error in medical query handling: {e}")
        return get_fallback_medical_response(message)

def get_fallback_medical_response(query: str) -> str:
    """Provide intelligent fallback responses for medical queries"""
    query_lower = query.lower()
    
    # Map symptoms to potential departments
    symptom_department_map = {
        'fever': 'General Medicine or Infectious Diseases',
        'headache': 'Neurology or General Medicine',
        'cold': 'General Medicine or ENT',
        'cough': 'Pulmonology or General Medicine',
        'chest pain': 'Cardiology or Emergency Medicine',
        'stomach': 'Gastroenterology or General Medicine',
        'heart': 'Cardiology',
        'brain': 'Neurology or Neurosurgery',
        'lung': 'Pulmonology',
        'kidney': 'Nephrology',
        'liver': 'Gastroenterology',
        'bone': 'Orthopedics',
        'skin': 'Dermatology',
        'eye': 'Ophthalmology',
        'ear': 'ENT',
        'nose': 'ENT',
        'throat': 'ENT',
        'child': 'Pediatrics',
        'pregnant': 'Gynecology',
        'cancer': 'Oncology',
        'diabetes': 'Endocrinology',
        'blood pressure': 'Cardiology or General Medicine',
        'mental': 'Psychiatry',
        'anxiety': 'Psychiatry',
        'depression': 'Psychiatry'
    }
    
    # Find relevant department
    relevant_dept = "the appropriate medical department"
    for symptom, dept in symptom_department_map.items():
        if symptom in query_lower:
            relevant_dept = dept
            break
    
    return f"""I understand you're asking about a medical concern. While I can provide general information, it's important to consult with healthcare professionals for proper medical advice.

Based on your query, you may want to visit our **{relevant_dept}** department at KG Hospital. 

Our medical staff can provide:
- Proper diagnosis and examination
- Personalized treatment plans
- Professional medical guidance
- Follow-up care and monitoring

For immediate assistance, please contact KG Hospital at 📞 0422-2324105 or visit our emergency department if this is urgent.

Would you like me to help you find specific doctors in {relevant_dept.split(' or ')[0]} department?"""

# =============================================================================
# IMPROVED CHAT ENDPOINT WITH BETTER NUMBER HANDLING
# =============================================================================
@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Enhanced chat endpoint with improved number reference handling."""
    global conversation_chain

    try:
        # Cleanup expired sessions periodically
        cleanup_expired_sessions()
        
        # Get or create user session
        user_id = message.user_id or "anonymous"
        session = get_user_session(user_id)
        
        print(f"Chat request ({message.user_role}): {message.message}")
        print(f"Current session context: {session.context_type}, Doctors in session: {len(session.last_doctor_list)}")
        
        # IMPROVED: Check if user is referencing a number from previous list
        ref_number = detect_number_reference(message.message)
        if ref_number is not None:
            print(f"Detected number reference: {ref_number}")
            print(f"Session valid: {session.is_session_valid()}")
            print(f"Available doctors in session: {[doc['number'] for doc in session.last_doctor_list]}")
            
            if session.is_session_valid():
                # Check if it's a doctor reference
                doctor = session.get_doctor_by_number(ref_number)
                if doctor:
                    print(f"Found doctor: {doctor['name']} (Number {doctor['number']})")
                    # Get detailed information about this doctor
                    detailed_info = get_doctor_detailed_info(doctor['name'], doctor['specialty'])
                    
                    if detailed_info:
                        response_text = detailed_info
                    else:
                        # Fallback to basic info
                        response_text = f"**{doctor['name']}**\n\n"
                        response_text += f"**Specialty:** {doctor['specialty']}\n\n"
                        if doctor['info']:
                            response_text += f"**Additional Information:** {doctor['info']}\n\n"
                        response_text += "For appointments or more information, please contact KG Hospital at 0422-2324105."
                    
                    formatted_answer = format_response_text(response_text)
                    formatted_answer = add_actionable_elements(formatted_answer)
                    
                    # Add appointment booking option
                    formatted_answer += f"\n\nWould you like to book an appointment with {doctor['name']}?"
                    
                    return ChatResponse(
                        response=formatted_answer,
                        timestamp=datetime.now().isoformat(),
                        is_appointment_request=False,
                        appointment_id=None,
                        show_appointment_button=True,
                        suggested_reason=f"Consultation with {doctor['name']}",
                        context_type='doctor_detail'
                    )
                
                # Check if it's a department reference
                department = session.get_department_by_number(ref_number)
                if department:
                    print(f"Found department: {department['name']}")
                    response_text = f"**{department['name']}**\n\n"
                    if department['info']:
                        response_text += f"{department['info']}\n\n"
                    response_text += "For more information, please contact KG Hospital at 0422-2324105."
                    
                    formatted_answer = format_response_text(response_text)
                    formatted_answer = add_actionable_elements(formatted_answer)
                    
                    return ChatResponse(
                        response=formatted_answer,
                        timestamp=datetime.now().isoformat(),
                        is_appointment_request=False,
                        appointment_id=None,
                        context_type='department_detail'
                    )
            
            # Number not found in context or session expired
            if session.context_type == 'doctors' and session.last_doctor_list:
                available_numbers = [str(doc['number']) for doc in session.last_doctor_list]
                error_msg = f"I don't see number {ref_number} in the current doctors list. Please choose a valid number from: {', '.join(available_numbers)}"
            elif session.context_type == 'departments' and session.last_department_list:
                available_numbers = [str(dept['number']) for dept in session.last_department_list]
                error_msg = f"I don't see number {ref_number} in the current departments list. Please choose a valid number from: {', '.join(available_numbers)}"
            else:
                error_msg = f"I don't have an active numbered list to reference. Please ask me about doctors or departments first."
            
            return ChatResponse(
                response=error_msg,
                timestamp=datetime.now().isoformat(),
                is_appointment_request=False,
                appointment_id=None
            )
        
        # Check if this is a simple greeting
        greeting_patterns = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']
        message_lower = message.message.lower().strip()
        is_greeting = any(message_lower == pattern or message_lower.startswith(f"{pattern} ") or message_lower.startswith(f"{pattern}!") for pattern in greeting_patterns)
        
        if is_greeting:
            greeting_responses = {
                "visitor": "Hello! I'm here to help you with KG Hospital information. How can I assist you today?",
                "staff": "Hello. How can I help you today?",
                "admin": "Hello. How can I assist you with hospital management today?"
            }
            greeting_answer = greeting_responses.get(message.user_role, greeting_responses["visitor"])
            
            # Clear any previous context on new greeting
            session.clear_context()
            
            return ChatResponse(
                response=greeting_answer,
                timestamp=datetime.now().isoformat(),
                is_appointment_request=False,
                appointment_id=None
            )
        
        # Check if this is a hospital location request
        location_keywords = ['hospital location', 'where is the hospital', 'hospital address', 
                            'how to reach', 'directions', 'where are you located', 'location',
                            'address of hospital', 'hospital directions', 'where is kg hospital',
                            'where is kghospital', 'hospil location', 'hsplt location']
        is_location_query = any(keyword in message_lower for keyword in location_keywords)
        
        if is_location_query:
            location_response = """📍 **KG Hospital Location:**

**Address:**
No. 5, Arts College Road,
Coimbatore - 641 018,
Tamil Nadu, India

**Contact:**
📞 Phone: 0422-2324105

**How to Reach:**
KG Hospital is located on Arts College Road in Coimbatore city center, easily accessible by all modes of transport.

For detailed directions and map, please visit: https://www.kghospital.com/"""
            
            location_response = add_actionable_elements(location_response)
            
            return ChatResponse(
                response=location_response,
                timestamp=datetime.now().isoformat(),
                is_appointment_request=False,
                appointment_id=None
            )
        
        # Check if this is a specific doctors/departments list request
        query_type = detect_query_type(message.message)
        
        if query_type:
            answer = ""
            raw_doctor_list = ""
            if query_type == 'doctors':
                raw_doctor_list = get_doctors_list()
                if raw_doctor_list:
                    answer = raw_doctor_list
                    # Extract and store structured doctor info WITH RAW LIST
                    try:
                        retriever = vectorstore.as_retriever(
                            search_type="mmr",
                            search_kwargs={'k': 10, 'fetch_k': 25, 'lambda_mult': 0.5}
                        )
                        docs = retriever.invoke("list all doctors and their specialties")
                        context = "\n\n".join([doc.page_content for doc in docs])
                        structured_doctors = extract_structured_doctor_info(context)
                        if structured_doctors:
                            # IMPROVED: Store both structured data and raw list
                            session.set_doctor_list(structured_doctors, raw_doctor_list)
                            print(f"Structured doctors stored: {[doc['number'] for doc in structured_doctors]}")
                    except Exception as e:
                        print(f"Error extracting structured doctors: {e}")
                        # Still store the raw list as fallback
                        session.set_doctor_list([], raw_doctor_list)
                else:
                    # Fallback if RAG doesn't return doctors
                    answer = "I'll help you find information about our doctors. Let me check our available medical staff..."
                    # Use medical query handler as fallback
                    answer = handle_medical_query("doctors list", message.user_role)
                        
            elif query_type == 'departments':
                departments = get_departments_list()
                if departments:
                    answer = departments
                else:
                    answer = handle_medical_query("hospital departments list", message.user_role)
            
            # If we got a specific answer, format and return it
            if answer:
                formatted_answer = format_response_text(answer)
                formatted_answer = add_actionable_elements(formatted_answer)
                
                # Add helpful instruction for numbered references
                if query_type in ['doctors', 'separate']:
                    formatted_answer += "\n\n💡 *Tip: Type a doctor's number (e.g., \"1\" or \"doctor 3\") to get detailed information and book an appointment.*"
                
                return ChatResponse(
                    response=formatted_answer,
                    timestamp=datetime.now().isoformat(),
                    is_appointment_request=False,
                    appointment_id=None,
                    context_type='doctors' if query_type in ['doctors', 'separate'] else 'departments'
                )
        
        # Check if this is a medical query and handle it intelligently
        is_medical_query = detect_information_query(message.message)
        
        if is_medical_query:
            medical_answer = handle_medical_query(message.message, message.user_role)
            formatted_answer = format_response_text(medical_answer)
            formatted_answer = add_actionable_elements(formatted_answer)
            
            return ChatResponse(
                response=formatted_answer,
                timestamp=datetime.now().isoformat(),
                is_appointment_request=False,
                appointment_id=None,
                show_appointment_button=True,
                suggested_reason="Medical consultation",
                context_type='medical'
            )
        
        # Continue with normal RAG processing for other queries
        if conversation_chain:
            try:
                response = conversation_chain.invoke({'question': message.message})
                answer = response.get('answer', '')
                
                # Check if the answer contains restrictive phrases and improve it
                restrictive_phrases = [
                    "I don't have that specific information",
                    "not in my current knowledge base", 
                    "please contact KG Hospital",
                    "I don't know",
                    "I cannot provide"
                ]
                
                if any(phrase in answer for phrase in restrictive_phrases):
                    # Try to provide a more helpful response using medical query handler
                    improved_answer = handle_medical_query(message.message, message.user_role)
                    if improved_answer and not any(phrase in improved_answer for phrase in restrictive_phrases):
                        answer = improved_answer
                
                # Check if the answer contains a list of doctors (for specialty queries)
                if re.search(r'\d+\.\s+Dr\.', answer):
                    # This looks like a doctor list - extract and store it
                    try:
                        retriever = vectorstore.as_retriever(
                            search_type="mmr",
                            search_kwargs={'k': 10, 'fetch_k': 25, 'lambda_mult': 0.5}
                        )
                        docs = retriever.invoke(message.message)
                        context = "\n\n".join([doc.page_content for doc in docs])
                        structured_doctors = extract_structured_doctor_info(context)
                        if structured_doctors:
                            session.set_doctor_list(structured_doctors)
                            # Add helpful instruction
                            answer += "\n\n💡 *Tip: Type a doctor's number (e.g., \"1\" or \"doctor 2\") to get detailed information and book an appointment.*"
                    except Exception as e:
                        print(f"Error extracting structured doctors from RAG: {e}")
                    
            except Exception as e:
                print(f"RAG chain error: {e}")
                # Fallback to direct LLM response
                answer = handle_medical_query(message.message, message.user_role)
        else:
            # Fallback when no conversation chain
            answer = handle_medical_query(message.message, message.user_role)

        if not answer.strip():
            answer = ("I'm happy to help with your query about KG Hospital. "
                     "For detailed information, you can contact KG Hospital's support at 0422-2324105 "
                     "or visit the front desk for assistance.")

        formatted_answer = format_response_text(answer)
        formatted_answer = add_actionable_elements(formatted_answer)

        # Detect appointment intent
        is_appointment = False
        new_appointment_id = None
        show_booking_button = False
        suggested_reason_text = None
        
        try:
            wants_appointment = False
            has_info_query = detect_information_query(message.message)
            
            if 'detect_appointment_intent' in globals() and callable(detect_appointment_intent):
                wants_appointment = bool(detect_appointment_intent(message.message))
            
            # COMPOUND QUERY: User asks about symptoms/doctors AND wants appointment
            if (has_info_query or is_medical_query) and wants_appointment:
                show_booking_button = True
                
                # Extract reason from the query for pre-filling
                reason_keywords = {
                    'fever': 'Fever treatment',
                    'headache': 'Headache consultation', 
                    'pain': 'Pain management',
                    'cold': 'Cold and flu',
                    'cough': 'Cough treatment',
                    'diabetes': 'Diabetes consultation',
                    'blood pressure': 'Blood pressure checkup',
                    'heart': 'Cardiac consultation',
                    'stomach': 'Gastric issues',
                    'chest pain': 'Chest pain consultation',
                    'back pain': 'Back pain treatment',
                    'throat': 'Throat infection',
                    'flu': 'Flu treatment',
                    'allergy': 'Allergy consultation',
                    'skin': 'Skin condition',
                    'breathing': 'Respiratory issues',
                    'dizzy': 'Dizziness consultation',
                    'vomit': 'Vomiting/Nausea',
                    'injury': 'Injury treatment',
                    'checkup': 'General checkup',
                    'consultation': 'General consultation'
                }
                
                message_lower = message.message.lower()
                for keyword, reason in reason_keywords.items():
                    if keyword in message_lower:
                        suggested_reason_text = reason
                        break
                
                if not any("appointment" in line.lower() for line in formatted_answer.split('\n')):
                    formatted_answer += "\n\nWould you like to book an appointment with one of our doctors?"
                
            # SIMPLE APPOINTMENT REQUEST: User only wants to book
            elif wants_appointment:
                details = {"date": None, "time": None, "reason": None}
                if 'extract_appointment_details' in globals() and callable(extract_appointment_details):
                    try:
                        details = extract_appointment_details(message.message) or details
                    except Exception:
                        pass
                
                # Extract phone number from message
                phone_pattern = r'(\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9})'
                phone_match = re.search(phone_pattern, message.message)
                phone_number = phone_match.group(1) if phone_match else None
                
                preferred_date = details.get('date') or 'Not specified'
                preferred_time = details.get('time') or 'Not specified'
                reason = details.get('reason') or 'General consultation'
                
                if 'save_appointment_request' in globals() and callable(save_appointment_request):
                    try:
                        new_appointment_id = save_appointment_request(
                            preferred_date=preferred_date,
                            preferred_time=preferred_time,
                            reason=reason,
                            user_role=message.user_role,
                            original_message=message.message,
                            phone_number=phone_number
                        )
                        if new_appointment_id:
                            is_appointment = True
                            # Extract name from message
                            name = "Patient"
                            name_patterns = [
                                r'(?:for|name:?)\s+([A-Za-z]+)',
                                r'^([A-Za-z]+)\s+\(',
                                r'([A-Za-z]+)\s+\d{10}'
                            ]
                            for pattern in name_patterns:
                                name_match = re.search(pattern, message.message, re.IGNORECASE)
                                if name_match:
                                    name = name_match.group(1).capitalize()
                                    break
                            
                            phone_line = f"[TEL:{phone_number}]" if phone_number else "Not provided"
                            formatted_answer = (
                                f"Appointment request has been successfully sent to the admin, soon we will reach out to you.\n\n"
                                f"Name: {name}\n"
                                f"Phone: {phone_line}\n"
                                f"Date: {preferred_date}\n"
                                f"Time: {preferred_time}\n"
                                f"Reason: {reason}"
                            )
                    except Exception:
                        pass
        except Exception as e:
            print(f"Appointment detection error: {e}")

        # Save chat history
        try:
            if save_chat_history:
                save_chat_history(
                    user_id=user_id,
                    user_role=message.user_role,
                    message=message.message,
                    response=formatted_answer,
                    is_appointment=is_appointment,
                )
        except Exception:
            pass

        return ChatResponse(
            response=formatted_answer,
            timestamp=datetime.now().isoformat(),
            is_appointment_request=is_appointment,
            appointment_id=new_appointment_id,
            show_appointment_button=show_booking_button,
            suggested_reason=suggested_reason_text,
            context_type=session.context_type if session.is_session_valid() else None
        )

    except Exception as e:
        print(f"Chat error: {str(e)}")
        import traceback
        traceback.print_exc()
        # Provide helpful error response instead of crashing
        error_response = "I apologize for the technical issue. Please try again or contact KG Hospital directly at 0422-2324105 for assistance."
        return ChatResponse(
            response=error_response,
            timestamp=datetime.now().isoformat(),
            is_appointment_request=False,
            appointment_id=None
        )

# =============================================================================
# RESPONSE FORMATTER
# =============================================================================
def format_response_text(text: str) -> str:
    """Format chatbot output into clean, ChatGPT-like layout for React frontend."""
    import re
    if not text:
        return "I'm happy to assist. You can also contact KG Hospital for detailed guidance."

    original_text = text.strip()
    
    # Check if this contains table content
    has_markdown_table = ('|' in original_text and '---' in original_text)
    has_table_request = 'table format' in original_text.lower()
    
    if has_markdown_table or has_table_request:
        lines = original_text.split('\n')
        cleaned_lines = []
        in_table = False
        
        for line in lines:
            stripped_line = line.strip()
            
            if stripped_line.startswith('|') and stripped_line.count('|') >= 3:
                if not in_table:
                    in_table = True
                cleaned_lines.append(line)
                continue
                
            if stripped_line.startswith('|') and '---' in stripped_line:
                cleaned_lines.append(line)
                continue
                
            if in_table and not stripped_line.startswith('|'):
                in_table = False
                
            if not stripped_line.startswith('|') or not in_table:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    # Fix broken words
    text = re.sub(r'([a-zA-Z])\s*\n\s*s\b', r'\1s', original_text)
    text = re.sub(r'([a-zA-Z])\s*\n\s*([a-z]+)', r'\1\2', text)
    text = re.sub(r'([a-zA-Z,])\s*\n\s*([a-z][^A-Z]*)', r'\1 \2', text)
    text = re.sub(r'(\d+)[\.\]]\s*\n+\s*', r'\1. ', text)
    text = re.sub(r',?\s*(?:ID|Ext|Extension):\s*\d+', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def add_actionable_elements(text: str) -> str:
    """Add special markers for actionable elements like phone numbers, doctor profiles, locations."""
    # Add markers for phone numbers
    phone_pattern = r'(\+?\d{1,3}[-.\s]?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4,})'
    text = re.sub(phone_pattern, r'[TEL:\1]', text)
    
    # Specialty map
    specialty_map = {
        'cardiologist': 'cardiologist',
        'cardiology': 'cardiologist',
        'neurologist': 'neurologist',
        'neurology': 'neurologist',
        'orthopedic': 'orthopedic-surgeon',
        'orthopedics': 'orthopedic-surgeon',
        'pediatrician': 'pediatrician',
        'pediatrics': 'pediatrician',
        'radiologist': 'radiologist',
        'radiology': 'radiologist',
        'general surgeon': 'general-surgeon',
        'surgery': 'general-surgeon',
        'surgeon': 'general-surgeon',
        'oncologist': 'oncologist',
        'oncology': 'oncologist',
        'gynecologist': 'gynecologist',
        'gynecology': 'gynecologist',
        'dermatologist': 'dermatologist',
        'dermatology': 'dermatologist',
        'ent': 'ent-specialist',
        'ent specialist': 'ent-specialist',
        'ophthalmologist': 'ophthalmologist',
        'ophthalmology': 'ophthalmologist',
        'psychiatrist': 'psychiatrist',
        'psychiatry': 'psychiatrist',
        'urologist': 'urologist',
        'urology': 'urologist',
        'gastroenterologist': 'gastroenterologist',
        'gastroenterology': 'gastroenterologist',
        'pulmonologist': 'pulmonologist',
        'pulmonology': 'pulmonologist',
        'endocrinologist': 'endocrinologist',
        'endocrinology': 'endocrinologist',
        'nephrologist': 'nephrologist',
        'nephrology': 'nephrologist',
        'anesthesiologist': 'anesthesiologist',
        'anesthesiology': 'anesthesiologist'
    }
    
    lines = text.split('\n')
    processed_lines = []
    current_specialty = None
    
    for line in lines:
        line_lower = line.lower()
        for specialty_key in specialty_map.keys():
            if specialty_key in line_lower:
                current_specialty = specialty_map[specialty_key]
                break
        
        doctor_pattern = r'((?:Dr\.?|Doctor)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)(?:\s+\.?([A-Z]))?)(?=\s*(?:\(|,|-|$|\n|;|:))'
        
        def replace_doctor(match):
            full_match = match.group(0).strip()
            doctor_name = match.group(2).strip()
            suffix = match.group(3) if match.group(3) else ''
            
            specialty_slug = current_specialty
            
            complete_name = doctor_name
            if suffix:
                complete_name = f"{doctor_name} {suffix}"
            
            name_slug = complete_name.lower()
            name_slug = re.sub(r'\s+', '-', name_slug)
            name_slug = re.sub(r'-+', '-', name_slug)
            name_slug = name_slug.strip('-')
            name_slug = f"dr-{name_slug}"
            
            if specialty_slug:
                return f'[DOCTORPROFILE:{full_match}|{specialty_slug}|{name_slug}]'
            else:
                return full_match
        
        processed_line = re.sub(doctor_pattern, replace_doctor, line)
        processed_lines.append(processed_line)
    
    text = '\n'.join(processed_lines)
    
    doctor_profile_count = text.count('[DOCTORPROFILE:')
    if doctor_profile_count >= 3:
        if not '[DOCTORSLIST:' in text:
            text += '\n\n[DOCTORSLIST:For complete doctors list, visit our website]'
    
    department_pattern = r'^\s*\d+[\.)]\s+[A-Z]'
    department_count = len(re.findall(department_pattern, text, re.MULTILINE))
    
    if department_count >= 3:
        if not '[DEPARTMENTSLIST:' in text:
            text += '\n\n[DEPARTMENTSLIST:For complete departments list, visit our website]'
    
    location_keywords = ['No. 5, Arts College Road', 'Arts College Road, Coimbatore']
    for keyword in location_keywords:
        if keyword in text:
            text = text.replace(keyword, f'[LOCATION:{keyword}]')
            break
    
    emergency_pattern = r'(emergency|ambulance|helpline)[\s:]+(\+?\d[\d\s-]+)'
    text = re.sub(emergency_pattern, r'\1: [EMERGENCY:\2]', text, flags=re.IGNORECASE)
    
    return text

# =============================================================================
# OTHER ENDPOINTS
# =============================================================================
@app.get("/")
async def root():
    return {
        "message": "KG Hospital AI Chatbot API",
        "status": "running",
        "version": "1.0.0",
        "firebase_initialized": FIREBASE_INITIALIZED,
        "documents_loaded": len(loaded_documents) > 0,
        "active_sessions": len(user_sessions)
    }

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    allowed_extensions = ['.pdf', '.csv', '.xlsx', '.xls']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}"
        )

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
    temp_file_path = temp_file.name

    try:
        content = await file.read()
        temp_file.write(content)
        temp_file.close()

        success, message = upload_file_to_firebase(temp_file_path, file.filename)

        if success:
            reload_success, reload_message = reload_all_documents()
            os.remove(temp_file_path)

            if reload_success:
                return {"message": f"Document uploaded and processed successfully: {message}",
                        "reload_status": reload_message, "filename": file.filename}
            else:
                return {"message": f"Document uploaded but processing failed: {reload_message}",
                        "filename": file.filename}
        else:
            os.remove(temp_file_path)
            raise HTTPException(status_code=500, detail=message)

    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/documents")
async def list_documents():
    documents = list_firebase_files()
    return {"documents": documents, "count": len(documents), "firebase_status": FIREBASE_INITIALIZED}

@app.post("/reload-documents")
async def reload_documents_endpoint():
    success, message = reload_all_documents()
    if success:
        return {"message": message, "status": "success", "documents_loaded": len(loaded_documents)}
    else:
        raise HTTPException(status_code=500, detail=message)

@app.get("/system/status")
async def system_status():
    return {
        "firebase_initialized": FIREBASE_INITIALIZED,
        "documents_loaded": len(loaded_documents),
        "vectorstore_ready": vectorstore is not None,
        "conversation_chain_ready": conversation_chain is not None,
        "groq_api_configured": bool(os.getenv("GROQ_API_KEY")),
        "active_sessions": len(user_sessions),
        "timestamp": datetime.now().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    print("Starting KG Hospital Chatbot API...")
    print(f"Firebase Status: {'Connected' if FIREBASE_INITIALIZED else 'Not Connected'}")

    if FIREBASE_INITIALIZED:
        print("Loading initial documents...")
        success, message = reload_all_documents()
        if success:
            print(message)
        else:
            print(message)

    print("KG Hospital Chatbot API is ready!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="info")