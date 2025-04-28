// Общие JavaScript функции для сайта

// Функция для обработки фиксированного хедера при прокрутке
function initStickyHeader() {
    const header = document.querySelector('.site-header');
    if (!header) return;
    
    const scrollThreshold = 100;
    let isHeaderSticky = false;
    let ticking = false;
    
    function handleScroll() {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const currentScroll = window.scrollY;
                const shouldBeSticky = currentScroll > scrollThreshold;
                
                // Только если изменилось состояние
                if (isHeaderSticky !== shouldBeSticky) {
                    isHeaderSticky = shouldBeSticky;
                    
                    if (shouldBeSticky) {
                        header.classList.add('sticky-header');
                    } else {
                        header.classList.remove('sticky-header');
                    }
                }
                
                ticking = false;
            });
            ticking = true;
        }
    }
    
    // Проверяем позицию прокрутки при загрузке страницы
    handleScroll();
    
    // Добавляем обработчик события прокрутки с улучшенной производительностью
    window.addEventListener('scroll', handleScroll, { passive: true });
}

// Функция для закрытия флэш-сообщений
document.addEventListener('DOMContentLoaded', function() {
    // Получаем все кнопки закрытия для флэш-сообщений
    const closeButtons = document.querySelectorAll('.alert .btn-close');
    
    // Добавляем обработчик события для каждой кнопки
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Находим родительский элемент alert и удаляем его
            const alert = this.parentElement;
            alert.classList.remove('show');
            alert.classList.add('fade');
            setTimeout(() => {
                alert.remove();
            }, 150);
        });
    });
    
    // Автоматически скрываем флэш-сообщения через 5 секунд
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            alert.classList.remove('show');
            alert.classList.add('fade');
            setTimeout(() => {
                alert.remove();
            }, 150);
        });
    }, 5000);

    // Мобильное меню
    const menuToggle = document.querySelector('.menu-toggle');
    const navContent = document.querySelector('.nav-content');
    
    if (menuToggle && navContent) {
        menuToggle.addEventListener('click', function() {
            navContent.classList.toggle('active');
            menuToggle.classList.toggle('active');
        });
    }
    
    // Закрытие уведомлений
    const notifications = document.querySelectorAll('.notification');
    notifications.forEach(notification => {
        const closeButton = notification.querySelector('.notification-close');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                notification.style.opacity = '0';
                setTimeout(() => {
                    notification.remove();
                }, 300);
            });
        }
    });
    
    // Анимация появления элементов при скролле
    const observerOptions = {
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.card, .button, .gradient-text').forEach(el => {
        observer.observe(el);
    });
}); 

// Основной JavaScript файл

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация фиксированного хедера
    initStickyHeader();
    
    // Инициализация мобильного меню
    initMobileMenu();
    
    // Обработка языкового селектора
    initLanguageSelector();
    
    // Инициализация уведомлений
    initNotifications();
    
    // Проверка и исправление iOS специфичных проблем
    fixiOSSpecifics();
    
    // Добавляем класс для определения типа устройства
    detectDeviceType();
    
    // Оптимизация для сенсорных устройств
    optimizeTouchInteraction();
    
    // Прогрессивная загрузка изображений
    initProgressiveImages();
    lazyLoadImages();
    
    // Оптимизация производительности
    optimizePerformance();
    
    // Анимация появления элементов при прокрутке
    animateOnScroll();
    window.addEventListener('scroll', animateOnScroll);
    
    // Обработка FAQ аккордеона
    const faqItems = document.querySelectorAll('.faq-item');
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        question.addEventListener('click', () => {
            const isActive = item.classList.contains('active');
            
            // Закрываем все активные элементы
            faqItems.forEach(faqItem => {
                faqItem.classList.remove('active');
            });
            
            // Если элемент не был активен, открываем его
            if (!isActive) {
                item.classList.add('active');
            }
        });
    });
    
    // Обработка переключения планов тарифов
    const pricingCards = document.querySelectorAll('.pricing-card');
    pricingCards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            pricingCards.forEach(c => c.classList.remove('hovered'));
            card.classList.add('hovered');
        });
    });
    
    // Плавная прокрутка до якорей
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 80,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Анимация счетчиков статистики
    animateCounters();
    
    // Обработка подписки на рассылку
    const newsletterForm = document.querySelector('.newsletter-form');
    if (newsletterForm) {
        newsletterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const emailInput = this.querySelector('.newsletter-input');
            const email = emailInput.value.trim();
            
            if (email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                // Здесь будет AJAX-запрос на сервер для сохранения email
                alert('Спасибо за подписку!');
                emailInput.value = '';
            } else {
                alert('Пожалуйста, введите корректный email');
            }
        });
    }
});

