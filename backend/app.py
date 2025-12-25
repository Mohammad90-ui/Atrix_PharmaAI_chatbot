"""
FastAPI Backend for Clinical Trial Query Chatbot
Provides /chat endpoint for grounded question-answering.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
from pathlib import Path

from data_loader import DataLoader
from retriever import Retriever
from chatbot_engine import ChatbotEngine
from logger import ChatLogger


from contextlib import asynccontextmanager

# Global components
data_loader = None
retriever = None
chatbot_engine = None
chat_logger = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize components on startup and clean up on shutdown."""
    global data_loader, retriever, chatbot_engine, chat_logger
    
    # Paths to data files
    base_path = Path(__file__).parent
    excel_path = base_path / "Pharma_Clinical_Trial_AllDrugs.xlsx"
    docx_path = base_path / "Pharma_Clinical_Trial_Notes.docx"
    
    # Load data
    print("Loading data sources...")
    data_loader = DataLoader(str(excel_path), str(docx_path))
    excel_df, doc_chunks, excel_chunks = data_loader.load_all()
    
    print(f"Loaded {len(doc_chunks)} doc chunks and {len(excel_chunks)} excel chunks")
    
    # Build retrieval index
    print("Building retrieval indices...")
    retriever = Retriever()
    retriever.build_index(doc_chunks, excel_chunks)
    
    # Initialize chatbot engine
    chatbot_engine = ChatbotEngine()
    
    # Initialize logger
    chat_logger = ChatLogger()
    
    print("Chatbot ready!")
    
    yield
    
    # Cleanup (if any)
    print("Shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="Clinical Trial Query Chatbot API",
    description="Pharma-focused chatbot for querying clinical trial data",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    user_message: str


class ChatResponse(BaseModel):
    session_id: str
    assistant_message: str
    source_citation: str
    retrieved_count: int
    is_clarification: bool = False
    is_unknown: bool = False


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Clinical Trial Query Chatbot API is running"
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    
    Args:
        request: ChatRequest with session_id and user_message
        
    Returns:
        ChatResponse with assistant message, source citation, and metadata
    """
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    user_message = request.user_message.strip()
    
    if not user_message:
        raise HTTPException(status_code=400, detail="User message cannot be empty")
    
    # Resolve pronouns using conversation history
    enhanced_query = chatbot_engine._resolve_pronouns(user_message, session_id)
    
    # Check if clarification is needed
    needs_clarification, clarification_msg = retriever.needs_clarification(enhanced_query)
    
    if needs_clarification:
        # Log clarification request
        chat_logger.log_query(
            session_id=session_id,
            user_message=user_message,
            assistant_message=clarification_msg,
            source_used="none",
            retrieved_count=0,
            is_clarification=True
        )
        
        return ChatResponse(
            session_id=session_id,
            assistant_message=clarification_msg,
            source_citation="none",
            retrieved_count=0,
            is_clarification=True
        )
    
    # Classify query to determine source preference
    source_preference = retriever.classify_query(enhanced_query)
    
    # Retrieve relevant context
    doc_results, excel_results = retriever.search(
        enhanced_query,
        top_k=5,
        source_preference=source_preference
    )
    
    # Get best results
    best_results, primary_source = retriever.get_best_results(
        doc_results, excel_results, max_results=3
    )
    
    # Generate response
    assistant_message, source_citation = chatbot_engine.generate_response(
        user_message,
        best_results,
        primary_source,
        session_id
    )
    
    # Determine if response is unknown or safety refusal
    is_unknown = "don't know based on the available data" in assistant_message
    is_safety_refusal = "cannot provide medical advice" in assistant_message
    
    # Log the interaction
    chat_logger.log_query(
        session_id=session_id,
        user_message=user_message,
        assistant_message=assistant_message,
        source_used=source_citation,
        retrieved_count=len(best_results),
        is_unknown=is_unknown,
        is_safety_refusal=is_safety_refusal
    )
    
    return ChatResponse(
        session_id=session_id,
        assistant_message=assistant_message,
        source_citation=source_citation,
        retrieved_count=len(best_results),
        is_unknown=is_unknown
    )


@app.get("/api/metrics")
async def get_metrics():
    """Get chatbot usage metrics."""
    return chat_logger.get_metrics_summary()


@app.post("/api/reset_session")
async def reset_session(session_id: str):
    """Reset conversation history for a session."""
    if session_id in chatbot_engine.conversation_history:
        del chatbot_engine.conversation_history[session_id]
    return {"status": "success", "message": f"Session {session_id} reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
