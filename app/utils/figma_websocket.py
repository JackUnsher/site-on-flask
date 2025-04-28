import asyncio
import json
import logging
import os
from datetime import datetime
import websockets

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('figma_websocket')

# Словарь для хранения подключенных клиентов по каналам
connected_clients = {}
command_results = {}


async def register_client(websocket, channel_id):
    """Регистрирует клиента в указанном канале"""
    if channel_id not in connected_clients:
        connected_clients[channel_id] = set()
    connected_clients[channel_id].add(websocket)
    logger.info(f"Client registered to channel: {channel_id}")


async def unregister_client(websocket):
    """Удаляет клиента из всех каналов"""
    for channel_id in list(connected_clients.keys()):
        if websocket in connected_clients[channel_id]:
            connected_clients[channel_id].remove(websocket)
            logger.info(f"Client unregistered from channel: {channel_id}")
            
            # Если канал пуст, удаляем его
            if len(connected_clients[channel_id]) == 0:
                del connected_clients[channel_id]


async def send_command(channel_id, command, params=None):
    """Отправляет команду всем клиентам в канале и ожидает результат"""
    if channel_id not in connected_clients or not connected_clients[channel_id]:
        logger.error(f"No clients in channel: {channel_id}")
        return {"error": f"No clients in channel: {channel_id}"}
    
    # Создаем уникальный ID для команды
    command_id = f"{command}_{datetime.now().timestamp()}"
    
    # Создаем объект Future для получения результата
    command_results[command_id] = asyncio.Future()
    
    # Формируем сообщение команды
    message = {
        "type": "command",
        "id": command_id,
        "command": command,
        "params": params or {}
    }
    
    # Отправляем команду всем клиентам в канале
    websockets_to_remove = set()
    for websocket in connected_clients[channel_id]:
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            websockets_to_remove.add(websocket)
    
    # Удаляем закрытые соединения
    for websocket in websockets_to_remove:
        await unregister_client(websocket)
    
    try:
        # Ожидаем результат с таймаутом
        result = await asyncio.wait_for(command_results[command_id], timeout=30.0)
        return result
    except asyncio.TimeoutError:
        logger.error(f"Command {command_id} timed out")
        return {"error": "Command timed out"}
    finally:
        # Удаляем Future из словаря
        if command_id in command_results:
            del command_results[command_id]


async def handle_message(websocket, message):
    """Обрабатывает входящие сообщения от клиентов"""
    try:
        data = json.loads(message)
        message_type = data.get('type')
        
        if message_type == 'join_channel':
            channel_id = data.get('channel_id')
            if channel_id:
                await register_client(websocket, channel_id)
                await websocket.send(json.dumps({
                    "type": "channel_joined",
                    "channel_id": channel_id
                }))
            else:
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "Channel ID is required"
                }))
        
        elif message_type == 'command_result':
            command_id = data.get('id')
            if command_id and command_id in command_results:
                result = {
                    "success": data.get('success', False)
                }
                
                if result["success"]:
                    result["result"] = data.get('result')
                else:
                    result["error"] = data.get('error')
                
                command_results[command_id].set_result(result)
            else:
                logger.warning(f"Received result for unknown command: {command_id}")
        
        else:
            logger.warning(f"Unknown message type: {message_type}")
    
    except json.JSONDecodeError:
        logger.error("Failed to parse message as JSON")
        await websocket.send(json.dumps({
            "type": "error",
            "message": "Invalid JSON"
        }))


async def handle_client(websocket, path):
    """Обрабатывает подключение клиента"""
    logger.info(f"Client connected")
    
    try:
        async for message in websocket:
            await handle_message(websocket, message)
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    finally:
        await unregister_client(websocket)


async def start_server(host='localhost', port=8765):
    """Запускает WebSocket сервер"""
    server = await websockets.serve(handle_client, host, port)
    logger.info(f"WebSocket server started at ws://{host}:{port}")
    return server


def get_websocket_url():
    """Возвращает URL для WebSocket сервера из переменных окружения"""
    return os.environ.get('FIGMA_SOCKET_URL', 'ws://localhost:8765')


def get_channel_id():
    """Возвращает ID канала из переменных окружения"""
    return os.environ.get('FIGMA_CHANNEL', 'figma-channel') 