// Мобильное меню
function initMobileMenu() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navContent = document.querySelector('.nav-content');
    
    if (menuToggle && navContent) {
        menuToggle.addEventListener('click', function() {
            menuToggle.classList.toggle('active');
            navContent.classList.toggle('active');
            document.body.classList.toggle('menu-open');
            
            // Предотвращаем скролл body при открытом меню
            if (navContent.classList.contains('active')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        });
        
        // Закрытие меню при клике на ссылку
        const navLinks = navContent.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                menuToggle.classList.remove('active');
                navContent.classList.remove('active');
                document.body.classList.remove('menu-open');
                document.body.style.overflow = '';
            });
        });
    }
    
    // Обработка клика вне меню для его закрытия
    document.addEventListener('click', function(event) {
        if (navContent && navContent.classList.contains('active')) {
            const isClickInside = navContent.contains(event.target) || 
                                  menuToggle.contains(event.target);
            
            if (!isClickInside) {
                menuToggle.classList.remove('active');
                navContent.classList.remove('active');
                document.body.classList.remove('menu-open');
                document.body.style.overflow = '';
            }
        }
    });
}

// Языковой селектор
function initLanguageSelector() {
    const langButton = document.getElementById('languageButton');
    const langDropdown = document.querySelector('.language-dropdown');
    
    if (langButton && langDropdown) {
        langButton.addEventListener('click', function(e) {
            e.stopPropagation();
            langDropdown.classList.toggle('show');
        });
        
        // Закрытие при клике вне селектора
        document.addEventListener('click', function() {
            if (langDropdown.classList.contains('show')) {
                langDropdown.classList.remove('show');
            }
        });
    }
}

// Инициализация уведомлений
function initNotifications() {
    const notifications = document.querySelectorAll('.notification');
    const closeButtons = document.querySelectorAll('.notification-close');
    
    notifications.forEach(notification => {
        // Автоматическое скрытие через 5 секунд
        setTimeout(() => {
            notification.classList.add('notification-hiding');
            
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    });
    
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const notification = this.closest('.notification');
            notification.classList.add('notification-hiding');
            
            setTimeout(() => {
                notification.remove();
            }, 300);
        });
    });
}

// Исправление iOS-специфичных проблем
function fixiOSSpecifics() {
    // Проверяем, является ли устройство iOS
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
    
    if (isIOS) {
        // Добавляем класс для iOS-специфичных стилей
        document.documentElement.classList.add('ios-device');
        
        // Исправление проблемы с фиксированными элементами при фокусе на поля ввода
        const inputs = document.querySelectorAll('input, textarea, select');
        const fixedElements = document.querySelectorAll('.fixed-element');
        
        inputs.forEach(input => {
            input.addEventListener('focus', () => {
                fixedElements.forEach(el => {
                    el.style.position = 'absolute';
                });
            });
            
            input.addEventListener('blur', () => {
                fixedElements.forEach(el => {
                    el.style.position = '';
                });
            });
        });
        
        // Исправление для 100vh в Safari на iOS
        const fullHeightElements = document.querySelectorAll('.full-height');
        function setHeight() {
            const vh = window.innerHeight * 0.01;
            document.documentElement.style.setProperty('--vh', `${vh}px`);
            
            fullHeightElements.forEach(el => {
                el.style.height = `calc(var(--vh, 1vh) * 100)`;
            });
        }
        
        setHeight();
        window.addEventListener('resize', setHeight);
    }
}

// Определение типа устройства
function detectDeviceType() {
    // Проверка на мобильное устройство
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    
    if (isMobile) {
        document.documentElement.classList.add('mobile-device');
    } else {
        document.documentElement.classList.add('desktop-device');
    }
    
    // Проверка на сенсорный экран
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
        document.documentElement.classList.add('touch-device');
    } else {
        document.documentElement.classList.add('no-touch-device');
    }
    
    // Проверка на ориентацию экрана
    checkOrientation();
    window.addEventListener('resize', checkOrientation);
}

