/**
 * HTML Generator - компонент для генерации HTML из данных Figma
 * Автоматически анализирует структуру макета и создает семантическую разметку
 * с поддержкой принципа "от фона к наполнению и от шапки к футеру"
 */

const fs = require('fs');
const path = require('path');

/**
 * Генерирует HTML код на основе структуры из Figma
 * @param {Object} structure - Структура дизайна из Figma
 * @param {Object} options - Настройки генерации
 * @returns {String} HTML-код
 */
function generateHTML(structure, options = {}) {
  // Значения по умолчанию
  const config = {
    prefix: options.prefix || '',
    semanticNames: options.semanticNames !== false,
    outputPath: options.outputPath || null,
    classNameStyle: options.classNameStyle || 'kebab', // kebab, camel, BEM
    includeDataAttributes: options.includeDataAttributes !== false
  };
  
  // Анализ структуры и определение основных разделов
  const sections = analyzeSections(structure);
  
  // Формирование HTML документа
  let html = `<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${options.title || 'Сгенерировано из Figma'}</title>
  <link rel="stylesheet" href="${options.cssPath || 'styles.css'}">
</head>
<body>
`;

  // Добавляем фон (если есть)
  if (sections.background) {
    html += generateBackgroundHTML(sections.background, config);
  }
  
  // Добавляем шапку (если есть)
  if (sections.header) {
    html += generateHeaderHTML(sections.header, config);
  }
  
  // Основное содержимое
  html += generateMainContentHTML(sections.content, config);
  
  // Добавляем футер (если есть)
  if (sections.footer) {
    html += generateFooterHTML(sections.footer, config);
  }
  
  html += `</body>
</html>`;

  // Сохраняем в файл, если указан путь
  if (config.outputPath) {
    fs.writeFileSync(config.outputPath, html);
    console.log(`HTML сохранен в ${config.outputPath}`);
  }
  
  return html;
}

/**
 * Анализирует структуру дизайна и определяет основные разделы
 * @param {Object} structure - Структура дизайна из Figma
 * @returns {Object} Объект с основными разделами (фон, шапка, контент, футер)
 */
function analyzeSections(structure) {
  const sections = {
    background: null,
    header: null,
    content: [],
    footer: null
  };
  
  if (!structure || !structure.children || !Array.isArray(structure.children)) {
    return sections;
  }
  
  // Определение размеров "холста" для относительных расчетов
  const canvasWidth = structure.size ? structure.size.width : 1440;
  const canvasHeight = structure.size ? structure.size.height : 900;
  
  // Поиск фоновых элементов (покрывающих большую часть холста)
  const possibleBackgrounds = structure.children.filter(node => {
    // Проверяем, покрывает ли элемент значительную часть холста
    if (!node.size) return false;
    
    const nodeArea = node.size.width * node.size.height;
    const canvasArea = canvasWidth * canvasHeight;
    const areaCoverage = nodeArea / canvasArea;
    
    // Если элемент покрывает более 80% холста, считаем его фоновым
    return areaCoverage > 0.8 && ['RECTANGLE', 'FRAME', 'INSTANCE'].includes(node.type);
  });
  
  if (possibleBackgrounds.length > 0) {
    // Выбираем самый нижний слой как фон (с наименьшим zIndex)
    sections.background = possibleBackgrounds.sort((a, b) => a.zIndex - b.zIndex)[0];
  }
  
  // Сортируем все элементы по вертикальной позиции
  const sortedNodes = [...structure.children]
    .filter(node => node !== sections.background) // Исключаем фоновый элемент
    .sort((a, b) => {
      // Если у нас есть позиция, используем ее
      const aY = a.position ? a.position.y : 0;
      const bY = b.position ? b.position.y : 0;
      return aY - bY;
    });
  
  if (sortedNodes.length === 0) {
    return sections;
  }
  
  // Определение шапки (верхний элемент с небольшой высотой)
  const firstNode = sortedNodes[0];
  if (firstNode.position && firstNode.position.y < canvasHeight * 0.15 && 
      firstNode.size && firstNode.size.height < canvasHeight * 0.3) {
    sections.header = firstNode;
    sortedNodes.shift(); // Удаляем шапку из списка
  }
  
  // Определение футера (нижний элемент с небольшой высотой)
  if (sortedNodes.length > 0) {
    const lastNode = sortedNodes[sortedNodes.length - 1];
    if (lastNode.position && 
        lastNode.position.y + (lastNode.size ? lastNode.size.height : 0) > canvasHeight * 0.7 && 
        lastNode.size && lastNode.size.height < canvasHeight * 0.3) {
      sections.footer = lastNode;
      sortedNodes.pop(); // Удаляем футер из списка
    }
  }
  
  // Оставшиеся элементы считаем основным контентом
  sections.content = sortedNodes;
  
  return sections;
}

