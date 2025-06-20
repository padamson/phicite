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


# Test highlight creation
print_separator("Testing POST /highlights/")
response = requests.post(
    f"{BASE_URL}/highlights/",
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

highlight_id = data["id"]
doi = data["doi"]

if not isinstance(highlight_id, int):
    test_failed(f"'id' is not a number: {highlight_id}", response)

if doi != "10.1234/example.5678":
    test_failed(f"'doi' is not 10.1234/example.5678: {doi}", response)

test_passed(f"Created highlight with ID {highlight_id} and DOI {doi}")

# Test highlight retrieval
print_separator(f"Testing GET /highlights/{highlight_id}/")
response = requests.get(f"{BASE_URL}/highlights/{highlight_id}/")
if response.status_code != 200:
    test_failed(f"Expected status code 200, got {response.status_code}", response)
try:
    data = response.json()
except json.JSONDecodeError:
    test_failed("Response is not valid JSON", response)
if "id" not in data or "doi" not in data or "highlight" not in data:
    test_failed("Response is missing required fields", response)
if data["id"] != highlight_id:
    test_failed(f"Expected id {highlight_id}, got {data['id']}", response)
if data["doi"] != "10.1234/example.5678":
    test_failed(f"Expected doi '10.1234/example.5678', got {data['doi']}", response)
if data["highlight"] != {
    "1": {"rect": [100, 200, 300, 220], "text": "first part"},
    "2": {"rect": [50, 100, 250, 120], "text": "second part"}
}:
    test_failed("Highlight data does not match", response)
if data["comment"] != "This is an important passage":
    test_failed(f"Expected comment 'This is an important passage', got {data['comment']}", response)
if data["created_at"] is None:
    test_failed("Created_at field is missing", response)
if not isinstance(data["created_at"], str):
    test_failed("Created_at field is not a string", response)

test_passed(f"Retrieved highlight with ID {highlight_id}, DOI {doi}, and highlight data matches")

# Test highlight update
print_separator(f"Testing PUT /highlights/{highlight_id}/")
response = requests.put(
    f"{BASE_URL}/highlights/{highlight_id}/",
    json={
        "doi": "10.1234/example.5678",
        "highlight": {
            "1": {"rect": [100, 200, 300, 220], "text": "updated part"},
            "2": {"rect": [50, 100, 250, 120], "text": "second part"}
        },
        "comment": "Updated comment"
    }
)
if response.status_code != 200:
    test_failed(f"Expected status code 200, got {response.status_code}", response)
try:
    data = response.json()
except json.JSONDecodeError:
    test_failed("Response is not valid JSON", response)
if data["doi"] != "10.1234/example.5678":
    test_failed(f"Expected doi '10.1234/example.5678', got {data['doi']}", response)
if data["highlight"] != {
    "1": {"rect": [100, 200, 300, 220], "text": "updated part"},
    "2": {"rect": [50, 100, 250, 120], "text": "second part"}
}:
    test_failed("Highlight data does not match", response)
if data["comment"] != "Updated comment":
    test_failed(f"Expected comment 'Updated comment', got {data['comment']}", response)
if data["created_at"] is None:
    test_failed("Created_at field is missing", response)
if not isinstance(data["created_at"], str):
    test_failed("Created_at field is not a string", response)
test_passed("highlight updated successfully")

# Test highlights listing
print_separator("Testing GET /highlights/")
response = requests.get(f"{BASE_URL}/highlights/")
if response.status_code != 200:
    test_failed(f"Expected status code 200, got {response.status_code}", response)
try:
    data = response.json()
except json.JSONDecodeError:
    test_failed("Response is not valid JSON", response)
if not isinstance(data, list) or len(data) == 0:
    test_failed("Expected a non-empty list of highlights", response)
test_passed("Retrieved list of highlights")

# Test highlight deletion
print_separator(f"Testing DELETE /highlights/{highlight_id}/")
response = requests.delete(f"{BASE_URL}/highlights/{highlight_id}/")
if response.status_code != 200:
    test_failed(f"Expected status code 200, got {response.status_code}", response)
try:
    data = response.json()
except json.JSONDecodeError:
    test_failed("Response is not valid JSON", response)
if data["id"] != highlight_id:
    test_failed(f"Expected id {highlight_id}, got {data['id']}", response)
test_passed(f"highlight {highlight_id} deleted successfully")

# Test highlight retrieval after deletion
print_separator(f"Testing GET /highlights/{highlight_id}/ after deletion")
response = requests.get(f"{BASE_URL}/highlights/{highlight_id}/")
if response.status_code != 404:
    test_failed(f"Expected status code 404, got {response.status_code}", response)
try:
    data = response.json()
except json.JSONDecodeError:
    test_failed("Response is not valid JSON", response)
if data["detail"] != "highlight not found":
    test_failed(f"Expected 'highlight not found', got {data['detail']}", response)
test_passed(f"Confirmed highlight {highlight_id} not found after deletion")


print("\nAll tests passed successfully!")