// Проверка ориентации экрана
function checkOrientation() {
    if (window.innerHeight > window.innerWidth) {
        document.documentElement.classList.add('portrait');
        document.documentElement.classList.remove('landscape');
    } else {
        document.documentElement.classList.add('landscape');
        document.documentElement.classList.remove('portrait');
    }
}

// Оптимизация для сенсорных устройств
function optimizeTouchInteraction() {
    // Добавляем метку о загрузке JS для использования в CSS
    document.documentElement.classList.add('js-loaded');
    
    // Оптимизация для ссылок и кнопок
    const interactiveElements = document.querySelectorAll('a, button, .clickable');
    
    interactiveElements.forEach(el => {
        // Добавляем атрибут role="button" для семантики, если элемент кликабельный
        if (el.classList.contains('clickable') && !el.getAttribute('role')) {
            el.setAttribute('role', 'button');
        }
        
        // Добавляем обработчик для более быстрого отклика
        el.addEventListener('touchstart', function() {
            this.classList.add('active-touch');
        }, { passive: true });
        
        el.addEventListener('touchend', function() {
            this.classList.remove('active-touch');
        }, { passive: true });
    });
    
    // Проверяем и улучшаем доступность интерактивных элементов
    improveAccessibility();
}

// Улучшение доступности
function improveAccessibility() {
    // Добавляем подсказки для полей, у которых нет label
    const inputs = document.querySelectorAll('input:not([type="hidden"]), textarea, select');
    
    inputs.forEach(input => {
        if (!input.getAttribute('aria-label') && !document.querySelector(`label[for="${input.id}"]`)) {
            const placeholder = input.getAttribute('placeholder');
            if (placeholder) {
                input.setAttribute('aria-label', placeholder);
            }
        }
    });
    
    // Настраиваем атрибуты tabindex для правильной навигации с клавиатуры
    const skipLinks = document.querySelectorAll('.skip-link');
    skipLinks.forEach(link => {
        link.setAttribute('tabindex', '1');
    });
}

// Прогрессивная загрузка изображений
document.addEventListener('DOMContentLoaded', function() {
    initProgressiveImages();
    lazyLoadImages();
});

// Инициализация прогрессивной загрузки изображений
function initProgressiveImages() {
    const progressiveImages = document.querySelectorAll('.progressive-image-container');
    
    progressiveImages.forEach(container => {
        const placeholder = container.querySelector('.progressive-image-placeholder');
        const image = container.querySelector('.progressive-image');
        
        if (image && image.getAttribute('data-src')) {
            const imgSrc = image.getAttribute('data-src');
            const newImage = new Image();
            newImage.src = imgSrc;
            
            newImage.onload = function() {
                image.src = imgSrc;
                image.classList.add('loaded');
                if (placeholder) {
                    placeholder.style.opacity = 0;
                }
            };
        }
    });
}

// Ленивая загрузка изображений
function lazyLoadImages() {
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('img.lazy');
        
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const image = entry.target;
                    if (image.dataset.src) {
                        image.src = image.dataset.src;
                        image.classList.remove('lazy');
                        imageObserver.unobserve(image);
                    }
                }
            });
        });
        
        lazyImages.forEach(image => {
            imageObserver.observe(image);
        });
    } else {
        // Фоллбэк для браузеров, не поддерживающих IntersectionObserver
        setTimeout(loadLazyImagesLegacy, 250);
    }
}

// Фоллбэк для ленивой загрузки
function loadLazyImagesLegacy() {
    const lazyImages = document.querySelectorAll('img.lazy');
    
    lazyImages.forEach(image => {
        if (image.dataset.src) {
            image.src = image.dataset.src;
            image.classList.remove('lazy');
        }
    });
}

// Оптимизация производительности
document.addEventListener('DOMContentLoaded', function() {
    optimizePerformance();
});

