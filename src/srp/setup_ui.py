import http.server
import socketserver
import urllib.parse
import json
import asyncio
import webbrowser
import os
import sys

# Ensure we can import modules from src (Add project root to sys.path)
import os   
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.srp.client import SrpClient
from src.srp.config import Config

PORT = 8000

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SRP Server Setup</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f5f5f7;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        h1 {
            text-align: center;
            color: #1d1d1f;
            margin-bottom: 1.5rem;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            color: #86868b;
            font-size: 0.9rem;
        }
        input {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #d2d2d7;
            border-radius: 8px;
            box-sizing: border-box; 
            font-size: 1rem;
        }
        button {
            width: 100%;
            padding: 0.75rem;
            background-color: #0071e3;
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        button:hover {
            background-color: #0077ed;
        }
        button:disabled {
            background-color: #999;
            cursor: not-allowed;
        }
        .status {
            margin-top: 1rem;
            text-align: center;
            font-size: 0.9rem;
            min-height: 1.2rem;
        }
        .error { color: #ff3b30; }
        .success { color: #34c759; }
        .spinner {
            display: inline-block;
            width: 12px;
            height: 12px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
            margin-right: 8px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Connect SRP Account</h1>
        <form id="setupForm">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required placeholder="Enter SRP Username">
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required placeholder="Enter SRP Password">
            </div>
            <button type="submit" id="submitBtn">Connect</button>
        </form>
        <div id="status" class="status"></div>
    </div>

    <script>
        const form = document.getElementById('setupForm');
        const statusDiv = document.getElementById('status');
        const submitBtn = document.getElementById('submitBtn');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = form.username.value;
            const password = form.password.value;

            // UI Loading State
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner"></span>Connecting...';
            statusDiv.textContent = '';
            statusDiv.className = 'status';

            try {
                const response = await fetch('/verify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    statusDiv.textContent = 'Success! Credentials saved. You can close this window.';
                    statusDiv.className = 'status success';
                    submitBtn.textContent = 'Connected';
                } else {
                    throw new Error(data.message || 'Verification failed');
                }
            } catch (error) {
                statusDiv.textContent = error.message;
                statusDiv.className = 'status error';
                submitBtn.disabled = false;
                submitBtn.textContent = 'Connect';
            }
        });
    </script>
</body>
</html>
"""

async def verify_credentials(username, password):
    client = SrpClient(username, password)
    try:
        await client.login()
        # Fetch accounts to automatically get the Account ID
        accounts = await client.get_all_accounts()
        if not accounts or 'billAccountList' not in accounts or not accounts['billAccountList']:
             return False, "Login successful, but no Billing Accounts found."
        
        # Pick the first active account
        account_id = str(accounts['billAccountList'][0]['account'])
        
        # Save to config
        Config.save_credentials(username, password, account_id)
        return True, "Credentials verified and saved."
    except Exception as e:
        return False, str(e)
    finally:
        await client.close()


class SetupHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/verify':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'message': 'Missing fields'}).encode('utf-8'))
                return

            # Run async verification in sync handler
            success, message = asyncio.run(verify_credentials(username, password))
            
            self.send_response(200 if success else 401)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': success, 'message': message}).encode('utf-8'))

def run_server():
    print(f"Starting Setup UI at http://localhost:{PORT}")
    webbrowser.open(f"http://localhost:{PORT}")
    with socketserver.TCPServer(("", PORT), SetupHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down setup server.")

if __name__ == "__main__":
    run_server()
