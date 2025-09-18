import os
import subprocess
import requests
import json

# === ЗАГРУЗКА КОНФИГА ===
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

GITHUB_TOKEN = config["github_token"]  # Токен теперь из файла
ORG_NAME = "biggest-backups-projects"
BASE_PATH = r"x:\.trash\ya"

# GitHub API endpoint
GITHUB_API = "https://api.github.com"

# Заголовки для авторизации
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def create_repo(repo_name):
    """Создать репозиторий в организации"""
    url = f"{GITHUB_API}/orgs/{ORG_NAME}/repos"
    data = {
        "name": repo_name,
        "private": True,  # можно True, если нужны приватные
        "auto_init": False
    }

    r = requests.post(url, headers=HEADERS, json=data)
    if r.status_code == 201:
        print(f"[OK] Создан репозиторий: {repo_name}")
        return True
    elif r.status_code == 422:
        print(f"[SKIP] Репозиторий уже существует: {repo_name}")
        return True
    else:
        print(f"[ERR] Не удалось создать {repo_name}: {r.status_code} {r.text}")
        return False

def push_folder_to_github(folder_path, repo_name):
    """Инициализировать и запушить папку на GitHub"""
    try:
        # Инициализация git
        subprocess.run("git init", cwd=folder_path, shell=True, check=True)
        subprocess.run("git add .", cwd=folder_path, shell=True, check=True)
        subprocess.run('git commit -m "ya"', cwd=folder_path, shell=True, check=True)

        # Добавляем remote
        remote_url = f"https://{GITHUB_TOKEN}@github.com/{ORG_NAME}/{repo_name}.git"
        subprocess.run("git remote remove origin", cwd=folder_path, shell=True)
        subprocess.run(f"git remote add origin {remote_url}", cwd=folder_path, shell=True, check=True)

        # Пушим
        subprocess.run("git branch -M main", cwd=folder_path, shell=True, check=True)
        subprocess.run("git push -u origin main --force", cwd=folder_path, shell=True, check=True)

        print(f"[PUSHED] {folder_path} → {repo_name}")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Git ошибка в {folder_path}: {e}")

def main():
    for folder in os.listdir(BASE_PATH):
        folder_path = os.path.join(BASE_PATH, folder)

        # Проверяем что это папка и не начинается с "+"
        if os.path.isdir(folder_path) and not folder.startswith("+"):
            repo_name = f"ya.{folder}"

            # Создание репозитория
            #if create_repo(repo_name):
            create_repo(repo_name)
                # Пуш содержимого
                #push_folder_to_github(folder_path, repo_name)

if __name__ == "__main__":
    main()
