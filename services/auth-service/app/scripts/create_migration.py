#!/usr/bin/env python3
"""
Скрипт для создания новой миграции Alembic.

Использование:
    python scripts/create_migration.py "Название миграции"
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Необходимо указать название миграции!")
        print("Использование: python scripts/create_migration.py \"Название миграции\"")
        sys.exit(1)
    
    migration_name = sys.argv[1]
    
    # Получаем путь к корню проекта
    project_dir = Path(__file__).parent.parent.absolute()
    
    # Переходим в директорию проекта
    os.chdir(project_dir)
    
    # Запускаем команду alembic
    try:
        subprocess.run(
            [
                "alembic", 
                "revision", 
                "--autogenerate", 
                "-m", 
                migration_name
            ], 
            check=True
        )
        print(f"Миграция '{migration_name}' успешно создана!")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при создании миграции: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 