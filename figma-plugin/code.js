// Код плагина Figma для интеграции с Cursor MCP
let socket;

// Обработчик сообщений от UI
figma.ui.onmessage = async (message) => {
  switch (message.type) {
    case 'connect':
      // Сохраняем URL сокета и ID канала
      figma.clientStorage.setAsync('socketUrl', message.socketUrl);
      figma.clientStorage.setAsync('channelId', message.channelId);
      
      // Уведомление об успешном подключении
      figma.notify(`Connected to WebSocket at ${message.socketUrl}`);
      break;
      
    case 'disconnect':
      // Очищаем сохраненные данные
      figma.clientStorage.deleteAsync('socketUrl');
      figma.clientStorage.deleteAsync('channelId');
      
      figma.notify('Disconnected from WebSocket');
      break;
      
    case 'execute-command':
      try {
        // Выполнение команды, полученной от MCP
        const result = await executeCommand(message.command, message.params);
        
        // Отправляем результат обратно в UI
        figma.ui.postMessage({
          type: 'command-result',
          id: message.id,
          success: true,
          result
        });
      } catch (error) {
        // Если произошла ошибка, отправляем её
        figma.ui.postMessage({
          type: 'command-result',
          id: message.id,
          success: false,
          error: error.message
        });
      }
      break;
  }
};

// Функция для выполнения команд
async function executeCommand(command, params) {
  switch (command) {
    case 'get_document_info':
      return {
        name: figma.root.name,
        id: figma.root.id,
        type: figma.root.type,
        children: figma.root.children.map(child => ({
          id: child.id,
          name: child.name,
          type: child.type
        }))
      };
      
    case 'get_selection':
      return figma.currentPage.selection.map(node => ({
        id: node.id,
        name: node.name,
        type: node.type
      }));
      
    case 'get_node_info':
      const node = figma.getNodeById(params.node_id);
      if (!node) throw new Error(`Node with ID ${params.node_id} not found`);
      
      return {
        id: node.id,
        name: node.name,
        type: node.type,
        visible: node.visible,
        locked: node.locked
      };
      
    // Добавьте дополнительные команды по мере необходимости
    
    default:
      throw new Error(`Unknown command: ${command}`);
  }
}

// Показываем UI
figma.showUI(__html__, { width: 300, height: 400 });

// Обработчик команды из меню
figma.on('run', ({ command }) => {
  if (command === 'connect') {
    // Команда подключения
  }
}); 