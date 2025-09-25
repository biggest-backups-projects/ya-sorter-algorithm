import os
import shutil
import stat
import ctypes

# путь к родительской директории
BASE_DIR = r"x:\cloud\ya src"

def remove_readonly(func, path, _):
    """Снимаем readonly и пробуем удалить снова"""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def remove_hidden_attr(path):
    """Снимаем скрытый атрибут Windows"""
    FILE_ATTRIBUTE_HIDDEN = 0x02
    FILE_ATTRIBUTE_SYSTEM = 0x04
    attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
    if attrs != -1:
        new_attrs = attrs & ~(FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
        ctypes.windll.kernel32.SetFileAttributesW(str(path), new_attrs)

def main():
    # проходим по первому уровню папок
    for name in os.listdir(BASE_DIR):
        full_path = os.path.join(BASE_DIR, name)

        if not os.path.isdir(full_path):
            continue

        # убираем + в начале названия
        if name.startswith("+"):
            new_name = name.lstrip("+")
            new_path = os.path.join(BASE_DIR, new_name)

            # переименуем, если не конфликтует
            if not os.path.exists(new_path):
                print(f"Переименовываю: {name} -> {new_name}")
                os.rename(full_path, new_path)
                full_path = new_path
            else:
                print(f"⚠ Пропущено, уже существует: {new_name}")
                full_path = new_path  # чтобы .git всё равно проверился

        # удаляем .git внутри этой папки
        git_dir = os.path.join(full_path, ".git")
        if os.path.exists(git_dir) and os.path.isdir(git_dir):
            print(f"Удаляю .git в {full_path}")
            try:
                remove_hidden_attr(git_dir)
                shutil.rmtree(git_dir, onerror=remove_readonly)
            except Exception as e:
                print(f"Ошибка удаления {git_dir}: {e}")

if __name__ == "__main__":
    main()
