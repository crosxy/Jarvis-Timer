from core.spells import parse_spell_data

# Rotas padrão na ordem do lobby caso a API venha vazia
DEFAULT_ROLES = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]

# Estilos e Badges dos Elos (Fundo, Cor do Texto e Borda)
RANK_BADGES = {
    "IRON": {"text": "I", "color": "#A0A0A0", "bg": "#2A2B30", "border": "#51484A"},
    "BRONZE": {"text": "B", "color": "#E58E62", "bg": "#3B261D", "border": "#8C523A"},
    "SILVER": {"text": "S", "color": "#D1E0E5", "bg": "#2D353B", "border": "#8098A0"},
    "GOLD": {"text": "G", "color": "#FFD700", "bg": "#3B321D", "border": "#CD8832"},
    "PLATINUM": {"text": "P", "color": "#00E5FF", "bg": "#1D373B", "border": "#4E9996"},
    "EMERALD": {"text": "E", "color": "#00FF66", "bg": "#1D3B26", "border": "#239D60"},
    "DIAMOND": {"text": "D", "color": "#B8B8FF", "bg": "#28263B", "border": "#576BCE"},
    "MASTER": {"text": "M", "color": "#FF80FF", "bg": "#3B1D38", "border": "#9D42C7"},
    "GRANDMASTER": {"text": "GM", "color": "#FF5555", "bg": "#3B1D1D", "border": "#C83232"},
    "CHALLENGER": {"text": "C", "color": "#FFF099", "bg": "#3B351D", "border": "#F4C875"},
    "UNRANKED": {"text": "-", "color": "#888888", "bg": "#1E1E1E", "border": "#3A3D4D"},
}


def sanitize_champion_name(name: str) -> str:
    """Ajusta exceções e remove caracteres especiais dos nomes dos campeões para buscar a imagem correta no DataDragon."""
    if not name:
        return ""

    exceptions = {
        "wukong": "MonkeyKing",
        "renata glasc": "Renata",
        "nunu & willump": "Nunu",
    }

    clean = name.strip()
    if clean.lower() in exceptions:
        return exceptions[clean.lower()]

    # Remove aspas simples, pontos e espaços (ex: Cho'Gath -> Chogath, Kai'Sa -> Kaisa)
    clean = (
        clean.replace("'", "")
        .replace("’", "")
        .replace(".", "")
        .replace(" ", "")
    )

    return clean.capitalize()


def get_enemy_spells(enemy):
    if not enemy or "summonerSpells" not in enemy:
        return ("SummonerFlash", 300), ("SummonerDot", 180)

    spells_data = enemy.get("summonerSpells", {})

    s1_obj = spells_data.get("summonerSpellOne", {})
    s2_obj = spells_data.get("summonerSpellTwo", {})

    s1_name, s1_cd = parse_spell_data(s1_obj)
    s2_name, s2_cd = parse_spell_data(s2_obj)

    return (s1_name, s1_cd), (s2_name, s2_cd)


def get_enemy_players(data):
    if not data or "allPlayers" not in data:
        return []

    active_player = data.get("activePlayer", {}).get("summonerName", "")
    local_team = None

    for player in data.get("allPlayers", []):
        if player.get("summonerName") == active_player:
            local_team = player.get("team")
            break

    enemies = []
    idx = 0
    for player in data.get("allPlayers", []):
        if local_team and player.get("team") == local_team:
            continue

        (s1_name, s1_cd), (s2_name, s2_cd) = get_enemy_spells(player)

        # Se a API não preencher a position, usa a rota padrão da ordem
        raw_position = player.get("position", "").upper()
        if not raw_position and idx < len(DEFAULT_ROLES):
            raw_position = DEFAULT_ROLES[idx]

        # Nome do campeão sanitizado para carregar a imagem perfeita
        raw_champ_name = player.get("championName", "Unknown")
        clean_champ_name = sanitize_champion_name(raw_champ_name)

        enemies.append(
            {
                "puuid": player.get("puuid", ""),
                "summonerName": player.get("summonerName", ""),
                "riotIdGameName": player.get("riotIdGameName", ""),
                "riotIdTagline": player.get("riotIdTagline", ""),
                "championName": clean_champ_name,
                "level": player.get("level", 1),
                "position": raw_position,
                "spell1": s1_name,
                "spell1_cd": s1_cd,
                "spell2": s2_name,
                "spell2_cd": s2_cd,
                "isDead": player.get("isDead", False),
                "respawnTimer": player.get("respawnTimer", 0),
                # Campos de Rank (Podem ser preenchidos pela LCU API/Riot API)
                "tier": player.get("tier", "UNRANKED"),
                "division": player.get("division", ""),
            }
        )
        idx += 1

    return enemies


def update_rank_badge_widget(badge_label, rank_tier: str = "UNRANKED", division: str = ""):
    """
    Atualiza uma QLabel com o formato de Badge elegante (Ex: S1, B4, E2).
    """
    tier = str(rank_tier).upper()
    style = RANK_BADGES.get(tier, RANK_BADGES["UNRANKED"])

    div_map = {"I": "1", "II": "2", "III": "3", "IV": "4", "1": "1", "2": "2", "3": "3", "4": "4"}
    div_num = div_map.get(str(division).upper(), "")

    label_text = f"{style['text']}{div_num}" if style["text"] != "-" else "-"

    badge_label.setText(label_text)
    badge_label.setStyleSheet(f"""
        QLabel {{
            background-color: {style['bg']};
            color: {style['color']};
            font-size: 9px;
            font-weight: bold;
            border: 1px solid {style['border']};
            border-radius: 3px;
            padding: 1px 3px;
        }}
    """)