import urllib.request
try:
    r = urllib.request.urlopen("http://localhost:8501", timeout=5)
    print(f"App is UP — HTTP {r.status}")
except Exception as e:
    print(f"App is DOWN — {e}")
