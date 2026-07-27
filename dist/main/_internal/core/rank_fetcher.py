"""
rank_fetcher.py

Busca o elo (rank) dos jogadores na Riot API oficial, já que a Live Client
Data API (127.0.0.1:2999) NÃO expõe elo de ninguém.

IMPORTANTE: nessa versão do client, a Live Client API também não manda o
`puuid` dos jogadores (campo vazio). Por isso resolvemos o puuid a partir
do Riot ID (nome + tag, ex: "Fulano#BR1") usando o endpoint account-v1
ANTES de buscar o rank. Se um dia a Riot passar a mandar o puuid direto,
dá pra pular essa primeira chamada.

Fluxo completo por jogador:
  1. riotIdGameName + riotIdTagline  -> account-v1 (rota REGIONAL)      -> puuid
  2. puuid                            -> summoner-v4 (rota de PLATAFORMA) -> summonerId
  3. summonerId                       -> league-v4 (rota de PLATAFORMA)   -> tier/division

Como funciona na prática:
  - O rank de alguém não muda durante a partida, então buscamos UMA VEZ
    por jogador (cache por "gameName#tagLine") e guardamos em memória.
  - A busca roda numa thread separada (`request_rank_async`), pra não
    travar o loop de 300ms do main.py esperando resposta de rede.
  - O main.py só lê o cache (`get_cached_rank`), que começa como
    "UNRANKED" e atualiza sozinho assim que a thread termina.

REQUISITOS:
  - Precisa de uma API key da Riot (https://developer.riotgames.com/)
  - Salve a key num arquivo chamado `riot_api_key.txt` na raiz do projeto
    (mesma pasta do main.py), só com a key dentro, sem mais nada.
  - Adicione `riot_api_key.txt` no seu .gitignore! Nunca suba ela pro git.
"""

import os
import threading
import urllib.parse

import requests

# 🌎 Troque aqui se jogar em outro servidor (ex: "na1", "euw1", "kr", "la1", "la2")
PLATFORM = "br1"

# Rota REGIONAL usada só pelo account-v1 (não é a mesma coisa que PLATFORM!)
# br1/la1/la2/na1 -> "americas" | euw1/eun1/tr1/ru -> "europe" | kr/jp1 -> "asia"
PLATFORM_TO_REGION = {
    "br1": "americas", "la1": "americas", "la2": "americas", "na1": "americas", "oc1": "americas",
    "euw1": "europe", "eun1": "europe", "tr1": "europe", "ru": "europe",
    "kr": "asia", "jp1": "asia",
}
REGION = PLATFORM_TO_REGION.get(PLATFORM, "americas")

# Quando a Live Client API não manda a tag (ela esconde a tag de outros
# jogadores por privacidade), chutamos a tag padrão da região. A maioria
# das contas nunca trocou a tag manualmente, então isso acerta bastante,
# mas NÃO é garantido (falha pra quem tem tag customizada tipo #Pony).
DEFAULT_TAG_GUESS = PLATFORM.upper()  # ex: "BR1"

API_KEY_FILE = "riot_api_key.txt"

_rank_cache: dict[str, dict] = {}
_fetching: set[str] = set()
_lock = threading.Lock()

DEFAULT_RANK = {"tier": "UNRANKED", "division": ""}


def _load_api_key() -> str | None:
    if not os.path.exists(API_KEY_FILE):
        print(f"[rank_fetcher] Arquivo '{API_KEY_FILE}' não encontrado. Crie ele com sua API key da Riot.")
        return None
    with open(API_KEY_FILE, "r") as f:
        key = f.read().strip()
    return key or None


def _headers() -> dict:
    key = _load_api_key()
    return {"X-Riot-Token": key} if key else {}


