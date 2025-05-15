#!/usr/bin/env python3
"""
Скрипт для просмотра истории миграций Alembic.

Использование:
    python scripts/show_migrations.py
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    # Получаем путь к корню проекта
    project_dir = Path(__file__).parent.parent.absolute()
    
    # Переходим в директорию проекта
    os.chdir(project_dir)
    
    # Запускаем команду alembic для просмотра истории миграций
    try:
        print("История миграций:")
        subprocess.run(
            [
                "alembic", 
                "history", 
                "--verbose"
            ], 
            check=True
        )
        
        print("\nТекущая ревизия:")
        subprocess.run(
            [
                "alembic", 
                "current"
            ], 
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при получении истории миграций: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 