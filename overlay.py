import json
import os
from core.objectives_tracker import ObjectivesTracker
from player_card import PlayerCard
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QVBoxLayout,
    QWidget,
)
from toast import Toast, friendly_spell_name

CONFIG_FILE = "config.json"


class Overlay(QWidget):

  def __init__(self):
    super().__init__()

    self.setMinimumWidth(210)
    self.is_locked = True

    # 🔒 Flags de Janela: Mantém no topo, sem borda do Windows, aceita interações
    self.setWindowFlags(
        Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
    )
    self.setAttribute(Qt.WA_TranslucentBackground)

    # ⌨️ Atalho do Teclado: CTRL + L para Travar / Destravar movimentação
    self.shortcut_lock = QShortcut(QKeySequence("Ctrl+L"), self)
    self.shortcut_lock.activated.connect(self.toggle_lock)

    # Container Principal
    self.container = QFrame(self)
    self.apply_lock_style()

    container_layout = QVBoxLayout(self.container)
    container_layout.setContentsMargins(4, 4, 4, 4)
    container_layout.setSpacing(2)

    # Toast e Trackers
    self.toast = Toast()
    self.obj_tracker = ObjectivesTracker()

    self.players = []
    for i in range(5):
      card = PlayerCard()
      card.spell_ready.connect(self._on_spell_ready)
      self.players.append(card)
      container_layout.addWidget(card)

    main_layout = QVBoxLayout(self)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.addWidget(self.container)

    self._drag_pos = None
    self.load_config()

  def check_objectives_alerts(self, game_data):
    """Dispara pop-ups para avisos prévios de objetivos (Dragão, Barão, etc)."""
    if not game_data:
      return

    # 🛑 REGRA DAS VASTILARVAS: Se o tempo de jogo passar de 13min40s (820s), desativa qualquer alerta de larvas
    game_time = game_data.get("gameData", {}).get("gameTime", 0)

    alerts = self.obj_tracker.check_objectives(game_data)
    for obj_icon, message in alerts:
      # Ignora o aviso de larvas se o jogo já passou do tempo do Arauto (~14 min)
      if "larva" in message.lower() and game_time > 820:
        continue

      self.toast.show_message(obj_icon, message)

  def toggle_lock(self):
    """Alterna a trava de movimentação (Arrastar Janela com Ctrl+L)."""
    self.is_locked = not self.is_locked
    self.apply_lock_style()

  def apply_lock_style(self):
    if self.is_locked:
      # Travado: Borda dourada padrão
# No __init__ do overlay.py:
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(9, 14, 21, 0.92);
                border: 2px solid #C8AA6E;
                border-radius: 4px;
            }
        """)
    else:
      # Destravado: Borda vermelha chamativa (Pronto para arrastar)
      self.container.setStyleSheet("""
                QFrame {
                    background-color: rgba(10, 14, 20, 240);
                    border: 2px solid #FF3333;
                    border-radius: 6px;
                }
            """)

  def load_config(self):
    if os.path.exists(CONFIG_FILE):
      try:
        with open(CONFIG_FILE, "r") as f:
          data = json.load(f)
          self.move(data.get("x", 100), data.get("y", 100))
          return
      except Exception:
        pass

    screen = QApplication.primaryScreen().geometry()
    x = screen.width() - self.width() - 15
    y = 120
    self.move(x, y)

  def save_config(self):
    try:
      pos = self.pos()
      with open(CONFIG_FILE, "w") as f:
        json.dump(
            {
                "x": pos.x(),
                "y": pos.y(),
            },
            f,
        )
    except Exception as e:
      print(f"Erro ao salvar configurações: {e}")

  def update_players(self, enemies):
    for card, player in zip(self.players, enemies):
      card.update_player(
          player["championName"],
          player["level"],
          player.get("position", ""),
          player.get("spell1", "SummonerFlash"),
          player.get("spell1_cd", 300),
          player.get("spell2", "SummonerDot"),
          player.get("spell2_cd", 180),
      )

  def _on_spell_ready(self, champion, spell_name):
    nice_spell = friendly_spell_name(spell_name)
    self.toast.show_message(champion, f" {nice_spell} em 10s!")

  def mousePressEvent(self, event):
    # Só permite arrastar a janela se estiver DESTRAVADO (Ctrl + L)
    if not self.is_locked and event.button() == Qt.LeftButton:
      self._drag_pos = (
          event.globalPosition().toPoint() - self.frameGeometry().topLeft()
      )
      event.accept()

  def mouseMoveEvent(self, event):
    if not self.is_locked and event.buttons() == Qt.LeftButton and self._drag_pos:
      self.move(event.globalPosition().toPoint() - self._drag_pos)
      event.accept()

  def mouseReleaseEvent(self, event):
    if not self.is_locked:
      self._drag_pos = None
      self.save_config()

  def clear_all_timers(self):
    """Reseta todos os feitiços e esconde avisos na tela quando o jogo acaba."""
    for card in self.players:
      if hasattr(card, "spell1"):
        card.spell1.reset_spell()
      if hasattr(card, "spell2"):
        card.spell2.reset_spell()

    if hasattr(self, "toast"):
      self.toast.hide()