/* JavaScript для мобильной навигации */
document.addEventListener('DOMContentLoaded', function() {
    // Кнопка переключения бокового меню
    const menuToggle = document.querySelector('.menu-toggle');
    const sidebar = document.querySelector('.sidebar') || document.querySelector('.admin-sidebar');
    const content = document.querySelector('.content-wrapper') || document.querySelector('.admin-content');
    const body = document.body;
    
    // Создаем элемент overlay для затемнения при открытом меню
    let overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    body.appendChild(overlay);
    
    // Обработчик для кнопки меню
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
            
            // Запрещаем прокрутку body при открытом меню
            if (sidebar.classList.contains('show')) {
                body.style.overflow = 'hidden';
            } else {
                body.style.overflow = '';
            }
        });
    }
    
    // Закрытие меню при клике на оверлей
    overlay.addEventListener('click', function() {
        sidebar.classList.remove('show');
        overlay.classList.remove('show');
        body.style.overflow = '';
    });
    
    // Закрытие меню при изменении размера окна
    window.addEventListener('resize', function() {
        if (window.innerWidth > 991) {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
            body.style.overflow = '';
        }
    });
    
    // Добавление кнопки меню, если её нет
    if (!menuToggle) {
        const newMenuToggle = document.createElement('button');
        newMenuToggle.className = 'menu-toggle';
        newMenuToggle.innerHTML = '<i class="fas fa-bars"></i>';
        body.appendChild(newMenuToggle);
        
        newMenuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
            overlay.classList.toggle('show');
            
            if (sidebar.classList.contains('show')) {
                body.style.overflow = 'hidden';
            } else {
                body.style.overflow = '';
            }
        });
    }
    
    // Обработка таблиц для мобильных устройств
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        if (!table.parentElement.classList.contains('table-responsive')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'table-responsive';
            table.parentNode.insertBefore(wrapper, table);
            wrapper.appendChild(table);
        }
    });
}); 