from flask import render_template, jsonify
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    """Регистрирует обработчики ошибок для приложения"""
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Обработчик ошибки 400 Bad Request."""
        if request_wants_json():
            return jsonify({"error": "Bad request", "details": str(error)}), 400
        return render_template('errors/400.html', error=error), 400
    
    @app.errorhandler(401)
    def unauthorized_error(error):
        """Обработчик ошибки 401 Unauthorized."""
        if request_wants_json():
            return jsonify({"error": "Unauthorized", "details": str(error)}), 401
        return render_template('errors/401.html', error=error), 401
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Обработчик ошибки 403 Forbidden."""
        if request_wants_json():
            return jsonify({"error": "Forbidden", "details": str(error)}), 403
        return render_template('errors/403.html', error=error), 403
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Обработчик ошибки 404 Not Found."""
        if request_wants_json():
            return jsonify({"error": "Not found", "details": str(error)}), 404
        return render_template('errors/404.html', error=error), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Обработчик ошибки 500 Internal Server Error."""
        app.logger.error(f"Server Error: {error}")
        if request_wants_json():
            return jsonify({"error": "Internal server error", "details": str(error)}), 500
        return render_template('errors/500.html', error=error), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Обработчик для всех необработанных исключений."""
        app.logger.error(f"Unhandled Exception: {error}", exc_info=True)
        
        # Если это уже HTTP-исключение, обрабатываем его как есть
        if isinstance(error, HTTPException):
            if request_wants_json():
                return jsonify({
                    "error": error.name,
                    "details": error.description
                }), error.code
            return render_template(f'errors/{error.code}.html', error=error), error.code
        
        # Для всех других исключений возвращаем 500
        if request_wants_json():
            return jsonify({
                "error": "Internal server error", 
                "details": str(error)
            }), 500
        return render_template('errors/500.html', error=error), 500


def request_wants_json():
    """Определяет, хочет ли клиент получить ответ в формате JSON."""
    from flask import request
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return (best == 'application/json' and
            request.accept_mimetypes[best] > request.accept_mimetypes['text/html']) 