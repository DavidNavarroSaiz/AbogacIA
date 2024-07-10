from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict
from document_downloader import DocumentDownloader
from utils_Chromadb import UtilsDB
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from utils_mongoDb import MongoDBUtils
from Embedding_Chain_Bot import EmbeddingChainChatBot
import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
app = FastAPI()

# Load existing chat sessions from MongoDB into user_chatbots
db_utils = MongoDBUtils()
user_chatbots = {}

unique_session_ids = db_utils.get_unique_session_ids()
for session_id in unique_session_ids:
    user_chatbots[session_id] = EmbeddingChainChatBot(session_id=session_id)
    print(f"Loaded existing user with session_id: {session_id}")

class DownloadRequest(BaseModel):
    temas_legales: Dict[str, int] = Field(
        default={"Divorcio": 10, "PQR": 2, "Abandono de bienes": 10, "Abandono de menores": 10},
        description="A dictionary where the keys are legal topics and the values are the number of documents to download for each topic."
    )

class DeleteRequest(BaseModel):
    filename: str

class SessionInput(BaseModel):
    session_id: str
    
class QuestionInput(BaseModel):
    """
    Pydantic model for incoming question input.
    """
    query: str
    session_id: str
    

@app.post("/download_documents/")
async def download_documents(request: DownloadRequest):
    try:
        downloader = DocumentDownloader(
            topics=request.temas_legales
        )
        downloader.run()
        return {"status": "success", "message": "Documents downloaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/delete_document/")
async def delete_document(request: DeleteRequest):
    try:
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        vectordb = Chroma(persist_directory="abogacia_data", embedding_function=OpenAIEmbeddings())
        utils_db = UtilsDB(vectordb)
        result = utils_db.delete_DB_document_and_file(request.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/load_chat_history")
async def load_chat_history(session_input: SessionInput):
    session_id = session_input.session_id
      # Retrieve the EmbeddingChainChatBot instance for the user or create a new instance if it doesn't exist
    if session_id not in user_chatbots:
        user_chatbots[session_id] = EmbeddingChainChatBot(session_id=session_id)
        print("new user created with session_id: ",session_id)
        chain_chatbot = user_chatbots[session_id]
        chain_chatbot.memory.chat_memory.add_ai_message("Hello, I'm AbogacIA Chatbot. \n How can i Help You today?")
        chat_history = chain_chatbot.load_chat_history()

    else:        
        chain_chatbot = user_chatbots[session_id]        
        chat_history = chain_chatbot.load_chat_history()

    return {"chat_history": chat_history}

@app.post("/ask_chain_bot")
def ask_chain_bot(question_input: QuestionInput):
    question = question_input.query
    session_id = question_input.session_id

    # Check if session_id exists in user_chatbots
    if session_id not in user_chatbots:
        error_message = f"Session with session_id '{session_id}' not found. Please create a new session."
        return {"error": error_message,"answer": ""}

    chain_chatbot = user_chatbots[session_id]
    
    response = "Please enter a valid question"  # Default response if query is not provided or an error occurs
    if question != "":
        embedding_chain_bot_response = chain_chatbot.ask_model(question, True)
        if embedding_chain_bot_response != "":
            response = embedding_chain_bot_response

    print("Question:", question)
    print("Answer:", response)
    return {"answer": response,"error": ""}





if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
