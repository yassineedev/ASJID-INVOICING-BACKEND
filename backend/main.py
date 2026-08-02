from fastapi import FastAPI
import requests
from fastapi.middleware.cors import CORSMiddleware
from Generator.invoice import Generator, GeneratorError

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/users")
def read_item():
    api = "https://script.google.com/macros/s/AKfycbzR4ayLk5HUYAFpilIWUm7ay9ga_5IcwwtOyUc50_MC9hkt5ueYeHyz_HniFGXo5Hs/exec?action=getClients"
    data = requests.get(api).json()
    return data["data"]


@app.get("/users/paid")
def filter_paid():
    data = read_item()
    filtered_data = [i for i in data if i.get("isPaid")]
    return filtered_data


@app.get("/generate")
def generate():
    try:
        data = filter_paid()
        g = Generator(data)
        g.generate_bills()
    except GeneratorError as e:
        return e
