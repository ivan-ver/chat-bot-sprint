import json
import os
import re



def replace_names_in_file(file_path, old_names, new_name):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for old_name in old_names:
            pattern = r'\b' + re.escape(old_name) + r'\b'
            content = re.sub(pattern, new_name, content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        return False


def process_all_files(knowledge_base_dir, name_mapping):
    processed_count = 0
    error_count = 0
    for filename, data in name_mapping.items():
        file_path = os.path.join(knowledge_base_dir, f"{filename}.txt")

        if os.path.exists(file_path):
            success = replace_names_in_file(
                file_path,
                data['old_names'],
                data['new_name']
            )
            if success:
                processed_count += 1
            else:
                error_count += 1
        else:
            print(f"Файл не найден: {file_path}")
            error_count += 1


if __name__ == "__main__":
    json_file_path = 'task-2/terms_map.json'
    knowledge_base_dir = 'task-2/knowledge_base'
    try:
        with open(json_file_path) as f:
            name_mapping = json.load(f)
        process_all_files(knowledge_base_dir, name_mapping)
        print(f"Загружено {len(name_mapping)} записей для замены")
    except Exception as e:
        print(f"Ошибка при загрузке JSON файла: {e}")


