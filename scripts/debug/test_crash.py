import http.server, socketserver, threading, subprocess
class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        data = self.rfile.read(length).decode('utf-8')
        with open('crash.log', 'w') as f:
            f.write(data)
        self.send_response(200)
        self.end_headers()
        threading.Thread(target=self.server.shutdown).start()

httpd = socketserver.TCPServer(('', 9999), Handler)
t = threading.Thread(target=httpd.serve_forever)
t.start()
print('Listening on 9999...')
subprocess.Popen([".venv\\Scripts\\python.exe", "desktop_app.py"])
t.join()
print('Log received.')
