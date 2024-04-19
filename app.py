from fastapi import FastAPI, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from json import load
from rank_bm25 import BM25Okapi
from algoliasearch.search_client import SearchClient
from dotenv import load_dotenv
from os import getenv
from firebase_admin import initialize_app, credentials, firestore

load_dotenv()


app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


with open("index.json") as index_file:
    corpus = load(index_file)

tokenized_corpus = [doc.lower().split(" ") for doc in corpus]

bm25 = BM25Okapi(tokenized_corpus)

client = SearchClient.create(
    getenv("ALGOLIA_APP_ID"), getenv("ALGOLIA_API_KEY"))

index = client.init_index("products")

firebase_config = {
    "type": getenv("FIREBASE_type"),
    "project_id": getenv("FIREBASE_project_id"),
    "private_key_id": getenv("FIREBASE_private_key_id"),
    "private_key": getenv("FIREBASE_private_key").replace("\\n", "\n"),
    "client_email": getenv("FIREBASE_client_email"),
    "client_id": getenv("FIREBASE_client_id"),
    "auth_uri": getenv("FIREBASE_auth_uri"),
    "token_uri": getenv("FIREBASE_token_uri"),
    "auth_provider_x509_cert_url": getenv("FIREBASE_auth_provider_x509_cert_url"),
    "client_x509_cert_url": getenv("FIREBASE_client_x509_cert_url"),
    "universe_domain": getenv("FIREBASE_universe_domain"),
}

creds = credentials.Certificate(firebase_config)

initialize_app(creds)


@app.get("/")
def read_root(query: str = Query()):

    tokenized_query = query.split(" ")

    suggestions = bm25.get_top_n(tokenized_query, corpus, n=10)

    return suggestions


@app.get("/search")
def get_search(query: str = Query()):
    products = []

    for product in index.search(query)["hits"]:

        products.append({
            "name": product["name"],
            "price": float(product["price"]),
            "rating": product["rating"],
            "image": product["images"][0],
            "id": product["product_id"]
        })

    return products


@app.get("/product/{id}")
def get_product(id: str = Path()):
    return firestore.client().collection("products").document(id).get().to_dict()
