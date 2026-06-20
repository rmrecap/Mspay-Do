import os
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
