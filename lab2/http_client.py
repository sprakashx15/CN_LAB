#!/usr/bin/env python


"""
Task-1 (hTTP)
- Send GET and POST requests to a test API/website.
- Display response status code, headers, and body.
- Log errors if the request fails.
"""

import json
import logging
from urllib import request, error

logging.basicConfig(level=logging.INFO)

def http_get(url: str):
    try:
        logging.info(f"GET {url}")
        with request.urlopen(url, timeout=10) as resp:
            print("Status:", resp.status)
            print("Headers:", dict(resp.headers))
            print("Body:", resp.read().decode()[:200]) 
    except error.URLError as e:
        logging.error(f"GET failed: {e}")

def http_post(url: str, data: dict):
    try:
        logging.info(f"POST {url}")
        encoded = json.dumps(data).encode()
        req = request.Request(url, data=encoded, headers={"Content-Type": "application/json"})
        with request.urlopen(req, timeout=10) as resp:
            print("Status:", resp.status)
            print("Headers:", dict(resp.headers))
            print("Body:", resp.read().decode()[:200])
    except error.URLError as e:
        logging.error(f"POST failed: {e}")

if __name__ == "__main__":
    http_get("https://httpbin.org/get")
    http_post("https://httpbin.org/post", {"assignment": "Computer networks", "Lab2": "question1(HTTP)"})
