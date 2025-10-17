# main.py - No Authentication Version
import re
import os
import tempfile
import time
from datetime import datetime
from typing import List

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
        # Try package-style import if Backend is a package
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
            # Read CSV to format each row as a structured document
            df = pd.read_csv(file_path)
            print(f"Loaded CSV with {len(df)} rows and columns: {list(df.columns)}")
            
            # Convert each row to a structured text document
            from langchain.schema import Document
            documents = []
            for idx, row in df.iterrows():
                # Create structured text from row data
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
            # Read Excel to format each row as a structured document
            df = pd.read_excel(file_path)
            print(f"Loaded Excel with {len(df)} rows and columns: {list(df.columns)}")
            
            # Convert each row to a structured text document
            from langchain.schema import Document
            documents = []
            for idx, row in df.iterrows():
                # Create structured text from row data
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

    # Optimal K value for ALL queries - balanced between coverage and noise
    # Higher K = more context but potential noise
    # Lower K = precise but might miss information
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 10,           # Retrieve 10 most relevant diverse documents for ALL queries
            "fetch_k": 25,     # Consider 25 candidates for MMR selection
            "lambda_mult": 0.5 # Balance relevance vs diversity
        }
    )

    memory = ConversationBufferMemory(
        llm=llm,
        output_key='answer',
        memory_key='chat_history',
        return_messages=True
    )

    # Optimized RAG prompt template following industry best practices
    qa_prompt_template = """You are an AI assistant for KG Hospital. Your role is to provide accurate, helpful information to hospital visitors, staff, and administrators.

CRITICAL INSTRUCTIONS:
1. Use ONLY the information provided in the Context below to answer questions
2. If the Context doesn't contain the answer, respond with: "I don't have that specific information in my current knowledge base. Please contact KG Hospital at 0422-2324105 or visit the front desk for accurate information."
3. Never make up or assume information not present in the Context
4. Be concise, clear, and professional
5. For medical advice: Always say "Please consult with a doctor for medical advice"

Context (Retrieved Information):
{context}

Previous Conversation:
{chat_history}

Current Question: {question}

Instructions for Response:
- If answering about doctors: Include name, specialty, and contact if available
- If answering about departments: Include location, services, and contact hours
- If answering about appointments: Guide through the booking process
- If answering about facilities: Be specific about location and timings
- For lists (doctors, departments, etc.): Always use numbered format (1. 2. 3.) NOT bullet points
- Keep responses under 200 words unless listing requires more

Answer:"""

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
        
        # Supported file extensions
        supported_extensions = ('.pdf', '.csv', '.xlsx', '.xls')

        for blob in blobs:
            # Check if file has a supported extension
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

        # Get the original file extension to preserve it
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
# HELPER FUNCTIONS FOR SPECIFIC QUERIES
# =============================================================================
def detect_information_query(message: str) -> bool:
    """Detect if user is asking for information about symptoms, doctors, or treatment.
    These queries should return information first before offering appointment booking."""
    message_lower = message.lower().strip()
    
    # Keywords indicating user wants information first
    info_keywords = [
        'who should i consult', 'which doctor', 'what doctor', 'who to consult',
        'who can i see', 'who do i see', 'which specialist',
        'fever', 'headache', 'pain', 'cold', 'cough', 'symptom',
        'treatment for', 'cure for', 'specialist for', 'doctor for',
        'suffering from', 'have', 'got', 'experiencing',
        'diabetes', 'blood pressure', 'heart', 'stomach', 'back pain',
        'chest pain', 'throat', 'skin', 'allergy'
    ]
    
    return any(keyword in message_lower for keyword in info_keywords)

