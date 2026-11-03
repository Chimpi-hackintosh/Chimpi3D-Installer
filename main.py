import sys, json, math
from pathlib import Path
import numpy as np
import trimesh
import requests
from PIL import Image
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout, QListWidget, QFileDialog, QMessageBox, QInputDialog, QSplitter, QComboBox
import pyqtgraph.opengl as gl
from chimpi_features import NFCWallet, rounded_square

class Chimpi3D(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chimpi3D 0.3.1")
        self.resize(1170, 730)
        self.meshes = []
        self.nfc_tags = []
        self.wallet = NFCWallet()
        self.visible = []
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        bar = QHBoxLayout()
        for title, fn in [("OBJ/STL", self.import_mesh), ("PNG → 3D", self.png3d),
                          ("Exportar OBJ", lambda: self.export(".obj")),
                          ("Exportar STL", lambda: self.export(".stl")),
                          ("Salvar projeto", self.save),
                          ("Abrir projeto", self.load_project),
                          ("Thingiverse", lambda: QDesktopServices.openUrl(QUrl("https://www.thingiverse.com/")))]:
            button = QPushButton(title)
            button.clicked.connect(fn)
            bar.addWidget(button)
        layout.addLayout(bar)
        panes = QSplitter()
        layout.addWidget(panes)
        left = QWidget()
        l = QVBoxLayout(left)
        l.addWidget(QLabel("OBJETOS"))
        self.objects = QListWidget()
        self.objects.currentRowChanged.connect(self.redraw)
        l.addWidget(self.objects)
        for shape in ("Cubo", "Esfera", "Cilindro", "Cone", "Quadrado UICorner"):
            b = QPushButton("Adicionar " + shape)
            b.clicked.connect(lambda checked=False, s=shape: self.primitive(s))
            l.addWidget(b)
        for name, callback in (("Mover XYZ", self.move), ("Redimensionar", self.scale),
                               ("Duplicar", self.duplicate), ("Excluir", self.delete)):
            b = QPushButton(name)
            b.clicked.connect(callback)
            l.addWidget(b)
        l.addWidget(QLabel("NFC VIRTUAL (OPCIONAL)"))
        self.nfc_balance = QLabel()
        l.addWidget(self.nfc_balance)
        for title, callback in (
            ("Resgatar código NFC", self.redeem_nfc),
            ("Vincular TAG ao objeto", self.attach_nfc),
            ("Remover TAG do objeto", self.detach_nfc),
            ("Exportar TAGs (.json)", self.export_nfc),
        ):
            button = QPushButton(title)
            button.clicked.connect(callback)
            l.addWidget(button)
        self.update_nfc_label()
        panes.addWidget(left)
        self.view = gl.GLViewWidget()
        self.view.setCameraPosition(distance=18, elevation=30)
        grid = gl.GLGridItem()
        grid.setSize(50, 50)
        self.view.addItem(grid)
        panes.addWidget(self.view)
        right = QWidget()
        r = QVBoxLayout(right)
        r.addWidget(QLabel("CHIMPIAI"))
        self.prompt = QLineEdit()
        self.prompt.setPlaceholderText("Ex: criar uma esfera")
        r.addWidget(self.prompt)
        self.mode = QComboBox()
        self.mode.addItems(["IA offline simples", "Ollama local: llama3.2:1b"])
        r.addWidget(self.mode)
        ai = QPushButton("Gerar forma 3D")
        ai.clicked.connect(self.ai_generate)
        r.addWidget(ai)
        r.addWidget(QLabel("IMPRESSORA 3D"))
        self.printer = QComboBox()
        self.printer.addItems(["OctoPrint", "Moonraker"])
        r.addWidget(self.printer)
        self.host = QLineEdit()
        self.host.setPlaceholderText("http://192.168.1.10:5000")
        r.addWidget(self.host)
        self.key = QLineEdit()
        self.key.setPlaceholderText("Chave de API (opcional)")
        self.key.setEchoMode(QLineEdit.Password)
        r.addWidget(self.key)
        send = QPushButton("Enviar G-code (não imprimir)")
        send.clicked.connect(self.send_gcode)
        r.addWidget(send)
        r.addWidget(QLabel("G-code deve ser feito em um slicer"))
        r.addStretch()
        panes.addWidget(right)
        panes.setSizes([240, 690, 250])

    def alert(self, message):
        QMessageBox.information(self, "Chimpi3D", str(message))

    def add(self, mesh, name):
        if not isinstance(mesh, trimesh.Trimesh) or mesh.is_empty:
            raise ValueError("Modelo vazio ou inválido")
        self.meshes.append(mesh)
        self.nfc_tags.append(None)
        self.objects.addItem(name)
        self.objects.setCurrentRow(len(self.meshes)-1)
        self.redraw()

    def current(self):
        i = self.objects.currentRow()
        return i if 0 <= i < len(self.meshes) else None

    def redraw(self, *_):
        for item in self.visible:
            self.view.removeItem(item)
        self.visible.clear()
        for i, mesh in enumerate(self.meshes):
            data = gl.MeshData(vertexes=np.asarray(mesh.vertices), faces=np.asarray(mesh.faces))
            color = (0.2, 0.8, 1, 1) if i == self.current() else (0.8, 0.8, 0.9, 1)
            item = gl.GLMeshItem(meshdata=data, color=color, smooth=False, shader="shaded", drawEdges=True)
            self.view.addItem(item)
            self.visible.append(item)

    def primitive(self, shape):
        if shape == "Quadrado UICorner": mesh = rounded_square()
        elif shape == "Cubo": mesh = trimesh.creation.box(extents=(2, 2, 2))
        elif shape == "Esfera": mesh = trimesh.creation.icosphere(subdivisions=2)
        elif shape == "Cilindro": mesh = trimesh.creation.cylinder(radius=1, height=2)
        else: mesh = trimesh.creation.cone(radius=1, height=2)
        self.add(mesh, shape)

    def move(self):
        i = self.current()
        if i is None: return
        text, ok = QInputDialog.getText(self, "Mover", "X, Y, Z (ex: 1,0,2)")
        if ok:
            try:
                coords = [float(x) for x in text.split(",")]
                if len(coords) != 3: raise ValueError("Use 3 coordenadas")
                self.meshes[i].apply_translation(coords)
                self.redraw()
            except Exception as e: self.alert(e)

    def scale(self):
        i = self.current()
        if i is None: return
        value, ok = QInputDialog.getDouble(self, "Escalar", "Multiplicador", 1, 0.01, 100, 2)
        if ok:
            self.meshes[i].apply_scale(value)
            self.redraw()

    def duplicate(self):
        i = self.current()
        if i is not None: self.add(self.meshes[i].copy(), "Cópia")

    def delete(self):
        i = self.current()
        if i is not None:
            self.meshes.pop(i)
            self.wallet.return_tag(self.nfc_tags.pop(i))
            self.update_nfc_label()
            self.objects.takeItem(i)
            self.redraw()

    def pick(self, title, filter):
        return QFileDialog.getOpenFileName(self, title, "", filter)[0]

    def import_mesh(self):
        path = self.pick("Importar modelo", "OBJ/STL/PLY (*.obj *.stl *.ply)")
        if path:
            try: self.add(trimesh.load(path, force="mesh"), Path(path).name)
            except Exception as e: self.alert(e)

    def png3d(self):
        path = self.pick("Selecionar PNG", "PNG (*.png)")
        if not path: return
        try:
            pic = Image.open(path).convert("L")
            pic.thumbnail((24,24))
            arr = np.array(pic)
            pieces = []
            for y in range(arr.shape[0]):
                for x in range(arr.shape[1]):
                    height = 0.2 + float(arr[y,x])/255*2
                    cube = trimesh.creation.box(extents=(1,1,height))
                    cube.apply_translation((x,-y,height/2))
                    pieces.append(cube)
            self.add(trimesh.util.concatenate(pieces), "Relevo PNG")
        except Exception as e: self.alert(e)

    def export(self, ext):
        path = QFileDialog.getSaveFileName(self, "Exportar", "chimpi3d"+ext, "3D (*"+ext+")")[0]
        if path:
            try:
                if not self.meshes: raise ValueError("Cena vazia")
                trimesh.util.concatenate(self.meshes).export(path)
            except Exception as e: self.alert(e)

    def save(self):
        path = QFileDialog.getSaveFileName(self,"Salvar","projeto.chimpi3d","Chimpi3D (*.chimpi3d)")[0]
        if path:
            obj = {"format": "chimpi3d-1", "meshes": [
                {"vertices": m.vertices.tolist(), "faces": m.faces.tolist(),
                 "nfc": self.nfc_tags[i], "name": self.objects.item(i).text()}
                for i, m in enumerate(self.meshes)
            ]}
            Path(path).write_text(json.dumps(obj), encoding="utf-8")

    def load_project(self):
        path = self.pick("Abrir projeto","Chimpi3D (*.chimpi3d)")
        if path:
            try:
                obj = json.loads(Path(path).read_text(encoding="utf-8"))
                if obj.get("format") != "chimpi3d-1": raise ValueError("Formato inválido")
                self.meshes.clear()
                self.nfc_tags.clear()
                self.objects.clear()
                for entry in obj.get("meshes", []):
                    self.add(trimesh.Trimesh(vertices=entry["vertices"],
                                            faces=entry["faces"]), entry.get("name", "Objeto"))
                    self.nfc_tags[-1] = entry.get("nfc")
            except Exception as e: self.alert(e)

    def update_nfc_label(self):
        self.nfc_balance.setText(f"TAGs virtuais disponíveis: {self.wallet.balance}")

    def redeem_nfc(self):
        code, ok = QInputDialog.getText(self, "Resgatar TAGs NFC", "Código de resgate")
        if not ok:
            return
        if self.wallet.redeem(code):
            self.alert("NFC300 resgatado: +300 TAGs VIRTUAIS para vincular aos objetos!")
        else:
            self.alert("Código inválido ou já resgatado neste computador")
        self.update_nfc_label()

    def attach_nfc(self):
        i = self.current()
        if i is None:
            self.alert("Selecione um objeto 3D primeiro")
            return
        if self.nfc_tags[i]:
            self.alert("Este objeto já possui uma TAG NFC virtual")
            return
        try:
            self.nfc_tags[i] = self.wallet.issue()
            self.update_nfc_label()
            self.alert("TAG virtual vinculada ao objeto. Não é um chip NFC físico")
        except Exception as exc:
            self.alert(exc)

    def detach_nfc(self):
        i = self.current()
        if i is None:
            return
        self.wallet.return_tag(self.nfc_tags[i])
        self.nfc_tags[i] = None
        self.update_nfc_label()

    def export_nfc(self):
        path = QFileDialog.getSaveFileName(self, "Exportar etiquetas virtuais",
                                           "chimpi3d-nfc.json", "JSON (*.json)")[0]
        if path:
            data = [{"objeto": self.objects.item(i).text(), "tag_virtual": tag}
                    for i, tag in enumerate(self.nfc_tags) if tag]
            Path(path).write_text(json.dumps({"tipo": "nfc-virtual",
                                              "objetos": data}, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
            self.alert(f"{len(data)} TAGs virtuais exportadas como metadados JSON")

    def ai_generate(self):
        prompt = self.prompt.text().strip()
        if not prompt: return
        response = prompt.lower()
        if self.mode.currentIndex() == 1:
            try:
                result = requests.post("http://127.0.0.1:11434/api/generate", json={
                    "model": "llama3.2:1b", "prompt":
                    "Diga apenas cubo, esfera, cone ou cilindro para: " + prompt,
                    "stream": False
                }, timeout=30)
                result.raise_for_status()
                response = result.json()["response"].lower()
            except Exception as e:
                self.alert("Ollama não disponível: " + str(e))
                return
        if "esfer" in response or "bola" in response: shape = "Esfera"
        elif "cilind" in response or "tubo" in response: shape = "Cilindro"
        elif "cone" in response: shape = "Cone"
        else: shape = "Cubo"
        self.primitive(shape)

    def send_gcode(self):
        path = self.pick("G-code do slicer","G-code (*.gcode)")
        if not path: return
        url = self.host.text().strip().rstrip("/")
        if not url.startswith(("http://","https://")):
            self.alert("Digite o endereço HTTP(S) da impressora")
            return
        if QMessageBox.question(self, "Confirmação", "Enviar arquivo sem iniciar a impressão?") != QMessageBox.Yes:
            return
        try:
            headers = {}
            if self.printer.currentText() == "OctoPrint":
                endpoint = "/api/files/local"
                if self.key.text(): headers["X-Api-Key"] = self.key.text()
            else:
                endpoint = "/server/files/upload"
                if self.key.text(): headers["Authorization"] = "Bearer " + self.key.text()
            with open(path, "rb") as f:
                response = requests.post(url + endpoint, headers=headers,
                                         files={"file": (Path(path).name, f)}, timeout=45)
            response.raise_for_status()
            self.alert("Arquivo enviado, confira o painel antes de imprimir")
        except Exception as e: self.alert(e)

if __name__ == "__main__":
    application = QApplication(sys.argv)
    application.setStyle("Fusion")
    app = Chimpi3D()
    app.show()
    from support_notice import attach_qt
    attach_qt(app, "Chimpi3D-Installer", "0.3.1")
    sys.exit(application.exec())
