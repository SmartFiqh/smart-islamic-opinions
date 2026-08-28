import os
from pathlib import Path

# إنشاء المجلدات
folders = [
    "data",
    "database",
    "utils",
    "ui",
    "translations",
    "assets",
    "tests"
]

for folder in folders:
    Path(folder).mkdir(exist_ok=True)
    Path(folder, "__init__.py").touch()

# إنشاء الملفات الرئيسية
files = [
    "app.py",
    "requirements.txt",
    ".env",
    ".gitignore",
    "README.md"
]

for file in files:
    Path(file).touch()

print("✅ تم إنشاء جميع المجلدات والملفات بنجاح!")