def detect_query_type(message: str):
    """Detect if user is asking for COMPLETE doctors/departments list ONLY.
    Returns None for specific questions that need RAG processing."""
    message_lower = message.lower().strip()
    
    # IMPORTANT: Check for specific questions first - these should use RAG, not bypass it
    specific_question_indicators = [
        'blood bank', 'cardiology', 'neurology', 'orthopedic', 'pediatric', 'radiology',
        'surgery', 'emergency', 'oncology', 'gynecology', 'dermatology', 'diabetology',
        'psychiatry', 'nephrology', 'urology', 'gastroenterology', 'pulmonology',
        'do you have', 'is there', 'does', 'can i', 'how do', 'when', 'where', 'why',
        'what is', 'what are the', 'tell me about', 'information about', 'details about',
        'who is', 'which doctor', 'specific', 'particular', 'specializes in', 'expert in'
    ]
    
    # If it's a specific question about a department or specialty, use RAG
    if any(indicator in message_lower for indicator in specific_question_indicators):
        return None  # Let RAG handle specific questions
    
    # Only proceed if it's a GENERAL list request
    # Very specific patterns for complete list requests
    complete_list_patterns = [
        # Exact matches only
        message_lower == 'doctors',
        message_lower == 'doctor',
        message_lower == 'docs',
        message_lower == 'doc',
        message_lower == 'departments',
        message_lower == 'department',
        message_lower == 'depts',
        message_lower == 'dept',
        # List requests without specifics
        message_lower in ['list doctors', 'list all doctors', 'all doctors', 'doctors list', 
                          'doctor list', 'docs list', 'doc list', 'doctors', 'show doctors', 
                          'show all doctors', 'give me doctors', 'show me doctors'],
        message_lower in ['list departments', 'list all departments', 'all departments', 
                          'departments list', 'show departments', 'show all departments', 
                          'give me departments'],
        # Combined requests
        'doctors with their dept' in message_lower and len(message_lower) < 40,
        'docs with their dept' in message_lower and len(message_lower) < 40,
    ]
    
    # Check if it's a complete list request
    is_complete_list = any(complete_list_patterns)
    
    if not is_complete_list:
        return None  # Use RAG for anything else
    
    # Determine type only for complete list requests
    if 'doctors with their dept' in message_lower or 'docs with their dept' in message_lower:
        return 'doctors'
    elif any(word in message_lower for word in ['doctors', 'doctor', 'docs', 'doc']) and \
         any(word in message_lower for word in ['departments', 'department']):
        return 'separate'
    elif any(word in message_lower for word in ['doctors', 'doctor', 'docs', 'doc']):
        return 'doctors'
    elif any(word in message_lower for word in ['departments', 'department', 'depts', 'dept']):
        return 'departments'
    
    return None

def get_doctors_list():
    """Return a formatted list of doctors with their specialties."""
    if not conversation_chain or not vectorstore:
        return None
    
    try:
        # Use the same retriever configuration as main chain for consistency
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 10, 'fetch_k': 25, 'lambda_mult': 0.5}
        )
        docs = retriever.invoke("list all doctors and their specialties")
        
        # Extract doctor information from the retrieved documents
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Use LLM to extract just doctor names and specialties
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        prompt = f"""Based on the following context, list ONLY the doctor names with their specialties/departments on the SAME line.

Format each entry as: Dr. Name, Specialty/Department

Important rules:
- Each doctor's specialty MUST be on the same line as their name
- Use format: "Dr. Name, Specialty" (all on one line, separated by comma)
- Do NOT include IDs, employee numbers, extensions, or contact information
- Do not add any introductory text, notes, or additional information
- Do not add phrases like "may not be exhaustive" or disclaimers
- Use NUMBERED format (1. 2. 3.) NOT bullet points (•)

Context:
{context}

Doctors:"""
        
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"Error getting doctors list: {e}")
        return None

def get_departments_list():
    """Return a formatted list of departments."""
    if not conversation_chain or not vectorstore:
        return None
    
    try:
        # Use the same retriever configuration as main chain for consistency
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={'k': 10, 'fetch_k': 25, 'lambda_mult': 0.5}
        )
        docs = retriever.invoke("list all hospital departments")
        
        # Extract department information from the retrieved documents
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Use LLM to extract just department names
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        prompt = f"""Based on the following context, list ONLY the department names.

Do not add any introductory text, notes, explanations, or additional information.
Do not add phrases like "may not be exhaustive" or "additional departments not listed".
Use NUMBERED format (1. 2. 3.) NOT bullet points (•).

Context:
{context}

Departments:"""
        
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        print(f"Error getting departments list: {e}")
        return None

