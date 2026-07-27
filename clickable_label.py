from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel


class ClickableLabel(QLabel):

    spell_ready = Signal(str)  # emite o nome do spell quando o cooldown termina sozinho

    def __init__(self, spell_name, total_cooldown):
        super().__init__()
        self.spell_name = spell_name
        self.total_cooldown = total_cooldown
        self.remaining = 0
        self.is_flashing = False

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_timer)

        self.setScaledContents(True)
        self.setFixedSize(32, 32)
        self.setAlignment(Qt.AlignCenter)

    def set_spell_info(self, name, icon_path, cooldown):
        self.spell_name = name
        self.total_cooldown = cooldown
        if self.remaining <= 0 and icon_path:
            self.setPixmap(QPixmap(icon_path))

    def reset_spell(self):
        """Para qualquer timer ativo e reseta o feitiço imediatamente."""
        self.reset_cooldown(natural=False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
         if self.remaining <= 0:
           self.start_cooldown()
        else:
           self.reset_cooldown()

    # 🎯 Libera o foco imediatamente após o clique para não travar o mouse no mapa
           self.clearFocus()
        if self.window():
           self.window().clearFocus()

    def start_cooldown(self):
        self.remaining = self.total_cooldown
        self.setText(self.format_time(self.remaining))
        self.setStyleSheet("""
            border: 2px solid #C8AA6E;
            border-radius: 4px;
            background-color: #0A0E14;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 10px;
        """)
        self.timer.start()

    def reset_cooldown(self, natural=False):
        self.timer.stop()
        self.remaining = 0
        self.is_flashing = False
        self.setText("")
        # Restaura a imagem original
        from core.assets import get_spell_icon

        path = get_spell_icon(self.spell_name)
        if path:
            self.setPixmap(QPixmap(path))
        self.setStyleSheet(
            "border: 1px solid #333; border-radius: 4px; background-color: #111;"
        )

        if natural:
            self.spell_ready.emit(self.spell_name)

    def update_timer(self):
        self.remaining -= 1

        if self.remaining > 0:
            self.setText(self.format_time(self.remaining))

            # 🚨 AVISO PRÉVIO: Faltam exatamente 10 segundos!
            if self.remaining == 10:
                self.spell_ready.emit(self.spell_name)

            # 🚨 Pisca nos últimos 10 segundos
            if self.remaining <= 10:
                self.is_flashing = not self.is_flashing
                if self.is_flashing:
                    self.setStyleSheet("""
                        border: 2px solid #FF3333;
                        background-color: #550000;
                        color: #FFD700;
                        font-weight: bold;
                        font-size: 11px;
                    """)
                else:
                    self.setStyleSheet("""
                        border: 2px solid #FFD700;
                        background-color: #111;
                        color: #FFFFFF;
                        font-weight: bold;
                        font-size: 10px;
                    """)
        else:
            self.reset_cooldown(natural=False)

    def format_time(self, seconds):
        m = seconds // 60
        s = seconds % 60
        return f"{m}:{s:02d}" if m > 0 else f"{s}s"