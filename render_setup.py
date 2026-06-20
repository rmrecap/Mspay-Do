import os
import glob
import importlib.util

spec = importlib.util.find_spec('fastapi_jwt_auth')
if spec and spec.submodule_search_locations:
    pkg_dir = spec.submodule_search_locations[0]
    for fname in ('config.py', 'auth_config.py'):
        fpath = os.path.join(pkg_dir, fname)
        if os.path.exists(fpath):
            with open(fpath, 'r') as f:
                content = f.read()
            patched = content.replace(
                'from pydantic import',
                'from pydantic.v1 import'
            )
            if patched != content:
                with open(fpath, 'w') as f:
                    f.write(patched)
                print(f"Patched {fpath}")

# Fix Axios baseURL in React build - handle empty port (443/80)
build_js = glob.glob("build/static/js/main.*.js")
for fpath in build_js:
    if os.path.exists(fpath):
        with open(fpath, 'r') as f:
            content = f.read()
        # Fix: window.location.protocol + "//" + window.location.hostname + ":" + window.location.port
        # When port is empty (443/80), this produces "https://host:" which is malformed.
        old = 'window.location.protocol+"//"+window.location.hostname+":"+window.location.port'
        new = 'window.location.protocol+"//"+window.location.hostname+(window.location.port?":"+window.location.port:"")'
        if old in content:
            content = content.replace(old, new)
            with open(fpath, 'w') as f:
                f.write(content)
            print(f"Patched {fpath} - fixed empty port in baseURL")
        else:
            # Try with spaces
            old2 = 'window.location.protocol + "//" + window.location.hostname + ":" + window.location.port'
            new2 = 'window.location.protocol + "//" + window.location.hostname + (window.location.port ? ":" + window.location.port : "")'
            if old2 in content:
                content = content.replace(old2, new2)
                with open(fpath, 'w') as f:
                    f.write(content)
                print(f"Patched {fpath} - fixed empty port in baseURL")
