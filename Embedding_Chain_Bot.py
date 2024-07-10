"""
Class representing a chatbot that utilizes langchain.
"""
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain.chains.conversation.memory import ConversationSummaryBufferMemory,ConversationBufferWindowMemory,ConversationBufferMemory
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain_community.llms import OpenAI
from langchain_community.callbacks.manager import get_openai_callback
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate


from langchain_mongodb import MongoDBChatMessageHistory





import openai
import time
import os

class EmbeddingChainChatBot():
    """
    Class representing a chatbot that utilizes LangChain for conversation handling and interacts with GPT-3.5 Turbo for answering user questions.

    Attributes:
        GPTmodel_name (str): The name of the GPT model to use (default: "gpt-3.5-turbo-1106").
        temperature_gpt (float): The temperature for GPT response generation (default: 0.5).
        memory_tokens (int): The maximum number of tokens to use for conversation history memory (default: 200).
        embedding_number_documents (int): The number of documents to retrieve in the similarity search (default: 3).
        total_cost (float): Total cost of tokens used by GPT-3.5 Turbo.
        last_memory_messages (int): Number of previous messages to store in memory.
        ef (OpenAIEmbeddings): Object representing the OpenAI embedding function.
        vectordb (Chroma): Chroma instance for storing and retrieving document embeddings.
        retriever (ChromaRetriever): Retriever instance for similarity search.
        qachat (ConversationalRetrievalChain): Conversational retrieval chain for handling conversations.

    Methods:
        __init__(): Initialize the EmbeddingChainChatBot instance.
        ask_model(question, print_info): Process user's question and generate a response.
    """
    def __init__(self,session_id, memory_type='buffer_window'):
        """
        Initialize the EmbeddingChainChatBot instance.

        Parameters:
            memory_type (str): Type of memory to use for conversation history.
                - 'buffer': Basic buffer memory.
                - 'buffer_window': Buffer window memory with a limited number of previous messages.
                - 'buffer_summary': Summary buffer memory with a token limit.
                Default is 'buffer_window'.

        Attributes:
            GPTmodel_name (str): The name of the GPT model to use (default: "gpt-3.5-turbo-1106").
            temperature_gpt (float): The temperature for GPT response generation (default: 0.5).
            llm (ChatOpenAI): ChatOpenAI instance for GPT-based language models.
            llm_memory (OpenAI): OpenAI instance for memory-related language models.
            memory_tokens (int): The maximum number of tokens to use for conversation history memory (default: 200).
            embedding_number_documents (int): The number of documents to retrieve in the similarity search (default: 3).
            total_cost (float): Total cost of tokens used by GPT-3.5 Turbo.
            last_memory_messages (int): Number of previous messages to store in memory.
            memory (ConversationBufferMemory or ConversationBufferWindowMemory or ConversationSummaryBufferMemory): Memory instance based on the specified type.

        Example:
            chatbot = EmbeddingChainChatBot(memory_type='buffer_window')
        """
        load_dotenv()
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.db_name = os.getenv("MONGODD_NAME")
        self.collection_name = os.getenv("COLLECTION_NAME")
        self.connection_string = os.getenv("CONNECTION_STRING")
        self.docs = []
        self.question = ""
        self.doc_scores = []
        self.context = []
        answer = ""
        self.gpt_answer = ""
        self.GPTmodel_name = "gpt-3.5-turbo-0125"
        self.temperature_gpt = 0.5
        self.memory_tokens = 500
        self.embedding_number_documents = 6
        self.total_cost = 0
        self.memory_type = memory_type
        self.session_id = session_id   
        self.setup_model()
        
        
    def setup_model(self):
        """
        Set up the EmbeddingChainChatBot model by configuring memory, embeddings, and the conversational retrieval chain.

        Raises:
            ValueError: If an invalid memory_type is provided.
            """
          
        


        self.message_history = MongoDBChatMessageHistory(
            connection_string=self.connection_string, session_id=self.session_id,
            database_name=self.db_name, collection_name= self.collection_name
        )
        
        if self.memory_type == 'buffer':
            self.memory = ConversationBufferMemory(memory_key="chat_history", input_key='question', output_key='answer', return_messages=True,chat_memory=self.message_history)
        elif self.memory_type == 'buffer_window':
            
            self.last_memory_messages = 2
            self.memory = ConversationBufferWindowMemory(k=self.last_memory_messages, memory_key="chat_history", input_key='question', output_key='answer', return_messages=True,chat_memory=self.message_history)
        elif self.memory_type == 'buffer_summary':
            llm_memory = OpenAI(temperature=self.temperature_gpt, model_name=self.GPTmodel_name)
            self.memory = ConversationSummaryBufferMemory(llm=llm_memory, max_token_limit=self.memory_tokens, memory_key="chat_history",
                                         input_key='question', output_key='answer', return_messages=True,chat_memory=self.message_history)
        else: 
            print("please input a valid memory type: \n buffer, buffer_window, buffer_summary")
        self.ef = OpenAIEmbeddings()
            
        self.vectordb = Chroma(persist_directory=f"./abogacia_data", embedding_function=self.ef)

        print("There are",  self.vectordb._collection.count(), "in the collection")
        self.retriever = self.vectordb.as_retriever(search_kwargs={"k": self.embedding_number_documents})
        
        
        llm = ChatOpenAI(temperature=self.temperature_gpt, model_name=self.GPTmodel_name)
        self.prompt_generation()
        # Create the multipurpose chain
        print()
        self.qachat = ConversationalRetrievalChain.from_llm(
            llm=llm,
            memory=self.memory,
            retriever=self.retriever, 
            condense_question_prompt = self.condense_prompt,
            combine_docs_chain_kwargs={"prompt": self.question_prompt},
            return_source_documents=True,
            verbose=True,
            
        )
    def load_chat_history(self):
        return self.message_history.messages
    
    def ask_model(self,question,print_info = False):
        """
        Process user's question and generate a response.

        Args:
            question (str): The user's input question.
            print_info (bool): Whether to print additional information about the response (default: False).

        Returns:
            str: The response generated by the chatbot.
        """
        with get_openai_callback() as cost:
            data =self.qachat(question)
            answer = data['answer']
            print(data)
            
            
        if print_info == True:
        
            # Extracting the 'source' metadata information
            sources = [doc.metadata.get('source', '') for doc in data.get('source_documents', [])]

            # Print the extracted 'source' information
            print('Sources: \n ')
            for source in sources:
                print(f"Source: {source}")
                
            # chat_history = data.get('chat_history', [])
            # print('chat history: \n')
