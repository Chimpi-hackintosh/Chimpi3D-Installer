"""CLI of my pc: instala Chimpi3D de um Release oficial, com verificação SHA-256.

O executável 'of' precisa estar instalado antes do uso. Não existe instalação
sem que os bytes do aplicativo sejam obtidos de alguma origem.
"""
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
import uuid
from pathlib import Path

OWNER = "Chimpi-hackintosh"
REPOSITORY = "Chimpi3D-Installer"
API = f"https://api.github.com/repos/{OWNER}/{REPOSITORY}/releases/latest"
RELEASE_PATH = f"/{OWNER}/{REPOSITORY}/releases/download/"
MAX_BYTES = 700 * 1024 * 1024

MACOS_NAMES = {
    12: "Monterey", 13: "Ventura", 14: "Sonoma",
    15: "Sequoia", 26: "Tahoe", 27: "GoldenGate",
}


def parse_macos_version(value):
    """Valida versões oficiais macOS 12 a 27 e nomes opcionais."""
    match = re.fullmatch(r"([0-9]{1,2})(?:-(.+))?", str(value).strip())
    if not match:
        raise ValueError("Versão macOS inválida, exemplo: 27-GoldenGate")
    major = int(match.group(1))
    expected = MACOS_NAMES.get(major)
    if expected is None:
        raise ValueError("Versão macOS fora da lista: 12, 13, 14, 15, 26 ou 27")
    if match.group(2):
        given = re.sub(r"[^a-z0-9]", "", match.group(2).casefold())
        canonical = re.sub(r"[^a-z0-9]", "", expected.casefold())
        if given != canonical:
            raise ValueError(f"macOS {major} é {expected}, não {match.group(2)}")
    return major


def validate_macos_environment(declared_version=None, actual_version=None, architecture=None):
    """Não permitir que um parâmetro arbitrário finja ser o macOS instalado."""
    detected = actual_version if actual_version is not None else platform.mac_ver()[0]
    if not detected:
        raise ValueError("Não foi possível detectar a versão do macOS instalado")
    major = int(detected.split(".", 1)[0])
    if major not in MACOS_NAMES:
        raise ValueError(f"macOS {major} não está na faixa documentada 12 a 27")
    if declared_version is not None and parse_macos_version(declared_version) != major:
        raise ValueError(
            f"Este Mac usa macOS {major} ({MACOS_NAMES[major]}), "
            f"mas o parâmetro informou {declared_version}"
        )
    arch = (architecture or platform.machine()).lower()
    if major == 27 and arch not in ("arm64", "aarch64"):
        raise ValueError("macOS 27 Golden Gate requer Apple Silicon")
    if arch not in ("arm64", "aarch64", "x86_64", "amd64"):
        raise ValueError("Arquitetura de Mac não reconhecida: " + arch)
    return major




def parse_command(argv):
    if argv == ["--version"]:
        return {"version": True}
    if len(argv) < 5 or argv[:2] != ["my", "pc"] or "install" not in argv:
        raise ValueError("Uso: of my pc --os Windows|Linux|macOS [--os-version VERSÃO] [--edition EDIÇÃO] install Chimpi3D [--original]")
    idx = argv.index("install")
    parameters = argv[2:idx]
    opts = {}
    i = 0
    while i < len(parameters):
        key = parameters[i]
        if key not in ("--os", "--os-version", "--edition") or key in opts:
            raise ValueError("Opção desconhecida ou repetida: " + key)
        j = i + 1
        while j < len(parameters) and not parameters[j].startswith("--"):
            j += 1
        if j == i + 1:
            raise ValueError("Falta valor para " + key)
        opts[key] = " ".join(parameters[i + 1:j])
        i = j
    extra = argv[idx + 1:]
    if extra not in (["Chimpi3D"], ["Chimpi3D", "--original"]):
        raise ValueError("Use 'install Chimpi3D', com --original opcional no final")
    if opts.get("--os") not in ("Windows", "Linux", "macOS"):
        raise ValueError("Informe --os Windows, Linux ou macOS")
    opts["original"] = extra[-1] == "--original"
    return opts


def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Chimpi3D-of/0.3.1", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def _download(asset, target):
    from urllib.parse import urlparse
    url = asset.get("browser_download_url", "")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "github.com" or not parsed.path.startswith(RELEASE_PATH):
        raise ValueError("URL de download não pertence aos Releases oficiais")
    expected_length = asset.get("size")
    if expected_length and expected_length > MAX_BYTES:
        raise ValueError("Arquivo de instalação acima do limite permitido")
    req = urllib.request.Request(url, headers={"User-Agent": "Chimpi3D-of/0.3.1"})
    digest = hashlib.sha256()
    count = 0
    with urllib.request.urlopen(req, timeout=120) as response, open(target, "wb") as out:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            count += len(chunk)
            if count > MAX_BYTES:
                raise ValueError("Download excedeu o limite de tamanho")
            digest.update(chunk)
            out.write(chunk)
    if expected_length and count != expected_length:
        raise ValueError("Download incompleto")
    return digest.hexdigest()


def _verify(checksums, filename, digest):
    match = re.search(r"(?m)^([a-fA-F0-9]{64})\s+\*?" + re.escape(filename) + r"$", checksums)
    if not match or digest.lower() != match.group(1).lower():
        raise ValueError("A verificação SHA-256 falhou. Instalação cancelada")


