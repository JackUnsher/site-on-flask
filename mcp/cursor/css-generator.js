/**
 * CSS Generator - компонент для генерации CSS из данных Figma
 * 
 * Преобразует структуру дизайна из Figma в готовые CSS стили
 * с поддержкой переменных, семантических имен и оптимизацией
 */

const fs = require('fs');
const path = require('path');

// Глобальная карта стилей для дедупликации
const styleMap = new Map();

/**
 * Основная функция генерации CSS
 * @param {Object} structure - Структура дизайна из Figma
 * @param {Object} options - Настройки генерации
 * @returns {String} CSS-код
 */
function generateCSS(structure, options = {}) {
  // Значения по умолчанию
  const config = {
    prefix: options.prefix || '',
    useVariables: options.useVariables !== false,
    semanticNames: options.semanticNames !== false,
    optimizeOutput: options.optimizeOutput !== false,
    outputPath: options.outputPath || null
  };
  
  // Очистка карты стилей для нового запуска
  styleMap.clear();
  
  // Извлечение цветовой палитры из дизайна
  const colorPalette = extractColorPalette(structure);
  
  // Начинаем генерацию с корневых переменных
  let css = ':root {\n';
  
  // Добавляем переменные цветов
  Object.entries(colorPalette).forEach(([name, value]) => {
    css += `  --color-${name}: ${value};\n`;
  });
  
  // Добавляем типографские переменные, если они есть
  const typographyVars = extractTypography(structure);
  Object.entries(typographyVars).forEach(([name, value]) => {
    css += `  --font-${name}: ${value};\n`;
  });
  
  css += '}\n\n';
  
  // Базовые стили для всей страницы
  css += `body {
  margin: 0;
  padding: 0;
  font-family: var(--font-family, Arial, sans-serif);
  color: var(--color-text, #333);
  background-color: var(--color-background, #fff);
}\n\n`;
  
  // Обрабатываем структуру рекурсивно
  css += processStructure(structure, config);
  
  // Сохраняем в файл, если указан путь
  if (config.outputPath) {
    fs.writeFileSync(config.outputPath, css);
    console.log(`CSS сохранен в ${config.outputPath}`);
  }
  
  return css;
}

/**
 * Извлечение цветовой палитры из структуры дизайна
 * @param {Object} structure - Структура дизайна
 * @returns {Object} - Объект с переменными цветов
 */
function extractColorPalette(structure) {
  const colors = {
    primary: '#1E88E5',
    secondary: '#424242',
    accent: '#FF5722',
    background: '#FFFFFF',
    text: '#333333',
    light: '#F5F5F5',
    dark: '#212121',
    success: '#4CAF50',
    warning: '#FFC107',
    error: '#F44336'
  };
  
  // Находим все цвета в структуре
  const foundColors = new Set();
  
  function extractColorsFromNode(node) {
    if (!node) return;
    
    // Извлекаем цвета из заливок
    if (node.fills && Array.isArray(node.fills)) {
      node.fills.forEach(fill => {
        if (fill.type === 'SOLID' && fill.color) {
          const color = rgbaToHex(
            Math.round(fill.color.r * 255),
            Math.round(fill.color.g * 255),
            Math.round(fill.color.b * 255),
            fill.opacity || 1
          );
          foundColors.add(color);
        }
      });
    }
    
    // Извлекаем цвета из обводок
    if (node.strokes && Array.isArray(node.strokes)) {
      node.strokes.forEach(stroke => {
        if (stroke.type === 'SOLID' && stroke.color) {
          const color = rgbaToHex(
            Math.round(stroke.color.r * 255),
            Math.round(stroke.color.g * 255),
            Math.round(stroke.color.b * 255),
            stroke.opacity || 1
          );
          foundColors.add(color);
        }
      });
    }
    
    // Рекурсивно обрабатываем дочерние элементы
    if (node.children && Array.isArray(node.children)) {
      node.children.forEach(child => {
        extractColorsFromNode(child);
      });
    }
  }
  
  // Запускаем рекурсивное извлечение
  extractColorsFromNode(structure);
  
  // Создаем объект с переменными цветов
  // В реальном проекте здесь было бы более интеллектуальное сопоставление,
  // например, через сравнение с цветами брендбука
  
  return colors;
}

