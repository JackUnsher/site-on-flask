#!/usr/bin/env python
"""
Cursor MCP Python Handler для интеграции с Figma
Этот скрипт обрабатывает сообщения от WebSocket сервера и Cursor
"""

import os
import sys
import json
import time
import base64
import logging
import websocket
import threading
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mcp_figma.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("cursor_mcp")

# Константы
WS_SERVER = "ws://localhost:8080"
CHANNEL = "cursor_mcp"
CLIENT_TYPE = "cursor"
ASSETS_DIR = "app/static/assets"


class CursorFigmaHandler:
    """Обработчик для связи между Cursor и Figma через WebSocket"""
    
    def __init__(self, ws_url=WS_SERVER, channel=CHANNEL, client_type=CLIENT_TYPE):
        self.ws_url = ws_url
        self.channel = channel
        self.client_type = client_type
        self.ws = None
        self.connected = False
        self.assets_dir = self._ensure_assets_dir()
        self.image_cache = {}  # Кэш для хранения экспортированных изображений
        
    def _ensure_assets_dir(self):
        """Создает директорию assets, если она не существует"""
        assets_path = Path(ASSETS_DIR)
        if not assets_path.exists():
            assets_path.mkdir(parents=True, exist_ok=True)
        return assets_path
    
    def connect(self):
        """Подключение к WebSocket серверу"""
        try:
            # Определяем обработчики событий WebSocket
            self.ws = websocket.WebSocketApp(
                self.ws_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            # Запускаем WebSocket в отдельном потоке
            self.ws_thread = threading.Thread(target=self.ws.run_forever)
            self.ws_thread.daemon = True
            self.ws_thread.start()
            
            logger.info(f"Подключение к {self.ws_url}")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения: {str(e)}")
            return False
    
    def on_open(self, ws):
        """Обработчик события открытия соединения WebSocket"""
        logger.info("WebSocket соединение установлено")
        self.connected = True
        
        # Отправляем запрос на присоединение к каналу
        self.join_channel()
    
    def join_channel(self):
        """Присоединение к каналу для коммуникации с Figma"""
        if not self.connected:
            logger.error("Невозможно присоединиться к каналу: нет соединения")
            return False
        
        join_message = {
            "type": "join",
            "channel": self.channel,
            "client": self.client_type
        }
        
        self.ws.send(json.dumps(join_message))
        logger.info(f"Запрос на присоединение к каналу {self.channel} отправлен")
        return True
    
    def on_message(self, ws, message):
        """Обработчик входящих сообщений"""
        try:
            data = json.loads(message)
            logger.info(f"Получено сообщение типа: {data.get('type', 'unknown')}")
            
            # Обработка различных типов сообщений
            if data.get("type") == "joined":
                logger.info(f"Успешно присоединились к каналу: {data.get('channel')}")
            
            elif data.get("type") == "export-item-complete":
                self.handle_exported_image(data.get("data"))
            
            elif data.get("type") == "export-complete":
                logger.info(f"Экспорт завершен: {data.get('totalExported')} элементов")
            
            elif data.get("type") == "error":
                logger.error(f"Ошибка от сервера: {data.get('message')}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {str(e)}")
    
    def on_error(self, ws, error):
        """Обработчик ошибок WebSocket"""
        logger.error(f"WebSocket ошибка: {str(error)}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """Обработчик закрытия соединения WebSocket"""
        self.connected = False
        logger.info(f"WebSocket соединение закрыто: {close_status_code} - {close_msg}")
    
    def handle_exported_image(self, data):
        """Обработка экспортированного изображения"""
        if not data:
            logger.error("Пустые данные изображения")
            return
        
        try:
            node_id = data.get("nodeId")
            node_name = data.get("nodeName", "image")
            img_format = data.get("format", "png").lower()
            img_width = data.get("width", 0)
            img_height = data.get("height", 0)
            img_bytes = data.get("bytes")
            
            if not img_bytes:
                logger.error("Отсутствуют байты изображения")
                return
            
            # Формируем имя файла и путь
            sanitized_name = self._sanitize_filename(node_name)
            filename = f"{sanitized_name}_{int(time.time())}_{img_width}x{img_height}.{img_format}"
            filepath = self.assets_dir / filename
            
            # Конвертируем байты изображения и сохраняем
            img_data = bytes(img_bytes)
            with open(filepath, "wb") as f:
                f.write(img_data)
            
            relative_path = f"/static/assets/{filename}"
            logger.info(f"Изображение сохранено: {relative_path}")
            
            # Сохраняем в кэше
            self.image_cache[node_id] = {
                "path": relative_path,
                "width": img_width,
                "height": img_height,
                "format": img_format,
                "name": node_name
            }
            
            return relative_path
        
        except Exception as e:
            logger.error(f"Ошибка обработки изображения: {str(e)}")
            return None
    
    def _sanitize_filename(self, filename):
        """Очистка имени файла от недопустимых символов"""
        import re
        # Заменяем все не-алфавитно-цифровые символы на underscore
        return re.sub(r'[^\w\-_.]', '_', filename).lower()
    
    def request_document_info(self):
        """Запрос информации о текущем документе Figma"""
        if not self.connected:
            logger.error("Невозможно отправить запрос: нет соединения")
            return False
        
        message = {
            "type": "get-document-info"
        }
        
        self.ws.send(json.dumps(message))
        logger.info("Запрос информации о документе отправлен")
        return True
    
    def scan_for_images(self):
        """Запрос на сканирование изображений в Figma"""
        if not self.connected:
            logger.error("Невозможно отправить запрос: нет соединения")
            return False
        
        message = {
            "type": "scan-for-images"
        }
        
        self.ws.send(json.dumps(message))
        logger.info("Запрос на сканирование изображений отправлен")
        return True
    
    def export_all_images(self, format="PNG", scale=1):
        """Запрос на экспорт всех изображений"""
        if not self.connected:
            logger.error("Невозможно отправить запрос: нет соединения")
            return False
        
        message = {
            "type": "export-all-images",
            "format": format,
            "scale": scale
        }
        
        self.ws.send(json.dumps(message))
        logger.info(f"Запрос на экспорт всех изображений отправлен (формат: {format}, масштаб: {scale})")
        return True
    
    def close(self):
        """Закрытие соединения"""
        if self.ws:
            self.ws.close()
            logger.info("WebSocket соединение закрыто")
    
    def get_cached_images(self):
        """Получение списка кэшированных изображений"""
        return self.image_cache


def main():
    """Основная функция для запуска обработчика"""
    logger.info("Запуск Cursor MCP Python Handler")
    
    handler = CursorFigmaHandler()
    if handler.connect():
        try:
            # Ожидаем успешного подключения
            time.sleep(2)
            
            # Сканируем изображения
            if len(sys.argv) > 1 and sys.argv[1] == "scan":
                handler.scan_for_images()
            
            # Экспортируем изображения
            if len(sys.argv) > 1 and sys.argv[1] == "export":
                format = "PNG"
                scale = 1
                if len(sys.argv) > 2:
                    format = sys.argv[2]
                if len(sys.argv) > 3:
                    scale = float(sys.argv[3])
                handler.export_all_images(format, scale)
            
            # Держим процесс работающим
            while True:
                time.sleep(1)
        
        except KeyboardInterrupt:
            logger.info("Завершение работы по запросу пользователя")
        finally:
            handler.close()
    else:
        logger.error("Не удалось подключиться к WebSocket серверу")


if __name__ == "__main__":
    main() 