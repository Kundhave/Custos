import os
from dotenv import load_dotenv

load_dotenv()

conn = os.getenv("REDIS_CONN")
print("Connection string loaded:", conn[:50] if conn else "NOT FOUND")