// Функции оптимизации производительности
function optimizePerformance() {
    // Детектирование медленных устройств
    const isLowEndDevice = 
        navigator.hardwareConcurrency <= 2 || 
        navigator.deviceMemory <= 2 || 
        /(Android [4-6])|(iPhone OS [7-9])/.test(navigator.userAgent);
    
    if (isLowEndDevice) {
        document.body.classList.add('low-end-device');
        
        // Отключение тяжелых анимаций на слабых устройствах
        const animatedElements = document.querySelectorAll('.animated-element, .feature-card, .pricing-card, .hero-content');
        animatedElements.forEach(el => {
            el.classList.add('reduce-motion-mobile');
        });
        
        // Упрощение градиентов
        const gradientElements = document.querySelectorAll('.gradient-bg');
        gradientElements.forEach(el => {
            el.classList.add('simple-bg');
        });
    }
    
    // Оптимизация скроллинга
    let isTicking = false;
    window.addEventListener('scroll', function() {
        if (!isTicking) {
            window.requestAnimationFrame(function() {
                // Оптимизированный обработчик скролла
                const scrollElements = document.querySelectorAll('.scroll-animate');
                scrollElements.forEach(el => {
                    if (isElementInViewport(el)) {
                        el.classList.add('in-viewport');
                    }
                });
                isTicking = false;
            });
            isTicking = true;
        }
    });
}

// Проверка, находится ли элемент в видимой области
function isElementInViewport(el) {
    const rect = el.getBoundingClientRect();
    
    return (
        rect.top <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.bottom >= 0 &&
        rect.left <= (window.innerWidth || document.documentElement.clientWidth) &&
        rect.right >= 0
    );
}

// Анимация появления элементов при прокрутке
function animateOnScroll() {
    const elements = document.querySelectorAll('.benefit-card, .service-card');
    
    elements.forEach(element => {
        const elementTop = element.getBoundingClientRect().top;
        const elementBottom = element.getBoundingClientRect().bottom;
        
        if (elementTop < window.innerHeight && elementBottom > 0) {
            element.classList.add('fade-in');
        }
    });
}

// Анимация счетчиков статистики
function animateCounters() {
    const counterElements = document.querySelectorAll('.hero-stat-value');
    counterElements.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-count'));
        const duration = 2000; // 2 секунды
        const increment = target / (duration / 16); // 60fps
        
        let current = 0;
        const timer = setInterval(() => {
            current += increment;
            counter.textContent = Math.floor(current).toLocaleString();
            
            if (current >= target) {
                counter.textContent = target.toLocaleString();
                clearInterval(timer);
            }
        }, 16);
    });
}

// Функциональность для FAQ
document.addEventListener('DOMContentLoaded', () => {
    // Обработка FAQ
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        
        question.addEventListener('click', () => {
            const isActive = item.classList.contains('active');
            
            // Закрываем все вопросы
            faqItems.forEach(faqItem => {
                faqItem.classList.remove('active');
            });
            
            // Если элемент не был активным, делаем его активным
            if (!isActive) {
                item.classList.add('active');
            }
        });
    });
    
    // Открываем первый вопрос по умолчанию
    if (faqItems.length > 0) {
        faqItems[0].classList.add('active');
    }
    
    // Анимация для цифр в hero секции
    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start).toLocaleString();
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }
    
    // Запускаем анимацию цифр, когда страница загружена
    const statistics = document.querySelectorAll('.hero-stat-value');
    
    if (statistics.length > 0) {
        statistics.forEach(stat => {
            const endValue = parseInt(stat.getAttribute('data-value') || '0');
            animateValue(stat, 0, endValue, 1500);
        });
    }
    
    // Активация табов для периодов в секции графиков
    const periodOptions = document.querySelectorAll('.period-option');
    const chartContainers = document.querySelectorAll('.chart-data');
    
    if (periodOptions.length > 0 && chartContainers.length > 0) {
        periodOptions.forEach(option => {
            option.addEventListener('click', () => {
                // Удаляем активный класс у всех опций
                periodOptions.forEach(opt => opt.classList.remove('active'));
                
                // Добавляем активный класс к нажатой опции
                option.classList.add('active');
                
                // Получаем период
                const period = option.getAttribute('data-period');
                
                // Скрываем все данные графиков и показываем только нужные
                chartContainers.forEach(container => {
                    container.style.display = 'none';
                    if (container.getAttribute('data-period') === period) {
                        container.style.display = 'block';
                    }
                });
            });
        });
        
        // Активируем первую опцию по умолчанию
        if (periodOptions[0]) {
            periodOptions[0].click();
        }
    }
}); 