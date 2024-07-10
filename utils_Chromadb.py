import os
from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import CharacterTextSplitter
import tiktoken
import time
import openai
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
    
class UtilsDB():
    def __init__(self, vectordb:Chroma):
        self.vectordb = vectordb
        self.total_token_count = 0
        self.docs_counter = 0
        

    def delete_DB_document_and_file(self, filename):
        """
        Deletes a document from the database and its corresponding file.

        Args:
            filename (str): The name of the file to delete.

        Returns:
            dict: A dictionary containing the status and message of the deletion process.
        """
        file_deleted = False
        db_deleted = False

        # Search for the file in the downloaded folders
        for root, dirs, files in os.walk("./downloads"):
            if filename in files:
                file_to_delete = os.path.join(root, filename)
                os.remove(file_to_delete)
                file_deleted = True
                print(f"File '{file_to_delete}' deleted from the folder.")
                break

        if not file_deleted:
            print(f"File '{filename}' not found in the folder.")

        # Retrieve all documents from the database and filter by filename
        all_documents = self.vectordb.get()
        matching_ids = [
            doc_id for doc_id, metadata in zip(all_documents['ids'], all_documents['metadatas'])
            if metadata['source'].endswith(filename)
        ]

        if matching_ids:
            self.vectordb.delete(matching_ids)
            db_deleted = True
            print(f"Document with filename '{filename}' deleted from the database.")
        else:
            print(f"Document with filename '{filename}' not found in the database.")

        print(f"There are {self.vectordb._collection.count()} documents in the collection after deleting.")

        if file_deleted and db_deleted:
            return {"status": "success", "message": f"Document '{filename}' deleted successfully from both the folder and the database."}
        elif file_deleted:
            return {"status": "partial success", "message": f"Document '{filename}' deleted from the folder but not found in the database."}
        elif db_deleted:
            return {"status": "partial success", "message": f"Document '{filename}' deleted from the database but not found in the folder."}
        else:
            return {"status": "failure", "message": f"Document '{filename}' not found in both the folder and the database."}



    def add_db_doc(self, filename):
        print("filename",filename)
        if filename:
            doc_path = filename
            if doc_path.endswith(".pdf"):
                loader = PyMuPDFLoader(doc_path)
            elif doc_path.endswith('.docx') or doc_path.endswith('.doc'):
                loader = Docx2txtLoader(doc_path)
            elif doc_path.endswith('.txt'):
                loader = TextLoader(doc_path)
            else:
                print("file format not supported")
                return
            
            doc = loader.load()

            # Implementing the text splitter
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=30)
            documents_split = text_splitter.split_documents(doc)
            if documents_split:
                self.vectordb.add_documents(documents_split)

            result = f"stored in database: {filename} file number {self.vectordb._collection.count()}"
            print(result)
            self.docs_counter += 1
            return result
        else:
            print("failed to store document, filename doesn't exist")


    def num_tokens_from_string(self, string: str) -> int:
        encoding = tiktoken.get_encoding('cl100k_base')
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def number_of_documents(self):
        data = self.vectordb.get()
        num_docs = len(data.get('metadatas', []))
        return num_docs

    def number_of_sources_docs(self):
        data = self.vectordb.get()
        num_docs_urls = 0
        num_docs_non_urls = 0
        urls = []
        non_urls = []

        for metadata in data["metadatas"]:
            source = metadata["source"]
            if source.startswith("https://") or source.startswith("http://"):
                num_docs_urls += 1
                urls.append(source)
            else:
                num_docs_non_urls += 1
                non_urls.append(source)

        num_sources_urls = len(set(urls))
        num_sources_non_urls = len(set(non_urls))

        return num_sources_urls, num_docs_urls, num_sources_non_urls, num_docs_non_urls
    


    # def number_of_sources_docs(self): 
        
    #     # num_docs = self.vectordb._collection.count()
    #     # num_docs = self.vectordb.get()
    #     # Access the 'metadatas' key and get the length of the list
    #     data=  self.vectordb.get()
    #     print("data",data)
    #     # num_docs = len(self.vectordb.get('metadatas', {}).get('metadatas', {}).get('source', []))
    #     num_docs = len(data.get('metadatas', []))
    #     sources = set(metadata["source"] for metadata in data["metadatas"])


    #     # Counting the number of sources
    #     num_sources = len(sources)

    #     return num_sources,num_docs
    def ask_vector_db(self,question):

        start_time = time.time()



        docs = self.vectordb.similarity_search_with_relevance_scores(question)
        end_time = time.time()

        output_markdown = f"result took: {end_time - start_time:.4f} seconds\n```\n"

        # Iterate through the documents and add a space between them
        for doc in docs:
            output_markdown += f"{doc}\n\n"

        output_markdown += "```"    
        print(output_markdown)
        return docs

if __name__ == "__main__":


    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    vectordb = Chroma(persist_directory="abogacia_data",embedding_function=OpenAIEmbeddings())   
    utils_db = UtilsDB(vectordb)
    result = utils_db.number_of_sources_docs()
    print(result)
    question = "tengo un caso de una separacion en curso, una de las personas fallecio, como funcionaria la separacion de bienes en ese proceso?"
    question = "quiero generar un documento de separacion entre dos personas, el caso es muy complejo por que hay violencia infantil, el señor abuso de la hija, y le pegaba constantemente a la esposa"
    result = utils_db.ask_vector_db(question)
