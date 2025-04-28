// WebSocket-сервер для связи между Figma и Cursor MCP
const WebSocket = require('ws');
const http = require('http');
const fs = require('fs');
const path = require('path');

// Настройки сервера
const PORT = process.env.PORT || 8080;
const HOSTNAME = process.env.HOSTNAME || 'localhost';

// Создаем HTTP сервер
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Cursor MCP WebSocket Server\n');
});

// Создаем WebSocket сервер
const wss = new WebSocket.Server({ server });

// Хранилище для каналов и подключений
const channels = new Map();

// Обработка WebSocket соединений
wss.on('connection', (ws) => {
  console.log('Новое соединение установлено');
  
  let channelName = '';
  let clientType = '';
  
  // Обработка сообщений
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      console.log('Получено сообщение:', data.type);
      
      // Обработка команды join
      if (data.type === 'join') {
        channelName = data.channel;
        clientType = data.client;
        
        console.log(`Клиент ${clientType} подключился к каналу ${channelName}`);
        
        // Создаем канал, если он не существует
        if (!channels.has(channelName)) {
          channels.set(channelName, new Map());
        }
        
        // Регистрируем клиента в канале
        const channel = channels.get(channelName);
        channel.set(ws, clientType);
        
        // Отправляем подтверждение подключения
        ws.send(JSON.stringify({
          type: 'joined',
          channel: channelName,
          client: clientType,
          message: `Успешно подключен к каналу ${channelName} как ${clientType}`
        }));
        
        return;
      }
      
      // Если канал не указан, выдаем ошибку
      if (!channelName) {
        ws.send(JSON.stringify({
          type: 'error',
          message: 'Необходимо сначала подключиться к каналу используя команду join'
        }));
        return;
      }
      
      // Обработчики специальных сообщений
      if (data.type === 'export-item' || data.type === 'export-data') {
        handleExportData(data, channelName, clientType);
      }
      
      // Отправляем сообщение всем клиентам в канале, кроме отправителя
      const channel = channels.get(channelName);
      if (channel) {
        channel.forEach((type, client) => {
          if (client !== ws && client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify({
              ...data,
              sender: clientType
            }));
          }
        });
      }
      
    } catch (error) {
      console.error('Ошибка обработки сообщения:', error);
      ws.send(JSON.stringify({
        type: 'error',
        message: `Ошибка обработки сообщения: ${error.message}`
      }));
    }
  });
  
  // Обработка отключения
  ws.on('close', () => {
    console.log(`Клиент ${clientType} отключился от канала ${channelName}`);
    
    // Удаляем клиента из канала
    if (channelName && channels.has(channelName)) {
      const channel = channels.get(channelName);
      channel.delete(ws);
      
      // Если канал пуст, удаляем его
      if (channel.size === 0) {
        channels.delete(channelName);
        console.log(`Канал ${channelName} удален, так как нет подключенных клиентов`);
      }
    }
  });
  
  // Отправляем приветственное сообщение
  ws.send(JSON.stringify({
    type: 'welcome',
    message: 'Добро пожаловать на сервер Cursor MCP! Используйте команду join для подключения к каналу.'
  }));
});

// Обработка экспортированных данных
function handleExportData(data, channelName, clientType) {
  if (data.type === 'export-item') {
    saveExportedImage(data.data);
  } else if (data.type === 'export-data') {
    // Для массового экспорта
    if (Array.isArray(data.data)) {
      data.data.forEach(item => {
        saveExportedImage(item);
      });
    }
  }
}

// Сохранение экспортированного изображения
function saveExportedImage(imageData) {
  if (!imageData || !imageData.bytes) {
    console.error('Некорректные данные изображения');
    return;
  }
  
  // Создаем директорию для сохранения, если её нет
  const assetsDir = path.join(process.cwd(), 'app', 'static', 'assets');
  if (!fs.existsSync(assetsDir)) {
    fs.mkdirSync(assetsDir, { recursive: true });
  }
  
  // Формируем имя файла
  const fileName = sanitizeFilename(imageData.nodeName) + '_' + Date.now() + '.' + imageData.format.toLowerCase();
  const filePath = path.join(assetsDir, fileName);
  
  // Конвертируем массив байтов обратно в бинарные данные
  const buffer = Buffer.from(imageData.bytes);
  
  // Сохраняем файл
  fs.writeFile(filePath, buffer, (err) => {
    if (err) {
      console.error('Ошибка сохранения файла:', err);
      return;
    }
    
    console.log(`Изображение сохранено: ${filePath}`);
    
    // Относительный путь для использования в коде
    const relativePath = '/static/assets/' + fileName;
    console.log(`Относительный путь: ${relativePath}`);
  });
}

// Очистка имени файла от недопустимых символов
function sanitizeFilename(filename) {
  return filename.replace(/[^a-z0-9]/gi, '_').toLowerCase();
}

// Запуск сервера
server.listen(PORT, HOSTNAME, () => {
  console.log(`Сервер WebSocket запущен на http://${HOSTNAME}:${PORT}`);
  console.log('Ожидание подключений...');
}); 