# backend/config.py
# Centralized configuration for JWT authentication and token expiration.

import os
from dotenv import load_dotenv

# Load environment variables from the root .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Secret key used for signing JWT tokens.
# Falls back to a default value if the environment variable is not set.
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")

# Algorithm used for JWT encoding/decoding.
JWT_ALGORITHM = "HS256"

# Access token expiration time in minutes.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))