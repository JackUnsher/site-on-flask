#!/usr/bin/env python
"""
WebSocket сервер на Python для Cursor MCP
"""

import os
import sys
import json
import logging
import asyncio
import websockets
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ws_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ws_server")

# Константы
HOST = "localhost"
PORT = 8083
ASSETS_DIR = "app/static/assets"

# Хранилище для каналов и подключений
channels = {}
clients = {}

async def handle_client(websocket):
    """Обработчик подключения клиента"""
    client_id = id(websocket)
    clients[client_id] = {
        "websocket": websocket,
        "channel": None,
        "type": None
    }
    
    logger.info(f"Новое подключение: {client_id}")
    
    try:
        # Отправляем приветственное сообщение
        await websocket.send(json.dumps({
            "type": "welcome",
            "message": "Добро пожаловать на сервер Cursor MCP! Используйте команду join для подключения к каналу."
        }))
        
        # Основной цикл обработки сообщений
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type", "unknown")
                logger.info(f"Получено сообщение типа {msg_type} от клиента {client_id}")
                
                # Обработка команды join
                if msg_type == "join":
                    channel_name = data.get("channel")
                    client_type = data.get("client", "unknown")
                    
                    if not channel_name:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Не указано имя канала"
                        }))
                        continue
                    
                    # Создаем канал, если он не существует
                    if channel_name not in channels:
                        channels[channel_name] = []
                    
                    # Добавляем клиента в канал
                    channels[channel_name].append(client_id)
                    clients[client_id]["channel"] = channel_name
                    clients[client_id]["type"] = client_type
                    
                    logger.info(f"Клиент {client_id} ({client_type}) присоединился к каналу {channel_name}")
                    
                    # Отправляем подтверждение
                    await websocket.send(json.dumps({
                        "type": "joined",
                        "channel": channel_name,
                        "client": client_type,
                        "message": f"Успешно подключен к каналу {channel_name} как {client_type}"
                    }))
                
                # Обработка экспорта изображения
                elif msg_type in ["export-item", "export-data"]:
                    save_path = await handle_export_data(data)
                    if save_path:
                        logger.info(f"Сохранено изображение: {save_path}")
                
                # Пересылка сообщения другим клиентам в канале
                await broadcast_message(client_id, data)
                
            except json.JSONDecodeError:
                logger.error(f"Ошибка декодирования JSON от клиента {client_id}")
            except Exception as e:
                logger.error(f"Ошибка обработки сообщения: {str(e)}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Соединение с клиентом {client_id} закрыто")
    finally:
        # Удаляем клиента из всех каналов
        channel_name = clients[client_id]["channel"]
        if channel_name and channel_name in channels:
            if client_id in channels[channel_name]:
                channels[channel_name].remove(client_id)
            
            # Удаляем пустой канал
            if not channels[channel_name]:
                del channels[channel_name]
        
        # Удаляем клиента
        if client_id in clients:
            del clients[client_id]
        
        logger.info(f"Клиент {client_id} отключен")

async def broadcast_message(sender_id, message):
    """Отправка сообщения всем клиентам в канале, кроме отправителя"""
    if sender_id not in clients:
        return
    
    channel_name = clients[sender_id]["channel"]
    if not channel_name or channel_name not in channels:
        return
    
    message["sender"] = clients[sender_id]["type"]
    
    for client_id in channels[channel_name]:
        if client_id != sender_id:
            try:
                await clients[client_id]["websocket"].send(json.dumps(message))
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения клиенту {client_id}: {str(e)}")

async def handle_export_data(data):
    """Обработка экспортированных данных"""
    try:
        if data["type"] == "export-item":
            return await save_exported_image(data["data"])
        elif data["type"] == "export-data" and isinstance(data["data"], list):
            paths = []
            for item in data["data"]:
                path = await save_exported_image(item)
                if path:
                    paths.append(path)
            return paths
    except Exception as e:
        logger.error(f"Ошибка обработки экспорта: {str(e)}")
    return None

async def save_exported_image(image_data):
    """Сохранение экспортированного изображения"""
    if not image_data or "bytes" not in image_data:
        logger.error("Некорректные данные изображения")
        return None
    
    try:
        # Создаем директорию для сохранения, если её нет
        assets_dir = Path(ASSETS_DIR)
        if not assets_dir.exists():
            assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Формируем имя файла
        node_name = image_data.get("nodeName", "image")
        img_format = image_data.get("format", "png").lower()
        
        # Очистка имени файла от недопустимых символов
        import re
        sanitized_name = re.sub(r'[^\w\-_.]', '_', node_name).lower()
        
        # Добавляем временную метку и размеры
        import time
        filename = f"{sanitized_name}_{int(time.time())}.{img_format}"
        file_path = assets_dir / filename
        
        # Конвертируем массив байтов в бинарные данные
        img_bytes = bytes(image_data["bytes"])
        
        # Сохраняем файл
        with open(file_path, "wb") as f:
            f.write(img_bytes)
        
        # Относительный путь для использования в коде
        relative_path = f"/static/assets/{filename}"
        logger.info(f"Изображение сохранено: {relative_path}")
        
        return relative_path
        
    except Exception as e:
        logger.error(f"Ошибка сохранения изображения: {str(e)}")
        return None

async def main():
    """Основная функция запуска сервера"""
    try:
        # Создаем директорию для assets, если её нет
        assets_dir = Path(ASSETS_DIR)
        if not assets_dir.exists():
            assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Запускаем сервер
        async with websockets.serve(handle_client, HOST, PORT):
            logger.info(f"WebSocket сервер запущен на ws://{HOST}:{PORT}")
            logger.info("Нажмите Ctrl+C для остановки...")
            
            # Держим сервер работающим
            await asyncio.Future()
    
    except Exception as e:
        logger.error(f"Ошибка запуска сервера: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {str(e)}")
        sys.exit(1) 