from sentence_transformers import SentenceTransformer
import chromadb

class MyChromaMemory:
    def __init__(self, collection_name="agent_memory"):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = chromadb.HttpClient(host="localhost", port=8010)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add(self, text):
        embedding = self.model.encode([text])[0].tolist()
        doc_id = f"doc_{len(self.collection.get()['ids'])}"
        self.collection.add(documents=[text], embeddings=[embedding], ids=[doc_id])

    def search(self, query, n_results=3):
        query_embedding = self.model.encode([query])[0].tolist()
        result = self.collection.query(query_embeddings=[query_embedding], n_results=n_results)
        return result["documents"][0]

# Usage
memory = MyChromaMemory()
# memory.add("Python is a powerful programming language.")
# memory.add("Cow eats grass.")

def get_data():
    res = memory.search("Tell me about Cow")
    return res
