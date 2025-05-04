import os

class Config:
    # Directly set the database URI for development
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:Pritam@127.0.0.1/codehub"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