def _resolve_puuid(game_name: str, tag_line: str) -> str | None:
    """Riot ID (nome#tag) -> puuid, via rota REGIONAL (account-v1)."""
    headers = _headers()
    if not headers:
        return None

    name_enc = urllib.parse.quote(game_name)
    tag_enc = urllib.parse.quote(tag_line)
    url = f"https://{REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name_enc}/{tag_enc}"

    res = requests.get(url, headers=headers, timeout=3)

    if res.status_code == 401:
        print("[rank_fetcher] API key inválida ou expirada. Gere uma nova em developer.riotgames.com")
        return None
    if res.status_code == 404:
        print(f"[rank_fetcher] Riot ID '{game_name}#{tag_line}' não encontrado (conta pode não existir nessa região).")
        return None
    if res.status_code == 429:
        print("[rank_fetcher] Rate limit da Riot API atingido.")
        return None
    if res.status_code != 200:
        print(f"[rank_fetcher] Erro {res.status_code} ao resolver Riot ID '{game_name}#{tag_line}'")
        return None

    return res.json().get("puuid")


def _fetch_rank_blocking(game_name: str, tag_line: str) -> dict:
    """Faz as chamadas reais na Riot API. Roda dentro da thread background."""
    headers = _headers()
    if not headers:
        return DEFAULT_RANK

    try:
        print(f"[rank_fetcher] Resolvendo puuid pra '{game_name}#{tag_line}'...")
        puuid = _resolve_puuid(game_name, tag_line)
        if not puuid:
            return DEFAULT_RANK

        # 2. puuid -> summonerId (rota de PLATAFORMA)
        summoner_url = f"https://{PLATFORM}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        summoner_res = requests.get(summoner_url, headers=headers, timeout=3)

        if summoner_res.status_code == 429:
            print("[rank_fetcher] Rate limit da Riot API atingido, tentando de novo depois.")
            return DEFAULT_RANK
        if summoner_res.status_code != 200:
            print(f"[rank_fetcher] Erro {summoner_res.status_code} ao buscar summoner ({game_name}#{tag_line})")
            return DEFAULT_RANK

        summoner_id = summoner_res.json().get("id")
        if not summoner_id:
            return DEFAULT_RANK

        # 3. summonerId -> entradas de liga (rota de PLATAFORMA)
        league_url = f"https://{PLATFORM}.api.riotgames.com/lol/league/v4/entries/by-summoner/{summoner_id}"
        league_res = requests.get(league_url, headers=headers, timeout=3)

        if league_res.status_code != 200:
            print(f"[rank_fetcher] Erro {league_res.status_code} ao buscar liga ({game_name}#{tag_line})")
            return DEFAULT_RANK

        entries = league_res.json()
        for entry in entries:
            if entry.get("queueType") == "RANKED_SOLO_5x5":
                print(f"[rank_fetcher] OK: {game_name}#{tag_line} = {entry.get('tier')} {entry.get('rank')}")
                return {"tier": entry.get("tier", "UNRANKED"), "division": entry.get("rank", "")}

        for entry in entries:
            if entry.get("queueType") == "RANKED_FLEX_SR":
                print(f"[rank_fetcher] OK (flex): {game_name}#{tag_line} = {entry.get('tier')} {entry.get('rank')}")
                return {"tier": entry.get("tier", "UNRANKED"), "division": entry.get("rank", "")}

        print(f"[rank_fetcher] {game_name}#{tag_line} é unranked de verdade.")
        return DEFAULT_RANK

    except requests.exceptions.RequestException as e:
        print(f"[rank_fetcher] Erro de rede: {e}")
        return DEFAULT_RANK


def request_rank_async(game_name: str, tag_line: str):
    """Dispara a busca em background, se ainda não tiver sido buscada/estiver buscando."""
    if not game_name:
        return

    tag_line = tag_line or DEFAULT_TAG_GUESS
    cache_key = f"{game_name}#{tag_line}"

    with _lock:
        if cache_key in _rank_cache or cache_key in _fetching:
            return
        _fetching.add(cache_key)

    def worker():
        result = _fetch_rank_blocking(game_name, tag_line)
        with _lock:
            _rank_cache[cache_key] = result
            _fetching.discard(cache_key)

    threading.Thread(target=worker, daemon=True).start()


def get_cached_rank(game_name: str, tag_line: str) -> dict:
    """Leitura instantânea (sem rede) — use isso no loop de 300ms."""
    tag_line = tag_line or DEFAULT_TAG_GUESS
    cache_key = f"{game_name}#{tag_line}"
    with _lock:
        return _rank_cache.get(cache_key, DEFAULT_RANK)


def clear_cache():
    with _lock:
        _rank_cache.clear()
        _fetching.clear()