/**
 * Извлечение типографики из структуры дизайна
 * @param {Object} structure - Структура дизайна
 * @returns {Object} - Объект с переменными типографики
 */
function extractTypography(structure) {
  const typography = {
    'family': 'Arial, sans-serif',
    'size-base': '16px',
    'size-small': '14px',
    'size-large': '18px',
    'weight-normal': '400',
    'weight-bold': '700',
    'line-height': '1.5'
  };
  
  // Находим все текстовые стили в структуре
  const fontSizes = new Set();
  const fontFamilies = new Set();
  const fontWeights = new Set();
  const lineHeights = new Set();
  
  function extractTypographyFromNode(node) {
    if (!node) return;
    
    // Извлекаем стили из текстовых узлов
    if (node.type === 'TEXT') {
      if (node.fontSize) fontSizes.add(node.fontSize);
      if (node.fontName && node.fontName.family) fontFamilies.add(node.fontName.family);
      if (node.fontName && node.fontName.style) {
        // Преобразуем стиль в вес (приблизительно)
        const weight = fontStyleToWeight(node.fontName.style);
        if (weight) fontWeights.add(weight);
      }
      if (node.lineHeight && typeof node.lineHeight === 'object' && node.lineHeight.value) {
        lineHeights.add(node.lineHeight.value);
      }
    }
    
    // Рекурсивно обрабатываем дочерние элементы
    if (node.children && Array.isArray(node.children)) {
      node.children.forEach(child => {
        extractTypographyFromNode(child);
      });
    }
  }
  
  // Запускаем рекурсивное извлечение
  extractTypographyFromNode(structure);
  
  // Обновляем типографику, если нашли значения
  if (fontFamilies.size > 0) {
    typography['family'] = Array.from(fontFamilies).join(', ') + ', sans-serif';
  }
  
  // Сортируем и выбираем базовые размеры
  if (fontSizes.size > 0) {
    const sortedSizes = Array.from(fontSizes).sort((a, b) => a - b);
    
    // Определяем наиболее часто используемый размер как базовый
    // В реальном проекте здесь был бы более сложный анализ
    typography['size-base'] = `${sortedSizes[Math.floor(sortedSizes.length / 2)]}px`;
    
    if (sortedSizes.length > 2) {
      typography['size-small'] = `${sortedSizes[0]}px`;
      typography['size-large'] = `${sortedSizes[sortedSizes.length - 1]}px`;
    }
  }
  
  return typography;
}

/**
 * Преобразует строковый стиль шрифта в числовой вес
 * @param {String} style - Стиль шрифта (Regular, Bold, и т.д.)
 * @returns {Number|null} - Числовой вес шрифта
 */
function fontStyleToWeight(style) {
  if (!style) return null;
  
  // Нормализуем стиль к нижнему регистру
  const normalized = style.toLowerCase();
  
  // Соответствие стилей весам
  const styleToWeight = {
    'thin': 100,
    'extra light': 200,
    'light': 300,
    'regular': 400,
    'normal': 400,
    'medium': 500,
    'semi bold': 600,
    'semibold': 600,
    'bold': 700,
    'extra bold': 800,
    'black': 900
  };
  
  // Ищем прямое соответствие
  if (styleToWeight[normalized]) {
    return styleToWeight[normalized];
  }
  
  // Ищем частичное соответствие
  for (const [key, value] of Object.entries(styleToWeight)) {
    if (normalized.includes(key)) {
      return value;
    }
  }
  
  // По умолчанию считаем Regular
  return 400;
}

/**
 * Рекурсивная обработка структуры для генерации CSS
 * @param {Object} node - Текущий узел структуры
 * @param {Object} config - Настройки генерации
 * @param {String} parentSelector - Селектор родительского элемента
 * @returns {String} - Сгенерированный CSS
 */
