#!/usr/bin/env python3
import requests
import json
import sys
import time

BASE_URL = "https://hidden-river-48977-576d654d245b.herokuapp.com"

def print_separator(message):
    print()
    print("==========================")
    print(message)
    print("==========================")
    print()

def test_failed(message, response=None):
    print(f"Test failed: {message}")
    if response:
        try:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except json.JSONDecodeError:
            print(f"Response text: {response.text}")
    sys.exit(1)

def test_passed(message):
    print(f"Test passed: {message}")

# Test summary creation
print_separator("Testing POST /summaries/")
response = requests.post(
    f"{BASE_URL}/summaries/",
    json={"url": "http://testdriven.io"}
)

if response.status_code != 201:
    test_failed(f"Expected status code 201, got {response.status_code}", response)

try:
    data = response.json()
except json.JSONDecodeError:
    test_failed("Response is not valid JSON", response)

if "id" not in data or "url" not in data:
    test_failed("Response does not contain 'id' or 'url'", response)

summary_id = data["id"]
url = data["url"]

if not isinstance(summary_id, int):
    test_failed(f"'id' is not a number: {summary_id}", response)

if url != "http://testdriven.io/":
    test_failed(f"'url' is not http://testdriven.io/: {url}", response)

test_passed(f"Created summary with ID {summary_id} and URL {url}")

# Test summary retrieval - wait a moment for processing
time.sleep(2)
print_separator(f"Testing GET /summaries/{summary_id}/")
response = requests.get(f"{BASE_URL}/summaries/{summary_id}/")

if response.status_code != 200:
    test_failed(f"Expected status code 200, got {response.status_code}", response)

try:
    data = response.json()
except json.JSONDecodeError:
    test_failed("Response is not valid JSON", response)

if "id" not in data or "url" not in data or "summary" not in data:
    test_failed("Response is missing required fields", response)

if data["id"] != summary_id:
    test_failed(f"Expected id {summary_id}, got {data['id']}", response)

if data["url"] != "http://testdriven.io/":
    test_failed(f"Expected url 'http://testdriven.io/', got {data['url']}", response)

if not data["summary"].startswith("Our"):
    test_failed("Summary does not start with 'Our'", response)

test_passed(f"Retrieved summary with ID {summary_id}, URL {url}, and summary starts with 'Our'")

# Test summaries listing
print_separator("Testing GET /summaries/")
response = requests.get(f"{BASE_URL}/summaries/")

if response.status_code != 200:
    test_failed(f"Expected status code 200, got {response.status_code}", response)

try:
    data = response.json()
except json.JSONDecodeError:
    test_failed("Response is not valid JSON", response)

if not isinstance(data, list) or len(data) == 0:
    test_failed("Expected a non-empty list of summaries", response)

test_passed("Retrieved list of summaries")

# Test summary update
print_separator(f"Testing PUT /summaries/{summary_id}/")
response = requests.put(
    f"{BASE_URL}/summaries/{summary_id}/",
    json={"url": "http://testdriven.io", "summary": "Updated summary"}
)

if response.status_code != 200:
    test_failed(f"Expected status code 200, got {response.status_code}", response)

try:
    data = response.json()
except json.JSONDecodeError:
    test_failed("Response is not valid JSON", response)

if data["summary"] != "Updated summary":
    test_failed(f"Expected summary 'Updated summary', got {data['summary']}", response)

test_passed("Summary updated successfully")

# Test summary deletion
print_separator(f"Testing DELETE /summaries/{summary_id}/")
response = requests.delete(f"{BASE_URL}/summaries/{summary_id}/")

if response.status_code != 200:
    test_failed(f"Expected status code 200, got {response.status_code}", response)

try:
    data = response.json()
except json.JSONDecodeError:
    test_failed("Response is not valid JSON", response)

if data["id"] != summary_id:
    test_failed(f"Expected id {summary_id}, got {data['id']}", response)

test_passed("Summary deleted successfully")

# Test citation creation
print_separator("Testing POST /citations/")
response = requests.post(
    f"{BASE_URL}/citations/",
    json={
        "doi": "10.1234/example.5678",
        "highlight": {
            "1": {"rect": [100, 200, 300, 220], "text": "first part"},
            "2": {"rect": [50, 100, 250, 120], "text": "second part"}
        },
        "comment": "This is an important passage"
    }
)
if response.status_code != 201:
    test_failed(f"Expected status code 201, got {response.status_code}", response)

try:
    data = response.json()
except json.JSONDecodeError:
    test_failed("Response is not valid JSON", response)

if "id" not in data or "doi" not in data:
    test_failed("Response does not contain 'id' or 'doi'", response)

citation_id = data["id"]
doi = data["doi"]

if not isinstance(citation_id, int):
    test_failed(f"'id' is not a number: {citation_id}", response)

if doi != "10.1234/example.5678":
    test_failed(f"'doi' is not 10.1234/example.5678: {doi}", response)

test_passed(f"Created citation with ID {citation_id} and DOI {doi}")

print("\nAll tests passed successfully!")