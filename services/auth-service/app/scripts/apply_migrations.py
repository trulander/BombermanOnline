#!/usr/bin/env python3
"""
Скрипт для применения миграций Alembic.

Использование:
    python scripts/apply_migrations.py [revision]
    
Аргументы:
    revision - опциональный аргумент, указывающий до какой ревизии применять миграции.
               По умолчанию: 'head' (последняя миграция).
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    # Получаем ревизию, если она указана
    revision = "head"
    if len(sys.argv) > 1:
        revision = sys.argv[1]
    
    # Получаем путь к корню проекта
    project_dir = Path(__file__).parent.parent.absolute()
    
    # Переходим в директорию проекта
    os.chdir(project_dir)
    
    # Запускаем команду alembic для применения миграций
    try:
        subprocess.run(
            [
                "alembic", 
                "upgrade", 
                revision
            ], 
            check=True
        )
        print(f"Миграции успешно применены до ревизии '{revision}'!")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при применении миграций: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 