# =============================================================================
# CHAT ENDPOINT WITH FORMATTED OUTPUT
# =============================================================================
@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Chat endpoint with user-friendly, readable responses."""
    global conversation_chain

    try:
        print(f"Chat request ({message.user_role}): {message.message}")
        
        # Check if this is a simple greeting - return hardcoded response
        greeting_patterns = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'greetings']
        message_lower = message.message.lower().strip()
        is_greeting = any(message_lower == pattern or message_lower.startswith(f"{pattern} ") or message_lower.startswith(f"{pattern}!") for pattern in greeting_patterns)
        
        if is_greeting:
            # Return role-specific greeting without any lists or extra info
            greeting_responses = {
                "visitor": "Hello! I'm here to help you with KG Hospital information. How can I assist you today?",
                "staff": "Hello. How can I help you today?",
                "admin": "Hello. How can I assist you with hospital management today?"
            }
            greeting_answer = greeting_responses.get(message.user_role, greeting_responses["visitor"])
            return ChatResponse(
                response=greeting_answer,
                timestamp=datetime.now().isoformat(),
                is_appointment_request=False,
                appointment_id=None
            )
        
        # Check if this is a specific doctors/departments list request
        query_type = detect_query_type(message.message)
        
        if query_type:
            answer = ""
            if query_type == 'doctors':
                doctors = get_doctors_list()
                if doctors:
                    answer = doctors
            elif query_type == 'departments':
                departments = get_departments_list()
                if departments:
                    answer = departments
            elif query_type == 'separate':
                doctors = get_doctors_list()
                departments = get_departments_list()
                if doctors and departments:
                    answer = f"**Doctors:**\n\n{doctors}\n\n**Departments:**\n\n{departments}"
                elif doctors:
                    answer = doctors
                elif departments:
                    answer = departments
            
            # If we got a specific answer, format and return it
            if answer:
                formatted_answer = format_response_text(answer)
                formatted_answer = add_actionable_elements(formatted_answer)
                
                return ChatResponse(
                    response=formatted_answer,
                    timestamp=datetime.now().isoformat(),
                    is_appointment_request=False,
                    appointment_id=None
                )
        
        # Continue with normal RAG processing for other queries

        if conversation_chain:
            response = conversation_chain.invoke({'question': message.message})
            answer = response.get('answer', '')
        else:
            llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

            system_prompts = {
                "visitor": """You are KG Hospital's AI Assistant for Visitors.

ROLE: Help visitors with general hospital information in a friendly, conversational way.

GREETING RESPONSES (for "hi", "hello", "hey", "good morning", "good evening"):
- Respond ONLY with: "Hello! I'm here to help you with KG Hospital information. How can I assist you today?"
- ABSOLUTELY NO DOCTOR LISTS - wait for them to ask
- ABSOLUTELY NO DEPARTMENT LISTS - wait for them to ask
- ABSOLUTELY NO EXAMPLES - just greet and ask how to help
- DO NOT include hospital phone numbers in greetings
- Keep greetings to 1-2 sentences maximum

RESPONSE GUIDELINES:
✓ Be warm, welcoming, and conversational
✓ For greetings: Keep it simple, ask how you can help
✓ For specific questions: Provide clear, direct answers
✓ Use simple language (avoid medical jargon)
✓ Only provide contact info when relevant to the query

TOPICS YOU HANDLE:
• Visiting hours and policies
• Hospital location, directions, and parking
• Facilities and amenities (cafeteria, restrooms, ATM)
• General inquiries and navigation
• Appointment booking guidance
• Doctor and department information (only when asked)

WHAT YOU DON'T HANDLE:
✗ Medical advice (refer to doctors)
✗ Patient medical records (privacy protected)
✗ Emergency situations (mention emergency contact only if asked)

If you don't know: "I don't have that information right now. You can visit our front desk or check our official website for more details."

