# AZURE_layer2/services/weaviate_services.py

import weaviate
from weaviate.connect import ConnectionParams
from weaviate import WeaviateClient
import uuid
import os
from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from config.settings import settings

load_dotenv(".env")

# Initialize OpenAI LLM
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

llm = OpenAI(api_key=openai_api_key, temperature=0.7)

# Define prompt template for generating positive suggestions
prompt_template = PromptTemplate(
    input_variables=["content"],
    template="Rephrase the following text into a positive version: {content}",
)

# Initialize Weaviate client
WEAVIATE_URL = settings.WEAVIATE_URL
connection_params = ConnectionParams.from_url(WEAVIATE_URL, grpc_port=50051)
weaviate_client = WeaviateClient(connection_params)


def generate_positive_suggestion(content: str) -> str:
    from langchain.chains import LLMChain

    chain = LLMChain(llm=llm, prompt=prompt_template)
    response = chain.run(content=content)
    return response.strip()


def store_in_weaviate_with_sentiment(content: str, author_id: int, sentiment: str):
    if not weaviate_client.is_ready():
        raise ConnectionError("Weaviate is not ready.")

    class_name = "EchoVector"

    if not weaviate_client.schema.contains({"classes": [{"class": class_name}]}):
        weaviate_client.schema.create_class(
            {
                "class": class_name,
                "properties": [
                    {"name": "content", "dataType": ["text"]},
                    {"name": "authorId", "dataType": ["int"]},
                    {"name": "sentiment", "dataType": ["text"]},
                ],
                "vectorizer": "text2vec-openai",
            }
        )

    object_uuid = str(uuid.uuid4())

    weaviate_client.data_object.create(
        data_object={"content": content, "authorId": author_id, "sentiment": sentiment},
        class_name=class_name,
        uuid=object_uuid,
    )

    return object_uuid
