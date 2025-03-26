from flask import render_template, flash, redirect, url_for, request, jsonify, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.main import bp as main_bp
from app.models import User, Client, Order
from app.forms import ClientForm, OrderForm, ProfileForm, PasswordChangeForm, FeedbackForm
from datetime import datetime, timedelta

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Неверное имя пользователя или пароль')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('auth/login.html', title='Вход', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Поздравляем, вы успешно зарегистрировались!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', title='Регистрация', form=form)

@main_bp.route('/')
@main_bp.route('/index')
@login_required
def index():
    return render_template('main/index.html', title='Главная')

@main_bp.route('/clients')
@login_required
def clients():
    clients = Client.query.filter_by(manager_id=current_user.id).all()
    return render_template('main/clients.html', title='Клиенты', clients=clients)

@main_bp.route('/clients/add', methods=['GET', 'POST'])
@login_required
def add_client():
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            company=form.company.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            manager_id=current_user.id
        )
        db.session.add(client)
        db.session.commit()
        flash('Клиент успешно добавлен!')
        return redirect(url_for('main.clients'))
    return render_template('main/client_form.html', title='Добавить клиента', form=form)

@main_bp.route('/clients/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(id):
    client = Client.query.get_or_404(id)
    if client.manager_id != current_user.id:
        abort(403)
    form = ClientForm(obj=client)
    if form.validate_on_submit():
        client.name = form.name.data
        client.company = form.company.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.address = form.address.data
        db.session.commit()
        flash('Данные клиента обновлены!')
        return redirect(url_for('main.clients'))
    return render_template('main/client_form.html', title='Редактировать клиента', form=form)

@main_bp.route('/clients/<int:id>/delete', methods=['POST'])
@login_required
def delete_client(id):
    client = Client.query.get_or_404(id)
    if client.manager_id != current_user.id:
        abort(403)
    db.session.delete(client)
    db.session.commit()
    flash('Клиент успешно удален!')
    return redirect(url_for('main.clients'))

@main_bp.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('main/orders.html', title='Заявки', orders=orders)

@main_bp.route('/orders/add', methods=['GET', 'POST'])
@login_required
def add_order():
    form = OrderForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(user_id=current_user.id).all()]
    
    if form.validate_on_submit():
        order = Order(
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            deadline=form.deadline.data,
            amount=form.amount.data,
            profit=form.profit.data,
            user_id=current_user.id,
            client_id=form.client_id.data
        )
        db.session.add(order)
        db.session.commit()
        flash('Заявка успешно создана!', 'success')
        return redirect(url_for('main.orders'))
    return render_template('main/order_form.html', title='Новая заявка', form=form)

@main_bp.route('/orders/<int:id>')
@login_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    if order.user_id != current_user.id:
        abort(403)
    return render_template('main/order_detail.html', title=order.title, order=order)

@main_bp.route('/orders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_order(id):
    order = Order.query.get_or_404(id)
    if order.user_id != current_user.id:
        abort(403)
    
    form = OrderForm()
    form.client_id.choices = [(c.id, c.name) for c in Client.query.filter_by(user_id=current_user.id).all()]
    
    if form.validate_on_submit():
        order.title = form.title.data
        order.client_id = form.client_id.data
        order.description = form.description.data
        order.status = form.status.data
        order.priority = form.priority.data
        order.deadline = form.deadline.data
        order.amount = form.amount.data
        order.profit = form.profit.data
        
        db.session.commit()
        flash('Заявка успешно обновлена!', 'success')
        return redirect(url_for('main.order_detail', id=order.id))
    
    form.title.data = order.title
    form.client_id.data = order.client_id
    form.description.data = order.description
    form.status.data = order.status
    form.priority.data = order.priority
    form.deadline.data = order.deadline
    form.amount.data = order.amount
    form.profit.data = order.profit
    
    return render_template('main/order_form.html', title='Редактировать заявку', form=form)

@main_bp.route('/orders/<int:id>/delete', methods=['POST'])
@login_required
def delete_order(id):
    order = Order.query.get_or_404(id)
    if order.user_id != current_user.id:
        abort(403)
    
    db.session.delete(order)
    db.session.commit()
    flash('Заявка успешно удалена!', 'success')
    return redirect(url_for('main.orders'))

@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Профиль обновлен!')
        return redirect(url_for('main.profile'))
    return render_template('main/profile.html', title='Личный кабинет', form=form)

@main_bp.route('/profile/password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = PasswordChangeForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Пароль успешно изменен!')
            return redirect(url_for('main.profile'))
        else:
            flash('Неверный текущий пароль')
    return render_template('main/change_password.html', title='Изменить пароль', form=form)

@main_bp.route('/feedback', methods=['GET', 'POST'])
def feedback():
    form = FeedbackForm()
    if form.validate_on_submit():
        # Здесь можно добавить логику отправки обратной связи
        flash('Спасибо за ваше сообщение!')
        return redirect(url_for('main.index'))
    return render_template('main/feedback.html', title='Обратная связь', form=form)

@main_bp.route('/analytics')
@login_required
def analytics():
    period = request.args.get('period', 'month')
    
    if period == 'month':
        start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    elif period == 'quarter':
        start_date = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date - timedelta(days=start_date.day - 1)
        start_date = start_date - timedelta(days=(start_date.month - 1) * 30)
        end_date = start_date + timedelta(days=90)
    else:  # year
        start_date = datetime.utcnow().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=365)
    
    orders = Order.query.filter(
        Order.manager_id == current_user.id,
        Order.created_at.between(start_date, end_date)
    ).all()
    
    total_amount = sum(order.amount or 0 for order in orders)
    total_profit = sum(order.profit or 0 for order in orders)
    
    return render_template('main/analytics.html', 
                         title='Аналитика',
                         orders=orders,
                         total_amount=total_amount,
                         total_profit=total_profit)

@main_bp.route('/terms')
def terms():
    return render_template('main/terms.html', title='Пользовательские соглашения') 