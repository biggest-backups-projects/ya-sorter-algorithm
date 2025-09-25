import os
import subprocess

# Путь к корневой папке
base_path = r"x:\.trash\ya\WAITING_POOLING"

# Обходим все подпапки
for root, dirs, files in os.walk(base_path):
    for d in dirs:
        folder_path = os.path.join(root, d)

        # Проверяем, что папка не начинается с "+"
        if not d.startswith("+"):
            print(f"Инициализация git в: {folder_path}")

            try:
                # Переходим в папку и выполняем команды
                subprocess.run("git init", cwd=folder_path, shell=True, check=True)
                subprocess.run("git add *", cwd=folder_path, shell=True, check=True)
                subprocess.run('git commit -m "ya"', cwd=folder_path, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Ошибка в {folder_path}: {e}")

    # Чтобы не уходить глубже в подпапки (если нужно только верхний уровень),
    # можно очистить dirs:
    # dirs[:] = []
