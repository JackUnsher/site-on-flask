// Показываем UI плагина
figma.showUI(__html__, { width: 380, height: 600 });

// Когда плагин запускается
figma.notify("Плагин запущен!");

// Состояние WebSocket-соединения
let wsConnection = null;

// Функция для подключения к WebSocket серверу
async function connectToWebSocket(port) {
  try {
    // Закрываем предыдущее соединение, если оно существует
    if (wsConnection && wsConnection.readyState !== WebSocket.CLOSED) {
      wsConnection.close();
    }
    
    // Создаем новое соединение
    wsConnection = new WebSocket(`ws://localhost:${port}`);
    
    // Отправляем уведомление в UI при успешном соединении
    wsConnection.onopen = () => {
      figma.ui.postMessage({ 
        type: 'ws-connected', 
        message: `Соединение с Cursor IDE установлено на порту ${port}` 
      });
    };
    
    // Обрабатываем сообщения от сервера
    wsConnection.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        // Отправляем сообщение в UI
        figma.ui.postMessage({ 
          type: 'ws-message', 
          data: message 
        });
        
        // Обрабатываем команды от Cursor IDE
        handleCursorCommand(message);
      } catch (error) {
        console.error('Ошибка при обработке сообщения от сервера:', error);
      }
    };
    
    // Обрабатываем закрытие соединения
    wsConnection.onclose = () => {
      figma.ui.postMessage({ 
        type: 'ws-disconnected', 
        message: 'Соединение с Cursor IDE закрыто' 
      });
      wsConnection = null;
    };
    
    // Обрабатываем ошибки
    wsConnection.onerror = (error) => {
      figma.ui.postMessage({ 
        type: 'ws-error', 
        message: 'Ошибка WebSocket соединения' 
      });
      console.error('WebSocket error:', error);
    };
    
    return { success: true };
  } catch (error) {
    console.error('Ошибка при подключении к WebSocket:', error);
    return { success: false, error: error.message };
  }
}

// Функция для отправки данных через WebSocket
function sendToWebSocket(data) {
  if (!wsConnection || wsConnection.readyState !== WebSocket.OPEN) {
    return { success: false, error: 'Нет активного соединения с Cursor IDE' };
  }
  
  try {
    wsConnection.send(JSON.stringify(data));
    return { success: true };
  } catch (error) {
    console.error('Ошибка при отправке данных через WebSocket:', error);
    return { success: false, error: error.message };
  }
}

// Обработка команд от Cursor IDE
function handleCursorCommand(message) {
  // Здесь можно добавить специфические действия по командам от IDE
  console.log('Получена команда от Cursor IDE:', message);
}

// Функция для экспорта структуры документа
async function exportDocumentStructure() {
  try {
    // Получаем текущую страницу
    const currentPage = figma.currentPage;
    
    // Создаем объект с данными о странице
    const pageData = {
      name: currentPage.name,
      id: currentPage.id,
      type: 'PAGE',
      children: []
    };
    
    // Функция для рекурсивного обхода узлов
    function processNode(node) {
      const nodeData = {
      id: node.id,
      name: node.name,
      type: node.type,
        visible: node.visible
      };
      
      // Добавляем позицию и размеры
      if ('x' in node) {
        nodeData.x = node.x;
        nodeData.y = node.y;
      }
      
      if ('width' in node) {
        nodeData.width = node.width;
        nodeData.height = node.height;
      }
      
      // Добавляем цвета заливки
      if ('fills' in node && node.fills) {
        nodeData.fills = node.fills;
      }
      
      // Добавляем обводку
      if ('strokes' in node && node.strokes) {
        nodeData.strokes = node.strokes;
      }
      
      // Добавляем скругления углов
      if ('cornerRadius' in node) {
        nodeData.cornerRadius = node.cornerRadius;
      }
      
      // Добавляем текст
      if (node.type === 'TEXT') {
        nodeData.characters = node.characters;
        nodeData.fontSize = node.fontSize;
        nodeData.fontName = node.fontName;
        nodeData.textAlignHorizontal = node.textAlignHorizontal;
        nodeData.textAlignVertical = node.textAlignVertical;
      }
      
      // Обрабатываем дочерние элементы
      if ('children' in node) {
        nodeData.children = [];
        for (const child of node.children) {
          nodeData.children.push(processNode(child));
        }
      }
      
      return nodeData;
    }
    
    // Обрабатываем все узлы на текущей странице
    for (const node of currentPage.children) {
      pageData.children.push(processNode(node));
    }
    
    return {
      success: true,
      data: pageData
    };
  } catch (error) {
    console.error('Ошибка при экспорте структуры документа:', error);
    return { success: false, error: error.message };
  }
}

