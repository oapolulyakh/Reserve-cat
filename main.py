import sys
import time

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
    logger.info(f"I get a picture with text '{text}'...")
    response = requests.get(url_photo)

    if response.status_code != 200:
        logger.error(f"Error when receiving an image: {response.status_code}")
        raise Exception(f"Error when receiving an image: {response.status_code}")
    data = response.json()
    image_url = data['url']
    filename = f"{text}_{data['id']}.jpg"
    logger.info(f"Image received URL: {image_url}")
    return image_url, filename

def check_or_create_yadisk_folder(token, folder_path):
    """
    Проверяет есть ли нужная папка, если ее нет, то создает папку с заданным именем
    """
    url_check = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {'Authorization': f'OAuth {token}'}
    params = {'path': folder_path}

    logger.info(f" Checking for a folder '{folder_path}'...")
    response = requests.get(url_check, headers=headers, params=params)
    if response.status_code == 404:
        logger.warning(f"Folder '{folder_path}' was not found, I'm creating a new one...")
        response = requests.put(url_check, headers=headers, params=params)
        if response.status_code != 201:
            logger.critical(f"Error when creating a folder: {response.status_code}, {response.text}")
            raise Exception(f"Error when creating a folder: {response.status_code}, {response.text}")
    elif response.status_code != 200:
        logger.error(f"Error checking the folder: {response.status_code}, {response.text}")
        raise Exception(f"Error checking the folder: {response.status_code}, {response.text}")

    logger.info(f"The folder '{folder_path}' is available.")

def wait_finish_upload(token, remote_path):
    """
        Ждёт, пока файл будет загружен на Яндекс.Диск.
        """
    url = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {'Authorization': f'OAuth {token}'}
    params = {'path': remote_path}
    while True:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            break
        elif response.status_code == 404:
            pass
        else:
            logger.error(f"Error during waiting for file upload: {response.status_code}, {response.text}")
            raise Exception(f"Error during waiting for file upload: {response.status_code}, {response.text}")
        time.sleep(2)
        logger.info(f"File '{remote_path}' is now available on Yandex.Disk.")

def upload_to_yadisk(token, local_filename, remote_path, image_url):
    """
    Загружает файл на яндекс диск
    """
    url_get_upload_link = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    headers = {'Authorization': f'OAuth {token}'}
    params = {'path': remote_path, 'url': image_url, 'overwrite': True}
    logger.info(f"I'm starting to upload the '{local_filename}' to Yandex.Disk...")
    response = requests.post(url_get_upload_link, headers=headers, params=params)

    if response.status_code not in (201,202):
        logger.error(f"Error when uploading a file: {response.status_code}, {response.text}")
        raise Exception(f"Error when uploading a file: {response.status_code}, {response.text}")

    wait_finish_upload(token, remote_path)

    logger.info(f"The file '{local_filename}' has been successfully uploaded to Yandex.Disk.")


def list_and_safe_json(token, folder_path):
    """
    Записывает данные в файл сontent.json
    """
    url = 'https://cloud-api.yandex.net/v1/disk/resources'
    headers = {'Authorization': f'OAuth {token}'}
    params = {'path': folder_path}

    logger.info(f"I get a list of files in the folder '{folder_path}'...")
    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        logger.error(f"Error when getting the file list: {response.status_code}, {response.text}")
        raise Exception(f"Error when getting the file list: {response.status_code}, {response.text}")

    content = response.json()
    items = content.get('_embedded', {}).get('items', [])
    content_json = [
        {'file_name': item['name'], 'file_size': item['size']} for item in items
    ]

    with open('content.json', 'w', encoding='utf-8') as f:
        json.dump(content_json, f, indent=4)

    logger.info(f"The file data is saved in content.json.")


if __name__ == '__main__':
    try:
        text = input('Введите текст для картинки: ')
        token = input('Введите токен для Яндекс.Диска: ').strip()
        group_name = 'pd-fpy_138'

        image_url, picture_filename = get_url_image(text)
        check_or_create_yadisk_folder(token, group_name)
        upload_to_yadisk(token, picture_filename, f"{group_name}/{picture_filename}", image_url)
        list_and_safe_json(token, group_name)
        logger.info("The operation was completed successfully.")
    except Exception as e:
        logger.exception(f"An unexpected error has occurred: {e}")
        sys.exit(1)




