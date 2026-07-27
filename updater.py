import os
import sys
import subprocess
import requests

# Versão atual da sua build
CURRENT_VERSION = "1.0.1"

# Repositório onde você vai postar as Releases no GitHub
GITHUB_REPO = "crosxy/JarvisTimer" # Exemplo: "william/JarvisTimer"

def check_for_updates():
    """
    Retorna (download_url, latest_version) se houver atualização disponível no GitHub.
    """
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            latest_version = data["tag_name"].replace("v", "").strip()
            
            # Comparação simples de versão
            if latest_version > CURRENT_VERSION:
                for asset in data.get("assets", []):
                    if asset["name"].endswith(".exe"):
                        return asset["browser_download_url"], latest_version
    except Exception as e:
        print(f"Erro ao checar atualizações: {e}")
        
    return None, None

def apply_update(download_url):
    """
    Baixa o novo .exe, cria um script batch temporário para substituir o antigo e reinicia o app.
    """
    if not getattr(sys, 'frozen', False):
        print("Modo dev: atualização ignorada.")
        return

    current_exe = sys.executable
    new_exe = current_exe + ".new"
    
    # 1. Baixa o executável atualizado
    r = requests.get(download_url, stream=True)
    with open(new_exe, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
            
    # 2. Script batch temporário
    bat_content = f"""
    @echo off
    timeout /t 2 /nobreak > nul
    move /y "{new_exe}" "{current_exe}"
    start "" "{current_exe}"
    del "%~f0"
    """
    
    bat_path = os.path.join(os.path.dirname(current_exe), "update.bat")
    with open(bat_path, "w") as f:
        f.write(bat_content)
        
    # 3. Executa o updater e encerra o app atual
    subprocess.Popen([bat_path], shell=True)
    sys.exit(0)