/**
 * Генерирует HTML для фонового элемента
 * @param {Object} node - Узел структуры, представляющий фон
 * @param {Object} config - Настройки генерации
 * @returns {String} HTML-код для фона
 */
function generateBackgroundHTML(node, config) {
  const className = generateClassName('background', node, config);
  const dataAttributes = config.includeDataAttributes ? ` data-figma-id="${node.id}"` : '';
  
  return `  <div class="${className}"${dataAttributes}></div>\n`;
}

/**
 * Генерирует HTML для шапки
 * @param {Object} node - Узел структуры, представляющий шапку
 * @param {Object} config - Настройки генерации
 * @returns {String} HTML-код для шапки
 */
function generateHeaderHTML(node, config) {
  const className = generateClassName('header', node, config);
  const dataAttributes = config.includeDataAttributes ? ` data-figma-id="${node.id}"` : '';
  
  let html = `  <header class="${className}"${dataAttributes}>\n`;
  
  // Анализируем содержимое шапки
  if (node.children && Array.isArray(node.children)) {
    // Ищем элементы навигации
    const navElements = node.children.filter(child => 
      isNavigationElement(child) || 
      (child.children && Array.isArray(child.children) && child.children.some(isNavigationElement))
    );
    
    // Ищем логотип или заголовок
    const logoElements = node.children.filter(child => 
      isLogoElement(child) ||
      (child.type === 'TEXT' && (child.characters || "").length < 30)
    );
    
    // Генерируем содержимое шапки
    if (logoElements.length > 0) {
      const logo = logoElements[0];
      if (logo.type === 'TEXT') {
        html += `    <h1 class="${generateClassName('logo', logo, config)}"${config.includeDataAttributes ? ` data-figma-id="${logo.id}"` : ''}>${logo.characters || logo.name}</h1>\n`;
      } else {
        html += `    <div class="${generateClassName('logo', logo, config)}"${config.includeDataAttributes ? ` data-figma-id="${logo.id}"` : ''}></div>\n`;
      }
    }
    
    if (navElements.length > 0) {
      const nav = navElements[0];
      html += `    <nav class="${generateClassName('nav', nav, config)}"${config.includeDataAttributes ? ` data-figma-id="${nav.id}"` : ''}>\n`;
      
      // Генерируем элементы навигации
      if (nav.children && Array.isArray(nav.children)) {
        html += '      <ul>\n';
        nav.children.filter(item => item.type === 'TEXT' || item.type === 'INSTANCE' || item.type === 'FRAME')
          .forEach(item => {
            const itemText = item.type === 'TEXT' ? (item.characters || item.name) : item.name;
            html += `        <li><a href="#"${config.includeDataAttributes ? ` data-figma-id="${item.id}"` : ''}>${itemText}</a></li>\n`;
          });
        html += '      </ul>\n';
      }
      
      html += '    </nav>\n';
    }
    
    // Если не нашли специальных элементов, просто рекурсивно обрабатываем все содержимое
    if (logoElements.length === 0 && navElements.length === 0) {
      html += processNodeChildren(node, config, 4);
    }
  }
  
  html += '  </header>\n';
  return html;
}

/**
 * Генерирует HTML для основного содержимого
 * @param {Array} nodes - Массив узлов структуры, представляющих основное содержимое
 * @param {Object} config - Настройки генерации
 * @returns {String} HTML-код для основного содержимого
 */
function generateMainContentHTML(nodes, config) {
  if (!nodes || nodes.length === 0) {
    return '  <main class="main-content"></main>\n';
  }
  
  let html = '  <main class="main-content">\n';
  
  // Группируем узлы по вертикальным секциям
  const sections = groupNodesIntoSections(nodes);
  
  // Генерируем HTML для каждой секции
  sections.forEach((sectionNodes, index) => {
    const sectionId = `section-${index + 1}`;
    const sectionClass = `content-section${index === 0 ? ' hero-section' : ''}`;
    
    html += `    <section id="${sectionId}" class="${sectionClass}">\n`;
    
    // Обрабатываем узлы секции, обнаруживая структуры "колонок"
    const columns = detectColumns(sectionNodes);
    
    if (columns.length > 1) {
      // Мультиколоночный макет
      html += '      <div class="columns-container">\n';
      
      columns.forEach((columnNodes) => {
        html += '        <div class="column">\n';
        columnNodes.forEach(node => {
          html += processNode(node, config, 10);
        });
        html += '        </div>\n';
      });
      
      html += '      </div>\n';
    } else {
      // Обычный макет
      sectionNodes.forEach(node => {
        html += processNode(node, config, 6);
      });
    }
    
    html += '    </section>\n';
  });
  
  html += '  </main>\n';
  return html;
}

