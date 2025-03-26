// Основной JavaScript файл для интерактивности интерфейса

document.addEventListener('DOMContentLoaded', function() {
    // Обработка исчезновения flash-сообщений
    const flashMessages = document.querySelectorAll('.flash-message');
    
    if (flashMessages.length > 0) {
        flashMessages.forEach(message => {
            // Добавляем кнопку закрытия к каждому flash-сообщению
            const closeButton = document.createElement('button');
            closeButton.innerHTML = '&times;';
            closeButton.className = 'flash-close';
            closeButton.addEventListener('click', function() {
                message.style.display = 'none';
            });
            
            message.appendChild(closeButton);
            
            // Автоматически скрываем сообщение через 5 секунд
            setTimeout(() => {
                message.style.opacity = '0';
                message.style.transition = 'opacity 0.5s';
                
                setTimeout(() => {
                    message.style.display = 'none';
                }, 500);
            }, 5000);
        });
    }
    
    // OPTIMIZE: Consider using a JavaScript library for complex UI interactions
    
    // Функция для активации навигационных элементов на основе текущего URL
    function setActiveNavItem() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }
    
    setActiveNavItem();
    
    // Обработка форм с AJAX (если потребуется)
    // TODO: Implement AJAX form submission for smooth UX
});

// Глобальная обработка ошибок
window.addEventListener('error', function(e) {
    console.error('Произошла ошибка:', e.message);
    // Можно добавить логирование ошибок на сервер
}); 