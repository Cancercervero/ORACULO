"""Local proxy server — sirve archivos estáticos + proxea OpenSky sin CORS"""
import os
import urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler

class ProxyHandler(SimpleHTTPRequestHandler):
    PROXY_ROUTES = {
        '/api/aircraft': 'https://opensky-network.org/api/states/all',
    }

    def do_GET(self):
        target = self.PROXY_ROUTES.get(self.path)
        if target:
            try:
                req = urllib.request.Request(target, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=20) as r:
                    data = r.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_response(502)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            super().do_GET()

    def log_message(self, fmt, *args):
        if '/api/' in args[0]:
            print(f'[proxy] {args[0]} {args[1]}')

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print('WIN MirrorWorld proxy: http://localhost:8080/mirror_world_3d.html')
HTTPServer(('', 8080), ProxyHandler).serve_forever()