/**
 * Группирует узлы в вертикальные секции
 * @param {Array} nodes - Массив узлов
 * @returns {Array} Массив массивов узлов, сгруппированных по секциям
 */
function groupNodesIntoSections(nodes) {
  if (!nodes || nodes.length === 0) {
    return [[]];
  }
  
  // Сортируем узлы по вертикальной позиции
  const sortedNodes = [...nodes].sort((a, b) => {
    const aY = a.position ? a.position.y : 0;
    const bY = b.position ? b.position.y : 0;
    return aY - bY;
  });
  
  const sections = [];
  let currentSection = [];
  let lastBottomY = 0;
  
  sortedNodes.forEach(node => {
    const nodeY = node.position ? node.position.y : 0;
    const nodeHeight = node.size ? node.size.height : 0;
    const nodeBottomY = nodeY + nodeHeight;
    
    // Если узел находится значительно ниже предыдущего, считаем его началом новой секции
    if (currentSection.length > 0 && nodeY > lastBottomY + 50) {
      sections.push(currentSection);
      currentSection = [];
    }
    
    currentSection.push(node);
    lastBottomY = Math.max(lastBottomY, nodeBottomY);
  });
  
  if (currentSection.length > 0) {
    sections.push(currentSection);
  }
  
  return sections;
}

/**
 * Обнаруживает колоночную структуру в наборе узлов
 * @param {Array} nodes - Массив узлов
 * @returns {Array} Массив массивов узлов, сгруппированных по колонкам
 */
function detectColumns(nodes) {
  if (!nodes || nodes.length <= 1) {
    return [nodes];
  }
  
  // Определяем горизонтальные позиции каждого узла
  const positionsX = nodes.map(node => {
    return {
      node,
      left: node.position ? node.position.x : 0,
      right: node.position ? node.position.x + (node.size ? node.size.width : 0) : 0
    };
  });
  
  // Сортируем узлы по горизонтальной позиции
  positionsX.sort((a, b) => a.left - b.left);
  
  // Проверяем наличие четких колонок
  // Узлы в одной колонке должны иметь близкие значения left
  const columns = [];
  let currentColumn = [positionsX[0].node];
  let currentLeft = positionsX[0].left;
  
  for (let i = 1; i < positionsX.length; i++) {
    const pos = positionsX[i];
    
    // Если узел находится значительно правее, считаем его началом новой колонки
    if (Math.abs(pos.left - currentLeft) > 30) {
      columns.push(currentColumn);
      currentColumn = [];
      currentLeft = pos.left;
    }
    
    currentColumn.push(pos.node);
  }
  
  if (currentColumn.length > 0) {
    columns.push(currentColumn);
  }
  
  // Если мы обнаружили только одну колонку, возвращаем исходный массив
  if (columns.length <= 1) {
    return [nodes];
  }
  
  return columns;
}

/**
 * Генерирует HTML для футера
 * @param {Object} node - Узел структуры, представляющий футер
 * @param {Object} config - Настройки генерации
 * @returns {String} HTML-код для футера
 */
