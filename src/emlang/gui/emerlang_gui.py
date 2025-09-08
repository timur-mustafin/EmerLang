# emerlang_gui.py
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets

# --- hook into your package ---
from emlang import Codebook
from emlang.encoder import encode as em_encode
from emlang.decoder import decode as em_decode

ENCODINGS = ("utf-8", "utf-8-sig", "utf-16-le", "utf-16-be")

def read_text_any(path: str) -> str:
    b = Path(path).read_bytes()
    for enc in ENCODINGS:
        try: return b.decode(enc)
        except Exception: pass
    return b.decode("utf-8", errors="replace")

# -----------------------------
# Generic placeholders for other tabs (wire your logic later)
# -----------------------------
class BuildTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lab = QtWidgets.QLabel("Build tab (wire your existing Build UI here)")
        lab.setAlignment(QtCore.Qt.AlignCenter)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(lab)

class EncodeTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lab = QtWidgets.QLabel("Encode tab (wire your existing Encode UI here)")
        lab.setAlignment(QtCore.Qt.AlignCenter)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(lab)

class DecodeTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lab = QtWidgets.QLabel("Decode tab (wire your existing Decode UI here)")
        lab.setAlignment(QtCore.Qt.AlignCenter)
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(lab)

# -----------------------------
# Demo tab with 2×2 layout + typewriter animation
# -----------------------------
@dataclass
class DemoConfig:
    a_text: str = "params? v.new test"
    b_text: str = "ckpt v0.44 opt=adam"
    structure: float = 0.2
    seed: int = 42
    after_delay_ms: int = 2000
    type_speed_ms: int = 15   # symbol interval (fast but smooth)

class Typewriter(QtCore.QObject):
    finished = QtCore.Signal()

    def __init__(self, target: QtWidgets.QPlainTextEdit, text: str, interval_ms: int = 15, parent=None):
        super().__init__(parent)
        self._target = target
        self._text = text
        self._i = 0
        self._timer = QtCore.QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.setInterval(interval_ms)

    def start(self):
        self._target.clear()
        self._i = 0
        self._timer.start()

    def _tick(self):
        if self._i >= len(self._text):
            self._timer.stop()
            self.finished.emit()
            return
        self._target.moveCursor(QtGui.QTextCursor.End)
        self._target.insertPlainText(self._text[self._i])
        self._i += 1

