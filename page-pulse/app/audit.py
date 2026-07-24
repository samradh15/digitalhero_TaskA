import time
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup

from app.errors import (
    timeout,
    connection_failed,
    too_many_redirects,
    upstream_error,
    non_html_response,
    response_too_large
)
from app.ssrf_guard import validate_url

async def run_audit(url: str) -> dict:
    # 1. Validate URL against SSRF
    validate_url(url)
    
    # 2. Fetch the page
    start_time = time.perf_counter()
    try:
        async with httpx.AsyncClient(max_redirects=5, verify=False) as client:
            # We don't verify SSL for a general diagnostic tool to at least return response status, 
            # though usually it's fine. Wait, let's keep verify=True for security, unless connection_failed handles it.
            # We'll use verify=True (default) and let connection_failed catch TLS errors.
            pass
    except Exception:
        pass
        
    try:
        async with httpx.AsyncClient(max_redirects=5) as client:
            response = await client.get(url, timeout=10.0)
            
            # Check content length before downloading if possible, though httpx reads to memory for small responses.
            # We will use streaming to prevent large downloads? The spec says "Body exceeds 5MB before parsing completes"
            # We'll use async with client.stream
            pass
    except Exception:
        pass
        
    # Let's write the actual fetch logic properly with streaming to enforce 5MB limit
    
    MAX_SIZE = 5 * 1024 * 1024  # 5MB
    
    try:
        async with httpx.AsyncClient(max_redirects=5) as client:
            # start timer
            start_time = time.perf_counter()
            
            async with client.stream("GET", url, timeout=10.0) as response:
                response_time_ms = int((time.perf_counter() - start_time) * 1000)
                
                status_code = response.status_code
                final_url = str(response.url)
                content_type_header = response.headers.get("content-type", "")
                
                if "text/html" not in content_type_header.lower():
                    raise non_html_response(content_type_header or "unknown")
                
                # Read content with size limit
                content_bytes = bytearray()
                async for chunk in response.aiter_bytes():
                    content_bytes.extend(chunk)
                    if len(content_bytes) > MAX_SIZE:
                        raise response_too_large()
                        
                html_content = content_bytes.decode(response.encoding or "utf-8", errors="replace")
                
    except httpx.TimeoutException:
        raise timeout()
    except httpx.TooManyRedirects:
        raise too_many_redirects()
    except httpx.RequestError as e:
        # DNS failure, connection refused, TLS error
        raise connection_failed(type(e).__name__)
    except Exception as e:
        from app.errors import AuditError
        if isinstance(e, AuditError):
            raise
        raise upstream_error()

    # 3. Parse HTML
    soup = BeautifulSoup(html_content, "html.parser")
    
    # 4. Extract metrics
    # title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else None
    
    # meta_description
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else None
    if not meta_description and meta_desc_tag:
        meta_description = None  # if empty
        
    # h1_count
    h1_count = len(soup.find_all("h1"))
    
    # images
    images = soup.find_all("img")
    images_total = len(images)
    images_missing_alt = sum(1 for img in images if not img.get("alt") or not img.get("alt").strip())
    
    # word_count
    # strip <script>, <style>, <nav>, <footer>, <header>
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
        
    text = soup.get_text(separator=" ")
    word_count = len(text.split())
    
    scanned_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return {
        "url": url,
        "final_url": final_url,
        "status_code": status_code,
        "response_time_ms": response_time_ms,
        "content_type": content_type_header,
        "title": title,
        "meta_description": meta_description,
        "h1_count": h1_count,
        "images_total": images_total,
        "images_missing_alt": images_missing_alt,
        "word_count": word_count,
        "scanned_at": scanned_at
    }
