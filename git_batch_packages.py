#!/usr/bin/env python3
"""
git_batch_packages.py

Запуск:
    python git_batch_packages.py /path/to/repo
или:
    python git_batch_packages.py
    (ввести путь вручную)

Поведение:
 - открывает <repo>/packages
 - для каждой подпапки делает отдельный git add / git commit с сообщением:
       packages -> <package_name>
 - каждые 5 успешных коммитов выполняет git push
 - логирует fatal-ошибки в log.txt рядом со скриптом и пропускает проблемную папку
 - игнорирует .git и папки без изменений (ничего коммитить)
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# --------------
LOG_FILE = os.path.join(os.path.dirname(__file__), "log.txt")
DELETE_ON_FATAL = False   # если True — при fatal будет пытаться удалить проблемную папку (опасно)
PUSH_BATCH_SIZE = 5       # пуш каждые N успешных коммитов
# --------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)


def run_git(args, cwd):
    """Запускает git с аргументами args (list) в каталоге cwd.
    Возвращает CompletedProcess; при отсутствии git — выбрасывает исключение.
    """
    cmd = ["git"] + args
    try:
        res = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
    except FileNotFoundError as e:
        logging.error("Git не найден в PATH. Установите git и попробуйте снова.")
        raise
    return res


def contains_fatal(text):
    if not text:
        return False
    return "fatal" in text.lower()


def has_changes_for_package(repo_root, package_rel_path):
    """
    Проверяет, есть ли изменения в пакете (в рабочем дереве или в индексе).
    Возвращает True если есть изменения (нужно коммитить), False если пусто.
    Использует: git status --porcelain <path>
    """
    res = run_git(["status", "--porcelain", "--", package_rel_path], cwd=repo_root)
    output = (res.stdout or "") + (res.stderr or "")
    # Если git вернул ошибку (например, путь некорректен) — тоже считаем, что изменений нет,
    # но логируем stderr.
    if res.returncode != 0:
        logging.warning(f"[status] git вернул код {res.returncode} для {package_rel_path}. output: {output.strip()}")
        # не прерываем — вернём False, чтобы не пытаться коммитить несуществующее
        return False
    return bool(output.strip())


def main():
    # Получаем путь к репозиторию
    if len(sys.argv) > 1:
        repo_root = sys.argv[1]
    else:
        repo_root = input("Введите путь к репозиторию: ").strip()

    if not os.path.isdir(repo_root):
        logging.error(f"Указанный путь не найден или не директория: {repo_root}")
        sys.exit(1)

    # Проверяем папку packages
    packages_dir = os.path.join(repo_root, "packages")
    if not os.path.isdir(packages_dir):
        logging.error(f"В репозитории не найдена папка 'packages' по пути: {packages_dir}")
        sys.exit(1)

    # Получаем список подпапок (игнорируем .git)
    entries = sorted(os.listdir(packages_dir))
    package_names = [name for name in entries if os.path.isdir(os.path.join(packages_dir, name)) and name != ".git"]

    logging.info(f"Найдено пакетов в packages/: {len(package_names)}")

    successful_commits_since_last_push = 0

    for pkg in package_names:
        pkg_rel = os.path.join("packages", pkg)  # относительный путь для git команд
        pkg_abs = os.path.join(packages_dir, pkg)
        logging.info(f"▶ Обрабатывается пакет: {pkg}")

        # Пропустить, если нет изменений
        try:
            if not has_changes_for_package(repo_root, pkg_rel):
                logging.info(f"[SKIP] Пакет '{pkg}' — нечего коммитить, пропускаю.")
                continue
        except Exception as e:
            logging.error(f"[ERROR] Не удалось проверить статус для {pkg}: {e}")
            # пропускаем пакет
            continue

        # git add packages/<pkg>/
        try:
            add_res = run_git(["add", "--", f"{pkg_rel}/"], cwd=repo_root)
        except Exception:
            logging.error(f"[FATAL] Не удалось выполнить git add для {pkg} — git отсутствует.")
            sys.exit(1)

        combined_add = (add_res.stdout or "") + (add_res.stderr or "")
        if add_res.returncode != 0:
            if contains_fatal(combined_add):
                logging.error(f"[FATAL][add] {pkg}: {combined_add.strip()}")
                if DELETE_ON_FATAL:
                    try:
                        import shutil
                        shutil.rmtree(pkg_abs)
                        logging.info(f"Папка удалена из-за fatal: {pkg_abs}")
                    except Exception as e:
                        logging.error(f"Ошибка при удалении {pkg_abs}: {e}")
                continue
            else:
                logging.warning(f"[add] non-zero exit для {pkg}: {combined_add.strip()}")
                continue

        # git commit -m "packages -> <pkg>"
        commit_message = f"packages -> {pkg}"
        commit_res = run_git(["commit", "-m", commit_message, "--", f"{pkg_rel}/"], cwd=repo_root)
        combined_commit = (commit_res.stdout or "") + (commit_res.stderr or "")

        if commit_res.returncode != 0:
            if contains_fatal(combined_commit):
                logging.error(f"[FATAL][commit] {pkg}: {combined_commit.strip()}")
                if DELETE_ON_FATAL:
                    try:
                        import shutil
                        shutil.rmtree(pkg_abs)
                        logging.info(f"Папка удалена из-за fatal: {pkg_abs}")
                    except Exception as e:
                        logging.error(f"Ошибка при удалении {pkg_abs}: {e}")
                continue
            elif "nothing to commit" in combined_commit.lower():
                logging.info(f"[commit] Нечего коммитить для {pkg} (после add).")
                continue
            else:
                logging.warning(f"[commit] non-zero exit для {pkg}: {combined_commit.strip()}")
                continue

        # Успешный коммит
        successful_commits_since_last_push += 1
        logging.info(f"[OK][commit] Успешно закоммичен пакет: {pkg} (batch count: {successful_commits_since_last_push})")

        # Если набралось PUSH_BATCH_SIZE коммитов — пушим
        if successful_commits_since_last_push >= PUSH_BATCH_SIZE:
            push_res = run_git(["push"], cwd=repo_root)
            combined_push = (push_res.stdout or "") + (push_res.stderr or "")
            if push_res.returncode != 0:
                if contains_fatal(combined_push):
                    logging.error(f"[FATAL][push] при попытке запушить после {successful_commits_since_last_push} коммитов: {combined_push.strip()}")
                    # не будем удалять коммиты — просто логируем и продолжаем с следующими пакетами
                else:
                    logging.warning(f"[push] non-zero exit при попытке запушить: {combined_push.strip()}")
                # после неудачного push мы продолжаем — локальные коммиты останутся
            else:
                logging.info(f"[OK][push] Успешно запушено после {successful_commits_since_last_push} коммитов.")
            successful_commits_since_last_push = 0

    # В конце пушим остаток, если есть
    if successful_commits_since_last_push > 0:
        logging.info(f"Пуш остатка: {successful_commits_since_last_push} коммит(ов).")
        # don't fix origin commit
        push_res = run_git(["push"], cwd=repo_root)
        combined_push = (push_res.stdout or "") + (push_res.stderr or "")
        if push_res.returncode != 0:
            if contains_fatal(combined_push):
                logging.error(f"[FATAL][push] при финальном пуше: {combined_push.strip()}")
            else:
                logging.warning(f"[push] non-zero exit при финальном пуше: {combined_push.strip()}")
        else:
            logging.info("[OK][push] Финальный push успешен.")

    logging.info("Готово. Все пакеты обработаны.")


if __name__ == "__main__":
    main()
