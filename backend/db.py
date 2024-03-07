# Importing modules
import os  # Provides functions for interacting with the operating system
from pymongo import MongoClient  # Python driver for MongoDB
import json  # Provides functions for working with JSON data
from bson.json_util import dumps as bson_dumps  # Serialize BSON documents to JSON format
from typing import Optional  # Import the Optional type hint, indicates an argument can be None

# Setting up MongoDB connection
uri = os.environ.get("MONGO_DB_URI")  # Retrieve MongoDB URI from environment variables
client = MongoClient(uri, connectTimeoutMS=30000, socketTimeoutMS=None)  # Create MongoDB client object
db = client.Cluster0  # Select a specific database named "Cluster0"
USERS = db.Users  # Retrieve a collection named "Users" from the selected database
PROMPTS = db.Prompts  # Retrieve a collection named "Prompts" from the selected database

# Defining constants
COST_PER_TOKEN = 0.000002  # Cost per token value, used for calculating total cost of usage

# Defining functions
def parse_json(data):
    """
    Parses JSON data.

    Args:
        data: JSON data to parse.

    Returns:
        Parsed JSON data.
    """
    return json.loads(bson_dumps(data))

def delete_user_message_history(email: str):
    """
    Deletes the message history for a user specified by email address.

    Args:
        email: Email address of the user.
    """
    USERS.find_one_and_update({'email': email},
                              {
                                  '$set': {'message_history': [], "summary": ""}
                              }
                              )

def store_usage(token_amount: int, new_messages: list, email: Optional[str] = None, ip: Optional[str] = None):
    """
    Stores usage information for a user.

    Args:
        token_amount: Amount of tokens used.
        new_messages: List of new messages.
        email: Email address of the user (optional).
        ip: IP address of the user (optional).
    """
    if email:
        USERS.find_one_and_update({'email': email},
                                  {
                                      '$inc': {'credits': -1, 'token_usage': token_amount, 'total_cost': token_amount * COST_PER_TOKEN},
                                      '$push': {'message_history': new_messages}
                                  }
                                  )
    elif ip:
        USERS.find_one_and_update({'ip': ip},
                                  {
                                      '$inc': {'credits': -1, 'token_usage': token_amount, 'total_cost': token_amount * COST_PER_TOKEN},
                                      '$push': {'message_history': new_messages}
                                  }
                                  )
    else:
        raise Exception("No email or ip provided")

def add_credits(customer_email: str):
    """
    Adds credits to a user's account.

    Args:
        customer_email: Email address of the user.

    Returns:
        Updated user object.
    """
    user = USERS.find_one_and_update({"email": customer_email}, {"$inc": {"credits": 100}})
    return user