function processStructure(node, config, parentSelector = '') {
  if (!node) return '';
  
  let css = '';
  
  // Генерируем селектор для текущего узла
  const selector = generateSelector(node, config, parentSelector);
  
  // Если селектор сгенерирован, создаем стили
  if (selector) {
    const styles = generateNodeStyles(node, config);
    
    // Добавляем стили, только если они не пустые
    if (styles.trim()) {
      css += `${selector} {\n${styles}}\n\n`;
    }
  }
  
  // Рекурсивно обрабатываем дочерние элементы
  if (node.children && Array.isArray(node.children)) {
    node.children.forEach(child => {
      css += processStructure(child, config, selector);
    });
  }
  
  return css;
}

/**
 * Генерирует CSS селектор для узла
 * @param {Object} node - Узел структуры
 * @param {Object} config - Настройки генерации
 * @param {String} parentSelector - Селектор родительского элемента
 * @returns {String} - CSS селектор
 */
function generateSelector(node, config, parentSelector = '') {
  if (!node || !node.id) return '';
  
  // Генерируем класс на основе типа и имени
  let className = '';
  
  if (config.semanticNames) {
    // Генерируем осмысленное имя на основе типа и имени узла
    if (node.name) {
      className = slugify(node.name);
    } else {
      className = `${node.type.toLowerCase()}-${node.id.slice(0, 8)}`;
    }
    
    // Добавляем префикс, если указан
    if (config.prefix) {
      className = `${config.prefix}-${className}`;
    }
  } else {
    // Простой селектор по ID
    className = `figma-${node.id}`;
  }
  
  // Соединяем с родительским селектором, если он есть
  if (parentSelector) {
    return `${parentSelector} .${className}`;
  }
  
  return `.${className}`;
}

/**
 * Генерирует CSS стили для узла
 * @param {Object} node - Узел структуры
 * @param {Object} config - Настройки генерации
 * @returns {String} - CSS свойства
 */
