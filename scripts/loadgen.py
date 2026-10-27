import os
import time

import requests

target = os.getenv("TARGET_URL", "http://127.0.0.1:8000/orders/demo-sku")
while True:
    try:
        requests.get(target, timeout=5)
    except requests.RequestException:
        pass
    time.sleep(0.5)
