from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, current_app
from flask_babel import _
from app.models.content import Content
from app.models.contract import ContractPlan
from datetime import datetime

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@main_bp.route('/index')
def index():
    """Главная страница сайта"""
    plans = ContractPlan.query.filter_by(is_active=True).all()
    return render_template('main/index.html', plans=plans)


@main_bp.route('/pricing')
def pricing():
    """Отображает информацию о тарифах"""
    # Получаем все активные тарифные планы
    plans = ContractPlan.query.filter_by(is_active=True).all()
    
    pricing_content = Content.get_by_type('pricing')
    if not pricing_content:
        # Если контент не найден, создаем заглушку
        pricing_content = Content(
            type='pricing',
            title=_('Pricing Plans'),
            content=_('Our pricing plans information is not available.'),
            is_html=False,
            last_updated=datetime.utcnow()
        )
    
    return render_template(
        'pricing.html', 
        title=_('Pricing Plans'),
        plans=plans,
        page=pricing_content
    )


@main_bp.route('/terms')
def terms():
    """Отображает условия использования"""
    terms_content = Content.get_by_type('terms')
    
    if not terms_content:
        # Если контент не найден, создаем заглушку
        terms_content = Content(
            type='terms',
            title=_('Terms of Use'),
            content=_('Terms of use content is not available.'),
            is_html=False,
            last_updated=datetime.utcnow()
        )
    
    return render_template('static_page.html', page=terms_content)


@main_bp.route('/privacy')
def privacy():
    """Отображает политику конфиденциальности"""
    privacy_content = Content.get_by_type('privacy')
    
    if not privacy_content:
        # Если контент не найден, создаем заглушку
        privacy_content = Content(
            type='privacy',
            title=_('Privacy Policy'),
            content=_('Privacy policy content is not available.'),
            is_html=False,
            last_updated=datetime.utcnow()
        )
    
    return render_template('static_page.html', page=privacy_content)


@main_bp.route('/about')
def about():
    """Отображает информацию о компании"""
    about_content = Content.get_by_type('about')
    
    if not about_content:
        # Если контент не найден, создаем заглушку
        about_content = Content(
            type='about',
            title=_('About Us'),
            content=_('About us content is not available.'),
            is_html=False,
            last_updated=datetime.utcnow()
        )
    
    return render_template('static_page.html', page=about_content)


@main_bp.route('/contact')
def contact():
    """Отображает контактную информацию"""
    contact_content = Content.get_by_type('contact')
    
    if not contact_content:
        # Если контент не найден, создаем заглушку
        contact_content = Content(
            type='contact',
            title=_('Contact Information'),
            content=_('Contact information is not available.'),
            is_html=False,
            last_updated=datetime.utcnow()
        )
    
    return render_template('static_page.html', page=contact_content)


@main_bp.route('/page/<string:page_type>')
def custom_page(page_type):
    """Отображает произвольный тип страницы"""
    page_content = Content.get_by_type(page_type)
    
    if not page_content:
        return render_template('404.html'), 404
    
    return render_template('static_page.html', page=page_content)


@main_bp.route('/faq')
def faq():
    """Отображает часто задаваемые вопросы"""
    faq_content = Content.get_by_type('faq')
    
    if not faq_content:
        # Если контент не найден, создаем заглушку
        faq_content = Content(
            type='faq',
            title=_('Frequently Asked Questions'),
            content=_('FAQ content is not available.'),
            is_html=False,
            last_updated=datetime.utcnow()
        )
    
    return render_template('static_page.html', page=faq_content) 