function generateNodeStyles(node, config) {
  let styles = '';
  
  // Базовые стили в зависимости от типа
  switch (node.type) {
    case 'FRAME':
    case 'GROUP':
      styles += '  display: flex;\n';
      styles += '  flex-direction: column;\n';
      break;
      
    case 'TEXT':
      if (node.characters) {
        // Применяем типографские стили
        if (node.fontSize) {
          styles += config.useVariables 
            ? '  font-size: var(--font-size-base);\n'
            : `  font-size: ${node.fontSize}px;\n`;
        }
        
        if (node.fontName && node.fontName.style) {
          const weight = fontStyleToWeight(node.fontName.style);
          styles += config.useVariables 
            ? '  font-weight: var(--font-weight-normal);\n'
            : `  font-weight: ${weight};\n`;
        }
        
        if (node.lineHeight && typeof node.lineHeight === 'object' && node.lineHeight.value) {
          styles += config.useVariables 
            ? '  line-height: var(--font-line-height);\n'
            : `  line-height: ${node.lineHeight.value};\n`;
        }
        
        if (node.textAlignHorizontal) {
          styles += `  text-align: ${node.textAlignHorizontal.toLowerCase()};\n`;
        }
      }
      break;
      
    case 'RECTANGLE':
      // Базовые стили для прямоугольников
      break;
      
    case 'ELLIPSE':
      styles += '  border-radius: 50%;\n';
      break;
  }
  
  // Общие стили для всех типов узлов
  
  // Размеры
  if (node.size) {
    if (node.size.width) {
      styles += `  width: ${node.size.width}px;\n`;
    }
    if (node.size.height) {
      styles += `  height: ${node.size.height}px;\n`;
    }
  }
  
  // Позиционирование, если нужно
  if (node.position) {
    // В большинстве случаев абсолютное позиционирование мы не хотим переносить в CSS
    // Но иногда это может быть полезно, например, для оверлеев
    if (node.isAbsolute) {
      styles += '  position: absolute;\n';
      if (node.position.x !== undefined) {
        styles += `  left: ${node.position.x}px;\n`;
      }
      if (node.position.y !== undefined) {
        styles += `  top: ${node.position.y}px;\n`;
      }
    }
  }
  
  // Заливки
  if (node.fills && Array.isArray(node.fills) && node.fills.length > 0) {
    const visibleFills = node.fills.filter(fill => fill.visible !== false);
    
    if (visibleFills.length > 0) {
      const fill = visibleFills[0]; // Берем первую видимую заливку
      
      if (fill.type === 'SOLID') {
        if (fill.color) {
          const opacity = fill.opacity !== undefined ? fill.opacity : 1;
          
          if (config.useVariables) {
            // Ищем подходящую переменную цвета
            const colorVar = findClosestColorVariable(
              Math.round(fill.color.r * 255),
              Math.round(fill.color.g * 255),
              Math.round(fill.color.b * 255)
            );
            styles += `  background-color: var(${colorVar});\n`;
            
            if (opacity < 1) {
              styles += `  opacity: ${opacity};\n`;
            }
          } else {
            const rgba = `rgba(${Math.round(fill.color.r * 255)}, ${Math.round(fill.color.g * 255)}, ${Math.round(fill.color.b * 255)}, ${opacity})`;
            styles += `  background-color: ${rgba};\n`;
          }
        }
      } else if (fill.type === 'IMAGE') {
        styles += '  background-size: cover;\n';
        styles += '  background-position: center;\n';
        // Здесь можно было бы установить background-image, если бы у нас был URL изображения
      } else if (fill.type === 'GRADIENT_LINEAR') {
        // Обработка линейных градиентов
        if (fill.gradientStops && Array.isArray(fill.gradientStops)) {
          const stops = fill.gradientStops.map(stop => {
            const color = `rgba(${Math.round(stop.color.r * 255)}, ${Math.round(stop.color.g * 255)}, ${Math.round(stop.color.b * 255)}, ${stop.color.a || 1})`;
            return `${color} ${Math.round(stop.position * 100)}%`;
          }).join(', ');
          
          let angle = '90deg'; // По умолчанию
          if (fill.gradientTransform) {
            // Вычисление угла из градиентной трансформации
            // Это упрощенная версия, на практике нужна более сложная логика
            angle = '90deg';
          }
          
          styles += `  background: linear-gradient(${angle}, ${stops});\n`;
        }
      }
    }
  }
  
  // Обводки
  if (node.strokes && Array.isArray(node.strokes) && node.strokes.length > 0) {
    const visibleStrokes = node.strokes.filter(stroke => stroke.visible !== false);
    
    if (visibleStrokes.length > 0) {
      const stroke = visibleStrokes[0]; // Берем первую видимую обводку
      
      if (stroke.type === 'SOLID') {
        if (stroke.color) {
          const opacity = stroke.opacity !== undefined ? stroke.opacity : 1;
          const weight = node.strokeWeight || 1;
          
          if (config.useVariables) {
            // Ищем подходящую переменную цвета
            const colorVar = findClosestColorVariable(
              Math.round(stroke.color.r * 255),
              Math.round(stroke.color.g * 255),
              Math.round(stroke.color.b * 255)
            );
            styles += `  border: ${weight}px solid var(${colorVar});\n`;
          } else {
            const rgba = `rgba(${Math.round(stroke.color.r * 255)}, ${Math.round(stroke.color.g * 255)}, ${Math.round(stroke.color.b * 255)}, ${opacity})`;
            styles += `  border: ${weight}px solid ${rgba};\n`;
          }
        }
      }
    }
  }
  
  // Скругление углов
  if (node.cornerRadius && node.cornerRadius > 0) {
    styles += `  border-radius: ${node.cornerRadius}px;\n`;
  }
  
  // Эффекты (тени и другие)
  if (node.effects && Array.isArray(node.effects)) {
    const shadows = node.effects.filter(effect => 
      (effect.type === 'DROP_SHADOW' || effect.type === 'INNER_SHADOW') && 
      effect.visible !== false
    );
    
    if (shadows.length > 0) {
      const shadowStrings = shadows.map(shadow => {
        const color = shadow.color;
        if (!color) return null;
        
        const rgba = `rgba(${Math.round(color.r * 255)}, ${Math.round(color.g * 255)}, ${Math.round(color.b * 255)}, ${color.a || 1})`;
        const shadowType = shadow.type === 'INNER_SHADOW' ? 'inset ' : '';
        return `${shadowType}${shadow.offset?.x || 0}px ${shadow.offset?.y || 0}px ${shadow.radius || 0}px ${shadow.spread || 0}px ${rgba}`;
      }).filter(Boolean).join(', ');
      
      if (shadowStrings) {
        styles += `  box-shadow: ${shadowStrings};\n`;
      }
    }
    
    // Размытие
    const blurs = node.effects.filter(effect =>
      (effect.type === 'LAYER_BLUR' || effect.type === 'BACKGROUND_BLUR') &&
      effect.visible !== false
    );
    
    if (blurs.length > 0) {
      const blur = blurs[0]; // Берем первое размытие
      if (blur.type === 'LAYER_BLUR') {
        styles += `  filter: blur(${blur.radius}px);\n`;
      } else if (blur.type === 'BACKGROUND_BLUR') {
        styles += `  backdrop-filter: blur(${blur.radius}px);\n`;
      }
    }
  }
  
  return styles;
}

