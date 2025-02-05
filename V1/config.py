import os

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://marwanekassa:n7oQSELguUxBnBm7@cluster0.ub2v4.mongodb.net/ecommerce?retryWrites=true&w=majority")