# # Print the extracted 'chat_history'
#             for idx, message in enumerate(chat_history, start=1):
#                 print(f"Message {idx}: {message}")
            print(f'cost:{cost}  \n ')
            self.total_cost += cost.total_tokens
            print("self.total_cost ",self.total_cost )
        return answer
    def prompt_generation(self):
        """
        Generate and set up prompt templates for the EmbeddingChainChatBot.

        This method initializes two prompt templates: 
        1. `self.condense_prompt`: Used to reformulate a follow-up question into a standalone question.
        2. `self.question_prompt`: Used to generate responses based on the chat history and user's current question.


        """
        
        template_condense = """
            Given a chat history and the latest user question \
            which might reference the chat history, formulate a standalone question \
            which can be understood without the chat history. Do NOT answer the question, \
            just reformulate it if needed and otherwise return it as is.
            Return the standalone question in the same language as the input

            Chat History:
            {chat_history}
            Follow Up Input: {question}
            Standalone question:"""
            
        self.condense_prompt= PromptTemplate.from_template(template_condense)
        
        
        
   
        template = ("""
                     \
                    
                    instructions: 
                    - You are a lawyer expert assistant that helps to solve, instruct and assist to a lawyer in different juridical cases . \
                    - You give recommendations, build documents, and continuously ask how you can help.
                    - provide complete informative answers, Focus on providing helpful and relevant information,
                    - Always Answer the Question in the same language as the user question.
                    - you return the helpful answer directly
                    - if you are asked for a document, letter, email or similar, please return the document template with all the required information.
                    
                    use the context as reference that may help in the juridical case, however if you dont consider it useful information still try to help the person
                    remember that the new user question can be related with the chat history.
                    Context that may help to answer question:\n{context}

                    Chat History:\n{chat_history}

                    Answer the User question:\n{question}

                    """)
        
        self.question_prompt = PromptTemplate.from_template(template)
        
        
if __name__ == "__main__":
   # Your Chatbot initialization
    session_id = 'test_session_1'

    chatbot = EmbeddingChainChatBot(session_id)
    questions = preguntas = [
    "Solicita asesoría sobre los derechos y obligaciones en casos de abandono de menores.",
    "¿Cómo proceder legalmente ante un caso de abandono de bienes por parte de un cónyuge?",
    "Necesito orientación sobre el proceso de divorcio y los pasos legales a seguir.",
    "Genera una carta para solicitar la custodia de un menor ante el juzgado.",
    "Ayúdame a redactar un documento de conciliación en un proceso de divorcio.",
    "Quiero presentar una petición ante el juzgado de familia, ¿qué información necesito incluir?",
    "¿Cuáles son los requisitos legales para establecer una pensión alimenticia?",
    "Proporciona orientación sobre cómo responder a una solicitud de paternidad.",
    "Necesito redactar una carta de notificación sobre el incumplimiento de visitas a menores.",
    "¿Qué documentos son necesarios para iniciar un proceso de adopción?",
    "¿Cómo solicitar una modificación de medidas en un proceso de divorcio?",
    "Ayúdame a redactar una queja formal ante la entidad reguladora.",
    "Genera un documento para solicitar la revisión de una sentencia judicial.",
    "Solicita información sobre los derechos de visita en casos de custodia compartida.",
    "¿Qué pasos debo seguir para realizar una separación de bienes?",
    "Ayúdame a redactar una carta de reclamación por incumplimiento de contrato.",
    "Necesito orientación sobre cómo presentar una demanda por violencia intrafamiliar.",
    "¿Qué información debo incluir en una solicitud de medidas cautelares?",
    "Genera un documento para solicitar la liquidación de bienes gananciales.",
    "Solicita asistencia para redactar una carta de autorización para representación legal."
]

    for i, question in enumerate(questions, 1):
        start_time = time.time()
        answer = chatbot.ask_model(question, True)
        end_time = time.time()
        
        print(f"Question {i} - Time taken: {end_time - start_time} seconds")
        print("question: \n", question)
        print("answer: \n", answer)
        print("\n" + "="*50 + "\n")  # Separator for better readability