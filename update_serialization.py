#!/usr/bin/env python
"""
Скрипт для автоматичної заміни використання to_dict() на Pydantic серіалізацію
"""
import os
import re
import sys
from pathlib import Path

# Словник відповідностей між моделями SQLAlchemy та їхніми Pydantic схемами
MODEL_TO_SCHEMA = {
    "MonoUser": "MonoUserResponse",
    "Group": "GroupResponse",
    "GroupInvitation": "GroupInvitationResponse",
    "Category": "CategoryResponse",
    "Config": "ConfigResponse",
    "User": "UserResponse",
    "SprSource": "SprSourceResponse",
    "SprTypePayment": "SprTypePaymentResponse",
}

def process_file(file_path):
    """Обробка файлу для заміни to_dict() на Pydantic серіалізацію"""
    print(f"Обробка файлу: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Шукаємо всі використання to_dict()
    to_dict_pattern = r"([a-zA-Z_][a-zA-Z0-9_]*)\.(to_dict\(\))"
    to_dict_matches = re.findall(to_dict_pattern, content)
    
    if not to_dict_matches:
        print(f"  В файлі {file_path} не знайдено використань to_dict()")
        return
    
    # Додаємо імпорти для схем Pydantic, які будуть використовуватись
    needed_schemas = set()
    
    for var_name, _ in to_dict_matches:
        # Спрощене визначення моделі за назвою змінної
        # Це не завжди точно, але дасть орієнтир
        for model_name, schema_name in MODEL_TO_SCHEMA.items():
            if model_name.lower() in var_name.lower():
                needed_schemas.add(schema_name)
    
    if not needed_schemas:
        print(f"  Не вдалося визначити схеми для заміни в {file_path}")
        return
    
    # Додаємо імпорт схем, якщо його ще немає
    schema_import = f"from api.schemas.common import {', '.join(sorted(needed_schemas))}"
    if "from api.schemas.common import" in content:
        # Оновлюємо існуючий імпорт
        content = re.sub(
            r"from api\.schemas\.common import ([^;\n]+)",
            lambda m: update_imports(m.group(1), needed_schemas),
            content
        )
    else:
        # Додаємо новий імпорт після інших імпортів
        import_section_end = re.search(r"^\s*$", content, re.MULTILINE)
        if import_section_end:
            pos = import_section_end.end()
            content = content[:pos] + schema_import + "\n" + content[pos:]
        else:
            # Якщо неможливо знайти кінець секції імпортів, додаємо на початок
            content = schema_import + "\n\n" + content
    
    # Замінюємо всі виклики to_dict() на відповідні Pydantic виклики
    for var_name, to_dict_call in to_dict_matches:
        model_type = None
        for model_name in MODEL_TO_SCHEMA:
            if model_name.lower() in var_name.lower():
                model_type = model_name
                break
        
        if model_type:
            schema_name = MODEL_TO_SCHEMA[model_type]
            content = content.replace(
                f"{var_name}.{to_dict_call}", 
                f"{schema_name}.model_validate({var_name}).model_dump()"
            )
    
    # Замінюємо варіанти [item.to_dict() for item in ...] на Pydantic варіанти
    list_comprehension_pattern = r"\[(.*?)\.to_dict\(\) for (.*?) in (.*?)\]"
    
    for match in re.finditer(list_comprehension_pattern, content):
        full_match = match.group(0)
        item_var = match.group(1)
        collection_var = match.group(3)
        
        # Визначаємо тип моделі для вибору схеми
        model_type = None
        for model_name in MODEL_TO_SCHEMA:
            # Спрощена евристика - припускаємо, що назва типу є частиною назви колекції
            if model_name.lower() in collection_var.lower():
                model_type = model_name
                break
        
        if model_type:
            schema_name = MODEL_TO_SCHEMA[model_type]
            replacement = f"[{schema_name}.model_validate({item_var}).model_dump() for {item_var} in {collection_var}]"
            content = content.replace(full_match, replacement)
    
    # Зберігаємо оновлений файл
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"  Оновлено файл: {file_path}")

def update_imports(current_imports, needed_schemas):
    """Оновити список імпортів, додавши нові схеми"""
    current_schema_set = set(s.strip() for s in current_imports.split(','))
    updated_schemas = sorted(current_schema_set.union(needed_schemas))
    return f"from api.schemas.common import {', '.join(updated_schemas)}"

def main():
    """Основна функція для обробки директорій та файлів"""
    base_dir = Path("/home/vik/pets/finman_api")
    api_dir = base_dir / "api"
    
    # Знаходимо всі Python файли в API директорії
    python_files = []
    for root, _, files in os.walk(api_dir):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    print(f"Знайдено {len(python_files)} Python файлів")
    
    # Обробляємо кожен файл
    for file_path in python_files:
        process_file(file_path)

if __name__ == "__main__":
    main()
