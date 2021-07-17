import os


class FileHelper:

    @staticmethod
    def trim_string_to_newline(string: str, trim_from: int) -> str:
        """Обрезает исходную строку до красной строки."""
        name = string[trim_from:]
        return name.partition('\n')[0]

    @staticmethod
    def format_file_name(file_name: str) -> str:
        """Форматирует имя файла."""
        file_name = file_name.strip()
        file_name = FileHelper.format_space_to_underscore(file_name)
        file_name = file_name.replace('/', '')
        return file_name

    @staticmethod
    def format_space_to_underscore(replace_string: str) -> str:
        """Заменяет в строке пробел на нижнее подчеркивание."""
        return replace_string.replace(' ', '_')

    @staticmethod
    def get_first_alpha_from_string(find_string: str) -> int:
        """Получает индекс первой буквы в строке."""
        return find_string.find(next(filter(str.isalpha, find_string)))

    @staticmethod
    def generate_name(full_path: str, save_path: str, file_name: str,
                      file_extension: str = 'pdf') -> str:
        """Генерирует название файла."""
        if not os.path.exists(full_path):
            return full_path

        file_number = 1
        while os.path.exists(f'{save_path}/{file_name}_{file_number}.{file_extension}'):
            file_number += 1

        new_full_path = f'{save_path}/{file_name}_{file_number}.{file_extension}'

        return new_full_path
