#!/usr/bin/env python3
"""
Windows System Cleaner - Улучшенная версия
Безопасная и оптимизированная утилита очистки системы для Windows 10/11
"""

import os
import shutil
import winshell
import logging
import subprocess
import sys
import ctypes
import json
import hashlib
from datetime import datetime
from pathlib import Path
from tqdm import tqdm
from typing import Dict, List, Set, Optional

# Конфигурация
CONFIG = {
    "backup_enabled": True,
    "backup_path": "cleaner_backups",
    "max_backup_age_days": 30,
    "safe_mode": True,
    "log_level": "INFO",
    "excluded_extensions": [".exe", ".dll", ".sys", ".ini"],
    "excluded_folders": ["Windows", "Program Files", "Program Files (x86)"]
}

class SystemCleaner:
    """Улучшенный очиститель системы с функциями безопасности"""
    
    def __init__(self):
        self.setup_logging()
        self.operations_log = []
        self.backup_dir = Path(CONFIG["backup_path"])
        self.setup_backup_dir()
        
    def setup_logging(self):
        """Настройка комплексного логирования"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        logging.basicConfig(
            level=getattr(logging, CONFIG["log_level"]),
            format=log_format,
            handlers=[
                logging.FileHandler('cleaner_enhanced.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_backup_dir(self):
        """Создание и управление директорией бэкапов"""
        try:
            self.backup_dir.mkdir(exist_ok=True)
            self.clean_old_backups()
        except Exception as e:
            self.logger.error(f"Ошибка настройки директории бэкапов: {e}")
            
    def clean_old_backups(self):
        """Удаление бэкапов старше заданного возраста"""
        try:
            cutoff_time = datetime.now().timestamp() - (CONFIG["max_backup_age_days"] * 86400)
            for backup_file in self.backup_dir.iterdir():
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    self.logger.info(f"Удален старый бэкап: {backup_file}")
        except Exception as e:
            self.logger.warning(f"Не удалось очистить старые бэкапы: {e}")
    
    def is_admin(self) -> bool:
        """Проверка прав администратора"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            self.logger.error(f"Ошибка проверки прав администратора: {e}")
            return False
    
    def run_as_admin(self):
        """Повышение привилегий с улучшенной обработкой ошибок"""
        try:
            if getattr(sys, 'frozen', False):
                script = sys.executable
            else:
                script = __file__
            
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}"', None, 1
            )
            sys.exit(0)
        except Exception as e:
            self.logger.critical(f"Ошибка повышения привилегий: {e}")
            print("❌ Не удалось повысить привилегии. Запустите вручную от имени администратора.")
            sys.exit(1)
    
    def is_safe_path(self, path: Path) -> bool:
        """Проверка безопасности пути перед операциями"""
        try:
            absolute_path = path.resolve()
            
            # Защита критических системных путей
            system_paths = [
                Path(os.environ.get('SYSTEMROOT', 'C:\\Windows')),
                Path("C:\\"),
                Path(os.environ.get('PROGRAMFILES', 'C:\\Program Files')),
            ]
            
            for system_path in system_paths:
                if system_path in absolute_path.parents or absolute_path == system_path:
                    self.logger.warning(f"Заблокирована операция с системным путем: {absolute_path}")
                    return False
            
            # Проверка исключенных папок
            for excluded in CONFIG["excluded_folders"]:
                if excluded in str(absolute_path):
                    self.logger.warning(f"Заблокирована операция с исключенной папкой: {absolute_path}")
                    return False
                    
            return True
        except Exception as e:
            self.logger.error(f"Ошибка проверки безопасности пути: {e}")
            return False
    
    def create_backup(self, path: Path) -> bool:
        """Создание бэкапа файла/директории перед удалением"""
        if not CONFIG["backup_enabled"]:
            return True
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{path.name}_{timestamp}_{hashlib.md5(str(path).encode()).hexdigest()[:8]}"
            backup_path = self.backup_dir / backup_name
            
            if path.is_file():
                shutil.copy2(path, backup_path)
            elif path.is_dir():
                shutil.copytree(path, backup_path, dirs_exist_ok=True)
                
            self.logger.info(f"Создан бэкап: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка создания бэкапа для {path}: {e}")
            return False
    
    def safe_delete(self, path: Path) -> bool:
        """Безопасное удаление файла/директории с бэкапом и валидацией"""
        try:
            if not path.exists():
                return True
                
            if not self.is_safe_path(path):
                return False
            
            # Создание бэкапа перед удалением
            if not self.create_backup(path):
                if CONFIG["safe_mode"]:
                    self.logger.warning(f"Ошибка бэкапа, пропуск удаления: {path}")
                    return False
            
            # Выполнение удаления
            if path.is_file() or path.is_symlink():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
                
            self.operations_log.append(f"УДАЛЕНО: {path}")
            self.logger.info(f"Успешно удалено: {path}")
            return True
            
        except PermissionError as e:
            self.logger.error(f"Доступ запрещен: {path} - {e}")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка удаления: {path} - {e}")
            return False
    
    def clean_directory(self, directory: str, description: str) -> bool:
        """Улучшенная очистка директории с проверками безопасности"""
        dir_path = Path(directory)
        
        if not dir_path.exists():
            self.logger.warning(f"Директория не существует: {directory}")
            print(f"⚠️ Директория не существует: {description}")
            return False
        
        if not self.is_safe_path(dir_path):
            print(f"❌ Заблокировано: {description} содержит защищенные системные файлы")
            return False
        
        print(f"\n🔍 Сканирование {description}...")
        
        try:
            items = list(dir_path.iterdir())
            if not items:
                print(f"✓ {description} уже очищена")
                return True
            
            deleted_count = 0
            error_count = 0
            
            with tqdm(total=len(items), desc=f"Очистка {description}", unit="item") as pbar:
                for item in items:
                    try:
                        if self.safe_delete(item):
                            deleted_count += 1
                        else:
                            error_count += 1
                    except Exception as e:
                        self.logger.error(f"Ошибка обработки {item}: {e}")
                        error_count += 1
                    finally:
                        pbar.update(1)
            
            print(f"✓ {description}: {deleted_count} элементов удалено, {error_count} ошибок")
            return error_count == 0
            
        except Exception as e:
            self.logger.error(f"Ошибка очистки директории: {description} - {e}")
            print(f"❌ Ошибка очистки {description}")
            return False
    
    def empty_recycle_bin(self) -> bool:
        """Безопасная очистка корзины"""
        try:
            if not user_confirmation("Очистить корзину? Это действие нельзя отменить."):
                return False
                
            winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False)
            self.operations_log.append("ОЧИЩЕНА_КОРЗИНА")
            self.logger.info("Корзина успешно очищена")
            print("✓ Корзина очищена")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка очистки корзины: {e}")
            print("❌ Не удалось очистить корзину")
            return False
    
    def run_disk_cleanup(self) -> bool:
        """Безопасный запуск очистки диска Windows"""
        try:
            if not user_confirmation("Запустить очистку диска Windows? Это может занять несколько минут."):
                return False
                
            print("🔄 Запуск очистки диска...")
            result = subprocess.run(["cleanmgr", "/sagerun:1"], 
                                  capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                self.logger.info("Очистка диска успешно завершена")
                print("✓ Очистка диска завершена")
                return True
            else:
                self.logger.error(f"Ошибка очистки диска: {result.stderr}")
                print("❌ Ошибка очистки диска")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("Таймаут очистки диска")
            print("❌ Таймаут очистки диска")
            return False
        except Exception as e:
            self.logger.error(f"Ошибка очистки диска: {e}")
            print("❌ Ошибка очистки диска")
            return False

    def show_backup_contents(self):
        """Показать содержимое бэкапов"""
        try:
            backups = list(self.backup_dir.iterdir())
            if not backups:
                print("📂 Бэкапы отсутствуют")
                return
            
            print(f"\n📂 Содержимое папки бэкапов ({len(backups)} файлов):")
            for backup in sorted(backups, key=lambda x: x.stat().st_mtime, reverse=True):
                size = backup.stat().st_size
                date = datetime.fromtimestamp(backup.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"  • {backup.name} ({size} байт, {date})")
        except Exception as e:
            print(f"❌ Ошибка чтения бэкапов: {e}")

    def show_operations_log(self):
        """Показать журнал операций"""
        if not self.operations_log:
            print("📝 Журнал операций пуст")
            return
        
        print(f"\n📝 Журнал операций ({len(self.operations_log)} записей):")
        for operation in self.operations_log[-10:]:  # Последние 10 операций
            print(f"  • {operation}")

def user_confirmation(message: str) -> bool:
    """Улучшенное подтверждение пользователя с предупреждениями безопасности"""
    print(f"\n⚠️ {message}")
    print("Введите 'ДА' для подтверждения или что-либо другое для отмены:")
    
    response = input().strip().upper()
    return response == 'ДА'

def display_menu():
    """Отображение улучшенного меню с информацией о безопасности"""
    menu = """
    🛡️ УЛУЧШЕННЫЙ ОЧИСТИТЕЛЬ WINDOWS - БЕЗОПАСНЫЙ РЕЖИМ
    =================================================
    
    🔒 Функции безопасности:
    • Защита системных файлов
    • Бэкап перед удалением
    • Валидация путей
    • Требуется подтверждение
    
    📋 Доступные операции:
    
    1. 🗂️  Очистить Рабочий стол (только пользовательские файлы)
    2. 🗑️  Очистить папку Temp
    3. 📊 Очистить временные файлы AppData
    4. 🖥️  Очистить временные файлы Local AppData
    5. 🗄️  Очистить корзину
    6. 🧹 Запустить очистку диска (требуются права администратора)
    7. 📊 Показать содержимое бэкапов
    8. 📝 Показать журнал операций
    9. 🚪 Выход
    
    ⚠️ Внимание: Некоторые операции требуют прав администратора
    """
    print(menu)

def get_user_choice() -> int:
    """Получение и валидация выбора пользователя в меню"""
    while True:
        try:
            choice = input("Введите ваш выбор (1-9): ").strip()
            if not choice:
                continue
            choice_num = int(choice)
            if 1 <= choice_num <= 9:
                return choice_num
            print("Пожалуйста, введите число от 1 до 9")
        except ValueError:
            print("Неверный ввод. Пожалуйста, введите число.")

def main():
    """Основная точка входа в приложение"""
    cleaner = SystemCleaner()
    
    # Проверка прав администратора для определенных операций
    if not cleaner.is_admin():
        print("🔒 Некоторые операции требуют прав администратора")
        if user_confirmation("Перезапустить с правами администратора?"):
            cleaner.run_as_admin()
    
    # Определение безопасных операций очистки
    cleaning_operations = {
        1: (os.path.expanduser("~/Desktop"), "Рабочий стол"),
        2: (os.environ.get('TEMP', ''), "Временные файлы"),
        3: (os.path.join(os.environ.get('APPDATA', ''), "..", "Local", "Temp"), "Временные файлы AppData"),
        4: (os.environ.get('LOCALAPPDATA', ''), "Временные файлы Local AppData")
    }
    
    while True:
        display_menu()
        choice = get_user_choice()
        
        if choice in cleaning_operations:
            path, description = cleaning_operations[choice]
            cleaner.clean_directory(path, description)
            
        elif choice == 5:
            cleaner.empty_recycle_bin()
            
        elif choice == 6:
            if cleaner.is_admin():
                cleaner.run_disk_cleanup()
            else:
                print("❌ Для очистки диска требуются права администратора")
                
        elif choice == 7:
            cleaner.show_backup_contents()
            
        elif choice == 8:
            cleaner.show_operations_log()
            
        elif choice == 9:
            print("👋 Спасибо за использование Улучшенного очистителя Windows!")
            break
        
        input("\nНажмите Enter для продолжения...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Операция отменена пользователем")
        sys.exit(1)
    except Exception as e:
        logging.critical(f"Неожиданная ошибка: {e}")
        print("❌ Произошла критическая ошибка. Проверьте логи для деталей.")
        sys.exit(1)
