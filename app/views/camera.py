from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.decorators import check_confirmed
from flask_babel import _
import os
from flask import current_app
import time
import random
from datetime import datetime

# Создаем blueprint для камер
camera_bp = Blueprint('camera', __name__)

# Список камер для демонстрации
DEMO_CAMERAS = [
    {
        'id': 1, 
        'name': 'Mining Farm A - Main Hall',
        'location': 'Siberia, Russia', 
        'status': 'online',
        'url': '#',
        'preview': 'camera_previews/camera1.jpg',
        'last_updated': datetime.utcnow()
    },
    {
        'id': 2, 
        'name': 'Mining Farm A - Cooling System', 
        'location': 'Siberia, Russia',
        'status': 'online',
        'url': '#',
        'preview': 'camera_previews/camera2.jpg',
        'last_updated': datetime.utcnow()
    },
    {
        'id': 3, 
        'name': 'Mining Farm B - Security Gate', 
        'location': 'Iceland', 
        'status': 'offline',
        'url': '#',
        'preview': 'camera_previews/camera3.jpg',
        'last_updated': datetime.utcnow()
    },
    {
        'id': 4, 
        'name': 'Mining Farm B - Server Room', 
        'location': 'Iceland', 
        'status': 'online',
        'url': '#',
        'preview': 'camera_previews/camera4.jpg',
        'last_updated': datetime.utcnow()
    },
    {
        'id': 5, 
        'name': 'Mining Farm C - Main Entrance', 
        'location': 'Norway', 
        'status': 'maintenance',
        'url': '#',
        'preview': 'camera_previews/camera5.jpg',
        'last_updated': datetime.utcnow()
    }
]

@camera_bp.before_request
@login_required
def before_request():
    """Выполняется перед каждым запросом к blueprint camera"""
    pass

@camera_bp.route('/')
def index():
    """Показывает список всех доступных камер"""
    # В реальном приложении здесь должна быть выборка камер из БД
    cameras = DEMO_CAMERAS
    
    # Обновляем статусы камер случайным образом для демонстрации
    for camera in cameras:
        if random.random() > 0.7:  # 30% шанс изменения статуса
            statuses = ['online', 'offline', 'maintenance']
            camera['status'] = random.choice(statuses)
        camera['last_updated'] = datetime.utcnow()
    
    return render_template('camera/index.html', 
                          title=_('Camera Views'),
                          cameras=cameras,
                          current_time=datetime.utcnow())

@camera_bp.route('/view/<int:camera_id>')
def view(camera_id):
    """Показывает видеопоток с конкретной камеры"""
    # В реальном приложении здесь должна быть выборка камеры из БД по ID
    camera = next((cam for cam in DEMO_CAMERAS if cam['id'] == camera_id), None)
    
    if not camera:
        flash(_('Requested camera not found'), 'error')
        return redirect(url_for('camera.index'))
    
    # Обновляем время последнего просмотра
    camera['last_updated'] = datetime.utcnow()
    
    return render_template('camera/view.html', 
                          title=_('Camera View - {}').format(camera['name']),
                          camera=camera)

@camera_bp.route('/api/status')
def api_status():
    """API endpoint для получения статуса всех камер"""
    # В реальном приложении здесь должна быть выборка камер из БД
    cameras = [{
        'id': camera['id'],
        'name': camera['name'],
        'status': camera['status'],
        'last_updated': camera['last_updated'].isoformat()
    } for camera in DEMO_CAMERAS]
    
    return jsonify({
        'success': True,
        'cameras': cameras,
        'timestamp': datetime.utcnow().isoformat()
    })

@camera_bp.route('/api/update_status/<int:camera_id>', methods=['POST'])
def api_update_status(camera_id):
    """API endpoint для обновления статуса камеры (для демонстрации)"""
    status = request.json.get('status')
    
    if not status or status not in ['online', 'offline', 'maintenance']:
        return jsonify({
            'success': False,
            'error': 'Invalid status'
        }), 400
    
    # В реальном приложении здесь должно быть обновление статуса в БД
    camera = next((cam for cam in DEMO_CAMERAS if cam['id'] == camera_id), None)
    
    if not camera:
        return jsonify({
            'success': False,
            'error': 'Camera not found'
        }), 404
    
    camera['status'] = status
    camera['last_updated'] = datetime.utcnow()
    
    return jsonify({
        'success': True,
        'camera': {
            'id': camera['id'],
            'name': camera['name'],
            'status': camera['status'],
            'last_updated': camera['last_updated'].isoformat()
        }
    }) 