function generateFooterHTML(node, config) {
  const className = generateClassName('footer', node, config);
  const dataAttributes = config.includeDataAttributes ? ` data-figma-id="${node.id}"` : '';
  
  let html = `  <footer class="${className}"${dataAttributes}>\n`;
  
  // Обрабатываем содержимое футера
  if (node.children && Array.isArray(node.children)) {
    // Классические элементы футеров
    const copyrightElements = node.children.filter(child => 
      child.type === 'TEXT' && 
      (child.characters || "").toLowerCase().includes('copyright') || 
      (child.characters || "").includes('©')
    );
    
    // Социальные иконки (обычно маленькие группы или фреймы)
    const socialElements = node.children.filter(child => 
      (child.name || "").toLowerCase().includes('social') || 
      (child.type === 'GROUP' || child.type === 'FRAME') && 
      child.children && 
      child.children.length >= 3 && 
      child.children.every(icon => icon.size && icon.size.width < 40 && icon.size.height < 40)
    );
    
    // Колонки ссылок в футере
    const linkColumns = node.children.filter(child => 
      (child.type === 'GROUP' || child.type === 'FRAME') && 
      child.children && 
      child.children.some(item => item.type === 'TEXT')
    );
    
    // Специальные секции для типовых элементов футера
    if (linkColumns.length > 0) {
      html += '    <div class="footer-nav">\n';
      
      linkColumns.forEach(column => {
        html += `      <div class="footer-column"${config.includeDataAttributes ? ` data-figma-id="${column.id}"` : ''}>\n`;
        
        // Обрабатываем заголовок колонки и ссылки
        if (column.children && Array.isArray(column.children)) {
          const textElements = column.children.filter(item => item.type === 'TEXT');
          
          if (textElements.length > 0) {
            // Первый текстовый элемент считаем заголовком
            const heading = textElements[0];
            html += `        <h3${config.includeDataAttributes ? ` data-figma-id="${heading.id}"` : ''}>${heading.characters || heading.name}</h3>\n`;
            
            // Остальные считаем ссылками
            if (textElements.length > 1) {
              html += '        <ul>\n';
              textElements.slice(1).forEach(link => {
                html += `          <li><a href="#"${config.includeDataAttributes ? ` data-figma-id="${link.id}"` : ''}>${link.characters || link.name}</a></li>\n`;
              });
              html += '        </ul>\n';
            }
          }
        }
        
        html += '      </div>\n';
      });
      
      html += '    </div>\n';
    }
    
    if (socialElements.length > 0) {
      const social = socialElements[0];
      html += `    <div class="social-links"${config.includeDataAttributes ? ` data-figma-id="${social.id}"` : ''}>\n`;
      
      if (social.children && Array.isArray(social.children)) {
        social.children.forEach(icon => {
          html += `      <a href="#" class="social-icon"${config.includeDataAttributes ? ` data-figma-id="${icon.id}"` : ''}></a>\n`;
        });
      }
      
      html += '    </div>\n';
    }
    
    if (copyrightElements.length > 0) {
      const copyright = copyrightElements[0];
      html += `    <div class="copyright"${config.includeDataAttributes ? ` data-figma-id="${copyright.id}"` : ''}>${copyright.characters || copyright.name}</div>\n`;
    }
    
    // Если не нашли типовых элементов, просто рекурсивно обрабатываем содержимое
    if (linkColumns.length === 0 && socialElements.length === 0 && copyrightElements.length === 0) {
      html += processNodeChildren(node, config, 4);
    }
  }
  
  html += '  </footer>\n';
  return html;
}

/**
 * Рекурсивно обрабатывает узел структуры
 * @param {Object} node - Узел структуры
 * @param {Object} config - Настройки генерации
 * @param {Number} indent - Уровень отступа для форматирования
 * @returns {String} HTML-код для узла
 */
function processNode(node, config, indent = 0) {
  if (!node) return '';
  
  const spaces = ' '.repeat(indent);
  let html = '';
  
  // Обрабатываем узел в зависимости от его типа
  switch (node.type) {
    case 'TEXT':
      html += processTextNode(node, config, indent);
      break;
      
    case 'RECTANGLE':
    case 'ELLIPSE':
      html += processShapeNode(node, config, indent);
      break;
      
    case 'FRAME':
    case 'GROUP':
    case 'INSTANCE':
      html += processContainerNode(node, config, indent);
      break;
      
    default:
      // Для неизвестных типов создаем div
      const className = generateClassName('unknown', node, config);
      const dataAttributes = config.includeDataAttributes ? ` data-figma-id="${node.id}"` : '';
      html += `${spaces}<div class="${className}"${dataAttributes}>${node.name || ''}</div>\n`;
  }
  
  return html;
}

/**
 * Обрабатывает текстовый узел
 * @param {Object} node - Текстовый узел
 * @param {Object} config - Настройки генерации
 * @param {Number} indent - Уровень отступа
 * @returns {String} HTML-код для текстового узла
 */
