# Tempos de nascimento e respawn (em segundos)
DRAGON_RESPAWN = 300  # 5 min (300s)
BARON_RESPAWN = 360  # 6 min (360s)

# 👾 LARVAS: Nascem aos 08:00 (480s)
LARVAE_SPAWN_TIME = 480
LARVAE_RESPAWN = 240  # 4 min entre ninhadas (240s)

# ⚔️ ARAUTO: Nasce aos 15:00 (900s)
HERALD_SPAWN_TIME = 900

# 👁️ BARÃO: Nasce aos 20:00 (1200s)
BARON_SPAWN_TIME = 1200


class ObjectivesTracker:

    def __init__(self):
        self.triggered_alerts = set()
        self.last_dragon_kill = 0
        self.last_baron_kill = 0
        self.larvae_cleared_time = 0

    def check_objectives(self, game_data):
        if not game_data:
            return []

        try:
            game_time = float(game_data.get("gameData", {}).get("gameTime", 0))
        except (ValueError, TypeError):
            game_time = 0

        events = game_data.get("events", {}).get("Events", [])
        alerts = []

        # 1. Atualiza histórico de abates via eventos do jogo
        for event in events:
            event_name = event.get("EventName", "")
            event_time = float(event.get("EventTime", 0))

            if (
                event_name == "DragonKill"
                and event_time > self.last_dragon_kill
            ):
                self.last_dragon_kill = event_time
                self._clear_alerts_with_prefix("dragon_respawn")

            elif (
                event_name == "BaronKill" and event_time > self.last_baron_kill
            ):
                self.last_baron_kill = event_time
                self._clear_alerts_with_prefix("baron_respawn")

            # Detecta quando o acampamento do Vazio/Horde é limpo
            elif event_name in [
                "HordeKill",
                "HordeDragonKill",
            ] and event_time > (self.larvae_cleared_time + 10):
                self.larvae_cleared_time = event_time
                self._clear_alerts_with_prefix("larvae_respawn")

        # ----------------------------------------------------
        # 🐉 2. DRAGÃO (Nascimento aos 05:00 ou Respawns)
        # ----------------------------------------------------
        if self.last_dragon_kill == 0:
            time_to_spawn = 300 - game_time
            if (
                0 < time_to_spawn <= 30
                and "dragon_first" not in self.triggered_alerts
            ):
                self.triggered_alerts.add("dragon_first")
                alerts.append(("dragon", " Dragão nasce em 30s!"))
        else:
            respawn_time = self.last_dragon_kill + DRAGON_RESPAWN
            time_to_spawn = respawn_time - game_time
            alert_key = f"dragon_respawn_{self.last_dragon_kill}"
            if (
                0 < time_to_spawn <= 30
                and alert_key not in self.triggered_alerts
            ):
                self.triggered_alerts.add(alert_key)
                alerts.append(("dragon", " Dragão nasce em 30s!"))

        # ----------------------------------------------------
        # 👾 3. LARVAS DO VAZIO (1ª ninhada aos 05:00 | 2ª aos +4 min)
        # ----------------------------------------------------
        if game_time < 825:  # Só monitora se for antes das 13:45
            if self.larvae_cleared_time == 0:
                # Primeira aparição (Avisa aos 04:30)
                time_to_larvae = LARVAE_SPAWN_TIME - game_time
                if (
                    0 < time_to_larvae <= 30
                    and "larvae_first" not in self.triggered_alerts
                ):
                    self.triggered_alerts.add("larvae_first")
                    alerts.append(("larvae", " Larvas do Vazio em 30s!"))
            else:
                # Segunda aparição (+4 min após a primeira ser limpa)
                respawn_time = self.larvae_cleared_time + LARVAE_RESPAWN
                time_to_larvae = respawn_time - game_time
                alert_key = f"larvae_respawn_{self.larvae_cleared_time}"
                if (
                    0 < time_to_larvae <= 30
                    and alert_key not in self.triggered_alerts
                ):
                    self.triggered_alerts.add(alert_key)
                    alerts.append(("larvae", " Larvas do Vazio em 30s!"))

        # ----------------------------------------------------
        # ⚔️ 4. ARAUTO DO VALE (Nascimento aos 14:00 = 840s)
        # ----------------------------------------------------
        time_to_herald = HERALD_SPAWN_TIME - game_time
        if (
            0 < time_to_herald <= 30
            and "herald_spawn" not in self.triggered_alerts
        ):
            self.triggered_alerts.add("herald_spawn")
            alerts.append(("herald", " Arauto do Vale em 30s!"))

        # ----------------------------------------------------
        # 👁️ 5. BARÃO (Nascimento aos 20:00 = 1200s ou Respawns)
        # ----------------------------------------------------
        if self.last_baron_kill == 0:
            time_to_baron = BARON_SPAWN_TIME - game_time
            if (
                0 < time_to_baron <= 30
                and "baron_first" not in self.triggered_alerts
            ):
                self.triggered_alerts.add("baron_first")
                alerts.append(("baron", "Barão nasce em 30s!"))
        else:
            respawn_time = self.last_baron_kill + BARON_RESPAWN
            time_to_spawn = respawn_time - game_time
            alert_key = f"baron_respawn_{self.last_baron_kill}"
            if (
                0 < time_to_spawn <= 30
                and alert_key not in self.triggered_alerts
            ):
                self.triggered_alerts.add(alert_key)
                alerts.append(("baron", " Barão nasce em 30s!"))

        return alerts

    def _clear_alerts_with_prefix(self, prefix):
        self.triggered_alerts = {
            k for k in self.triggered_alerts if not k.startswith(prefix)
        }