def _replace_application(source, destination):
    """Prepare the full copy before replacing the installed application."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".chimpi3d-stage-", dir=destination.parent) as temporary:
        staged = Path(temporary) / destination.name
        shutil.copytree(source, staged, symlinks=True)
        backup = destination.with_name(f".{destination.name}.backup-{uuid.uuid4().hex}")
        previous = destination.exists() or destination.is_symlink()
        if previous:
            destination.rename(backup)
        try:
            staged.rename(destination)
        except BaseException:
            if previous:
                try:
                    backup.rename(destination)
                except OSError as error:
                    # Keep the only good copy outside the temporary directory.
                    raise RuntimeError(f"A versão anterior foi preservada em {backup}") from error
            raise
        if previous:
            if backup.is_symlink() or backup.is_file():
                backup.unlink()
            else:
                shutil.rmtree(backup)


def _replace_launcher(source, destination):
    """Replace the launcher inode, allowing a running Linux 'of' to update itself."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.name}-", dir=destination.parent)
    os.close(descriptor)
    try:
        shutil.copy2(source, temporary)
        Path(temporary).chmod(0o755)
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _install_linux(archive, location):
    destination = Path.home() / ".local" / "share" / "Chimpi3D"
    with tarfile.open(archive, "r:gz") as tf:
        if not hasattr(tarfile, "data_filter"):
            raise RuntimeError("Atualize o Python: extração segura requer tarfile.data_filter")
        tf.extractall(location, filter="data")
    src = location / "Chimpi3D"
    if not (src / "Chimpi3D").is_file() or not (src / "of").is_file():
        raise ValueError("Pacote Linux incompleto")
    _replace_application(src, destination)
    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    launcher = bin_dir / "Chimpi3D"
    launcher.write_text('#!/bin/sh\nexec "$HOME/.local/share/Chimpi3D/Chimpi3D" "$@"\n', encoding="utf-8")
    launcher.chmod(0o755)
    _replace_launcher(src / "of", bin_dir / "of")
    print("Chimpi3D instalado em", destination)
    print("Certifique-se de incluir ~/.local/bin no PATH do terminal")


def _install_macos(archive, location):
    # O ditto preserva links simbólicos e metadados dentro de bundles .app
    subprocess.run(["ditto", "-x", "-k", str(archive), str(location)], check=True)
    apps = list(location.rglob("Chimpi3D.app"))
    if len(apps) != 1 or not (apps[0] / "Contents" / "MacOS" / "Chimpi3D").is_file():
        raise ValueError("Aplicativo macOS não encontrado no ZIP")
    src = apps[0]
    dest = Path.home() / "Applications" / "Chimpi3D.app"
    _replace_application(src, dest)
    of_files = [p for p in location.rglob("of") if p.is_file()]
    if of_files:
        bin_dir = Path.home() / ".local" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        _replace_launcher(of_files[0], bin_dir / "of")
    print("Chimpi3D instalado em", dest)
    print("O aplicativo não é notarizado pela Apple. Respeite as verificações de segurança do macOS")


def install(opts):
    os_name = opts["--os"]
    actual = {"Windows": "Windows", "Linux": "Linux", "macOS": "Darwin"}[os_name]
    if platform.system() != actual:
        raise ValueError("O sistema informado não corresponde ao computador atual")
    if os_name == "macOS":
        actual_major = validate_macos_environment(opts.get("--os-version"))
        print("macOS detectado:", actual_major, MACOS_NAMES[actual_major])
    elif "--os-version" in opts:
        print("Versão informada:", opts["--os-version"], "(não garante compatibilidade)")
    if "--edition" in opts:
        print("Distribuição informada:", opts["--edition"])
    print("Fonte oficial:", API)
    print("A instalação fará download automaticamente e verificará o SHA-256")
    release = _get_json(API)
    if not str(release.get("tag_name", "")).startswith("v0.3."):
        raise ValueError("A versão 0.3.x ainda não está disponível em Releases")
    asset_name = {
        "Windows": "Chimpi3D-Setup-Windows.exe",
        "Linux": "Chimpi3D-Linux-x86_64.tar.gz",
        "macOS": "Chimpi3D-macOS-AppleSilicon.app.zip" if platform.machine().lower() in ("arm64", "aarch64") else "Chimpi3D-macOS-Intel.app.zip",
    }[os_name]
    assets = {a["name"]: a for a in release.get("assets", [])}
    if asset_name not in assets or "SHA256SUMS.txt" not in assets:
        raise ValueError("Release incompleto: instalador ou lista SHA-256 ausentes")
    with tempfile.TemporaryDirectory(prefix="chimpi3d-") as root:
        directory = Path(root)
        sums_file = directory / "SHA256SUMS.txt"
        _download(assets["SHA256SUMS.txt"], sums_file)
        checksum_data = sums_file.read_text(encoding="utf-8")
        target = directory / asset_name
        digest = _download(assets[asset_name], target)
        _verify(checksum_data, asset_name, digest)
        print("Assinatura SHA-256 verificada. Iniciando instalação...")
        if os_name == "Windows":
            subprocess.run([str(target)], check=True)
        elif os_name == "Linux":
            _install_linux(target, directory / "extraido")
        else:
            _install_macos(target, directory / "extraido")
    print("Instalação concluída")


def main(argv=None):
    try:
        opts = parse_command(list(sys.argv[1:] if argv is None else argv))
        if opts.get("version"):
            print("of 0.3.1")
            return 0
        install(opts)
        return 0
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print("Erro:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
