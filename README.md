
# ABOGACIA

<a name="readme-top"></a>

<h3 align="center">AbogaIA Service</h3>

  <p >
    AbogacIA is an innovative Python-based project designed to enhance legal research and support through the integration of advanced technologies. This project involves creating a robust FastAPI service capable of automating the retrieval of legal documents from the Colombian judiciary website. By utilizing web scraping techniques, the service efficiently downloads court sentences and other pertinent legal documents related to specific topics.

    Once downloaded, the documents are stored in a Chroma vector database, ensuring fast and efficient retrieval of relevant information. AbogacIA leverages the Langchain framework to manage multiple chat sessions, with each interaction's messages being securely stored in MongoDB. When a user interacts with the chatbot, the service intelligently retrieves contextually relevant documents and utilizes a GPT model to provide accurate and insightful answers to legal inquiries.

    This sophisticated integration of web scraping, vector databases, and AI-powered chatbots positions AbogacIA as a cutting-edge solution for legal professionals seeking streamlined access to Colombian legislation and jurisprudence.
  </p>


</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
  </ol>
</details>






<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* python
* FastAPI
* MongoDB
* Chroma
* Langchain
* Selenium
* OpenAI

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started


### Prerequisites

Make sure you have the following prerequisites installed:

- Python (3.8 or higher)
- Git (for version control)


* It is recommended to create your own environment for this project:


### Installation
1. Clone the repository to your local machine:

    ```
    git clone https://github.com/DavidNavarroSaiz/AbogacIA
    ```

2. Navigate to the project directory:

    ``` 
    cd your-project
    ```

3. Install project dependencies using `pip`:

    ```
    pip install -r requirements.txt
    ```

4. setup the environment variables:
 
    Create a new file named .env in the root directory of your project.

    Open the .env file and add the following line with the URL with the connection with the database:


    ```
    OPENAI_API_KEY = <Open AI API KEY>
    MONGODD_NAME = <Database Name>
    COLLECTION_NAME = <Collection name>
    CONNECTION_STRING = <Connection String>
   
    ```
    replace the each space with the required field
    Save the .env file.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage


### Using the FastAPI Service

To use the FastAPI service for interacting with the service, follow these steps:

1. Run the FastAPI service:

    ```
    python main.py
    ```
    or using the console:

    ```
    uvicorn main:app --reload --port 8000
    ```

2. The service will start on a specified port (typically 8000). You can access the API endpoints using tools like `curl` or API testing platforms.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



# FastAPI Endpoints Documentation

### Endpoints

#### 1. Download Documents

**Endpoint:** `/download_documents/`  
**Method:** `POST`  
**Description:** This endpoint allows users to download legal documents based on specified topics.

**Request Body:**
{
  "temas_legales": {
    "Divorcio": 10,
    "PQR": 2,
    "Abandono de bienes": 10,
    "Abandono de menores": 10
  }
}

**Response:**
- **Status 200 (OK):** 
  {
    "status": "success",
    "message": "Documents downloaded successfully."
  }
- **Status 500 (Internal Server Error):**
  {
    "detail": "Error message"
  }

#### 2. Delete Document

**Endpoint:** `/delete_document/`  
**Method:** `DELETE`  
**Description:** This endpoint allows users to delete a specific document from the database and storage.

**Request Body:**
{
  "filename": "document_name"
}

**Response:**
- **Status 200 (OK):** 
  {
    "status": "success",
    "message": "Document deleted successfully."
  }
- **Status 500 (Internal Server Error):**
  {
    "detail": "Error message"
  }

#### 3. Load Chat History

**Endpoint:** `/load_chat_history/`  
**Method:** `POST`  
**Description:** This endpoint loads the chat history for a given session ID.

**Request Body:**
{
  "session_id": "user_session_id"
}

**Response:**
- **Status 200 (OK):** 
  {
    "chat_history": "Loaded chat history"
  }
- **Status 500 (Internal Server Error):**
  {
    "detail": "Error message"
  }

#### 4. Ask Chain Bot

**Endpoint:** `/ask_chain_bot/`  
**Method:** `POST`  
**Description:** This endpoint allows users to ask a question to the chatbot for a given session ID and receive a response.

**Request Body:**
{
  "query": "Your question",
  "session_id": "user_session_id"
}

**Response:**
- **Status 200 (OK):** 
  {
    "answer": "Chatbot response",
    "error": ""
  }
- **Status 400 (Bad Request):**
  {
    "error": "Please enter a valid question",
    "answer": ""
  }
- **Status 404 (Not Found):**
  {
    "error": "Session with session_id 'user_session_id' not found. Please create a new session.",
    "answer": ""
  }
- **Status 500 (Internal Server Error):**
  {
    "detail": "Error message"
  }
