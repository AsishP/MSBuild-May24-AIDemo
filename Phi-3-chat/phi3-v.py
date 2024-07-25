from azure.search.documents.indexes import SearchIndexerClient
from azure.ai.ml import MLClient
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import os
import azure.identity.aio
import asyncio
from chat import ChatThread, create_search_client, create_openai_client, SearchType

## Load variables and environment variables
print("\n Loading Variables: \n")
load_dotenv()
k=50
search_type="text"
use_semantic_reranker=False
sources_to_include=5

## Get secrets from Azure Key Vault
print("\n Fetching values from Key Vault \n")
keyvault_url = os.getenv("AZURE_KEYVAULT_URL")
secret_client = SecretClient(vault_url=keyvault_url, credential=DefaultAzureCredential())
subscriptionGUID = secret_client.get_secret(os.getenv("AZURE_KEYVAULT_SECRET_NAME")).value
searchKey = secret_client.get_secret(os.getenv("AZURE_KEYVAULT_SEARCHKEY")).value
openAIKey = secret_client.get_secret(os.getenv("AZURE_OPENAI_ENDPOINT_KEY")).value

# Phi-3 Chat Example
print("\n Connecting to Azure AI Studio instance to fetch Phi-3 deployment \n")
workspace_ml_client = MLClient(
    DefaultAzureCredential(),
    subscription_id=subscriptionGUID,
    resource_group_name=os.getenv("AZURE_RESOURCE_GROUP"),
    workspace_name=os.getenv("AZUREAI_PROJECT_NAME")
)

phi3_url = workspace_ml_client.online_endpoints.get(name=os.getenv("AZUREAI_PHI3V_ENDPOINT_NAME")).scoring_uri
phi3_key = workspace_ml_client.online_endpoints.get_keys(name=os.getenv("AZUREAI_PHI3V_ENDPOINT_NAME")).primary_key

chat_thread = ChatThread()

choice = input("Enter the choice of Messages to use: \n 1. Car Scratch analysis \n 2. Sceneic Description \n 3. Shelf with Defects \n")

messages1 = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://apstorimages01.blob.core.windows.net/images/carscratch2.jpg"
                    },
                },
                {
                    "type": "text",
                    "text": "Detail the scratch in the shown picture and return a JSON output with defect brief and locating the scratch in X, Y coordinates.",
                },
            ],
        }
    ]

messages2 = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://apstorimages01.blob.core.windows.net/images/carscratch2.jpg"
                    },
                },
                {
                    "type": "text",
                    "text": "Detail the scratch in the shown picture and return a JSON output with defect brief and locating the scratch in X, Y coordinates.",
                },
            ],
        }
    ]

messages3 = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "https://apstorimages01.blob.core.windows.net/images/deerpic1.jpg"
                    },
                },
                {
                    "type": "text",
                    "text": "Describe the scene in the shown picture with respect to its backgrond and detail the objects/animals in the scene.",
                },
            ],
        }
    ]

print("\n Searching and displaying results using Phi-3 V model ...")
async def chat_caller():
    await chat_thread.get_phi3v_response(
        endpoint_scoring_uri=phi3_url + "/v1/chat/completions",
        endpoint_authorization="Bearer " + phi3_key,
        deployment=os.getenv("AZUREAI_PHI3V_DEPLOYMENT_NAME"),
        messages = messages1 if choice == 1 else messages2 if choice == 2 else messages3,
        max_new_tokens=2048)

asyncio.run(chat_caller())
print("\n Phi-3 Chat output: \n")
print(chat_thread.get_last_message()["content"])


# print("\n Comparison of messages: \n")
# print(chat_thread.printMessages())