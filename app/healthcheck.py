import os
import urllib.request
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    port = os.getenv("APP_PORT", "8000")
    api_key = os.getenv("API_KEY")
    request = urllib.request.Request(
        f"http://localhost:{port}/health",
        headers={"X-API-Key": api_key},
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        if response.status != 200:
            raise RuntimeError(f"Healthcheck returned HTTP {response.status}")
        else:
            print("Server is Good!")


if __name__ == "__main__":
    main()
