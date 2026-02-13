import requests
import streamlit as st
import json

BASE_URL = "http://127.0.0.1:8000"

def fetch_data(endpoint, params=None):
    """
    Generic GET request handler.
    """
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params)
        return _handle_response(response)
    except requests.exceptions.RequestException as e:
        return {"error_code": "network_error", "message": f"Server not reachable: {str(e)}"}

def post_data(endpoint, payload):
    """
    Generic POST request handler.
    """
    try:
        response = requests.post(f"{BASE_URL}/{endpoint}", json=payload)
        return _handle_response(response)
    except requests.exceptions.RequestException as e:
        return {"error_code": "network_error", "message": f"Server not reachable: {str(e)}"}

def _handle_response(response):
    """
    Parses response and handles errors based on status code.
    """
    try:
        data = response.json()
        if response.status_code >= 400:
            # Expecting backend to return {"error_code": "...", "message": "..."}
            return data
        return data
    except ValueError:
        return {"error_code": "parsing_error", "message": "Invalid JSON response from server"}