Remember: Be helpful, accurate, and conversational. Don't overwhelm with unsolicited information.""",

                "staff": """You are KG Hospital's AI Assistant for Hospital Staff.

ROLE: Support staff with operational information, protocols, and resource access.

GREETING RESPONSES (for "hi", "hello", "hey", "good morning", "good evening"):
- Respond ONLY with: "Hello. How can I help you today?"
- ABSOLUTELY NO LISTS of any kind in greetings
- Keep greetings to 1 sentence only

RESPONSE GUIDELINES:
✓ Be precise and professional
✓ Prioritize efficiency - staff are busy
✓ For greetings: Brief, professional
✓ For queries: Include relevant policy references
✓ Provide step-by-step instructions when needed
✓ Format: Use numbered lists for procedures

TOPICS YOU HANDLE:
• Department contacts and extensions
• Emergency protocols and procedures
• Hospital policies and guidelines
• Equipment and resource locations
• Staff scheduling information
• Patient inquiry guidance (non-medical)

If you don't know: "This information is not in my current database. Please contact hospital administration at ext. 2100 or check the staff portal."

Example Response:
"For a Code Blue emergency:
1. Call ext. 2222 immediately
2. Start CPR if trained
3. Get the crash cart from the nearest nursing station
4. Clear the area for the response team
The ICU team responds within 2 minutes. See Emergency Protocol Manual Section 4.2 for full procedures."

Remember: You support healthcare professionals - be accurate, quick, and reliable.""",

                "admin": """You are KG Hospital's AI Assistant for Administrators.

ROLE: Provide management-level information for hospital operations and decision-making.

GREETING RESPONSES (for "hi", "hello", "hey", "good morning", "good evening"):
- Respond ONLY with: "Hello. How can I assist you with hospital management today?"
- ABSOLUTELY NO LISTS of any kind in greetings
- ABSOLUTELY NO CONTACT INFORMATION in greetings
- Keep greetings to 1 sentence only

RESPONSE GUIDELINES:
✓ Be professional, concise, and direct
✓ For greetings: Simple acknowledgment, no extra information
✓ For data requests: Provide comprehensive, structured information
✓ Include metrics and statistics when relevant
✓ NO public hospital phone numbers in responses (admins have internal access)

TOPICS YOU HANDLE:
• Hospital operations and performance
• Department coordination and resources
• Administrative procedures and policies
• Staff management and scheduling
• System status and analytics
• Doctor and department listings (only when requested)

RESPONSE APPROACH:
- For simple greetings: Brief professional response
- For data queries: Comprehensive structured information
- For unknowns: "This data is not available. Check internal management reports or department heads."

Remember: Admins need efficiency and accuracy, not marketing content. Be concise."""
            }

            system_prompt = system_prompts.get(message.user_role, system_prompts["visitor"])
            full_prompt = f"{system_prompt}\n\nUser Question: {message.message}\n\nResponse:"
            response = llm.invoke(full_prompt)
            answer = response.content

        if not answer.strip() or "I don't know" in answer or "I'm not sure" in answer:
            answer = ("I'm happy to help with your query. "
                      "While I don’t have specific information on that at the moment, "
                      "you can contact KG Hospital’s support or visit the front desk anytime for assistance.")

        formatted_answer = format_response_text(answer)
        
        # Add actionable elements (phone numbers, locations, etc.)
        formatted_answer = add_actionable_elements(formatted_answer)

        # Detect appointment intent and information query
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
            if has_info_query and wants_appointment:
                # Don't immediately book - show info with booking button
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
                }
                
                message_lower = message.message.lower()
                for keyword, reason in reason_keywords.items():
                    if keyword in message_lower:
                        suggested_reason_text = reason
                        break
                
                # Add appointment button prompt to the answer
                formatted_answer += "\n\nWould you like to book an appointment with one of these doctors?"
                
            # SIMPLE APPOINTMENT REQUEST: User only wants to book
            elif wants_appointment:
                # Extract simple details including phone number
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
                            # Extract name from message (look for patterns like "for [name]", "name: [name]", or just first word)
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
                            
                            # Replace the entire response with clean success message
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
        except Exception:
            pass

        # Save chat history via admin module (in-memory by default)
        try:
            if save_chat_history:
                save_chat_history(
                    user_id=message.user_id or "anonymous",
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
            suggested_reason=suggested_reason_text
        )

    except Exception as e:
        print(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

# =============================================================================
# RESPONSE FORMATTER
# =============================================================================
def format_response_text(text: str) -> str:
    """Format chatbot output into clean, ChatGPT-like layout for React frontend."""
    import re
    if not text:
        return "I'm happy to assist. You can also contact KG Hospital for detailed guidance."

    # Clean up the text first
    original_text = text.strip()
    
    # Check if this contains table content
    has_markdown_table = ('|' in original_text and '---' in original_text)
    has_table_request = 'table format' in original_text.lower()
    
    if has_markdown_table or has_table_request:
        # For table content, clean up but preserve the table structure
        lines = original_text.split('\n')
        cleaned_lines = []
        in_table = False
        
        for line in lines:
            stripped_line = line.strip()
            
            # Detect table start (header row with multiple |)
            if stripped_line.startswith('|') and stripped_line.count('|') >= 3:
                if not in_table:
                    # First table row - this starts our table
                    in_table = True
                cleaned_lines.append(line)  # Keep table rows
                continue
                
            # Detect table separator row
            if stripped_line.startswith('|') and '---' in stripped_line:
                cleaned_lines.append(line)  # Keep separator
                continue
                
            # If we're in a table and hit a non-table line, table ended
            if in_table and not stripped_line.startswith('|'):
                in_table = False
                
            # Always keep non-table content
            if not stripped_line.startswith('|') or not in_table:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    # STEP 1: Fix ALL broken words that got split (MOST IMPORTANT)
    # "department\ns" -> "departments"
    # "doctor\ns" -> "doctors" 
    # "service\ns" -> "services"
    # "hospital\ns" -> "hospitals"
    # Any word + \n + s = word + s
    text = re.sub(r'([a-zA-Z])\s*\n\s*s\b', r'\1s', original_text)
    
    # STEP 2: Fix other broken words (any letter + newline + lowercase letters)
    text = re.sub(r'([a-zA-Z])\s*\n\s*([a-z]+)', r'\1\2', text)
    
    # STEP 3: Fix broken sentences (words that should be on same line)
    # "The Hospital Has The Following\nDepartments:" -> "The Hospital Has The Following Departments:"
    text = re.sub(r'([a-zA-Z,])\s*\n\s*([a-z][^A-Z]*)', r'\1 \2', text)
    
    # STEP 3.5: Fix numbered lists where number is separated from content
    # "1.\n\nDr. Name" -> "1. Dr. Name"
    # "2]. \nDr. Name" -> "2. Dr. Name"
    text = re.sub(r'(\d+)[\.\]]\s*\n+\s*', r'\1. ', text)
    
    # STEP 3.6: Remove ID/extension information from doctor lists
    # ", ID: 1234" -> ""
    # ", Ext: 1234" -> ""
    text = re.sub(r',?\s*(?:ID|Ext|Extension):\s*\d+', '', text)
    
    # STEP 4: Clean up excessive whitespace
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
    text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines to double newline
    
    # STEP 5: Just return the cleaned text - no complex processing
    return text.strip()

def add_actionable_elements(text: str) -> str:
    """Add special markers for actionable elements like phone numbers, doctor profiles, locations."""
    # Add markers for phone numbers (only match actual phone numbers with 8+ digits, not short IDs)
    # Matches formats like: 0422-2324105, +91-9876543210, etc.
    phone_pattern = r'(\+?\d{1,3}[-.\s]?\(?\d{3,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{4,})'
    text = re.sub(phone_pattern, r'[TEL:\1]', text)
    
    # Map of specialties to URL-friendly slugs
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
    
    # Pattern to detect doctor with specialty context
    # Look for patterns like:
    # "Dr. Name (Specialty)" or "Dr. Name - Specialty" or "Dr. Name, Specialty"
    # or context from previous line mentioning specialty
    
    lines = text.split('\n')
    processed_lines = []
    current_specialty = None
    
    for line in lines:
        # Check if line mentions a specialty (for context)
        line_lower = line.lower()
        for specialty_key in specialty_map.keys():
            if specialty_key in line_lower:
                current_specialty = specialty_map[specialty_key]
                break
        
        # Enhanced Pattern to handle:
        # - "Dr. John Smith" (standard)
        # - "Dr. ARUN KUMAR U" (all caps with initial)
        # - "Dr. Balakrishnan .M" (name with suffix initial)
        # - "Dr. ASHNA ANN EAPEN" (all caps multi-word)
        # - "Dr. Kumudhini .D" (name with dot-initial suffix)
        # Pattern: Dr./Doctor + name + optional suffix (space + dot + letter OR space + letter)
        doctor_pattern = r'((?:Dr\.?|Doctor)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)(?:\s+\.?([A-Z]))?)(?=\s*(?:\(|,|-|$|\n|;|:))'
        
        def replace_doctor(match):
            full_match = match.group(0).strip()  # Full match including suffix
            doctor_name = match.group(2).strip()  # Main name part
            suffix = match.group(3) if match.group(3) else ''  # Suffix initial (if any)
            
            # Try to find specialty from current context
            specialty_slug = current_specialty
            
            # Convert doctor name to URL format
            # Build the complete name including suffix for URL
            complete_name = doctor_name
            if suffix:
                complete_name = f"{doctor_name} {suffix}"
            
            # Convert to slug: "ARUN KUMAR U" -> "arun-kumar-u"
            name_slug = complete_name.lower()
            name_slug = re.sub(r'\s+', '-', name_slug)  # spaces -> hyphens
            name_slug = re.sub(r'-+', '-', name_slug)  # multiple hyphens -> single
            name_slug = name_slug.strip('-')  # remove leading/trailing hyphens
            name_slug = f"dr-{name_slug}"
            
            if specialty_slug:
                # Format: [DOCTORPROFILE:Dr. Name Suffix|specialty-slug|dr-name-slug]
                return f'[DOCTORPROFILE:{full_match}|{specialty_slug}|{name_slug}]'
            else:
                # No specialty found, just return the name as-is
                return full_match
        
        # Replace doctor names in the line
        processed_line = re.sub(doctor_pattern, replace_doctor, line)
        processed_lines.append(processed_line)
    
    text = '\n'.join(processed_lines)
    
    # Check if this is a doctor listing (contains multiple doctor profile markers)
    doctor_profile_count = text.count('[DOCTORPROFILE:')
    
    # If listing multiple doctors (3 or more), also add a link to complete doctors list at the end
    if doctor_profile_count >= 3:
        if not '[DOCTORSLIST:' in text:
            text += '\n\n[DOCTORSLIST:For complete doctors list, visit our website]'
    
    # Add markers for hospital address/location (only for actual addresses, not "KG Hospital" name)
    # Only mark physical addresses, not every mention of "KG Hospital"
    location_keywords = ['No. 5, Arts College Road', 'Arts College Road, Coimbatore']
    for keyword in location_keywords:
        if keyword in text:
            text = text.replace(keyword, f'[LOCATION:{keyword}]')
            break  # Only mark first occurrence
    
    # Add markers for emergency numbers
    emergency_pattern = r'(emergency|ambulance|helpline)[\s:]+(\+?\d[\d\s-]+)'
    text = re.sub(emergency_pattern, r'\1: [EMERGENCY:\2]', text, flags=re.IGNORECASE)
    
    # Department markers disabled to avoid partial matches (e.g., "Surgery" in "Robotic Surgery")
    # Departments will display as plain text without clickable elements
    
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
        "documents_loaded": len(loaded_documents) > 0
    }

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    # Check if file format is supported
    allowed_extensions = ['.pdf', '.csv', '.xlsx', '.xls']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format. Allowed formats: {', '.join(allowed_extensions)}"
        )

    # Use the original file extension for temp file
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