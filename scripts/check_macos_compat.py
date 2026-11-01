"""Verifica as declarações de versão mínima do pacote macOS, sem fingir testar o SO."""
import plistlib
import re
import subprocess
import sys
from pathlib import Path

TARGET = (12, 0)
IMPORTANT = {"Chimpi3D", "QtCore", "QtGui", "QtWidgets", "QtOpenGL", "QtOpenGLWidgets"}


def version_tuple(text):
    values = tuple(int(x) for x in str(text).split(".")[:2])
    return values + (0,) * (2 - len(values))


def check(bundle):
    bundle = Path(bundle)
    plist_path = bundle / "Contents" / "Info.plist"
    with plist_path.open("rb") as stream:
        info = plistlib.load(stream)
    minimum = info.get("LSMinimumSystemVersion")
    if not minimum:
        raise RuntimeError("O aplicativo não declara LSMinimumSystemVersion")
    if version_tuple(minimum) > TARGET:
        raise RuntimeError(f"Info.plist exige macOS {minimum}, acima do Monterey 12")
    print(f"Info.plist: LSMinimumSystemVersion={minimum}")
    exe = bundle / "Contents" / "MacOS" / "Chimpi3D"
    selected = [exe]
    for path in bundle.rglob("*"):
        if path.is_file() and path.name in IMPORTANT - {"Chimpi3D"}:
            selected.append(path)
    checked = set()
    for path in selected:
        if path in checked:
            continue
        checked.add(path)
        result = subprocess.run(["otool", "-l", str(path)], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(f"Falha ao verificar o binário: {path}")
        commands = re.findall(r"cmd LC_BUILD_VERSION[\s\S]*?cmdsize \d+[\s\S]*?minos ([0-9.]+)", result.stdout)
        commands += re.findall(r"cmd LC_VERSION_MIN_MACOSX[\s\S]*?cmdsize \d+[\s\S]*?version ([0-9.]+)", result.stdout)
        if not commands:
            raise RuntimeError(f"Sem alvo mínimo detectável no binário: {path}")
        for value in commands:
            if version_tuple(value) > TARGET:
                raise RuntimeError(f"{path.name} exige macOS {value} e não rodará no Monterey 12")
        print(f"{path.name}: versões mínimas {', '.join(commands)}")
    if len(checked) < 2:
        raise RuntimeError("Não foi encontrado o framework Qt para verificar")
    print("Verificação básica do alvo Monterey 12 concluída")
    print("ATENÇÃO: isto não substitui um teste real em macOS 12, 13, 14, 15, 26 e 27")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python scripts/check_macos_compat.py dist/Chimpi3D.app")
    check(sys.argv[1])
