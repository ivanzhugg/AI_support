from openai import OpenAI
import os
from dotenv import load_dotenv


class Embedding():

    def __init__(self):
        load_dotenv()
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_EMBEDDING_MODEL")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        return

    
    def get_vector(self, text: str) -> list[float]:
        resp = self.client.embeddings.create(model=self.model, input=text)
        return resp.data[0].embedding

