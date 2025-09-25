import os
import subprocess
import requests
import json

ORG_NAME = "biggest-backups-projects"
BASE_PATH = r"x:\.trash\ya"

def push_folder_to_github(folder_path, repo_name):
    """пуш папки на GitHub"""
    try:
        # Добавляем remote
        remote_url = f"https://github.com/{ORG_NAME}/{repo_name}.git"
        #subprocess.run("git remote remove origin", cwd=folder_path, shell=True)
        subprocess.run(f"git remote add origin {remote_url}", cwd=folder_path, shell=True, check=True)

        # Пушим
        subprocess.run("git branch -M main", cwd=folder_path, shell=True, check=True)
        subprocess.run("git push -u origin main", cwd=folder_path, shell=True, check=True)

        print(f"[PUSHED] {folder_path} → {repo_name}")

    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Git ошибка в {folder_path}: {e}")

def main():
    for folder in os.listdir(BASE_PATH):
        folder_path = os.path.join(BASE_PATH, folder)

        # Проверяем что это папка и не начинается с "+"
        if os.path.isdir(folder_path) and not folder.startswith("+"):
            repo_name = f"ya.{folder}"

            # Пуш содержимого
            push_folder_to_github(folder_path, repo_name)

if __name__ == "__main__":
    main()
