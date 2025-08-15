import chromadb
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from dotenv import load_dotenv
import logging
from flask import current_app

# Load environment variables and setup logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaMemory:
    def __init__(self, collection_name="agent_memory"):
        """Initialize ChromaDB with OpenAI embeddings and LangChain text splitter."""
        try:
            # Initialize OpenAI embedding function
            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                model_name="text-embedding-3-small"
            )

            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
                separators=["\n\n", "\n", ".", "!", "?", ";", ",", " "]
            )

            # Initialize ChromaDB client
            self.client = chromadb.HttpClient(
                host=os.getenv("CHROMADB_HOST", "localhost"),
                port=int(os.getenv("CHROMADB_PORT", 8010))
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )

            logger.info(f"Initialized ChromaMemory with collection: {collection_name}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaMemory: {str(e)}")
            raise

    def add(self, text, metadata=None):
        """
        Add text to collection using LangChain's text splitter.
        
        Args:
            text (str): Text to add
            metadata (dict, optional): Additional metadata for the chunks
        """
        try:
            # Split text into chunks using LangChain
            chunks = self.text_splitter.split_text(text)
            
            # Prepare batch data
            doc_ids = [f"doc_{len(self.collection.get()['ids']) + i}" for i in range(len(chunks))]
            
            # Add metadata if provided
            if metadata:
                metadatas = [metadata for _ in chunks]
            else:
                metadatas = [{"source": "user_input", "timestamp": "now()"} for _ in chunks]

            # Batch add to collection
            self.collection.add(
                documents=chunks,
                ids=doc_ids,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully added {len(chunks)} chunks to collection")
            return True

        except Exception as e:
            logger.error(f"Failed to add text to collection: {str(e)}")
            return False

    def search(self, query, n_results=3, filter_metadata=None):
        """
        Search the collection with metadata filtering.
        
        Args:
            query (str): Search query
            n_results (int): Number of results to return
            filter_metadata (dict): Optional metadata filter
            
        Returns:
            list: List of search results with text and metadata
        """
        try:
            # Convert filter_metadata to ChromaDB where clause format
            where = None
            if filter_metadata:
                where = {
                    key: {"$eq": value}
                    for key, value in filter_metadata.items()
                }

            # Execute search
            result = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )

            if not result["documents"][0]:
                return []

            # Format results with relevance scores
            formatted_results = [
                {
                    "text": doc,
                    "metadata": meta,
                    "relevance": 1 - dist  # Convert distance to relevance score
                }
                for doc, meta, dist in zip(
                    result["documents"][0],
                    result["metadatas"][0],
                    result["distances"][0]
                )
            ]
            
            return formatted_results

        except Exception as e:
            current_app.logger.error(f"Search error in ChromaMemory: {str(e)}")
            return []

def get_memory_data(query="Tell me about ML"):
    try:
        memory = ChromaMemory()
        results = memory.search(query)
        return [result["text"] for result in results]
    except Exception as e:
        logger.error(f"Error in get_memory_data: {str(e)}")
        return ["Error retrieving data from memory."]