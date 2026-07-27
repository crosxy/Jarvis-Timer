import os
import sys
from core.assets import get_champion_icon
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QWidget

CHAMPION_FIXES = {
    "Nunu & Willump": "Nunu",
    "NunuWillump": "Nunu",
    "Wukong": "MonkeyKing",
    "Renata Glasc": "Renata",
    "K'Sante": "KSante",
}

SPELL_DISPLAY_NAMES = {
    "SummonerFlash": "Flash",
    "SummonerDot": "Ignite",
    "SummonerHeal": "Cura",
    "SummonerBarrier": "Barreira",
    "SummonerExhaust": "Enfraquecer",
    "SummonerTeleport": "Teleporte",
    "SummonerSmite": "Smite",
    "SummonerCleanse": "Purificar",
    "SummonerHaste": "Fantasma",
    "SummonerBoost": "Fantasma",
}


def friendly_spell_name(spell_name: str) -> str:
    return SPELL_DISPLAY_NAMES.get(
        spell_name, str(spell_name).replace("Summoner", "")
    )


def get_assets_dir():
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    assets_path = os.path.join(base_dir, "assets")
    if not os.path.exists(assets_path):
        assets_path = os.path.join(os.path.dirname(base_dir), "assets")

    return assets_path


def crop_transparent_borders(pixmap: QPixmap) -> QPixmap:
    image = pixmap.toImage()
    width, height = image.width(), image.height()

    min_x, min_y = width, height
    max_x, max_y = 0, 0

    for y in range(height):
        for x in range(width):
            if image.pixelColor(x, y).alpha() > 10:
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y

    if min_x <= max_x and min_y <= max_y:
        return QPixmap.fromImage(
            image.copy(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
        )

    return pixmap


def make_circular_pixmap(pixmap: QPixmap, size: int) -> QPixmap:
    scaled = pixmap.scaled(
        size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
    )

    out_pixmap = QPixmap(size, size)
    out_pixmap.fill(Qt.transparent)

    painter = QPainter(out_pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)

    x = (size - scaled.width()) / 2
    y = (size - scaled.height()) / 2
    painter.drawPixmap(int(x), int(y), scaled)

    painter.setClipping(False)

    pen_glow = QPen(QColor("#C8AA6E"), 1.2)
    painter.setPen(pen_glow)
    painter.drawEllipse(1, 1, size - 2, size - 2)

    pen_border = QPen(QColor("#785A28"), 1.0)
    painter.setPen(pen_border)
    painter.drawEllipse(2, 2, size - 4, size - 4)

    painter.end()
    return out_pixmap


class Toast(QWidget):
    DURATION_MS = 4000

    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Wrapper principal sem restrição de layout flexível
        self.wrapper = QWidget(self)

        # 💬 1. BALÃO DO TEXTO (32px de altura)
        self.container = QWidget(self.wrapper)
        self.container.setFixedHeight(32)
        self.container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(6, 10, 15, 245), stop:1 rgba(15, 23, 30, 245));
                border: 1.5px solid #C8AA6E;
                border-radius: 4px;
            }
        """)

        container_layout = QHBoxLayout(self.container)
        container_layout.setContentsMargins(12, 0, 32, 0)
        container_layout.setAlignment(Qt.AlignVCenter)

        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.label.setStyleSheet("""
            QLabel {
                font-family: 'UttumDotum', 'Segoe UI', sans-serif;
                color: #FFD700;
                font-size: 13px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)
        container_layout.addWidget(self.label)

        # 🖼️ 2. FOTO GRANDE (48px)
        self.champ_icon = QLabel(self.wrapper)
        self.champ_icon.setFixedSize(48, 48)
        self.champ_icon.setAlignment(Qt.AlignCenter)
        self.champ_icon.setStyleSheet("background: transparent; border: none;")

        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.addWidget(self.wrapper)

        self._queue = []
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._show_next)

        self.hide()

    def show_message(self, target_name: str, text: str):
        self._queue.append((target_name, text))
        if not self.isVisible():
            self._show_next()

    def _show_next(self):
        if not self._queue:
            self.hide()
            return

        target_name, text = self._queue.pop(0)
        icon_path = None

        assets_dir = get_assets_dir()
        obj_paths = {
            "dragon": os.path.join(assets_dir, "dragon.png"),
            "baron": os.path.join(assets_dir, "baron.png"),
            "herald": os.path.join(assets_dir, "herald.png"),
            "larvae": os.path.join(assets_dir, "larvae.png"),
        }

        if target_name in obj_paths and os.path.exists(obj_paths[target_name]):
            icon_path = obj_paths[target_name]
        elif target_name:
            sanitized_name = CHAMPION_FIXES.get(target_name, target_name)
            icon_path = get_champion_icon(sanitized_name)

        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                if target_name in obj_paths:
                    pixmap = crop_transparent_borders(pixmap)

                circular_pixmap = make_circular_pixmap(pixmap, 48)
                self.champ_icon.setPixmap(circular_pixmap)
                self.champ_icon.show()
            else:
                self.champ_icon.hide()
        else:
            self.champ_icon.hide()

        self.label.setText(text)
        self.label.adjustSize()
        self.container.adjustSize()

        # 📐 POSICIONAMENTO MANUAL
        container_w = self.container.width()

        # Balão centralizado na altura de 48px (y = 8)
        self.container.move(0, 8)

        # Foto sobrepõe a ponta direita do balão em 24px (metade da foto de 48px)
        icon_x = container_w - 24
        self.champ_icon.move(icon_x, 0)

        # Redimensiona explicitamente o tamanho total da janela
        total_w = icon_x + 48
        self.wrapper.setFixedSize(total_w, 48)
        self.setFixedSize(total_w, 48)

        # Garante que a foto sobressaia no topo
        self.champ_icon.raise_()

        # RECALCULA A POSIÇÃO NA TELA COM O TAMANHO NOVO DA JANELA!
        self._position_on_screen()

        self.show()
        self.raise_()
        self._hide_timer.start(self.DURATION_MS)

    def _position_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        # Coloca a 20px da borda direita considerando a LARGURA TOTAL atualizada
        x = screen.width() - self.width() - 10
        y = 400
        self.move(x, y)