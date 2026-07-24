import socket
import ipaddress
from urllib.parse import urlparse
from app.errors import invalid_url, private_address

def validate_url(url: str) -> str:
    """
    Validates a URL against SSRF by resolving its hostname and checking
    if it points to a private, loopback, link-local, or multicast IP.
    Returns the parsed and validated URL.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        raise invalid_url("Malformed URL.")

    if not parsed.scheme or not parsed.netloc:
        raise invalid_url("Malformed URL, missing scheme or host.")
        
    if parsed.scheme not in ("http", "https"):
        raise invalid_url("URL scheme must be http or https.")

    hostname = parsed.hostname
    if not hostname:
        raise invalid_url("Malformed URL, missing hostname.")

    try:
        # Resolve hostname to IP
        ip_addr_str = socket.gethostbyname(hostname)
    except socket.gaierror:
        raise invalid_url("Could not resolve hostname.")

    try:
        ip = ipaddress.ip_address(ip_addr_str)
    except ValueError:
        raise invalid_url("Invalid IP address resolved.")

    # Check for private, loopback, link-local, multicast
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
        raise private_address()
        
    return url
