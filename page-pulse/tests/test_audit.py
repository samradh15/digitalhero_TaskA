import pytest
from fastapi.testclient import TestClient
import httpx
import respx
from unittest.mock import patch

from app.main import app

client = TestClient(app)

@pytest.fixture
def healthy_page_html():
    return """
    <html>
        <head>
            <title>Healthy Page</title>
            <meta name="description" content="This is a healthy page.">
        </head>
        <body>
            <header>Boilerplate header</header>
            <nav>Nav link</nav>
            <h1>Heading 1</h1>
            <h1>Heading 2</h1>
            <p>This is some visible text that should count towards the word count. It has exactly eighteen words.</p>
            <img src="img1.jpg" alt="Image 1">
            <img src="img2.jpg" alt="">
            <img src="img3.jpg" alt="Image 3">
            <footer>Footer text</footer>
            <script>console.log('script');</script>
        </body>
    </html>
    """

@pytest.fixture
def minimal_page_html():
    return """
    <html>
        <head></head>
        <body>
            <p>Minimal</p>
        </body>
    </html>
    """

@respx.mock
@patch("socket.gethostbyname", return_value="8.8.8.8")
def test_happy_path_full_page(mock_dns, healthy_page_html):
    respx.get("http://example.com").mock(
        return_value=httpx.Response(200, text=healthy_page_html, headers={"content-type": "text/html"})
    )
    
    response = client.post("/api/audit", json={"url": "http://example.com"})
    assert response.status_code == 200
    
    data = response.json()
    assert data["url"] == "http://example.com"
    assert data["status_code"] == 200
    assert data["content_type"] == "text/html"
    assert data["title"] == "Healthy Page"
    assert data["meta_description"] == "This is a healthy page."
    assert data["h1_count"] == 2
    assert data["images_total"] == 3
    assert data["images_missing_alt"] == 1
    # Boilerplate stripped: "Healthy Page Heading 1 Heading 2 This is some visible text that should count towards the word count. It has exactly eighteen words." -> 23 words
    assert data["word_count"] == 23

@respx.mock
@patch("socket.gethostbyname", return_value="8.8.8.8")
def test_missing_title_and_meta(mock_dns, minimal_page_html):
    respx.get("http://example.com").mock(
        return_value=httpx.Response(200, text=minimal_page_html, headers={"content-type": "text/html"})
    )
    
    response = client.post("/api/audit", json={"url": "http://example.com"})
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] is None
    assert data["meta_description"] is None

def test_invalid_url_rejected():
    response = client.post("/api/audit", json={"url": "not a url"})
    assert response.status_code == 400
    
    data = response.json()
    assert data["error"]["code"] == "INVALID_URL"

@respx.mock
@patch("socket.gethostbyname", return_value="8.8.8.8")
def test_timeout_returns_clean_error(mock_dns):
    respx.get("http://example.com").mock(side_effect=httpx.TimeoutException("timeout"))
    
    response = client.post("/api/audit", json={"url": "http://example.com"})
    assert response.status_code == 504
    
    data = response.json()
    assert data["error"]["code"] == "TIMEOUT"
    assert data["error"]["message"] == "Couldn't reach this URL — the server didn't respond within 10s."

@respx.mock
@patch("socket.gethostbyname", return_value="8.8.8.8")
def test_non_html_response_rejected(mock_dns):
    respx.get("http://example.com").mock(
        return_value=httpx.Response(200, content=b"fake pdf", headers={"content-type": "application/pdf"})
    )
    
    response = client.post("/api/audit", json={"url": "http://example.com"})
    assert response.status_code == 415
    
    data = response.json()
    assert data["error"]["code"] == "NON_HTML_RESPONSE"
    assert data["error"]["message"] == "Expected text/html, but received application/pdf."

@respx.mock
@patch("socket.gethostbyname", return_value="192.168.1.1")
def test_private_address_blocked(mock_dns):
    # The mock fetch is deliberately not defined to assert it's never called.
    # If the SSRF guard fails, it would try to fetch and respx would raise an unmocked error.
    response = client.post("/api/audit", json={"url": "http://internal-server.local"})
    assert response.status_code == 400
    
    data = response.json()
    assert data["error"]["code"] == "PRIVATE_ADDRESS"
    assert respx.calls.call_count == 0

@respx.mock
@patch("socket.gethostbyname", return_value="8.8.8.8")
def test_too_many_redirects(mock_dns):
    respx.get("http://example.com").mock(side_effect=httpx.TooManyRedirects("too many redirects"))
    
    response = client.post("/api/audit", json={"url": "http://example.com"})
    assert response.status_code == 502
    
    data = response.json()
    assert data["error"]["code"] == "TOO_MANY_REDIRECTS"
    assert data["error"]["message"] == "This URL redirected more than 5 times."

@respx.mock
@patch("socket.gethostbyname", return_value="8.8.8.8")
def test_unhandled_exception_never_leaks_traceback(mock_dns):
    respx.get("http://example.com").mock(side_effect=ValueError("weird"))
    
    response = client.post("/api/audit", json={"url": "http://example.com"})
    assert response.status_code == 502
    
    data = response.json()
    assert data["error"]["code"] == "UPSTREAM_ERROR"
    assert "weird" not in response.text
    assert data["error"]["message"] == "An unexpected error occurred while processing the URL."
