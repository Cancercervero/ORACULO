"""Local proxy server — sirve archivos estáticos + proxea vuelos sin CORS.
   Fuente primaria: OpenSky. Fallback: adsb.lol (gratis, sin auth).
   Cache 60s: recargas no queman rate limit.
"""
import json
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from http.server import HTTPServer, SimpleHTTPRequestHandler

_cache: dict = {}
CACHE_TTL = 60

OPENSKY_URL = 'https://opensky-network.org/api/states/all'

# airplanes.live: 9 regiones cubre ~90% del tráfico global
APLIVE_REGIONS = [
    (51, 0, 500),    # Europa
    (40, -100, 500), # EEUU este
    (37, -122, 400), # EEUU oeste
    (35, 139, 500),  # Asia-Pacífico
    (20, 80, 500),   # Asia del Sur
    (25, 55, 500),   # Medio Oriente / Golfo
    (-10, 25, 600),  # África
    (-20, -60, 500), # Sudamérica
    (55, 80, 500),   # Rusia / Siberia
]

def _fetch(url, timeout=18):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def _aplive_to_opensky(all_ac: list) -> bytes:
    """Normaliza lista ac de airplanes.live → formato OpenSky states[]"""
    seen = set()
    states = []
    for ac in all_ac:
        lat = ac.get('lat')
        lon = ac.get('lon')
        key = ac.get('hex', '')
        if lat is None or lon is None or key in seen:
            continue
        seen.add(key)
        alt_ft = ac.get('alt_baro')
        alt_m  = float(alt_ft) * 0.3048 if isinstance(alt_ft, (int, float)) else 0
        gs_kts = ac.get('gs', 0)
        vel_ms = float(gs_kts) * 0.5144 if gs_kts else 0
        states.append([
            key,
            (ac.get('flight') or '').strip(),
            ac.get('r', ''),
            None, None,
            lon, lat,
            alt_m,
            bool(ac.get('gnd', False)),
            vel_ms,
            ac.get('track', 0),
            None, None, None, None, None, None,
        ])
    return json.dumps({'time': 0, 'states': states}).encode()

def fetch_from_aplive() -> bytes:
    def _region(lat, lon, dist):
        url = f'https://api.airplanes.live/v2/point/{lat}/{lon}/{dist}'
        return json.loads(_fetch(url, timeout=12)).get('ac', [])

    all_ac = []
    with ThreadPoolExecutor(max_workers=len(APLIVE_REGIONS)) as ex:
        futures = {ex.submit(_region, lat, lon, dist): (lat, lon) for lat, lon, dist in APLIVE_REGIONS}
        for fut in as_completed(futures, timeout=18):
            try:
                all_ac.extend(fut.result())
            except Exception as e:
                lat, lon = futures[fut]
                print(f'[proxy] aplive {lat},{lon} fail: {e}')

    result = _aplive_to_opensky(all_ac)
    count = len(json.loads(result)['states'])
    print(f'[proxy] airplanes.live OK → {count} ac')
    return result

def fetch_aircraft() -> bytes:
    try:
        data = _fetch(OPENSKY_URL)
        print(f'[proxy] OpenSky OK ({len(data)} bytes)')
        return data
    except Exception as e:
        print(f'[proxy] OpenSky FAIL ({e}) -> airplanes.live fallback')
    return fetch_from_aplive()

class ProxyHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        super().end_headers()

    def do_GET(self):
        path = self.path.split('?')[0]
        if path == '/api/aircraft':
            now = time.time()
            cached = _cache.get('aircraft')
            if cached and (now - cached[1]) < CACHE_TTL:
                data = cached[0]
                print(f'[proxy] /api/aircraft cache hit ({int(now-cached[1])}s)')
            else:
                try:
                    data = fetch_aircraft()
                    _cache['aircraft'] = (data, now)
                except Exception as e:
                    if cached:
                        data = cached[0]
                        print(f'[proxy] all sources failed, serving stale cache')
                    else:
                        self.send_response(502)
                        self.end_headers()
                        self.wfile.write(str(e).encode())
                        return
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(data)
        else:
            super().do_GET()

    def log_message(self, *args, **kwargs):
        pass  # silenciar logs HTTP del servidor base

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print('WIN MirrorWorld proxy: http://localhost:8080/mirror_world_3d.html')
HTTPServer(('', 8080), ProxyHandler).serve_forever()
