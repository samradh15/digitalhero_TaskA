# Page Pulse

A URL health-audit diagnostic tool, presented as a "clinical paper" chart.

## Design Decisions

### SSRF Guard
For security reasons, this tool actively blocks Server-Side Request Forgery (SSRF) attempts. Before fetching any URL, `page-pulse` resolves the hostname to an IP address and blocks the request if the IP falls within private, loopback, link-local, or multicast ranges (e.g., `127.0.0.0/8`, `192.168.0.0/16`, `10.0.0.0/8`). This prevents the application from being used to probe internal networks or services.

### Word Count Logic
To provide a more accurate count of the page's actual content (the "meat" of the page), the HTML parser specifically strips out common boilerplate tags before counting words. Tags removed include `<script>`, `<style>`, `<nav>`, `<footer>`, and `<header>`. This decision ensures that navigation links and footers do not artificially inflate the word count metric.

### Response Size Limit
The backend actively limits the response payload stream to a maximum of 5MB before completing the parse. Any payload exceeding this limit triggers a `413 Payload Too Large` error, protecting the server from out-of-memory errors on massive inputs.

### Built For
Built for Digital Heroes Training Task.
