SPELLS = {
    # Mapeamento por ID (Caso venha o ID numérico da API)
    1: {"name": "SummonerBoost", "title": "Cleanse", "cooldown": 210},
    3: {"name": "SummonerExhaust", "title": "Exhaust", "cooldown": 210},
    4: {"name": "SummonerFlash", "title": "Flash", "cooldown": 300},
    6: {"name": "SummonerHaste", "title": "Ghost", "cooldown": 210},
    7: {"name": "SummonerHeal", "title": "Heal", "cooldown": 240},
    11: {"name": "SummonerSmite", "title": "Smite", "cooldown": 15},
    12: {"name": "SummonerTeleport", "title": "Teleport", "cooldown": 360},
    13: {"name": "SummonerMana", "title": "Clarity", "cooldown": 240},
    14: {"name": "SummonerDot", "title": "Ignite", "cooldown": 180},
    21: {"name": "SummonerBarrier", "title": "Barrier", "cooldown": 180},
    32: {"name": "SummonerSnowball", "title": "Mark", "cooldown": 80},
    
    # Mapeamento direto por nome interno do DataDragon/Riot API
    "SummonerFlash": {"name": "SummonerFlash", "title": "Flash", "cooldown": 300},
    "SummonerDot": {"name": "SummonerDot", "title": "Ignite", "cooldown": 180},
    "SummonerTeleport": {"name": "SummonerTeleport", "title": "Teleport", "cooldown": 360},
    "SummonerExhaust": {"name": "SummonerExhaust", "title": "Exhaust", "cooldown": 210},
    "SummonerHeal": {"name": "SummonerHeal", "title": "Heal", "cooldown": 240},
    "SummonerBarrier": {"name": "SummonerBarrier", "title": "Barrier", "cooldown": 180},
    "SummonerHaste": {"name": "SummonerHaste", "title": "Ghost", "cooldown": 210},
    "SummonerBoost": {"name": "SummonerBoost", "title": "Cleanse", "cooldown": 210},
    "SummonerSmite": {"name": "SummonerSmite", "title": "Smite", "cooldown": 15},
}


def parse_spell_data(spell_obj):
    """Extrai a chave correta para o DataDragon e o cooldown de um objeto de feitiço"""
    if not spell_obj:
        return "SummonerFlash", 300

    raw_name = spell_obj.get("rawDescriptionName", "") or spell_obj.get("rawDisplayName", "")
    
    # Exemplo de rawDescriptionName: "GeneratedTip_Summoner_SummonerFlash_DisplayName"
    cleaned_key = "SummonerFlash"
    for known_key in SPELLS.keys():
        if isinstance(known_key, str) and known_key in raw_name:
            cleaned_key = known_key
            break

    spell_info = SPELLS.get(cleaned_key, {"name": "SummonerFlash", "cooldown": 300})
    return spell_info["name"], spell_info["cooldown"]