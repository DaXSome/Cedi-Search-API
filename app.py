from fastapi import FastAPI, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from algoliasearch.search_client import SearchClient
from dotenv import load_dotenv
from os import getenv
from pymongo import MongoClient

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

algolia_client = SearchClient.create(
    getenv("ALGOLIA_APP_ID"), getenv("ALGOLIA_API_KEY"))

algolia_index = algolia_client.init_index("products")

mongo_client = MongoClient(getenv("DB_URI"))
database = mongo_client["cedi_search"]
collection = database["indexed_products"]

search_params = {
    'restrictSearchableAttributes': ['name']
}


@app.get("/")
def read_root(query: str = Query()):
    suggestions = []
    for suggestion in algolia_index.search(query, search_params)["hits"]:
        suggestions.append(suggestion["name"])

    return suggestions


@app.get("/search")
def get_search(query: str = Query()):
    products = []

    for product in algolia_index.search(query, search_params)["hits"]:

        products.append({
            "name": product["name"],
            "price": float(product["price"]),
            "rating": product["rating"],
            "image": product["images"][0],
            "id": product["objectID"],
            "slug": product["slug"]
        })

    return products


@app.get("/product/{slug}")
def get_product(slug: str = Path()):
    return collection.find_one({"slug": slug})
