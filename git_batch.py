#!/usr/bin/env python3
"""
git_batch.py

Скрипт:
 - принимает путь к папке с поддиректориями (через аргумент CLI или ввод вручную);
 - пропускает .git;
 - если папка уже коммичена (нет изменений) — пропускает;
 - иначе делает git add, commit, push;
 - при fatal-ошибках логирует в log.txt и (опционально) удаляет папку.
"""

import os
import subprocess
import sys
import logging
from datetime import datetime

# ---------------------------
LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")
DELETE_ON_FATAL = False  # <- если True — удаляет папку при fatal
# ---------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)


def run_git(args, cwd):
    """Запускает git с аргументами args (список) в каталоге cwd."""
    cmd = ["git"] + args
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False
    )
    return result


def is_fatal(text):
    """Проверяет, содержит ли текст 'fatal' (нечувствительно к регистру)."""
    return "fatal" in text.lower() if text else False


def has_changes(dirname, repo_root):
    """
    Проверяет, есть ли изменения в папке dirname (в рабочем дереве или в индексе).
    Возвращает True, если есть что коммитить.
    """
    # Проверим git status --porcelain только для этой папки
    res = run_git(["status", "--porcelain", dirname], cwd=repo_root)
    output = (res.stdout or "").strip()
    if output == "":
        return False  # нет изменений
    return True


def main():
    # Получаем путь
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
    else:
        target_path = input("Введите путь к директории с папками: ").strip()

    if not os.path.isdir(target_path):
        logging.error(f"Указанный путь не найден или не директория: {target_path}")
        sys.exit(1)

    repo_root = target_path
    entries = sorted(os.listdir(target_path))
    dirs = [
        d for d in entries
        if os.path.isdir(os.path.join(target_path, d)) and d != ".git"
    ]

    logging.info(f"Найдено директорий (без .git): {len(dirs)} в {target_path}")

    for dirname in dirs:
        folder_path = os.path.join(target_path, dirname)
        logging.info(f"▶ Обрабатываю папку: {dirname}")

        # --- Проверяем, есть ли изменения в папке
        if not has_changes(dirname, repo_root):
            logging.info(f"[SKIP] Папка '{dirname}' уже закоммичена, пропускаю.")
            continue

        # --- git add
        add_res = run_git(["add", f"{dirname}/"], cwd=repo_root)
        combined_add = (add_res.stdout or "") + "\n" + (add_res.stderr or "")

        if add_res.returncode != 0:
            if is_fatal(combined_add):
                logging.error(f"[FATAL][add] {dirname}: {combined_add.strip()}")
                if DELETE_ON_FATAL:
                    try:
                        import shutil
                        shutil.rmtree(folder_path)
                        logging.info(f"Папка удалена из-за fatal: {folder_path}")
                    except Exception as e:
                        logging.error(f"Ошибка при удалении {folder_path}: {e}")
                continue
            else:
                logging.warning(f"[add] non-zero exit для {dirname}: {combined_add.strip()}")
                continue

        # --- git commit
        commit_res = run_git(["commit", "-m", dirname], cwd=repo_root)
        combined_commit = (commit_res.stdout or "") + "\n" + (commit_res.stderr or "")

        if commit_res.returncode != 0:
            if is_fatal(combined_commit):
                logging.error(f"[FATAL][commit] {dirname}: {combined_commit.strip()}")
                if DELETE_ON_FATAL:
                    try:
                        import shutil
                        shutil.rmtree(folder_path)
                        logging.info(f"Папка удалена из-за fatal: {folder_path}")
                    except Exception as e:
                        logging.error(f"Ошибка при удалении {folder_path}: {e}")
                continue
            elif "nothing to commit" in combined_commit.lower():
                logging.info(f"[commit] Нечего коммитить для {dirname}")
                continue
            else:
                logging.warning(f"[commit] Ошибка коммита {dirname}: {combined_commit.strip()}")
                continue

        # --- git push
        push_res = run_git(["push", "-u", "origin", "main"], cwd=repo_root)
        combined_push = (push_res.stdout or "") + "\n" + (push_res.stderr or "")

        if push_res.returncode != 0:
            if is_fatal(combined_push):
                logging.error(f"[FATAL][push] {dirname}: {combined_push.strip()}")
                if DELETE_ON_FATAL:
                    try:
                        import shutil
                        shutil.rmtree(folder_path)
                        logging.info(f"Папка удалена из-за fatal: {folder_path}")
                    except Exception as e:
                        logging.error(f"Ошибка при удалении {folder_path}: {e}")
                continue
            else:
                logging.warning(f"[push] Ошибка push для {dirname}: {combined_push.strip()}")
                continue

        logging.info(f"[OK] Успешно обработано и запушено: {dirname}")

    logging.info("✅ Все папки обработаны.")


if __name__ == "__main__":
    main()
