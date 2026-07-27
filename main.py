import os
import sys

from core.players import get_enemy_players
from overlay import Overlay
import pygetwindow as gw
from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
LIVE_CLIENT_URL = "https://127.0.0.1:2999/liveclientdata/allgamedata"


def get_assets_dir():
    """Retorna o caminho correto da pasta assets para dev e PyInstaller."""
    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets")


def load_custom_fonts(assets_dir):
    """Carrega automaticamente todas as fontes (.otf / .ttf) da pasta assets/fonts/."""
    fonts_dir = os.path.join(assets_dir, "fonts")
    
    if not os.path.exists(fonts_dir):
        return

    for font_file in os.listdir(fonts_dir):
        if font_file.lower().endswith((".otf", ".ttf")):
            font_path = os.path.join(fonts_dir, font_file)
            QFontDatabase.addApplicationFont(font_path)


def fetch_lol_game_data():
    try:
        res = requests.get(LIVE_CLIENT_URL, verify=False, timeout=1)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None


def should_be_visible(overlay_widget):
    """Retorna True se o jogo estiver focado OU se o mouse/clique estiver interagindo com o overlay"""
    try:
        if (
            overlay_widget.underMouse()
            or overlay_widget._drag_pos is not None
            or overlay_widget.isActiveWindow()
        ):
            return True

        active_win = gw.getActiveWindow()
        if active_win and active_win.title:
            title = active_win.title.lower()
            return "league of legends (tm) client" in title
    except Exception:
        pass
    return False


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Mantém o app vivo na bandeja!

    assets_dir = get_assets_dir()

    # 🎨 0. CARREGA AS FONTES CUSTOMIZADAS DA PASTA assets/fonts/
    load_custom_fonts(assets_dir)

    # 📌 1. CARREGA O ÍCONE DA BANDEJA PRIMEIRO
    icon_path = os.path.join(assets_dir, "icon.ico")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(assets_dir, "icon.png")

    tray_icon = QSystemTrayIcon(app)

    if os.path.exists(icon_path):
        tray_icon.setIcon(QIcon(icon_path))
    else:
        tray_icon.setIcon(app.style().standardIcon(QStyle.SP_ComputerIcon))

    tray_icon.setToolTip("JarvisTimer - LoL Overlay")

    # 📋 2. CRIA O MENU DO BOTÃO DIREITO
    tray_menu = QMenu()

    toggle_action = QAction("Mostrar / Ocultar Overlay", app)
    tray_menu.addAction(toggle_action)

    tray_menu.addSeparator()

    quit_action = QAction("Sair do JarvisTimer", app)
    quit_action.triggered.connect(app.quit)
    tray_menu.addAction(quit_action)

    tray_icon.setContextMenu(tray_menu)
    tray_icon.show()  # Exibe o ícone na bandeja imediatamente!

    # 📌 3. INICIALIZA O OVERLAY
    overlay = Overlay()

    # Conecta a ação de clique do menu com a janela do overlay
    toggle_action.triggered.connect(
        lambda: overlay.hide() if overlay.isVisible() else overlay.show()
    )

    # 🔄 4. LOOP DE ATUALIZAÇÃO
    def update():
        data = fetch_lol_game_data()

        # 🎮 SE O JOGO ESTIVER EM EXECUÇÃO E FOCADO
        if data and should_be_visible(overlay):
            if not overlay.isVisible():
                overlay.show()

            enemies = get_enemy_players(data)
            overlay.update_players(enemies)
            overlay.check_objectives_alerts(data)

        # 🛑 SE O JOGO FECHOU OU NÃO ESTÁ EM FOCO
        else:
            if overlay.isVisible():
                overlay.hide()

            # 🧹 Se a API do LoL parou de responder (partida acabou/cliente fechou)
            if not data:
                if hasattr(overlay, "clear_all_timers"):
                    overlay.clear_all_timers()

    timer = QTimer()
    timer.timeout.connect(update)
    timer.start(600)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()