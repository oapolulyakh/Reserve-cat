import sys
import requests
import json
import logging

logging.basicConfig(
    level=logging.INFO,              #
    format='%(asctime)s [%(levelname)s]: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('program.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def get_url_image(text):
    """
    Получение url картинки по заданному тексту
    """
    url_photo = f'https://cataas.com/cat/says/{text}?json=true'
    logger.info(f"Получаю картинку с текстом '{text}'...")
    response = requests.get(url_photo)

    if response.status_code != 200:
        logger.error(f"Ошибка при получении картинки: {response.status_code}")
        raise Exception(f"Ошибка при получении картинки: {response.status_code}")
    data = response.json()
    image_url = data['url']
    filename = f"{text}_{data['id']}.jpg"
    logger.info(f"Картинка получена, URL: {image_url}")
    return image_url, filename

def check_or_create_yadisk_folder(token, folder_path):
    """
    Проверяет есть ли нужная папка, если ее нет, то создает папку с заданным именем
    """
    url_check = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {'Authorization': f'OAuth {token}'}
    params = {'path': folder_path}

    logger.info(f"Проверяю наличие папки '{folder_path}'...")
    response = requests.get(url_check, headers=headers, params=params)
    if response.status_code == 404:
        logger.warning(f"Папка '{folder_path}' не найдена, создаю новую...")
        response = requests.put(url_check, headers=headers, params=params)
        if response.status_code != 201:
            logger.critical(f"Ошибка при создании папки: {response.status_code}, {response.text}")
            raise Exception(f"Ошибка при создании папки: {response.status_code}, {response.text}")
    elif response.status_code != 200:
        logger.error(f"Ошибка при проверке папки: {response.status_code}, {response.text}")
        raise Exception(f"Ошибка при проверке папки: {response.status_code}, {response.text}")

    logger.info(f"Папка '{folder_path}' доступна.")

def upload_to_yadisk(token, local_filename, remote_path, image_url):
    """
    Загружает файл на яндекс диск
    """
    url_get_upload_link = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    headers = {'Authorization': f'OAuth {token}'}
    params = {'path': remote_path, 'url': image_url, 'overwrite': True}
    logger.info(f"Начинаю загрузку файла '{local_filename}' на Яндекс.Диск...")
    response = requests.post(url_get_upload_link, headers=headers, params=params)

    if response.status_code not in (201, 202):
        logger.error(f"Ошибка при загрузке файла: {response.status_code}, {response.text}")
        raise Exception(f"Ошибка при загрузке файла: {response.status_code}, {response.text}")

    logger.info(f"Файл '{local_filename}' успешно загружен на Яндекс.Диск.")


def list_and_safe_json(token, folder_path):
    """
    Записывает данные в файл сontent.json
    """
    url = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {'Authorization': f'OAuth {token}'}
    params = {'path': folder_path}

    logger.info(f"Получаю список файлов в папке '{folder_path}'...")
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        logger.error(f"Ошибка при получении списка файлов: {response.status_code}, {response.text}")
        raise Exception(f"Ошибка при получении списка файлов: {response.status_code}, {response.text}")

    content = response.json()
    items = content.get('_embedded', {}).get('items', [])
    content_json = [
        {'file_name': item['name'], 'file_size': item['size']} for item in items
    ]

    with open('content.json', 'w', encoding='utf-8') as f:
        json.dump(content_json, f, indent=4)

    logger.info(f"Данные о файлах сохранены в content.json.")


if __name__ == '__main__':
    try:
        text = input('Введите текст для картинки: ')
        token = input('Введите токен для Яндекс.Диска: ').strip()
        group_name = 'pd-fpy_138'

        image_url, picture_filename = get_url_image(text)
        check_or_create_yadisk_folder(token, group_name)
        upload_to_yadisk(token, picture_filename, f"{group_name}/{picture_filename}", image_url)
        list_and_safe_json(token, group_name)
        logger.info("Операция выполнена успешно.")
    except Exception as e:
        logger.exception(f"Возникла непредвиденная ошибка: {e}")
        sys.exit(1)




