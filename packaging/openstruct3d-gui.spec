# -*- mode: python ; coding: utf-8 -*-
"""Spec do PyInstaller para o executavel desktop ``openstruct3d-gui``.

Uso (a partir da raiz do repositorio, com o extra ``build`` instalado —
``pip install -e ".[gui,build]"``):

    pyinstaller packaging/openstruct3d-gui.spec

Gera um executavel ONEFILE em ``dist/openstruct3d-gui`` (ou
``dist/openstruct3d-gui.exe`` no Windows). Ver
``docs/decisions/ADR-003-gui-arquitetura.md`` e
``docs/build/EMPACOTAMENTO.md`` para a limitacao de que um ``.exe``
Windows so pode ser gerado rodando o PyInstaller EM UM Windows (nao ha
cross-compilation) — este ``.spec`` e o mesmo nos dois sistemas
operacionais, so muda a maquina onde e executado.
"""

import os

from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis

# SPECPATH e injetado pelo PyInstaller no namespace do .spec com o
# diretorio ONDE ESTE ARQUIVO ESTA — usar caminhos absolutos derivados
# dele (em vez de relativos ao diretorio de trabalho) torna o comando
# `pyinstaller packaging/openstruct3d-gui.spec` funcionar de qualquer
# diretorio a partir do qual seja chamado (raiz do repo incluida).
_HERE = SPECPATH  # noqa: F821 - injetado pelo PyInstaller
_SRC = os.path.join(_HERE, "..", "src")

block_cipher = None

a = Analysis(
    [os.path.join(_HERE, "entrypoint.py")],
    pathex=[_SRC],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="openstruct3d-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
