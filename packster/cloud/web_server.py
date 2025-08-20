"""Web server for displaying Packster download information."""

import socket
import threading
import webbrowser
from pathlib import Path
from typing import Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse


class PacksterDownloadHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Packster download page."""
    
    def __init__(self, *args, download_info=None, **kwargs):
        self.download_info = download_info or {}
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_content = self._generate_html()
            self.wfile.write(html_content.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def _generate_html(self) -> str:
        """Generate HTML content for the download page."""
        download_url = self.download_info.get('download_url', '')
        file_name = self.download_info.get('file_name', '')
        gist_id = self.download_info.get('gist_id', '')
        expires_at = self.download_info.get('expires_at', '')
        
        download_command = f'curl -L "{download_url}" | tar -xz && cd {file_name.replace(".tar.gz", "")} && ./bootstrap.sh/bootstrap.sh'
        qr_command_template = f'curl -L "URL" | tar -xz && cd {file_name.replace(".tar.gz", "")} && ./bootstrap.sh/bootstrap.sh'
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Packster Migration Download</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }}
        .info-box {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 15px 0;
        }}
        .command-box {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            word-break: break-all;
            margin: 15px 0;
        }}
        .copy-btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 0;
        }}
        .copy-btn:hover {{
            background: #2980b9;
        }}
        .qr-section {{
            text-align: center;
            margin: 30px 0;
        }}
        .qr-code {{
            max-width: 300px;
            margin: 20px auto;
        }}
        .steps {{
            background: #e8f5e8;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .steps ol {{
            margin: 0;
            padding-left: 20px;
        }}
        .steps li {{
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Packster Migration Ready!</h1>
        
        <div class="info-box">
            <strong>Migration Details:</strong><br>
            Gist ID: {gist_id}<br>
            Expires: {expires_at}<br>
            File: {file_name}
        </div>
        
        <h3>📥 Download Command:</h3>
        <div class="command-box" id="download-command">
            {download_command}
        </div>
        
        <button class="copy-btn" onclick="copyCommand()">📋 Copy Command</button>
        
        <div class="qr-section">
            <h3>📱 QR Code (Scan with your phone):</h3>
            <div class="qr-code">
                <img src="data:image/png;base64,{self._generate_qr_base64(download_url)}" 
                     alt="QR Code" style="max-width: 100%;">
            </div>
            <p><em>Scan this QR code to get the download URL</em></p>
            <p><em>Then use: <code>{qr_command_template}</code></em></p>
        </div>
        
        <div class="steps">
            <h3>📋 Installation Steps:</h3>
            <ol>
                <li>Copy the command above (or scan the QR code)</li>
                <li>Open Terminal on your Mac</li>
                <li>Paste and run the command</li>
                <li>Wait for installation to complete</li>
                <li>Check the generated report.html for details</li>
            </ol>
        </div>
        
        <div class="info-box">
            <strong>💡 Tip:</strong> You can also just copy the URL and download manually:<br>
            <a href="{download_url}" target="_blank">{download_url}</a>
        </div>
    </div>
    
    <script>
        function copyCommand() {{
            const command = document.getElementById('download-command').textContent;
            navigator.clipboard.writeText(command).then(function() {{
                alert('Command copied to clipboard!');
            }});
        }}
    </script>
</body>
</html>
        """
    
    def _generate_qr_base64(self, data: str) -> str:
        """Generate QR code and return as base64 string."""
        try:
            import qrcode
            import base64
            from io import BytesIO
            
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return img_str
        except ImportError:
            return ""  # Return empty if qrcode not available


def start_web_server(download_info: dict, port: int = 8080) -> tuple[str, int]:
    """Start a web server to display download information.
    
    Args:
        download_info: Dictionary containing download information
        port: Port to run the server on
        
    Returns:
        Tuple of (server_url, actual_port)
    """
    # Find available port
    actual_port = port
    while actual_port < port + 10:
        try:
            server = HTTPServer(('', actual_port), PacksterDownloadHandler)
            break
        except OSError:
            actual_port += 1
    else:
        raise RuntimeError("No available ports found")
    
    # Set download info for the handler
    server.RequestHandlerClass.download_info = download_info
    
    # Get local IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    server_url = f"http://{local_ip}:{actual_port}"
    
    # Start server in background thread
    def run_server():
        server.serve_forever()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    return server_url, actual_port


def open_download_page(download_info: dict, port: int = 8080) -> str:
    """Start web server and open download page in browser.
    
    Args:
        download_info: Dictionary containing download information
        port: Port to run the server on
        
    Returns:
        URL of the web page
    """
    server_url, actual_port = start_web_server(download_info, port)
    
    # Open in browser
    try:
        webbrowser.open(server_url)
    except Exception:
        pass  # Browser might not be available
    
    return server_url
