# main.py - No Authentication Version
import re
import os
import tempfile
import time
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, storage
try:
    from firebase_admin import firestore as _firestore
except Exception:
    _firestore = None
from dotenv import load_dotenv
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
from langchain_community.document_loaders import UnstructuredPDFLoader, PyPDFLoader
from langchain_text_splitters.character import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain

# =============================================================================
# CONFIGURATION & INITIALIZATION
# =============================================================================
load_dotenv()

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

# =============================================================================
# DOCUMENT PROCESSING FUNCTIONS
# =============================================================================
def load_document(file_path: str):
    documents = []
    file_name = os.path.basename(file_path)

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

def setup_vectorstore(documents):
    if not documents:
        raise ValueError("No documents provided for vectorstore creation")

    print(f"Processing {len(documents)} document pages...")

    text_splitter = CharacterTextSplitter(
        separator='\n',
        chunk_size=800,
        chunk_overlap=100,
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
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )

    memory = ConversationBufferMemory(
        llm=llm,
        output_key='answer',
        memory_key='chat_history',
        return_messages=True
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        verbose=False,
        return_source_documents=False
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

        for blob in blobs:
            if blob.name.lower().endswith('.pdf'):
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

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
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
                os.remove(temp_file_path)
            except Exception as e:
                print(f"Failed to process {file_name}: {e}")
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

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
def detect_query_type(message: str):
    """Detect if user is asking for doctors, departments, or both."""
    message_lower = message.lower().strip()
    
    # Doctor patterns - more comprehensive
    doctor_patterns = ['doctor', 'doc', 'physician', 'specialist', 'dr.', 'dr ', 'doctors list', 'all doctors']
    # Department patterns - more comprehensive
    dept_patterns = ['department', 'dept', 'division', 'unit', 'departments list', 'all departments']
    
    has_doctor = any(pattern in message_lower for pattern in doctor_patterns)
    has_dept = any(pattern in message_lower for pattern in dept_patterns)
    
    # Check for list/show requests - more comprehensive patterns
    list_keywords = ['list', 'show', 'all', 'available', 'what are', 'tell me', 'give me', 'display']
    is_list_request = any(word in message_lower for word in list_keywords)
    
    # Also check for direct requests like "doctors", "departments", "docs list"
    direct_doctor_request = (
        message_lower in ['doctors', 'doctor', 'docs', 'doc', 'all doctors', 'doctors list', 'list doctors'] or
        message_lower.startswith(('list of doctor', 'list doctor', 'show doctor', 'all doctor'))
    )
    
    direct_dept_request = (
        message_lower in ['departments', 'department', 'depts', 'dept', 'all departments', 'departments list', 'list departments'] or
        message_lower.startswith(('list of department', 'list department', 'show department', 'all department'))
    )
    
    # Determine what to return
    if (is_list_request or direct_doctor_request or direct_dept_request):
        if (has_doctor and has_dept) or (direct_doctor_request and direct_dept_request):
            return 'both'
        elif has_doctor or direct_doctor_request:
            return 'doctors'
        elif has_dept or direct_dept_request:
            return 'departments'
    
    return None

def get_doctors_list():
    """Return a formatted list of doctors with their specialties."""
    if not conversation_chain or not vectorstore:
        return None
    
    try:
        # Query the vectorstore for doctor information
        retriever = vectorstore.as_retriever(search_kwargs={'k': 10})
        docs = retriever.invoke("list all doctors and their specialties")
        
        # Extract doctor information from the retrieved documents
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Use LLM to extract just doctor names and specialties
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        prompt = f"""Based on the following context, list ONLY the doctor names and their specialties.
Format: Dr. Name - Specialty

Do not add any introductory text, notes, or additional information.
Just list the doctors in a numbered format.

Context:
{context}

Doctors list:"""
        
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
        # Query the vectorstore for department information
        retriever = vectorstore.as_retriever(search_kwargs={'k': 8})
        docs = retriever.invoke("list all hospital departments")
        
        # Extract department information from the retrieved documents
        context = "\n\n".join([doc.page_content for doc in docs])
        
        # Use LLM to extract just department names
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
        prompt = f"""Based on the following context, list ONLY the department names.

Do not add any introductory text, notes, explanations, or additional information.
Do not add phrases like "may not be exhaustive" or "additional departments not listed".
Just list the departments in a numbered format.

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
            elif query_type == 'both':
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
                "visitor": """You are a helpful KG Hospital AI assistant helping visitors.
                
                Provide clear information about:
                - Visiting hours and policies
                - Hospital location and directions
                - Parking information and facilities
                - Hospital amenities and services
                
                Format your answers using natural sentences and organize information clearly.
                Only mention limitations or add notes when you genuinely don't have specific information or when the data is incomplete.
                Do NOT add cautionary notes like "may not be exhaustive" or "additional items not listed" when you have provided a complete answer.
                If information is unavailable, kindly suggest the visitor reach the hospital's help desk for more information.""",

                "staff": """You are a helpful KG Hospital AI assistant helping hospital staff.
                
                Provide organized information about:
                - Patient inquiry responses
                - Department information and contacts
                - Emergency protocols and procedures
                - Hospital policies and guidelines
                
                Format your answers using clear sentences and organize information logically.
                Only add notes about data limitations when you are genuinely uncertain or missing critical information.
                Do NOT add unnecessary disclaimers like "may not be exhaustive" when you have provided complete information from the context.
                If details are unavailable, politely mention that the staff can consult the hospital administration for accurate information.""",

                "admin": """You are a helpful KG Hospital AI assistant helping administrators.
                
                Provide comprehensive information about:
                - Hospital operations and management
                - System status and analytics
                - Administrative procedures
                - Staff coordination and policies
                
                Format your output using clear paragraphs and organize information systematically.
                Only include notes about data limitations when the information is genuinely incomplete or uncertain.
                Avoid adding generic disclaimers when you have provided a complete answer from the available context.
                If certain data is not accessible, inform that the admin team can review internal records or contact support for help."""
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

        # Detect appointment intent and save appointment if details are present
        is_appointment = False
        new_appointment_id = None
        try:
            wants_appointment = False
            if 'detect_appointment_intent' in globals() and callable(detect_appointment_intent):
                wants_appointment = bool(detect_appointment_intent(message.message))
            # If intent detected, save appointment
            if wants_appointment:
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
                            # Append a friendly confirmation to the AI's answer
                            confirmation = (f"\n\nAppointment request saved successfully.\n"
                                            f"Preferred: {preferred_date} at {preferred_time}\n"
                                            f"Reason: {reason}\n"
                                            f"Reference ID: {new_appointment_id}")
                            if phone_number:
                                confirmation += f"\nContact: [TEL:{phone_number}]"
                            formatted_answer = f"{formatted_answer}\n{confirmation}"
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
            appointment_id=new_appointment_id
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
    
    # STEP 3: ONLY fix numbered lists where number is completely separate from name
    # "1.\n\nBalasubramanian C" -> "1. Balasubramanian C"
    text = re.sub(r'(\d+\.)\s*\n+\s*([A-Za-z][A-Za-z\s]*?)(?=\s*\n\s*\d+\.|\s*$)', r'\1 \2', text)
    
    # STEP 4: Clean up excessive whitespace
    text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces to single space
    text = re.sub(r'\n{3,}', '\n\n', text)  # Multiple newlines to double newline
    
    # STEP 5: Just return the cleaned text - no complex processing
    return text.strip()

def add_actionable_elements(text: str) -> str:
    """Add special markers for actionable elements like phone numbers, doctor profiles, locations."""
    # Add markers for phone numbers (will be rendered as clickable tel: links in frontend)
    phone_pattern = r'(\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9})'
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
    
    # Add markers for hospital address/location
    location_keywords = ['KG Hospital', 'hospital address', 'hospital location', 'No. 5, Arts College Road', 'Coimbatore']
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
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
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
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")