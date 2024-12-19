from fastapi import FastAPI, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from algoliasearch.search.client import SearchClientSync
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

algolia_client = SearchClientSync(getenv("ALGOLIA_APP_ID"), getenv("ALGOLIA_API_KEY"))

mongo_client = MongoClient(getenv("DB_URI"))
database = mongo_client["cedi_search"]
collection = database["indexed_products"]

search_params = {
    'restrictSearchableAttributes': ['name']
}

def run_query(query):
        return algolia_client.search({
        "requests": [
            {
                "indexName": "products",
                "query": query
            }
        ]

    }).to_dict()["results"][0]["hits"]



@app.get("/")
def read_root(query: str = Query()):
    suggestions = []

    results = run_query(query)

    return [suggestion["name"] for suggestion in results]


@app.get("/search")
def get_search(query: str = Query()):
    products = []

    results = run_query(query)


    for product in results:

        products.append({
            "name": product["name"],
            "price": float(product["price"]),
            "rating": product["rating"],
            "image": "" if len(product["images"]) == 0 else product["images"][0],
            "id": product["objectID"],
            "slug": product["slug"]
        })

    return products


@app.get("/product/{slug}")
def get_product(slug: str = Path()):
    return collection.find_one({"slug": slug})