/**
 * Находит ближайшую переменную цвета
 * @param {Number} r - Красный компонент (0-255)
 * @param {Number} g - Зеленый компонент (0-255)
 * @param {Number} b - Синий компонент (0-255)
 * @returns {String} - Имя переменной цвета
 */
function findClosestColorVariable(r, g, b) {
  // Стандартные переменные цветов
  const colorVars = {
    'primary': [30, 136, 229],     // #1E88E5
    'secondary': [66, 66, 66],     // #424242
    'accent': [255, 87, 34],       // #FF5722
    'background': [255, 255, 255], // #FFFFFF
    'text': [51, 51, 51],          // #333333
    'light': [245, 245, 245],      // #F5F5F5
    'dark': [33, 33, 33],          // #212121
    'success': [76, 175, 80],      // #4CAF50
    'warning': [255, 193, 7],      // #FFC107
    'error': [244, 67, 54]         // #F44336
  };
  
  // Ищем ближайший цвет по евклидову расстоянию
  let closestVar = '--color-text';
  let minDistance = Infinity;
  
  for (const [name, color] of Object.entries(colorVars)) {
    const distance = Math.sqrt(
      Math.pow(r - color[0], 2) +
      Math.pow(g - color[1], 2) +
      Math.pow(b - color[2], 2)
    );
    
    if (distance < minDistance) {
      minDistance = distance;
      closestVar = `--color-${name}`;
    }
  }
  
  return closestVar;
}

/**
 * Преобразует RGBA в HEX
 * @param {Number} r - Красный компонент (0-255)
 * @param {Number} g - Зеленый компонент (0-255)
 * @param {Number} b - Синий компонент (0-255)
 * @param {Number} a - Альфа-канал (0-1)
 * @returns {String} - HEX-представление цвета
 */
function rgbaToHex(r, g, b, a = 1) {
  const toHex = (c) => {
    const hex = Math.round(c).toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  };
  
  const hex = `#${toHex(r)}${toHex(g)}${toHex(b)}`;
  
  if (a < 1) {
    return `${hex}${toHex(Math.round(a * 255))}`;
  }
  
  return hex;
}

/**
 * Преобразует строку в slug (для имен классов)
 * @param {String} text - Исходная строка
 * @returns {String} - Slug-версия строки
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

module.exports = {
  generateCSS,
  extractColorPalette,
  extractTypography
}; 