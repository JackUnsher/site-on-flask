/**
 * Cursor MCP Server
 * Двусторонний WebSocket сервер для автоматической синхронизации между Figma и Cursor IDE
 */

const WebSocket = require('ws');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// Конфигурация
const CONFIG = {
  PORT: 9912,
  ASSETS_DIR: path.join(process.cwd(), 'assets'),
  COMPONENTS_DIR: path.join(process.cwd(), 'components'),
  HTML_TEMPLATES_DIR: path.join(process.cwd(), 'templates'),
  STYLES_DIR: path.join(process.cwd(), 'static/css')
};

// Создаем необходимые директории, если они не существуют
function ensureDirectoriesExist() {
  [CONFIG.ASSETS_DIR, CONFIG.COMPONENTS_DIR, CONFIG.HTML_TEMPLATES_DIR, CONFIG.STYLES_DIR].forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
      console.log(`Создана директория: ${dir}`);
    }
  });
}

// Инициализация WebSocket сервера
function initWebSocketServer() {
  const wss = new WebSocket.Server({ port: CONFIG.PORT });
  
  console.log(`WebSocket сервер запущен на порту ${CONFIG.PORT}`);
  
  wss.on('connection', (ws) => {
    console.log('Новое соединение');
    
    ws.isAlive = true;
    ws.send(JSON.stringify({
      type: 'connected',
      message: 'Подключено к Cursor MCP серверу',
      version: '1.0.0'
    }));
    
    // Пинг для проверки активности соединения
    ws.on('pong', () => {
      ws.isAlive = true;
    });
    
    // Обработка сообщений от клиента
    ws.on('message', async (message) => {
      try {
        const data = JSON.parse(message);
        console.log(`Получено сообщение типа: ${data.type}`);
        
        // Обработка различных типов сообщений
        switch (data.type) {
          case 'hello':
            handleHello(ws, data);
            break;
            
          case 'structure-data':
            await handleStructureData(ws, data);
            break;
            
          case 'import-images':
            await handleImportImages(ws, data);
            break;
            
          case 'sync-start':
            handleSyncStart(ws, data);
            break;
            
          case 'sync-stop':
            handleSyncStop(ws, data);
            break;
            
          default:
            console.log(`Неизвестный тип сообщения: ${data.type}`);
            ws.send(JSON.stringify({
              type: 'error',
              message: `Неизвестный тип сообщения: ${data.type}`
            }));
        }
      } catch (error) {
        console.error('Ошибка обработки сообщения:', error);
        ws.send(JSON.stringify({
          type: 'error',
          message: `Ошибка обработки сообщения: ${error.message}`
        }));
      }
    });
    
    // Обработка закрытия соединения
    ws.on('close', () => {
      console.log('Соединение закрыто');
    });
    
    // Обработка ошибок
    ws.on('error', (error) => {
      console.error('Ошибка WebSocket:', error);
    });
  });
  
  // Интервал проверки соединений
  const interval = setInterval(() => {
    wss.clients.forEach((ws) => {
      if (ws.isAlive === false) return ws.terminate();
      
      ws.isAlive = false;
      ws.ping();
    });
  }, 30000);
  
  // Очистка интервала при закрытии сервера
  wss.on('close', () => {
    clearInterval(interval);
  });
  
  return wss;
}

// Обработчики сообщений

// Обработка приветственного сообщения
function handleHello(ws, data) {
  console.log(`Клиент представился: ${data.client}, версия: ${data.version}`);
  ws.send(JSON.stringify({
    type: 'hello',
    message: 'Привет от Cursor MCP сервера',
    version: '1.0.0'
  }));
}