function processTextNode(node, config, indent = 0) {
  const spaces = ' '.repeat(indent);
  const className = generateClassName('text', node, config);
  const dataAttributes = config.includeDataAttributes ? ` data-figma-id="${node.id}"` : '';
  const content = node.characters || node.name || '';
  
  // Выбираем HTML-тег в зависимости от размера текста и других свойств
  let tag = 'p';
  
  if (node.fontSize) {
    // Определяем тег на основе размера шрифта
    if (node.fontSize >= 32) {
      tag = 'h1';
    } else if (node.fontSize >= 24) {
      tag = 'h2';
    } else if (node.fontSize >= 20) {
      tag = 'h3';
    } else if (node.fontSize >= 18) {
      tag = 'h4';
    } else if (node.fontSize >= 16) {
      tag = 'h5';
    } else if (node.fontSize >= 14) {
      tag = 'h6';
    }
  }
  
  // Если содержимое похоже на кнопку, используем соответствующий элемент
  if (content.length < 20 && 
      (node.name || "").toLowerCase().includes('button') || 
      content.toLowerCase().includes('подроб') ||
      content.toLowerCase().includes('начать') ||
      content.toLowerCase().includes('отправить') ||
      content.toLowerCase().includes('купить') ||
      content.toLowerCase().includes('заказ') ||
      content.toLowerCase().includes('узнать')) {
    return `${spaces}<button class="${className}"${dataAttributes}>${content}</button>\n`;
  }
  
  return `${spaces}<${tag} class="${className}"${dataAttributes}>${content}</${tag}>\n`;
}

/**
 * Обрабатывает узел-фигуру (прямоугольник, эллипс)
 * @param {Object} node - Узел-фигура
 * @param {Object} config - Настройки генерации
 * @param {Number} indent - Уровень отступа
 * @returns {String} HTML-код для узла-фигуры
 */
function processShapeNode(node, config, indent = 0) {
  const spaces = ' '.repeat(indent);
  const className = generateClassName(node.type.toLowerCase(), node, config);
  const dataAttributes = config.includeDataAttributes ? ` data-figma-id="${node.id}"` : '';
  
  // Проверяем, похоже ли это на изображение
  const isImage = hasImageFill(node);
  
  if (isImage) {
    return `${spaces}<div class="${className} image-placeholder"${dataAttributes}></div>\n`;
  }
  
  return `${spaces}<div class="${className}"${dataAttributes}></div>\n`;
}

/**
 * Обрабатывает узел-контейнер (фрейм, группу, компонент)
 * @param {Object} node - Узел-контейнер
 * @param {Object} config - Настройки генерации
 * @param {Number} indent - Уровень отступа
 * @returns {String} HTML-код для узла-контейнера
 */
function processContainerNode(node, config, indent = 0) {
  const spaces = ' '.repeat(indent);
  const className = generateClassName(node.type.toLowerCase(), node, config);
  const dataAttributes = config.includeDataAttributes ? ` data-figma-id="${node.id}"` : '';
  
  // Проверяем, является ли контейнер карточкой
  const isCard = isCardElement(node);
  const elementTag = isCard ? 'article' : 'div';
  
  let html = `${spaces}<${elementTag} class="${className}${isCard ? ' card' : ''}"${dataAttributes}>\n`;
  
  // Добавляем дочерние элементы
  html += processNodeChildren(node, config, indent + 2);
  
  html += `${spaces}</${elementTag}>\n`;
  return html;
}

/**
 * Обрабатывает дочерние элементы узла
 * @param {Object} node - Родительский узел
 * @param {Object} config - Настройки генерации
 * @param {Number} indent - Уровень отступа
 * @returns {String} HTML-код для дочерних элементов
 */
function processNodeChildren(node, config, indent = 0) {
  if (!node.children || !Array.isArray(node.children) || node.children.length === 0) {
    return '';
  }
  
  let html = '';
  
  // Обрабатываем каждый дочерний элемент
  node.children.forEach(child => {
    html += processNode(child, config, indent);
  });
  
  return html;
}

/**
 * Проверяет, содержит ли узел заливку изображением
 * @param {Object} node - Узел структуры
 * @returns {Boolean} true, если узел содержит заливку изображением
 */
function hasImageFill(node) {
  if (!node || !node.fills || !Array.isArray(node.fills)) {
    return false;
  }
  
  return node.fills.some(fill => 
    fill.type === 'IMAGE' && 
    fill.visible !== false
  );
}

/**
 * Проверяет, является ли узел навигационным элементом
 * @param {Object} node - Узел структуры
 * @returns {Boolean} true, если узел похож на навигационный элемент
 */
