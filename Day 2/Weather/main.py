from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main():
    """Serve both standalone dashboards from this folder for browser API access."""
    app_directory = Path(__file__).resolve().parent
    handler = partial(SimpleHTTPRequestHandler, directory=str(app_directory))
    server = ThreadingHTTPServer(("127.0.0.1", 8000), handler)
    print("Weather: http://127.0.0.1:8000/")
    print("Clinical research: http://127.0.0.1:8000/clinical.html")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nWeather server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