// Обработка данных о структуре дизайна
async function handleStructureData(ws, data) {
  console.log('Получены данные о структуре дизайна');
  
  if (!data.data) {
    return ws.send(JSON.stringify({
      type: 'error',
      message: 'Отсутствуют данные о структуре'
    }));
  }
  
  try {
    // Сохраняем полную структуру для дальнейшего использования
    const structureFile = path.join(CONFIG.ASSETS_DIR, 'structure.json');
    fs.writeFileSync(structureFile, JSON.stringify(data.data, null, 2));
    
    console.log(`Структура сохранена в ${structureFile}`);
    
    // Анализируем структуру для создания компонентов
    const { htmlCode, cssCode } = await analyzeAndGenerateCode(data.data);
    
    // Сохраняем сгенерированный HTML и CSS
    if (htmlCode) {
      const htmlOutputPath = path.join(CONFIG.HTML_TEMPLATES_DIR, 'generated.html');
      fs.writeFileSync(htmlOutputPath, htmlCode);
      console.log(`HTML сохранен в ${htmlOutputPath}`);
    }
    
    if (cssCode) {
      const cssOutputPath = path.join(CONFIG.STYLES_DIR, 'generated.css');
      fs.writeFileSync(cssOutputPath, cssCode);
      console.log(`CSS сохранен в ${cssOutputPath}`);
    }
    
    // Отправляем ответ
    ws.send(JSON.stringify({
      type: 'structure-processed',
      message: 'Структура успешно обработана',
      outputs: {
        html: htmlCode ? 'generated.html' : null,
        css: cssCode ? 'generated.css' : null
      }
    }));
    
  } catch (error) {
    console.error('Ошибка обработки структуры:', error);
    ws.send(JSON.stringify({
      type: 'error',
      message: `Ошибка обработки структуры: ${error.message}`
    }));
  }
}

// Анализ структуры и генерация кода
async function analyzeAndGenerateCode(structure) {
  console.log('Анализ структуры и генерация кода...');
  
  // Определение основных секций (header, main content, footer)
  const sections = identifySections(structure);
  
  // Генерация HTML
  const htmlCode = generateHTML(sections);
  
  // Генерация CSS
  const cssCode = generateCSS(sections);
  
  return { htmlCode, cssCode };
}

// Определение основных секций макета
function identifySections(structure) {
  const sections = {
    header: null,
    content: [],
    footer: null,
    background: null
  };
  
  // Простая эвристика для определения частей макета
  // В реальном проекте здесь будет более сложная логика анализа
  
  if (structure && structure.children && Array.isArray(structure.children)) {
    // Сортируем узлы по вертикальной позиции
    const sortedNodes = [...structure.children].sort((a, b) => {
      return a.position.y - b.position.y;
    });
    
    // Фоновый элемент обычно занимает весь размер или большую часть макета
    const possibleBackgrounds = structure.children.filter(node => {
      const nodeArea = node.size.width * node.size.height;
      const totalArea = structure.size ? (structure.size.width * structure.size.height) : 0;
      
      return (totalArea > 0) && (nodeArea / totalArea > 0.8) && 
             (node.type === 'RECTANGLE' || node.type === 'FRAME');
    });
    
    if (possibleBackgrounds.length > 0) {
      sections.background = possibleBackgrounds[0];
    }
    
    // Шапка обычно находится вверху
    if (sortedNodes.length > 0) {
      const firstNode = sortedNodes[0];
      if (firstNode.position.y < 100 && firstNode.size.height < 200) {
        sections.header = firstNode;
      }
    }
    
    // Футер обычно находится внизу
    if (sortedNodes.length > 0) {
      const lastNode = sortedNodes[sortedNodes.length - 1];
      if (sortedNodes.length > 1 && lastNode.position.y > sortedNodes[sortedNodes.length - 2].position.y + 100) {
        sections.footer = lastNode;
      }
    }
    
    // Остальные элементы считаем контентом
    sortedNodes.forEach(node => {
      if (node !== sections.header && node !== sections.footer && node !== sections.background) {
        sections.content.push(node);
      }
    });
  }
  
  return sections;
}

// Генерация HTML кода на основе анализа структуры
function generateHTML(sections) {
  let html = `<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Generated from Figma</title>
  <link rel="stylesheet" href="static/css/generated.css">
</head>
<body>
`;

  // Добавляем контейнер для фона, если найден
  if (sections.background) {
    html += `  <div class="background" id="bg-${sections.background.id}"></div>\n`;
  }
  
  // Добавляем шапку, если найдена
  if (sections.header) {
    html += `  <header id="header-${sections.header.id}" class="header">
    <h1>${sections.header.name || 'Header'}</h1>
  </header>\n`;
  }
  
  // Добавляем основной контент
  html += `  <main class="main-content">\n`;
  
  sections.content.forEach((node, index) => {
    html += `    <section class="content-section" id="section-${node.id}">
      <h2>${node.name || `Section ${index + 1}`}</h2>
      ${generateNodeContent(node)}
    </section>\n`;
  });
  
  html += `  </main>\n`;
  
  // Добавляем футер, если найден
  if (sections.footer) {
    html += `  <footer id="footer-${sections.footer.id}" class="footer">
    <p>${sections.footer.name || 'Footer'}</p>
  </footer>\n`;
  }
  
  html += `</body>
</html>`;

  return html;
}

