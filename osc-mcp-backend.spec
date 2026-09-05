import sys, os
site_pkgs = os.path.abspath('.venv/Lib/site-packages')
if site_pkgs not in sys.path:
    sys.path.insert(0, site_pkgs)
# -*- mode: python ; coding: utf-8 -*-
import PyInstaller.utils.hooks as h

_hidden = [
    'uvicorn.logging','uvicorn.loops','uvicorn.loops.asyncio','uvicorn.protocols',
    'uvicorn.protocols.http','uvicorn.protocols.http.httptools_impl','uvicorn.protocols.http.h11_impl',
    'uvicorn.lifespan','uvicorn.lifespan.on',
    "_strptime", "_datetime",
    'cachetools', 'joserfc', 'joserfc.jwk', 'joserfc.jwt',
]
for _mod in ('key_value', 'pydantic'):
    try:
        _hidden += h.collect_submodules(_mod)
    except Exception:
        pass

a = Analysis(
    ['run_server.py'], pathex=['src'],
    datas=[('src/oscmcp', 'oscmcp')],
    hiddenimports=_hidden,
excludes=['tkinter','setuptools','pip','wheel','test','tests','unittest','_distutils_hack'],
    noarchive=True,
)
import os
# mcp/fastmcp call importlib.metadata.version() at import time - stripping their
# dist-info crashes the frozen backend (fleet-wide recurring bug, see
# TAURI_PRODUCTION_PITFALLS.md #12/#13). Keep these alongside the web deps.
for p in ['mcp', 'fastmcp', 'fastapi', 'uvicorn', 'pydantic', 'starlette', 'httpx', 'cachetools']:
    try:
        for src_path, dest_name in h.copy_metadata(p):
            if os.path.isfile(src_path):
                a.datas.append((dest_name, src_path, 'DATA'))
    except Exception:
        pass
# Remove massive binary files from bundled packages
SKIP = ['torch','playwright','bitsandbytes','llvmlite','pyarrow','pymupdf','grpc','numba','Cython','google','azure','boto3','botocore','matplotlib','PIL','pandas','scipy','sklearn','onnxruntime']
a.binaries = [b for b in a.binaries if not any(s in b[0].lower() for s in SKIP)]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas, name='osc-mcp-backend', debug=False, strip=False, upx=False, upx_exclude=[],
     runtime_tmpdir=None, console=False)
