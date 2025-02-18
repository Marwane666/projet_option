import os
import sys
import logging
import nest_asyncio
from dotenv import load_dotenv
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core import StorageContext, load_index_from_storage
from llama_index.embeddings.mistralai import MistralAIEmbedding
from llama_index.llms.mistralai import MistralAI
from llama_index.core.settings import Settings
from llama_index.core.node_parser import SemanticSplitterNodeParser

class PersonaPredictor:
    def __init__(self, dir_path="data_persona", persist_dir="storage5"):
        load_dotenv()
        self.dir_path = dir_path
        self.persist_dir = persist_dir
        nest_asyncio.apply()

    def initialize_and_persist_vectorstore(self):
        api_key = os.getenv("MISTRAL_API_KEY")
        print("API Key:", api_key)
        Settings.llm = MistralAI(max_tokens=10000, model="mistral-large-latest", api_key=api_key)  # Adapté pour MistralAI
        Settings.embed_model = MistralAIEmbedding(
                model_name="mistral-embed", 
                api_key=api_key,
                max_tokens=4000
            )

        if not os.path.exists(self.persist_dir):
            os.makedirs(self.persist_dir)

        if os.listdir(self.persist_dir):
            Settings.llm = MistralAI(max_tokens=10000, model="mistral-large-latest", api_key=api_key)  # Adapté pour MistralAI
            Settings.embed_model = MistralAIEmbedding(
                model_name="mistral-embed", 
                api_key=api_key,
                max_tokens=4000
            )
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
            Vector_index = load_index_from_storage(storage_context)
        else:
            reader = SimpleDirectoryReader(input_dir=self.dir_path)
            documents = reader.load_data()

            Settings.llm = MistralAI(max_tokens=10000, model="mistral-large-latest", api_key=api_key)  # Adapté pour MistralAI
            Settings.embed_model = MistralAIEmbedding(
                model_name="mistral-embed", 
                api_key=api_key,
                max_tokens=4000
            )
            Vector_index = VectorStoreIndex.from_documents(documents)
            Vector_index.storage_context.persist(persist_dir=self.persist_dir)
        query_engine = Vector_index.as_query_engine(chat_mode="context")
        return query_engine

    def predict_persona(self, user_events):
        """
        user_events: string describing user interactions
        Returns persona as text or JSON.
        """
        chat_engine = self.initialize_and_persist_vectorstore()
        query = f"En 1 mot si le persona est ['Découvreur' ou 'Précipité'] et 4 mots si le personna est ['Chercheur de bonnes affaires'], Quel est le persona de ce visiteur à travers son comportement ? {user_events}"
        print(user_events)
        response = chat_engine.query(query)
        print(response)
        return response

def save_persona_to_markdown(user_id, persona):
    file_path = f"personas/{user_id}.md"
    os.makedirs("personas", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(f"# Persona for user {user_id}\n\n{persona}\n")

if __name__ == "__main__":
    # Example usage
    sample_events = """[
    {
        "_id": {"$oid": "6765a5aa6937b467b10d4e57"},
        "type": "navigation",
        "page": "/categories/mode",
        "user": "Utilisateur1",
        "timestamp": {"$date": {"$numberLong": "1734718394804"}}
    },
    {
        "_id": {"$oid": "6765a5bb6937b467b10d4e58"},
        "type": "navigation",
        "page": "/categories/maison",
        "user": "Utilisateur1",
        "timestamp": {"$date": {"$numberLong": "1734720000000"}}
    },
    {
        "_id": {"$oid": "6765db03f48edf369cfd8131"},
        "type": "time_spent",
        "page": "/categories/mode",
        "user": "Utilisateur1",
        "time_spent": {"$numberInt": "400"},
        "timestamp": {"$date": {"$numberLong": "1734732051172"}}
    },
    {
        "_id": {"$oid": "6766f37c9eeed3bf112e2aea"},
        "type": "interaction",
        "interaction": "Ajout aux favoris",
        "page": "/categories/mode/produit123",
        "user": "Utilisateur1",
        "timestamp": {"$date": {"$numberLong": "1734803852303"}}
    },
    {
        "_id": {"$oid": "6766f48c9eeed3bf112e2b0a"},
        "type": "interaction",
        "interaction": "Inscription newsletter",
        "page": "/newsletter",
        "user": "Utilisateur1",
        "timestamp": {"$date": {"$numberLong": "1734804890000"}}
    }
]"""
    persona_predictor = PersonaPredictor()
    persona_response = persona_predictor.predict_persona(sample_events)
    print("Persona:", persona_response)