// Генерация содержимого узла в зависимости от его типа
function generateNodeContent(node) {
  switch (node.type) {
    case 'TEXT':
      return `<p class="text-node" data-figma-id="${node.id}">${node.characters || node.name}</p>`;
      
    case 'RECTANGLE':
    case 'ELLIPSE':
      return `<div class="shape-node ${node.type.toLowerCase()}" data-figma-id="${node.id}"></div>`;
      
    case 'FRAME':
    case 'GROUP':
      let content = `<div class="container-node ${node.type.toLowerCase()}" data-figma-id="${node.id}">`;
      
      if (node.children && Array.isArray(node.children)) {
        node.children.forEach(child => {
          content += generateNodeContent(child);
        });
      }
      
      content += `</div>`;
      return content;
      
    default:
      return `<div class="unknown-node" data-figma-id="${node.id}">${node.name || 'Unknown element'}</div>`;
  }
}

// Генерация CSS на основе анализа структуры
function generateCSS(sections) {
  let css = `/* Generated from Figma */
:root {
  --primary-color: #1E88E5;
  --secondary-color: #424242;
  --text-color: #333333;
  --background-color: #FFFFFF;
}

body {
  margin: 0;
  padding: 0;
  font-family: Arial, sans-serif;
  color: var(--text-color);
  background-color: var(--background-color);
}

`;

  // Стили для фона
  if (sections.background) {
    css += `.background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  ${generateNodeStyles(sections.background)}
}

`;
  }

  // Стили для шапки
  if (sections.header) {
    css += `.header {
  padding: 20px;
  ${generateNodeStyles(sections.header)}
}

`;
  }

  // Стили для основного контента
  css += `.main-content {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.content-section {
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 4px;
}

`;

  // Добавляем стили для каждой секции контента
  sections.content.forEach((node, index) => {
    css += `#section-${node.id} {
  ${generateNodeStyles(node)}
}

`;
  });

  // Стили для футера
  if (sections.footer) {
    css += `.footer {
  padding: 20px;
  text-align: center;
  ${generateNodeStyles(sections.footer)}
}

`;
  }

  // Общие стили для различных типов узлов
  css += `.text-node {
  margin: 0 0 10px 0;
}

.shape-node {
  width: 100%;
  height: 150px;
}

.rectangle {
  border-radius: 4px;
}

.ellipse {
  border-radius: 50%;
}

.container-node {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px;
}

`;

  return css;
}

// Генерация CSS стилей для узла
function generateNodeStyles(node) {
  let styles = '';
  
  // Обработка заливок
  if (node.fills && Array.isArray(node.fills) && node.fills.length > 0) {
    const fill = node.fills[0];
    if (fill.type === 'SOLID' && fill.visible !== false) {
      const color = fill.color;
      if (color) {
        const opacity = fill.opacity !== undefined ? fill.opacity : 1;
        const rgba = `rgba(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)}, ${opacity})`;
        styles += `background-color: ${rgba};\n  `;
      }
    }
  }
  
  // Обработка обводок
  if (node.strokes && Array.isArray(node.strokes) && node.strokes.length > 0) {
    const stroke = node.strokes[0];
    if (stroke.type === 'SOLID' && stroke.visible !== false) {
      const color = stroke.color;
      if (color) {
        const opacity = stroke.opacity !== undefined ? stroke.opacity : 1;
        const rgba = `rgba(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)}, ${opacity})`;
        styles += `border: ${node.strokeWeight || 1}px solid ${rgba};\n  `;
      }
    }
  }
  
  // Обработка скругления углов
  if (node.cornerRadius && node.cornerRadius > 0) {
    styles += `border-radius: ${node.cornerRadius}px;\n  `;
  }
  
  // Обработка эффектов тени
  if (node.effects && Array.isArray(node.effects)) {
    const shadows = node.effects.filter(effect => 
      (effect.type === 'DROP_SHADOW' || effect.type === 'INNER_SHADOW') && 
      effect.visible !== false
    );
    
    if (shadows.length > 0) {
      const shadow = shadows[0];
      const color = shadow.color;
      if (color) {
        const rgba = `rgba(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)}, ${color.a || 1})`;
        const shadowType = shadow.type === 'INNER_SHADOW' ? 'inset ' : '';
        styles += `box-shadow: ${shadowType}${shadow.offset?.x || 0}px ${shadow.offset?.y || 0}px ${shadow.radius || 0}px ${shadow.spread || 0}px ${rgba};\n  `;
      }
    }
  }
  
  return styles;
}

