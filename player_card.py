import os
import sys
from clickable_label import ClickableLabel
from core.assets import get_champion_icon, get_spell_icon
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

# Mapeamento apontando para os PNGs da pasta assets/lanes
LANE_FILES = {
    "TOP": "TOP.png",
    "JUNGLE": "JUNGLE.png",
    "JUG": "JUNGLE.png",
    "MIDDLE": "MIDDLE.png",
    "MID": "MIDDLE.png",
    "BOTTOM": "BOTTOM.png",
    "BOT": "BOTTOM.png",
    "UTILITY": "UTILITY.png",
    "SUPP": "UTILITY.png",
    "SUPPORT": "UTILITY.png",
}


def get_base_dir():
  """Garante o caminho absoluto correto para a pasta assets"""
  if getattr(sys, "frozen", False):
    return sys._MEIPASS
  current_file_dir = os.path.dirname(os.path.abspath(__file__))
  return os.path.dirname(current_file_dir)


class PlayerCard(QWidget):

  spell_ready = Signal(str, str)

  def __init__(self):
    super().__init__()

    self.setFixedHeight(38)

    # 🎨 ESTILO HEXTECH DO CARD INDIVIDUAL
    self.setStyleSheet("""
            QWidget {
                background: transparent;
                border-bottom: 1px solid rgba(200, 170, 110, 0.15);
            }
        """)

    root = QHBoxLayout(self)
    root.setContentsMargins(4, 2, 4, 2)
    root.setSpacing(6)
    root.setAlignment(Qt.AlignVCenter)

    # 1. FOTO DO CAMPEÃO (Moldura Dourada Hextech)
    self.champion_icon = QLabel()
    self.champion_icon.setFixedSize(30, 30)
    self.champion_icon.setStyleSheet("""
            QLabel {
                background: #000000;
                border: 1px solid #785A28;
                border-radius: 3px;
            }
        """)
    self.champion_icon.setScaledContents(True)
    root.addWidget(self.champion_icon)

    # 2. NOME + LEVEL (Fontes estilo HUD LoL)
    info = QVBoxLayout()
    info.setSpacing(0)
    info.setContentsMargins(0, 0, 0, 0)
    info.setAlignment(Qt.AlignVCenter)

    self.name = QLabel("Champion")
    self.name.setStyleSheet("""
            QLabel {
                font-family: 'UttumDotum', 'Segoe UI', sans-serif;
                font-size: 11px;
                font-weight: bold;
                color: #F0E6D2;
                background: transparent;
                border: none;
            }
        """)
    self.name.setFixedWidth(72)

    self.level = QLabel("Lv.1")
    self.level.setStyleSheet("""
            QLabel {
                font-family: 'UttumDotum', 'Segoe UI', sans-serif;
                color: #C8AA6E;
                font-size: 9px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
        """)

    info.addWidget(self.name)
    info.addWidget(self.level)
    root.addLayout(info)

    # 3. ÍCONE DA ROTA (PNG)
    self.lane_icon = QLabel()
    self.lane_icon.setFixedSize(18, 18)
    self.lane_icon.setAlignment(Qt.AlignCenter)
    self.lane_icon.setScaledContents(True)
    self.lane_icon.setStyleSheet("background: transparent; border: none;")
    root.addWidget(self.lane_icon)

    # 4. SPELLS (Estilo Métrica Hextech)
    self.spell1 = ClickableLabel("SummonerFlash", 300)
    self.spell2 = ClickableLabel("SummonerDot", 180)

    spell_style = """
            ClickableLabel {
                border: 1px solid #3C3C41;
                border-radius: 3px;
                background-color: #010A13;
            }
            ClickableLabel:hover {
                border: 1px solid #C8AA6E;
            }
        """

    self.spell1.setStyleSheet(spell_style)
    self.spell2.setStyleSheet(spell_style)

    root.addWidget(self.spell1)
    root.addWidget(self.spell2)

    self.spell1.spell_ready.connect(self._on_spell_ready)
    self.spell2.spell_ready.connect(self._on_spell_ready)

    self.current_champ = ""
    self.current_lane = ""

  def _on_spell_ready(self, spell_name):
    self.spell_ready.emit(self.current_champ, spell_name)

  def update_player(
      self,
      champion,
      level,
      position,
      spell1_name,
      spell1_cd,
      spell2_name,
      spell2_cd,
  ):
    # 🛡️ Texto seguro caso não venha nome
    display_name = str(champion).strip() if champion else "Champion"

    self.name.setText(display_name)
    self.level.setText(f"Lv.{level}")

    # 2. Atualiza foto do campeão
    self.current_champ = display_name
    champ_path = get_champion_icon(display_name)

    if champ_path and os.path.exists(champ_path):
      self.champion_icon.setPixmap(QPixmap(champ_path))
    else:
      alt_path = get_champion_icon(display_name.capitalize())
      if alt_path and os.path.exists(alt_path):
        self.champion_icon.setPixmap(QPixmap(alt_path))

    # 3. Atualiza ícone da Rota
    self.current_lane = position
    pos_key = str(position).upper().strip()

    if not pos_key or pos_key in ["NONE", "UNKNOWN", ""]:
      pos_key = "MIDDLE"

    file_name = LANE_FILES.get(pos_key, "MIDDLE.png")
    base_dir = get_base_dir()
    lane_path = os.path.join(base_dir, "assets", "lanes", file_name)

    if not os.path.exists(lane_path):
      lane_path = os.path.join("assets", "lanes", file_name)

    if os.path.exists(lane_path):
      self.lane_icon.setPixmap(QPixmap(lane_path))

    # 4. Atualiza Spells
    s1_path = get_spell_icon(spell1_name)
    s2_path = get_spell_icon(spell2_name)

    self.spell1.set_spell_info(spell1_name, s1_path, spell1_cd)
    self.spell2.set_spell_info(spell2_name, s2_path, spell2_cd)