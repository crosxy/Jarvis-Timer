import os
import requests
import sys

# 🗺️ Mapeamentos de nomes que a Riot altera no DataDragon ou exceções de formatação
SPECIAL_CHAMPIONS = {
    "Wukong": "MonkeyKing",
    "wukong": "MonkeyKing",
    "Nunu & Willump": "Nunu",
    "nunu": "Nunu",
    "Renata Glasc": "Renata",
    "renataglasc": "Renata",
    "Master Yi": "MasterYi",
    "masteryi": "MasterYi",
    "Tahm Kench": "TahmKench",
    "tahmkench": "TahmKench",
    "Dr. Mundo": "DrMundo",
    "DrMundo": "DrMundo",
    "drmundo": "DrMundo",
    "Dr Mundo": "DrMundo",
    "KSante": "KSante",
    "K'Sante": "KSante",
    "ksante": "KSante",
    "Cho'Gath": "Chogath",
    "chogath": "Chogath",
    "Kai'Sa": "Kaisa",
    "kaisa": "Kaisa",
    "Kha'Zix": "Khazix",
    "khazix": "Khazix",
    "Vel'Koz": "Velkoz",
    "velkoz": "Velkoz",
    "Bel'Veth": "Belveth",
    "belveth": "Belveth",
    "LeBlanc": "Leblanc",
    "leblanc": "Leblanc",
    "Nunu & Willump": "Nunu",
    "NunuWillump": "Nunu",
}

# 🗺️ Mapeamento de sinônimos de rotas/lanes da API do LoL
POSITION_MAP = {
    "TOP": "TOP",
    "JUNGLE": "JUNGLE",
    "JUG": "JUNGLE",
    "MIDDLE": "MIDDLE",
    "MID": "MIDDLE",
    "BOTTOM": "BOTTOM",
    "BOT": "BOTTOM",
    "UTILITY": "UTILITY",
    "SUPP": "UTILITY",
    "SUPPORT": "UTILITY",
}

# 🌐 URLs oficiais dos ícones das rotas em SVG (CommunityDragon)
LANE_URLS = {
    "TOP": (
        "https://raw.githubusercontent.com/RiotGames/developer-relations/main/cdragon/lane-icons/top.svg"
    ),
    "JUNGLE": (
        "https://raw.githubusercontent.com/RiotGames/developer-relations/main/cdragon/lane-icons/jungle.svg"
    ),
    "MIDDLE": (
        "https://raw.githubusercontent.com/RiotGames/developer-relations/main/cdragon/lane-icons/mid.svg"
    ),
    "BOTTOM": (
        "https://raw.githubusercontent.com/RiotGames/developer-relations/main/cdragon/lane-icons/bot.svg"
    ),
    "UTILITY": (
        "https://raw.githubusercontent.com/RiotGames/developer-relations/main/cdragon/lane-icons/support.svg"
    ),
}

# 🔍 Detecta se está rodando via .exe do PyInstaller ou script .py puro
if getattr(sys, "frozen", False):
  BASE_DIR = sys._MEIPASS
else:
  BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
CHAMPS_DIR = os.path.join(ASSETS_DIR, "champions")
SPELLS_DIR = os.path.join(ASSETS_DIR, "spells")
LANES_DIR = os.path.join(ASSETS_DIR, "lanes")

os.makedirs(CHAMPS_DIR, exist_ok=True)
os.makedirs(SPELLS_DIR, exist_ok=True)
os.makedirs(LANES_DIR, exist_ok=True)


def get_latest_ddragon_version() -> str:
  """Busca a versão mais recente do DataDragon da Riot."""
  try:
    res = requests.get(
        "https://ddragon.leagueoflegends.com/api/versions.json", timeout=2
    )
    if res.status_code == 200:
      return res.json()[0]
  except Exception:
    pass
  return "14.10.1"


DDRAGON_VERSION = get_latest_ddragon_version()


def format_champion_name(champion_name: str) -> str:
  """Trata o nome do campeão para bater com os arquivos da Riot e DataDragon."""
  if not champion_name:
    return ""

  raw_name = str(champion_name).strip()

  # 1. Checa se o nome bruto está na tabela de exceções
  if raw_name in SPECIAL_CHAMPIONS:
    return SPECIAL_CHAMPIONS[raw_name]

  # 2. Checa versão em minúsculas sem espaços na tabela
  clean_key = (
      raw_name.lower().replace(" ", "").replace("'", "").replace(".", "")
  )
  if clean_key in SPECIAL_CHAMPIONS:
    return SPECIAL_CHAMPIONS[clean_key]

  # 3. Capitalização padrão para os outros campeões (ex: "lux" -> "Lux")
  clean_name = (
      raw_name.replace(" ", "")
      .replace("'", "")
      .replace(".", "")
      .replace("-", "")
  )

  return clean_name.capitalize()


def get_champion_icon(champion_name: str) -> str:
  """Garante que a imagem do campeão existe localmente e retorna o caminho."""
  if not champion_name:
    return ""

  clean_name = format_champion_name(champion_name)
  file_path = os.path.join(CHAMPS_DIR, f"{clean_name}.png")

  # 1. Checagem direta de arquivo
  if os.path.exists(file_path):
    return file_path

  # 2. Busca case-insensitive na pasta (ex: acha "DrMundo.png" mesmo procurando "drmundo")
  if os.path.exists(CHAMPS_DIR):
    for file in os.listdir(CHAMPS_DIR):
      if file.lower() == f"{clean_name.lower()}.png":
        return os.path.join(CHAMPS_DIR, file)

  # 3. Tenta baixar do DataDragon oficial da Riot caso não exista localmente
  url = f"https://ddragon.leagueoflegends.com/cdn/{DDRAGON_VERSION}/img/champion/{clean_name}.png"
  try:
    res = requests.get(url, timeout=3)
    if res.status_code == 200:
      with open(file_path, "wb") as f:
        f.write(res.content)
      return file_path
  except Exception:
    pass

  return ""


def get_spell_icon(spell_name: str) -> str:
  """Garante que a imagem do feitiço existe localmente e retorna o caminho."""
  if not spell_name:
    return ""

  file_path = os.path.join(SPELLS_DIR, f"{spell_name}.png")

  if os.path.exists(file_path):
    return file_path

  # Busca case-insensitive na pasta de spells
  if os.path.exists(SPELLS_DIR):
    for file in os.listdir(SPELLS_DIR):
      if file.lower() == f"{spell_name.lower()}.png":
        return os.path.join(SPELLS_DIR, file)

  url = f"https://ddragon.leagueoflegends.com/cdn/{DDRAGON_VERSION}/img/spell/{spell_name}.png"
  try:
    res = requests.get(url, timeout=3)
    if res.status_code == 200:
      with open(file_path, "wb") as f:
        f.write(res.content)
      return file_path
  except Exception:
    pass

  return ""


def get_lane_icon(position: str) -> str:
  """Garante que o ícone em SVG da rota existe e retorna o caminho .svg!"""
  if not position:
    return ""

  raw_pos = position.upper().strip()
  pos = POSITION_MAP.get(raw_pos, raw_pos)

  if pos not in LANE_URLS:
    return ""

  file_path = os.path.join(LANES_DIR, f"{pos}.svg")

  if os.path.exists(file_path):
    return file_path

  try:
    res = requests.get(LANE_URLS[pos], timeout=3)
    if res.status_code == 200:
      with open(file_path, "wb") as f:
        f.write(res.content)
      return file_path
  except Exception:
    pass

  return ""