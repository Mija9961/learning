from sentence_transformers import SentenceTransformer
import chromadb
import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt_tab')

class MyChromaMemory:
    def __init__(self, collection_name="agent_memory"):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = chromadb.HttpClient(host="localhost", port=8010)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add(self, text):
        """Add text by splitting into sentences."""
        sentences = sent_tokenize(text)  # ✅ Split into sentences
        for i, sentence in enumerate(sentences):
            embedding = self.model.encode([sentence])[0].tolist()
            doc_id = f"doc_{len(self.collection.get()['ids']) + i}"
            self.collection.add(documents=[sentence], embeddings=[embedding], ids=[doc_id])


    def search(self, query, n_results=3):
        query_embedding = self.model.encode([query])[0].tolist()
        result = self.collection.query(query_embeddings=[query_embedding], n_results=n_results)
        result = result["documents"][0]
        if result:
            return result
        else:
            return ["Sorry, no data found! "]

# Usage
memory = MyChromaMemory()
# memory.add("ML is machine learning")

def get_data():
    res = memory.search("Tell me about Cat")
    return res