// Функция для экспорта изображений
async function exportImages(nodeIds) {
  try {
    const images = [];
    
    for (const nodeId of nodeIds) {
      // Находим узел по ID
      const node = figma.getNodeById(nodeId);
      
      if (!node) {
        console.warn(`Узел с ID ${nodeId} не найден`);
        continue;
      }
      
      // Экспортируем изображение
      if ('exportAsync' in node) {
        try {
          const imageBytes = await node.exportAsync({
            format: 'PNG',
            constraint: { type: 'SCALE', value: 2 }
          });
          
          // Конвертируем байты в base64
          const base64Image = figma.base64Encode(imageBytes);
          
          images.push({
            id: node.id,
            name: node.name,
            base64: base64Image
          });
        } catch (exportError) {
          console.error(`Ошибка при экспорте узла ${nodeId}:`, exportError);
        }
      } else {
        console.warn(`Узел ${nodeId} не поддерживает экспорт`);
      }
    }

  return {
      success: true,
      data: images
    };
  } catch (error) {
    console.error('Ошибка при экспорте изображений:', error);
    return { success: false, error: error.message };
  }
}

// Функция для поиска компонентов поста
async function findPostComponents() {
  // Ищем страницу с компонентами
  let componentsPage = null;
  
  // Ищем на текущей странице и в документе
  figma.root.children.forEach(page => {
    if (page.name.toLowerCase().includes('components') || 
        page.name.toLowerCase().includes('компоненты')) {
      componentsPage = page;
    }
  });
  
  if (!componentsPage) {
    // Если страница с компонентами не найдена, используем текущую
    componentsPage = figma.currentPage;
  }
  
  // Ищем компонент-сет постов
  let postComponentSet = null;
  
  // Функция для рекурсивного поиска компонент-сетов
  function findComponentSet(node) {
    if (node.type === 'COMPONENT_SET') {
      if (node.name.toLowerCase().includes('post') || 
          node.name.toLowerCase().includes('пост') ||
          node.name.toLowerCase().includes('card') || 
          node.name.toLowerCase().includes('карточка')) {
        return node;
      }
    }
    
    if ('children' in node) {
    for (const child of node.children) {
        const result = findComponentSet(child);
        if (result) return result;
      }
    }
    
    return null;
  }
  
  postComponentSet = findComponentSet(componentsPage);
  
  // Возвращаем результат поиска
  return postComponentSet;
}

// Функция для случайных чисел с ограничением
function getRandomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

