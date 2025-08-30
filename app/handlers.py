import base64
from django.core.files.base import ContentFile
from django.conf import settings
import os 
def save_signature_from_base64(signature_data, user):
    """
    Сохраняет подпись пользователя из строки Base64 в файл
    и присваивает его пользователю.
    """
    # Убираем префикс 'data:image/png;base64,' из строки
    format, imgstr = signature_data.split(';base64,')
    
    # Декодируем изображение из Base64 в бинарные данные
    img_data = base64.b64decode(imgstr)
    
    # Создаем файл с подписью в формате ContentFile
    img_file = ContentFile(img_data, name='signature.png')
    if os.path.isfile(f'./static/signatures/{user.username}_signature.png'):
        os.remove(f'./static/signatures/{user.username}_signature.png')
    # Сохраняем файл в поле signature модели пользователя
    user.signature.save(f"{user.username}_signature.png", img_file)

    # Сохраняем изменения в базе данных
    user.save()