function isNavigationElement(node) {
  if (!node) return false;
  
  const nodeName = (node.name || '').toLowerCase();
  
  // Проверяем имя узла на ключевые слова
  if (nodeName.includes('nav') || nodeName.includes('menu') || nodeName.includes('header-links')) {
    return true;
  }
  
  // Проверяем, содержит ли узел несколько текстовых элементов в горизонтальном ряду
  if (node.children && Array.isArray(node.children) && node.children.length >= 3) {
    const textItems = node.children.filter(child => child.type === 'TEXT');
    if (textItems.length >= 3) {
      // Проверяем, расположены ли они горизонтально
      const xPositions = textItems.map(item => item.position ? item.position.x : 0).sort((a, b) => a - b);
      const yPositions = textItems.map(item => item.position ? item.position.y : 0).sort((a, b) => a - b);
      
      // Если разброс по X значительно больше разброса по Y, считаем это горизонтальным меню
      const xSpread = xPositions[xPositions.length - 1] - xPositions[0];
      const ySpread = yPositions[yPositions.length - 1] - yPositions[0];
      
      if (xSpread > ySpread * 2) {
        return true;
      }
    }
  }
  
  return false;
}

/**
 * Проверяет, является ли узел логотипом
 * @param {Object} node - Узел структуры
 * @returns {Boolean} true, если узел похож на логотип
 */
function isLogoElement(node) {
  if (!node) return false;
  
  const nodeName = (node.name || '').toLowerCase();
  
  // Проверяем имя узла на ключевые слова
  if (nodeName.includes('logo') || nodeName.includes('brand') || nodeName.includes('логотип')) {
    return true;
  }
  
  // Проверяем, расположен ли узел в верхнем левом углу
  if (node.position && node.position.x < 100 && node.position.y < 100) {
    return true;
  }
  
  return false;
}

/**
 * Проверяет, является ли узел карточкой
 * @param {Object} node - Узел структуры
 * @returns {Boolean} true, если узел похож на карточку
 */
function isCardElement(node) {
  if (!node) return false;
  
  const nodeName = (node.name || '').toLowerCase();
  
  // Проверяем имя узла на ключевые слова
  if (nodeName.includes('card') || nodeName.includes('карточк') || nodeName.includes('item')) {
    return true;
  }
  
  // Проверяем, содержит ли узел компоненты типичной карточки
  if (node.children && Array.isArray(node.children)) {
    // Типичная карточка содержит изображение, заголовок и текст или кнопку
    const hasImage = node.children.some(child => 
      hasImageFill(child) || 
      (child.type === 'RECTANGLE' && child.size && child.size.width > 50 && child.size.height > 50)
    );
    
    const hasHeading = node.children.some(child => 
      child.type === 'TEXT' && 
      (child.fontSize === undefined || child.fontSize >= 16) &&
      (child.characters || '').length < 50
    );
    
    const hasText = node.children.some(child => 
      child.type === 'TEXT' && 
      (child.fontSize === undefined || child.fontSize < 16)
    );
    
    // Если есть и изображение, и заголовок, считаем это карточкой
    if ((hasImage && hasHeading) || (hasHeading && hasText)) {
      return true;
    }
  }
  
  return false;
}

/**
 * Генерирует имя класса на основе узла
 * @param {String} baseType - Базовый тип (text, rectangle, frame и т.п.)
 * @param {Object} node - Узел структуры
 * @param {Object} config - Настройки генерации
 * @returns {String} Имя класса
 */
function generateClassName(baseType, node, config) {
  if (!node) return baseType;
  
  let className = baseType;
  
  // Добавляем имя узла, если оно есть и включены семантические имена
  if (config.semanticNames && node.name) {
    const name = slugify(node.name);
    
    // Применяем нужный стиль именования
    switch (config.classNameStyle) {
      case 'kebab':
        className += ` ${name}`;
        break;
        
      case 'camel':
        className += ` ${camelCase(name)}`;
        break;
        
      case 'BEM':
        className += ` ${baseType}__${name}`;
        break;
        
      default:
        className += ` ${name}`;
    }
  }
  
  // Добавляем префикс, если указан
  if (config.prefix) {
    className = `${config.prefix}-${className}`;
  }
  
  return className;
}

/**
 * Преобразует строку в slug для имен классов
 * @param {String} text - Исходная строка
 * @returns {String} Slug-версия строки
 */
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

/**
 * Преобразует строку в camelCase
 * @param {String} text - Исходная строка
 * @returns {String} camelCase-версия строки
 */
function camelCase(text) {
  return text
    .toString()
    .toLowerCase()
    .replace(/[^a-z0-9]+(.)/g, (m, chr) => chr.toUpperCase())
    .replace(/^[A-Z]/, c => c.toLowerCase());
}

module.exports = {
  generateHTML,
  analyzeSections
}; 