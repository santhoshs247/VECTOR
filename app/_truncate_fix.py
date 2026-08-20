import os

filepath = r'd:\VECTOR\app\gui_app.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Keep only first 1387 lines (the clean new code)
with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines[:1387])

print(f"Truncated from {len(lines)} to 1387 lines")