// Функция для создания поста
async function createPost(data) {
  try {
    // Загружаем необходимые шрифты
    await figma.loadFontAsync({ family: "Inter", style: "Regular" });
    await figma.loadFontAsync({ family: "Inter", style: "Medium" });
    await figma.loadFontAsync({ family: "Inter", style: "Bold" });
    
    // Ищем компонент-сет для постов
    const postComponentSet = await findPostComponents();
    
    if (!postComponentSet) {
      // Если компонент-сет не найден, создадим простой компонент
      return await createSimpleComponent(data);
    }
    
    // Определяем, какой вариант компонента использовать
    const variants = postComponentSet.children;
    let selectedVariant = null;
    
    // Выбираем вариант на основе опций пользователя
    for (const variant of variants) {
      const variantName = variant.name.toLowerCase();
      
      // Проверяем соответствие темы
      const themMatches = data.darkMode ? 
        variantName.includes('dark') : 
        !variantName.includes('dark');
      
      // Проверяем соответствие изображений
      let imageMatches = false;
      
      if (data.imageType === 'none' && 
          (variantName.includes('no image') || !variantName.includes('image'))) {
        imageMatches = true;
      } else if (data.imageType === 'single' && 
               (variantName.includes('single image') || variantName.includes('one image'))) {
        imageMatches = true;
      } else if (data.imageType === 'multiple' && 
               (variantName.includes('multiple') || variantName.includes('gallery'))) {
        imageMatches = true;
      }
      
      if (themMatches && imageMatches) {
        selectedVariant = variant;
        break;
      }
    }
    
    // Если не нашли точное соответствие, берем первый вариант
    if (!selectedVariant && variants.length > 0) {
      selectedVariant = variants[0];
    }
    
    if (!selectedVariant) {
      // Если вариант все равно не найден, создаем базовый компонент
      return await createSimpleComponent(data);
    }
    
    // Создаем экземпляр выбранного варианта
    const newPost = selectedVariant.createInstance();
    
    // Ищем текстовые элементы в посте, которые нужно заменить
    const textNodes = [];
    
    function findTextNodes(node) {
      if (node.type === 'TEXT') {
        textNodes.push(node);
      } else if ('children' in node) {
        for (const child of node.children) {
          findTextNodes(child);
        }
      }
    }
    
    findTextNodes(newPost);
    
    // Заменяем текст на основе имен текстовых узлов
    for (const textNode of textNodes) {
      const nodeName = textNode.name.toLowerCase();
      
      // Заменяем имя пользователя
      if (nodeName.includes('username') || nodeName.includes('user name') || nodeName.includes('@')) {
        textNode.characters = '@' + data.username.replace(/^@/, '');
      } 
      // Заменяем отображаемое имя
      else if (nodeName.includes('name') || nodeName.includes('display') || nodeName.includes('profile')) {
        textNode.characters = data.name;
      } 
      // Заменяем описание
      else if (nodeName.includes('description') || nodeName.includes('text') || nodeName.includes('content')) {
        textNode.characters = data.description;
      } 
      // Заменяем количество лайков случайным числом
      else if (nodeName.includes('like') || nodeName.includes('лайк')) {
        textNode.characters = getRandomInt(1, 999).toString();
      } 
      // Заменяем количество комментариев случайным числом
      else if (nodeName.includes('comment') || nodeName.includes('коммент')) {
        textNode.characters = getRandomInt(0, 99).toString();
      }
    }
    
    // Позиционируем новый пост
    let offsetX = 100;
    let offsetY = 100;
    
    if (figma.currentPage.selection.length > 0) {
      const selected = figma.currentPage.selection[0];
      offsetX = selected.x + selected.width + 50;
      offsetY = selected.y;
    }
    
    newPost.x = offsetX;
    newPost.y = offsetY;
    
    // Добавляем новый пост на страницу
    figma.currentPage.appendChild(newPost);
    
    // Выбираем новый пост
    figma.currentPage.selection = [newPost];
    
    // Масштабируем вид для отображения поста
    figma.viewport.scrollAndZoomIntoView([newPost]);
    
    // Если есть WebSocket соединение, отправляем информацию о созданном посте
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      // Собираем данные о структуре поста
      const postData = {
        id: newPost.id,
        name: newPost.name,
        type: newPost.type,
        x: newPost.x,
        y: newPost.y,
        width: newPost.width,
        height: newPost.height
      };
      
      // Отправляем через WebSocket
      sendToWebSocket({
        type: 'post-created',
        data: postData
      });
    }
    
    return { success: true, postId: newPost.id };
  } catch (error) {
    console.error('Ошибка при создании поста:', error);
    return { success: false, error: error.message };
  }
}