class DemoTab(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cfg = DemoConfig()
        self.cb: Optional[Codebook] = None
        self._build_ui()
        self._wire()

    def _build_ui(self):
        # Controls row
        self.codebookEdit = QtWidgets.QLineEdit("codebook.json")
        self.codebookBtn = QtWidgets.QPushButton("Browse…")
        self.structSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.structSlider.setRange(0, 100)
        self.structSlider.setValue(int(self.cfg.structure * 100))
        self.structLabel = QtWidgets.QLabel(f"Structure: {self.cfg.structure:.2f}")

        self.seedSpin = QtWidgets.QSpinBox()
        self.seedSpin.setRange(0, 2**31-1)
        self.seedSpin.setValue(self.cfg.seed)

        self.runBtn = QtWidgets.QPushButton("Run demo")
        self.runBtn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_MediaPlay))

        # editable demo texts
        self.aEdit = QtWidgets.QLineEdit(self.cfg.a_text)
        self.bEdit = QtWidgets.QLineEdit(self.cfg.b_text)

        # Grid 2×2
        self.A_enc = QtWidgets.QPlainTextEdit(); self._prep_box(self.A_enc, "A (encoded)")
        self.B_enc = QtWidgets.QPlainTextEdit(); self._prep_box(self.B_enc, "B (encoded)")
        self.A_dec = QtWidgets.QPlainTextEdit(); self._prep_box(self.A_dec, "A decoded")
        self.B_dec = QtWidgets.QPlainTextEdit(); self._prep_box(self.B_dec, "B decoded")

        # Layouts
        toolbar = QtWidgets.QGridLayout()
        toolbar.addWidget(QtWidgets.QLabel("Codebook"), 0, 0)
        toolbar.addWidget(self.codebookEdit, 0, 1)
        toolbar.addWidget(self.codebookBtn, 0, 2)
        toolbar.addWidget(QtWidgets.QLabel("Structure"), 1, 0)
        toolbar.addWidget(self.structSlider, 1, 1)
        toolbar.addWidget(self.structLabel, 1, 2)
        toolbar.addWidget(QtWidgets.QLabel("Seed"), 2, 0)
        toolbar.addWidget(self.seedSpin, 2, 1)
        toolbar.addWidget(self.runBtn, 2, 2)

        demoRow = QtWidgets.QHBoxLayout()
        demoRow.addWidget(QtWidgets.QLabel("A text:"))
        demoRow.addWidget(self.aEdit)
        demoRow.addSpacing(12)
        demoRow.addWidget(QtWidgets.QLabel("B text:"))
        demoRow.addWidget(self.bEdit)
        demoRow.addStretch(1)

        grid = QtWidgets.QGridLayout()
        grid.addWidget(self.A_enc, 0, 0)
        grid.addWidget(self.B_enc, 0, 1)
        grid.addWidget(self.A_dec, 1, 0)
        grid.addWidget(self.B_dec, 1, 1)
        grid.setRowStretch(0, 1); grid.setRowStretch(1, 1)
        grid.setColumnStretch(0, 1); grid.setColumnStretch(1, 1)

        outer = QtWidgets.QVBoxLayout(self)
        outer.addLayout(toolbar)
        outer.addSpacing(6)
        outer.addLayout(demoRow)
        outer.addSpacing(6)
        outer.addLayout(grid)

        # Status
        self.status = QtWidgets.QLabel("")
        outer.addWidget(self.status)

    def _prep_box(self, box: QtWidgets.QPlainTextEdit, title: str):
        box.setReadOnly(True)
        box.setPlaceholderText(title)
        f = box.font(); f.setFamily("DejaVu Sans"); box.setFont(f)  # glyph-friendly default

    def _wire(self):
        self.codebookBtn.clicked.connect(self._pick_cb)
        self.structSlider.valueChanged.connect(self._on_struct)
        self.runBtn.clicked.connect(self._run_demo)

    def _pick_cb(self):
        p, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose codebook", self.codebookEdit.text(), "JSON (*.json)")
        if p: self.codebookEdit.setText(p)

    def _on_struct(self, v: int):
        self.structLabel.setText(f"Structure: {v/100:.2f}")

    def _load_codebook(self) -> Optional[Codebook]:
        path = self.codebookEdit.text().strip()
        try:
            cb = Codebook.load(path)
            self.status.setText(f"Loaded codebook: {path}")
            return cb
        except Exception as e:
            self.status.setText(f"Failed to load codebook: {e}")
            return None

    def _run_demo(self):
        self.A_enc.clear(); self.B_enc.clear(); self.A_dec.clear(); self.B_dec.clear()
        cb = self._load_codebook()
        if not cb:
            return
        # Gather config
        self.cfg.a_text = self.aEdit.text()
        self.cfg.b_text = self.bEdit.text()
        self.cfg.structure = self.structSlider.value()/100.0
        self.cfg.seed = self.seedSpin.value()

        # Encode using your library (real codebook => real look)
        try:
            a_em = em_encode(self.cfg.a_text, cb, structure=self.cfg.structure, seed=self.cfg.seed)
            b_em = em_encode(self.cfg.b_text, cb, structure=self.cfg.structure, seed=self.cfg.seed)
        except Exception as e:
            self.status.setText(f"Encode error: {e}")
            return

        # Typewriter animations
        self._tw_a = Typewriter(self.A_enc, a_em, interval_ms=self.cfg.type_speed_ms)
        self._tw_b = Typewriter(self.B_enc, b_em, interval_ms=self.cfg.type_speed_ms)

        # After both finished -> schedule decoding display
        self._tw_done = 0
        def _on_one_finished():
            self._tw_done += 1
            if self._tw_done == 2:
                QtCore.QTimer.singleShot(self.cfg.after_delay_ms, lambda: self._show_decoded(a_em, b_em, cb))

        self._tw_a.finished.connect(_on_one_finished)
        self._tw_b.finished.connect(_on_one_finished)

        self._tw_a.start()
        self._tw_b.start()
        self.status.setText("Demo running…")

    def _show_decoded(self, a_em: str, b_em: str, cb: Codebook):
        try:
            a_plain = em_decode(a_em, cb)
            b_plain = em_decode(b_em, cb)
        except Exception as e:
            self.status.setText(f"Decode error: {e}")
            return
        self.A_dec.setPlainText(a_plain)
        self.B_dec.setPlainText(b_plain)
        self.status.setText("Demo complete.")

# -----------------------------
# Main window with tabs
# -----------------------------
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EmerLang GUI")
        self.resize(1000, 700)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(BuildTab(), "Build")
        tabs.addTab(EncodeTab(), "Encode")
        tabs.addTab(DecodeTab(), "Decode")
        tabs.addTab(DemoTab(), "Demo")

        self.setCentralWidget(tabs)
        self._apply_dark_palette_if_supported()

    def _apply_dark_palette_if_supported(self):
        # simple dark mode hint; you can swap in qdarktheme if you like
        if QtWidgets.QApplication.palette().color(QtGui.QPalette.Window).lightness() > 128:
            return  # already light; skip
        # Keep system theme; consider integrating qdarktheme for more polish.

def main():
    app = QtWidgets.QApplication([])
    w = MainWindow()
    w.show()
    app.exec()

if __name__ == "__main__":
    main()
