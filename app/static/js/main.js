/**
 * Основные JavaScript-функции для приложения
 */

// Выполнить после загрузки документа
document.addEventListener('DOMContentLoaded', function() {
    // Инициализация всплывающих подсказок (Bootstrap Tooltips)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Инициализация всплывающих окон (Bootstrap Popovers)
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Автоматическое скрытие alert-сообщений
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Обработка клика по кнопке "Наверх"
    var scrollTopBtn = document.getElementById('scrollTopBtn');
    if (scrollTopBtn) {
        window.onscroll = function() {
            if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
                scrollTopBtn.style.display = 'block';
            } else {
                scrollTopBtn.style.display = 'none';
            }
        };
        
        scrollTopBtn.addEventListener('click', function() {
            document.body.scrollTop = 0; // Для Safari
            document.documentElement.scrollTop = 0; // Для Chrome, Firefox, IE и Opera
        });
    }
    
    // Подтверждение удаления элементов
    var deleteButtons = document.querySelectorAll('.btn-delete-confirm');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Вы уверены, что хотите удалить этот элемент?')) {
                e.preventDefault();
            }
        });
    });
    
    // Динамическая проверка форм
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Добавление текущего года в футер
    var yearElement = document.querySelector('.current-year');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }
});

/**
 * Функция для отправки AJAX-запросов
 * @param {string} url - URL для запроса
 * @param {string} method - HTTP метод (GET, POST, PUT, DELETE)
 * @param {Object} data - Данные для отправки
 * @param {function} callback - Функция обратного вызова после успешного запроса
 */
function makeAjaxRequest(url, method, data, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
    
    // Добавляем CSRF-токен для защиты от CSRF-атак
    var csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    if (csrfToken) {
        xhr.setRequestHeader('X-CSRFToken', csrfToken);
    }
    
    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            var response;
            try {
                response = JSON.parse(xhr.responseText);
            } catch (e) {
                response = xhr.responseText;
            }
            callback(null, response);
        } else {
            callback(new Error('Request failed with status ' + xhr.status), null);
        }
    };
    
    xhr.onerror = function() {
        callback(new Error('Network error'), null);
    };
    
    if (data) {
        xhr.send(JSON.stringify(data));
    } else {
        xhr.send();
    }
} 