// Функция для создания простого компонента (резервный вариант)
async function createSimpleComponent(data) {
  try {
    // Загружаем необходимые шрифты
    await figma.loadFontAsync({ family: "Inter", style: "Regular" });
    await figma.loadFontAsync({ family: "Inter", style: "Medium" });
    
    // Создаем фрейм для компонента
    const frame = figma.createFrame();
    frame.name = data.name || "Новый пост";
    frame.resize(data.width || 320, data.height || 240);
    
    // Устанавливаем цвет фона в зависимости от режима
    if (data.darkMode) {
      frame.fills = [{ type: 'SOLID', color: { r: 0.1, g: 0.1, b: 0.1 } }];
    } else {
      frame.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
    }
    
    frame.cornerRadius = 8;
    
    // Создаем и стилизуем аватар
    const avatar = figma.createEllipse();
    avatar.name = "avatar";
    avatar.resize(40, 40);
    avatar.x = 16;
    avatar.y = 16;
    avatar.fills = [{ type: 'SOLID', color: { r: 0.8, g: 0.8, b: 0.8 } }];
    
    // Создаем имя пользователя
    const userName = figma.createText();
    userName.name = "displayName";
    userName.characters = data.name;
    userName.fontSize = 16;
    userName.fontName = { family: "Inter", style: "Medium" };
    userName.x = 68;
    userName.y = 16;
    
    // Стилизуем текст в зависимости от темы
    if (data.darkMode) {
      userName.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
    } else {
      userName.fills = [{ type: 'SOLID', color: { r: 0.1, g: 0.1, b: 0.1 } }];
    }
    
    // Создаем имя пользователя в формате @username
    const handle = figma.createText();
    handle.name = "@username";
    handle.characters = '@' + data.username.replace(/^@/, '');
    handle.fontSize = 14;
    handle.x = 68;
    handle.y = 38;
    
    // Стилизуем @username в зависимости от темы
    if (data.darkMode) {
      handle.fills = [{ type: 'SOLID', color: { r: 0.7, g: 0.7, b: 0.7 } }];
  } else {
      handle.fills = [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } }];
    }
    
    // Создаем основной текст
    const content = figma.createText();
    content.name = "description";
    content.characters = data.description;
    content.fontSize = 14;
    content.x = 16;
    content.y = 72;
    content.resize(frame.width - 32, 100);
    
    // Стилизуем основной текст
    if (data.darkMode) {
      content.fills = [{ type: 'SOLID', color: { r: 0.9, g: 0.9, b: 0.9 } }];
    } else {
      content.fills = [{ type: 'SOLID', color: { r: 0.3, g: 0.3, b: 0.3 } }];
    }
    
    // Добавляем элементы во фрейм
    frame.appendChild(avatar);
    frame.appendChild(userName);
    frame.appendChild(handle);
    frame.appendChild(content);
    
    // Добавляем иконки взаимодействия
    const likesContainer = figma.createFrame();
    likesContainer.name = "likes";
    likesContainer.layoutMode = "HORIZONTAL";
    likesContainer.primaryAxisAlignItems = "CENTER";
    likesContainer.counterAxisAlignItems = "CENTER";
    likesContainer.resize(80, 24);
    likesContainer.x = 16;
    likesContainer.y = frame.height - 40;
    likesContainer.fills = [];
    
    const likesCount = figma.createText();
    likesCount.name = "likesLabel";
    likesCount.characters = getRandomInt(1, 999).toString();
    likesCount.fontSize = 14;
    
    // Стилизуем счетчики в зависимости от темы
    if (data.darkMode) {
      likesCount.fills = [{ type: 'SOLID', color: { r: 0.7, g: 0.7, b: 0.7 } }];
    } else {
      likesCount.fills = [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } }];
    }
    
    likesContainer.appendChild(likesCount);
    
    const commentsContainer = figma.createFrame();
    commentsContainer.name = "comments";
    commentsContainer.layoutMode = "HORIZONTAL";
    commentsContainer.primaryAxisAlignItems = "CENTER";
    commentsContainer.counterAxisAlignItems = "CENTER";
    commentsContainer.resize(80, 24);
    commentsContainer.x = 104;
    commentsContainer.y = frame.height - 40;
    commentsContainer.fills = [];
    
    const commentsCount = figma.createText();
    commentsCount.name = "commentsLabel";
    commentsCount.characters = getRandomInt(0, 99).toString();
    commentsCount.fontSize = 14;
    
    // Стилизуем счетчики в зависимости от темы
    if (data.darkMode) {
      commentsCount.fills = [{ type: 'SOLID', color: { r: 0.7, g: 0.7, b: 0.7 } }];
    } else {
      commentsCount.fills = [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } }];
    }
    
    commentsContainer.appendChild(commentsCount);
    
    frame.appendChild(likesContainer);
    frame.appendChild(commentsContainer);
    
    // Создаем компонент
    const component = figma.createComponent();
    component.resize(frame.width, frame.height);
    component.name = frame.name;
    
    // Копируем свойства и дочерние элементы из фрейма в компонент
    component.fills = frame.fills;
    component.cornerRadius = frame.cornerRadius;
    
    // Клонируем дочерние элементы
    for (const child of frame.children) {
      const clone = child.clone();
      component.appendChild(clone);
    }
    
    // Удаляем временный фрейм
    frame.remove();
    
    // Создаем экземпляр компонента
    const instance = component.createInstance();
    instance.x = component.width + 50;
    
    // Выделяем компонент
    figma.currentPage.selection = [component];
    
    // Масштабируем вид для отображения компонента
    figma.viewport.scrollAndZoomIntoView([component, instance]);
    
    // Если есть WebSocket соединение, отправляем информацию о созданном компоненте
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      // Собираем данные о структуре компонента
      const componentData = {
        id: component.id,
        name: component.name,
        type: component.type,
        x: component.x,
        y: component.y,
        width: component.width,
        height: component.height
      };
      
      // Отправляем через WebSocket
      sendToWebSocket({
        type: 'component-created',
        data: componentData
      });
    }
    
    return { success: true, componentId: component.id };
  } catch (error) {
    console.error('Ошибка при создании компонента:', error);
    return { success: false, error: error.message };
  }
}

