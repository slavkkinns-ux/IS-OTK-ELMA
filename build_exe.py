#!/usr/bin/env python3
"""
Скрипт сборки IS-OTK-ELMA.exe через PyInstaller.
Запуск: python build_exe.py
"""
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    print(f"\n{'='*60}")
    print(f">>> {' '.join(cmd)}")
    print(f"{'='*60}\n")
    return subprocess.run(cmd, cwd=cwd, check=False)


def main():
    project_dir = Path(__file__).parent.absolute()
    spec_file = project_dir / "IS-OTK-ELMA.spec"
    dist_dir = project_dir / "dist"
    build_dir = project_dir / "build"

    # 1. Проверка PyInstaller
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller не установлен. Устанавливаю...")
        result = run([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0"])
        if result.returncode != 0:
            print("Ошибка установки PyInstaller")
            return 1

    # 2. Очистка старых сборок
    print("\n>>> Очистка старых сборок...")
    
    def remove_readonly(func, path, excinfo):
        """Callback для shutil.rmtree: снимает readonly атрибут и повторяет."""
        os.chmod(path, stat.S_IWRITE)
        func(path)
    
    for d in (dist_dir, build_dir):
        if d.exists():
            try:
                shutil.rmtree(d, onerror=remove_readonly)
                print(f"Удалено: {d}")
            except Exception as e:
                print(f"Предупреждение: не удалось удалить {d}: {e}")

    # 3. Сборка через spec-файл
    result = run([
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ], cwd=project_dir)

    if result.returncode != 0:
        print("\n[FAILED] СБОРКА ПРОВАЛИЛАСЬ")
        return result.returncode

    # 4. Проверка результата - ищем любой IS-OTK-ELMA*.exe
    exe_files = list(dist_dir.glob("IS-OTK-ELMA*.exe"))
    if exe_files:
        # Берём самый новый
        exe_path = max(exe_files, key=lambda f: f.stat().st_mtime)
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("\n[SUCCESS] СБОРКА УСПЕШНА")
        print(f"Исполняемый файл: {exe_path}")
        print(f"Размер: {size_mb:.1f} MB")
        print(f"\nДля запуска: {exe_path}")
        
        # Если имя не стандартное — переименовываем
        standard_path = dist_dir / "IS-OTK-ELMA.exe"
        if exe_path != standard_path:
            try:
                if standard_path.exists():
                    standard_path.unlink()
                exe_path.rename(standard_path)
                print(f"Переименовано в: {standard_path}")
            except Exception as e:
                print(f"Предупреждение: не удалось переименовать: {e}")
    else:
        print("\n[ERROR] EXE не найден в dist/")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())