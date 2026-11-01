"""Recursos locais do Chimpi3D: quadrado arredondado e etiquetas NFC virtuais."""
import json
import math
import os
import uuid
from pathlib import Path


def rounded_square(width=2.0, height=2.0, depth=0.35, radius=0.35, segments=12):
    """Malha 3D fechada: retângulo extrudido com cantos arredondados (estilo UICorner)."""
    import numpy as np
    import trimesh
    width, height, depth, radius = map(float, (width, height, depth, radius))
    if min(width, height, depth) <= 0 or not 0 < radius <= min(width, height) / 2:
        raise ValueError("Dimensões ou raio dos cantos inválidos")
    if not isinstance(segments, int) or not 2 <= segments <= 128:
        raise ValueError("Segmentos devem ficar entre 2 e 128")
    hx, hy = width / 2, height / 2
    corners = [
        (-hx + radius, -hy + radius, math.pi, math.pi * 1.5),
        ( hx - radius, -hy + radius, math.pi * 1.5, math.pi * 2),
        ( hx - radius,  hy - radius, 0, math.pi / 2),
        (-hx + radius,  hy - radius, math.pi / 2, math.pi),
    ]
    ring = []
    for cx, cy, start, end in corners:
        for step in range(segments + 1):
            angle = start + (end - start) * step / segments
            point = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
            if not ring or math.dist(point, ring[-1]) > 1e-9:
                ring.append(point)
    if math.dist(ring[0], ring[-1]) < 1e-9:
        ring.pop()
    n = len(ring)
    bottom = [(x, y, -depth / 2) for x, y in ring]
    top = [(x, y, depth / 2) for x, y in ring]
    vertices = bottom + top + [(0, 0, -depth / 2), (0, 0, depth / 2)]
    faces = []
    for i in range(n):
        j = (i + 1) % n
        faces += [
            (2 * n, j, i),
            (2 * n + 1, n + i, n + j),
            (i, j, n + j),
            (i, n + j, n + i),
        ]
    mesh = trimesh.Trimesh(vertices=np.array(vertices), faces=np.array(faces), process=True)
    if not mesh.is_watertight:
        raise ValueError("Não foi possível criar uma malha fechada")
    return mesh


class NFCWallet:
    """Saldo local de TAGs VIRTUAIS. Não são chips ou créditos de servidor."""
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else Path.home() / ".chimpi3d" / "nfc.json"
        self.data = {"saldo": 0, "resgatados": [], "emitidos": []}
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Arquivo NFC inválido")
            self.data = {
                "saldo": max(0, int(data.get("saldo", 0))),
                "resgatados": list(data.get("resgatados", [])),
                "emitidos": list(data.get("emitidos", [])),
            }

    @property
    def balance(self):
        return self.data["saldo"]

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temp, self.path)

    def redeem(self, code):
        code = code.strip().upper()
        if code != "NFC300" or code in self.data["resgatados"]:
            return False
        self.data["resgatados"].append(code)
        self.data["saldo"] += 300
        self.save()
        return True

    def issue(self):
        if self.balance <= 0:
            raise ValueError("Sem TAGs virtuais disponíveis. Resgate NFC300")
        tag = "CHIMPI-NFC-" + uuid.uuid4().hex.upper()
        self.data["saldo"] -= 1
        self.data["emitidos"].append(tag)
        self.save()
        return tag

    def return_tag(self, tag):
        if tag and tag in self.data["emitidos"]:
            self.data["emitidos"].remove(tag)
            self.data["saldo"] += 1
            self.save()
            return True
        return False