// Обработчик сообщений от UI
figma.ui.onmessage = async (msg) => {
  console.log("Получено сообщение:", msg);
  
  // Обрабатываем различные типы сообщений
  switch (msg.type) {
    case 'connect-websocket':
      // Подключаемся к WebSocket серверу
      const wsResult = await connectToWebSocket(msg.port);
      if (wsResult.success) {
        figma.notify("Подключение к Cursor IDE выполнено!");
      } else {
        figma.notify("Ошибка подключения к Cursor IDE", { error: true });
        figma.ui.postMessage({ 
          type: 'error', 
          message: 'Ошибка подключения: ' + wsResult.error 
        });
      }
      break;
      
    case 'disconnect-websocket':
      // Отключаемся от WebSocket сервера
      if (wsConnection) {
        wsConnection.close();
        figma.notify("Отключено от Cursor IDE");
      }
      break;
    
    case 'export-structure':
      // Экспортируем структуру документа
      const structureResult = await exportDocumentStructure();
      if (structureResult.success) {
        // Если есть WebSocket соединение, отправляем структуру
        if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
          const sendResult = sendToWebSocket({
            type: 'document-structure',
            data: structureResult.data
          });
          
          if (sendResult.success) {
            figma.notify("Структура отправлена в Cursor IDE!");
            figma.ui.postMessage({ 
              type: 'structure-exported', 
              message: 'Структура документа успешно экспортирована и отправлена' 
            });
          } else {
            figma.notify("Ошибка отправки в Cursor IDE", { error: true });
            figma.ui.postMessage({ 
              type: 'error', 
              message: 'Ошибка отправки: ' + sendResult.error 
            });
          }
        } else {
          // Если нет соединения, отправляем структуру в UI
          figma.ui.postMessage({ 
            type: 'structure-data', 
            data: structureResult.data 
          });
        }
      } else {
        figma.notify("Ошибка экспорта структуры", { error: true });
        figma.ui.postMessage({ 
          type: 'error', 
          message: 'Ошибка экспорта структуры: ' + structureResult.error 
        });
      }
      break;
    
    case 'export-images':
      // Экспортируем изображения
      const imageResult = await exportImages(msg.nodeIds);
      if (imageResult.success) {
        // Если есть WebSocket соединение, отправляем изображения
        if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
          const sendResult = sendToWebSocket({
            type: 'exported-images',
            data: imageResult.data
          });
          
          if (sendResult.success) {
            figma.notify(`Отправлено ${imageResult.data.length} изображений в Cursor IDE!`);
            figma.ui.postMessage({ 
              type: 'images-exported', 
              message: `Экспортировано ${imageResult.data.length} изображений` 
            });
          } else {
            figma.notify("Ошибка отправки изображений", { error: true });
            figma.ui.postMessage({ 
              type: 'error', 
              message: 'Ошибка отправки изображений: ' + sendResult.error 
            });
          }
        } else {
          // Если нет соединения, отправляем данные в UI
          figma.ui.postMessage({ 
            type: 'image-data', 
            data: imageResult.data 
          });
        }
      } else {
        figma.notify("Ошибка экспорта изображений", { error: true });
      figma.ui.postMessage({ 
          type: 'error', 
          message: 'Ошибка экспорта изображений: ' + imageResult.error 
      });
      }
      break;
    
    case 'get-document-info':
      // Возвращаем информацию о документе
      const docInfo = {
        name: figma.root.name,
        currentPage: figma.currentPage.name,
        selection: figma.currentPage.selection.length > 0 ? 
                  figma.currentPage.selection.map(node => ({ id: node.id, name: node.name, type: node.type })) : 
                  []
      };
      
      figma.ui.postMessage({ 
        type: 'document-info', 
        data: docInfo 
      });
      break;
    
    case 'create-post':
      // Создаем пост
      const result = await createPost(msg.data);
      if (result.success) {
        figma.notify("Пост успешно создан!");
        figma.ui.postMessage({ 
          type: 'post-created', 
          data: { id: result.postId || result.componentId } 
        });
      } else {
        figma.notify("Ошибка при создании поста", { error: true });
        figma.ui.postMessage({ 
          type: 'error', 
          message: 'Ошибка при создании поста: ' + result.error 
        });
      }
      break;
      
    case 'create-component':
      // Создаем простой компонент (для обратной совместимости)
      const compResult = await createSimpleComponent(msg.data);
      if (compResult.success) {
        figma.notify("Компонент успешно создан!");
        figma.ui.postMessage({ 
          type: 'component-created', 
          data: { id: compResult.componentId } 
        });
      } else {
        figma.notify("Ошибка при создании компонента", { error: true });
      figma.ui.postMessage({ 
          type: 'error', 
          message: 'Ошибка при создании компонента: ' + compResult.error 
      });
      }
      break;
      
    case 'close-plugin':
      // Закрываем WebSocket соединение перед закрытием плагина
      if (wsConnection) {
        wsConnection.close();
      }
      
      // Закрываем плагин
      figma.closePlugin();
      break;
      
    default:
      // Неизвестный тип сообщения
      figma.ui.postMessage({ 
        type: 'error', 
        message: 'Неизвестный тип сообщения: ' + msg.type 
      });
  }
};