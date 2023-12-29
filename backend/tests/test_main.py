from fastapi.testclient import TestClient

from backend import main

client = TestClient(main.app)