// Обработка импорта изображений
async function handleImportImages(ws, data) {
  console.log('Получен запрос на импорт изображений');
  
  if (!data.data || !data.data.images || !Array.isArray(data.data.images)) {
    return ws.send(JSON.stringify({
      type: 'error',
      message: 'Отсутствуют данные об изображениях'
    }));
  }
  
  try {
    const images = data.data.images;
    console.log(`Получено ${images.length} изображений для импорта`);
    
    const results = [];
    
    // Обрабатываем каждое изображение
    for (const image of images) {
      if (!image.nodeId || !image.bytes || !Array.isArray(image.bytes)) {
        results.push({
          status: 'error',
          nodeId: image.nodeId || 'unknown',
          message: 'Некорректные данные изображения'
        });
        continue;
      }
      
      // Создаем имя файла на основе ID узла и имени (если есть)
      const fileName = `${image.nodeName ? slugify(image.nodeName) + '-' : ''}${image.nodeId}.${image.format || 'png'}`;
      const filePath = path.join(CONFIG.ASSETS_DIR, fileName);
      
      // Преобразуем массив байтов обратно в буфер
      const buffer = Buffer.from(image.bytes);
      
      // Сохраняем файл
      fs.writeFileSync(filePath, buffer);
      
      console.log(`Изображение сохранено: ${filePath}`);
      
      results.push({
        status: 'success',
        nodeId: image.nodeId,
        fileName: fileName,
        filePath: filePath
      });
    }
    
    // Отправляем результаты
    ws.send(JSON.stringify({
      type: 'images-imported',
      message: `Импортировано ${results.filter(r => r.status === 'success').length} из ${images.length} изображений`,
      results: results
    }));
    
  } catch (error) {
    console.error('Ошибка импорта изображений:', error);
    ws.send(JSON.stringify({
      type: 'error',
      message: `Ошибка импорта изображений: ${error.message}`
    }));
  }
}

// Обработка начала синхронизации
function handleSyncStart(ws, data) {
  console.log(`Начата синхронизация в режиме: ${data.mode || 'по умолчанию'}`);
  
  // Здесь можно добавить логику для начала автоматической синхронизации
  
  ws.send(JSON.stringify({
    type: 'sync-started',
    mode: data.mode || 'default',
    message: 'Синхронизация запущена'
  }));
}

// Обработка остановки синхронизации
function handleSyncStop(ws, data) {
  console.log('Синхронизация остановлена');
  
  // Здесь можно добавить логику для остановки автоматической синхронизации
  
  ws.send(JSON.stringify({
    type: 'sync-stopped',
    message: 'Синхронизация остановлена'
  }));
}

// Вспомогательные функции

// Преобразование строки в slug (для имен файлов)
function slugify(text) {
  return text
    .toString()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^\w\-]+/g, '')
    .replace(/\-\-+/g, '-')
    .replace(/^-+/, '')
    .replace(/-+$/, '');
}

// Запуск сервера
function startServer() {
  console.log('Запуск Cursor MCP сервера...');
  
  // Создаем необходимые директории
  ensureDirectoriesExist();
  
  // Инициализируем WebSocket сервер
  const wss = initWebSocketServer();
  
  console.log(`Cursor MCP сервер запущен на порту ${CONFIG.PORT}`);
  console.log('Ожидание подключений...');
  
  return wss;
}

// Запускаем сервер, если файл вызван напрямую
if (require.main === module) {
  startServer();
}

module.exports = { startServer }; 