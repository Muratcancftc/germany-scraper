"""Vercel build step: download the Camoufox browser into the project dir so it
gets bundled with the function. At runtime the browser is copied to /tmp (the
only writable location on Vercel Functions).
"""

import os
import subprocess
import sys


def main() -> None:
    cache = os.path.join(os.getcwd(), ".camoufox_cache")
    os.environ["XDG_CACHE_HOME"] = cache
    os.makedirs(cache, exist_ok=True)

    print("Fetching Camoufox browser...", flush=True)
    subprocess.run([sys.executable, "-m", "camoufox", "fetch"], check=True, env=os.environ)
    print("Camoufox browser ready.", flush=True)


if __name__ == "__main__":
    main()
