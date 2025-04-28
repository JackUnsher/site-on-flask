import asyncio
import websockets
import json
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Изменено с INFO на DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def handle_client(websocket):
    """Обработчик подключений клиентов"""
    client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"Новое подключение от клиента {client_info}")
    try:
        async for message in websocket:
            try:
                # Парсим сообщение от Figma
                data = json.loads(message)
                logger.info(f"Получено сообщение от {client_info}: {data}")
                
                # Проверяем тип сообщения
                if data.get('type') == 'join_channel':
                    channel_id = data.get('channel_id')
                    logger.info(f"Клиент {client_info} присоединился к каналу {channel_id}")
                    response = {
                        "type": "channel_joined",
                        "status": "ok",
                        "channel_id": channel_id
                    }
                else:
                    response = {
                        "type": "message_received",
                        "status": "ok",
                        "message": "Сообщение получено"
                    }
                
                await websocket.send(json.dumps(response))
                logger.debug(f"Отправлен ответ клиенту {client_info}: {response}")
                
            except json.JSONDecodeError as e:
                logger.error(f"Получено некорректное JSON-сообщение от {client_info}: {str(e)}")
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": "Некорректный формат JSON"
                }))
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Клиент {client_info} отключился: {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения от {client_info}: {str(e)}")

async def main():
    """Основная функция запуска сервера"""
    host = "0.0.0.0"
    port = 8765
    
    logger.info(f"Запуск WebSocket сервера на ws://{host}:{port}")
    
    try:
        async with websockets.serve(handle_client, host, port) as server:
            logger.info("Сервер успешно запущен и ожидает подключений")
            await asyncio.Future()  # Бесконечное выполнение
    except Exception as e:
        logger.error(f"Ошибка при запуске сервера: {str(e)}")

if __name__ == "__main__":
    try:
        logger.info("Инициализация WebSocket сервера...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Сервер остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка сервера: {str(e)}") 