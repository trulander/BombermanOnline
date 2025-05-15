#!/usr/bin/env python3
"""
Скрипт для отката миграций Alembic.

Использование:
    python scripts/rollback_migrations.py [revision]
    
Аргументы:
    revision - опциональный аргумент, указывающий до какой ревизии откатывать миграции.
               По умолчанию: '-1' (на одну миграцию назад).
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    # Получаем ревизию, если она указана
    revision = "-1"
    if len(sys.argv) > 1:
        revision = sys.argv[1]
    
    # Получаем путь к корню проекта
    project_dir = Path(__file__).parent.parent.absolute()
    
    # Переходим в директорию проекта
    os.chdir(project_dir)
    
    # Запускаем команду alembic для отката миграций
    try:
        subprocess.run(
            [
                "alembic", 
                "downgrade", 
                revision
            ], 
            check=True
        )
        print(f"Миграции успешно откачены до ревизии '{revision}'!")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при откате миграций: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 