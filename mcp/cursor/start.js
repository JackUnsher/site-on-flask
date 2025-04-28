#!/usr/bin/env node

/**
 * Скрипт запуска Cursor MCP сервера
 * Поддерживает различные режимы работы и конфигурацию
 */

const { program } = require('commander');
const chalk = require('chalk');
const path = require('path');
const fs = require('fs');
const { startServer } = require('./server');
const chokidar = require('chokidar');

// Настройка CLI интерфейса
program
  .name('cursor-mcp')
  .description('Cursor MCP - интеграция Figma и Cursor IDE')
  .version('1.0.0')
  .option('-p, --port <number>', 'Порт для WebSocket сервера', '9912')
  .option('-w, --watch', 'Активировать наблюдение за файлами проекта', false)
  .option('-a, --auto-import', 'Автоматически импортировать изображения и структуру', false)
  .option('-d, --debug', 'Включить подробное логирование', false)
  .option('-c, --config <path>', 'Путь к файлу конфигурации')
  .option('-o, --output <directory>', 'Директория для вывода генерируемых файлов')
  .parse(process.argv);

const options = program.opts();

// Проверка и загрузка конфигурации
let config = {
  port: parseInt(options.port) || 9912,
  watchMode: options.watch,
  autoImport: options.autoImport,
  debug: options.debug,
  outputDirectory: options.output || process.cwd(),
};

// Если указан файл конфигурации, загружаем из него
if (options.config) {
  try {
    const configPath = path.resolve(process.cwd(), options.config);
    if (fs.existsSync(configPath)) {
      const configData = require(configPath);
      config = { ...config, ...configData };
      console.log(chalk.green('✓ Конфигурация загружена из:', configPath));
    } else {
      console.warn(chalk.yellow('⚠ Файл конфигурации не найден:', configPath));
    }
  } catch (error) {
    console.error(chalk.red('✗ Ошибка загрузки конфигурации:'), error.message);
  }
}

// Выводим информацию о запуске
console.log(chalk.cyan('╔════════════════════════════════════╗'));
console.log(chalk.cyan('║       Cursor MCP Server 1.0        ║'));
console.log(chalk.cyan('╚════════════════════════════════════╝'));
console.log('');
console.log(chalk.white('• Порт:'), chalk.yellow(config.port));
console.log(chalk.white('• Режим наблюдения:'), config.watchMode ? chalk.green('Включен') : chalk.red('Выключен'));
console.log(chalk.white('• Автоимпорт:'), config.autoImport ? chalk.green('Включен') : chalk.red('Выключен'));
console.log(chalk.white('• Отладка:'), config.debug ? chalk.green('Включена') : chalk.red('Выключена'));
console.log(chalk.white('• Выходная директория:'), chalk.yellow(config.outputDirectory));
console.log('');

// Запуск сервера
const server = startServer();

// Если активирован режим наблюдения, настраиваем его
if (config.watchMode) {
  console.log(chalk.cyan('✓ Режим наблюдения активирован'));
  
  // Определяем директории для наблюдения
  const watchPaths = [
    path.join(process.cwd(), 'app/templates/**/*.html'),
    path.join(process.cwd(), 'app/static/css/**/*.css'),
    path.join(process.cwd(), 'assets/**/*'),
    path.join(process.cwd(), 'components/**/*'),
  ];
  
  // Инициализируем наблюдателя
  const watcher = chokidar.watch(watchPaths, {
    ignored: /(^|[\/\\])\../, // игнорируем скрытые файлы
    persistent: true
  });
  
  // Обработка событий наблюдателя
  watcher
    .on('ready', () => {
      console.log(chalk.green('✓ Наблюдение за файлами запущено'));
    })
    .on('change', (path) => {
      console.log(chalk.yellow(`Файл изменён: ${path}`));
      // Здесь можно добавить логику для обработки изменений файлов
    })
    .on('error', (error) => {
      console.error(chalk.red('✗ Ошибка наблюдения:'), error);
    });
}

// Обработка завершения процесса
process.on('SIGINT', () => {
  console.log(chalk.yellow('\nЗавершение работы сервера...'));
  server.close(() => {
    console.log(chalk.green('✓ Сервер остановлен'));
    process.exit(0);
  });
});

// Обработка необработанных исключений
process.on('uncaughtException', (err) => {
  console.error(chalk.red('✗ Необработанное исключение:'), err);
  process.exit(1);
});

console.log(chalk.green('✓ Сервер запущен и готов к работе!'));
console.log(chalk.gray('Нажмите Ctrl+C для завершения')); 