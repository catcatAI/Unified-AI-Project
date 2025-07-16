import unittest
import os
import sys

from src.services.main_api_server import app
from fastapi.testclient import TestClient


class TestMainAPIServer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_read_main(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to the Unified AI Project API"})

    def test_get_status(self):
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        self.assertIn("status", response.json())
        self.assertEqual(response.json()["status"], "running")
