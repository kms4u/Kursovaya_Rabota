from flask import Flask, render_template, request, redirect, flash
from config import Config

from models import (
    db,
    Child,
    Group,
    Attendance,
    Payment,
    Parent,
    Educator
)

from datetime import datetime
from sqlalchemy import func


app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)


# =====================================
# Главная страница
# =====================================
@app.route('/')
def index():

    children_count = Child.query.count()

    groups_count = Group.query.count()

    attendance_count = Attendance.query.count()

    payments_sum = db.session.query(
        func.sum(Payment.amount)
    ).scalar()

    parents_count = Parent.query.count()

    teachers_count = Educator.query.count()

    latest_children = Child.query.order_by(
        Child.id.desc()
    ).limit(5).all()

    return render_template(
        'index.html',

        children_count=children_count,
        groups_count=groups_count,
        attendance_count=attendance_count,
        payments_sum=payments_sum,

        parents_count=parents_count,
        teachers_count=teachers_count,

        latest_children=latest_children
    )


# =====================================
# Дети
# =====================================
@app.route('/children')
def children():

    query = Child.query

    # Поиск
    search = request.args.get('search')

    if search:

        query = query.filter(
            Child.full_name.ilike(f'%{search}%')
        )

    # Фильтр по группе
    group_id = request.args.get('group_id')

    if group_id and group_id != 'all':

        query = query.filter(
            Child.group_id == group_id
        )

    # Сортировка
    sort = request.args.get('sort')

    if sort == 'name_asc':

        query = query.order_by(
            Child.full_name.asc()
        )

    elif sort == 'name_desc':

        query = query.order_by(
            Child.full_name.desc()
        )

    elif sort == 'birth_asc':

        query = query.order_by(
            Child.birth_date.asc()
        )

    elif sort == 'birth_desc':

        query = query.order_by(
            Child.birth_date.desc()
        )

    children_list = query.all()

    groups = Group.query.all()

    return render_template(
        'children.html',
        children=children_list,
        groups=groups
    )


# =====================================
# Добавление ребенка
# =====================================
@app.route('/add_child', methods=['GET', 'POST'])
def add_child():

    groups = Group.query.all()

    if request.method == 'POST':

        child = Child(

            full_name=request.form['full_name'],

            birth_date=datetime.strptime(
                request.form['birth_date'],
                '%Y-%m-%d'
            ),

            group_id=request.form['group_id']
        )

        db.session.add(child)

        db.session.commit()

        return redirect('/children')

    return render_template(
        'add_child.html',
        groups=groups
    )


# =====================================
# Редактирование ребенка
# =====================================
@app.route('/edit_child/<int:id>', methods=['GET', 'POST'])
def edit_child(id):

    child = Child.query.get(id)

    groups = Group.query.all()

    if request.method == 'POST':

        child.full_name = request.form['full_name']

        child.birth_date = datetime.strptime(
            request.form['birth_date'],
            '%Y-%m-%d'
        )

        child.group_id = request.form['group_id']

        db.session.commit()

        return redirect('/children')

    return render_template(
        'edit_child.html',
        child=child,
        groups=groups
    )


# =====================================
# Удаление ребенка
# =====================================
@app.route('/delete_child/<int:id>')
def delete_child(id):
    child = Child.query.get_or_404(id)

    # Удаляем все связанные записи о посещаемости
    Attendance.query.filter_by(child_id=child.id).delete()

    # Удаляем все связанные платежи
    Payment.query.filter_by(child_id=child.id).delete()

    # Очищаем связи с родителями (если есть)
    child.parents.clear()

    # Теперь можно удалить ребенка
    db.session.delete(child)
    db.session.commit()

    return redirect('/')


# =====================================
# Родители
# =====================================
@app.route('/parents')
def parents():
    parents_list = Parent.query.options(db.joinedload(Parent.children)).all()
    return render_template(
        'parents.html',
        parents=parents_list
    )

# =====================================
# Добавление родителя
# =====================================
@app.route('/add_parent', methods=['GET', 'POST'])
def add_parent():
    children = Child.query.all()

    if request.method == 'POST':
        parent = Parent(
            full_name=request.form['full_name'],
            phone=request.form.get('phone', '')
        )
        db.session.add(parent)
        db.session.commit()

        # Добавляем связь с ребенком
        child_id = request.form.get('child_id')
        if child_id:
            child = Child.query.get(child_id)
            if child:
                parent.children.append(child)
                db.session.commit()

        flash('Родитель успешно добавлен', 'success')
        return redirect('/parents')

    return render_template('add_parent.html', children=children)


# =====================================
# Редактирование родителя
# =====================================
@app.route('/edit_parent/<int:id>', methods=['GET', 'POST'])
def edit_parent(id):
    parent = Parent.query.get_or_404(id)
    children = Child.query.all()

    if request.method == 'POST':
        parent.full_name = request.form['full_name']
        parent.phone = request.form.get('phone', '') or None  # Пустую строку в None

        # Очищаем старые связи
        parent.children.clear()

        # Добавляем выбранных детей
        child_ids = request.form.getlist('child_ids')
        for child_id in child_ids:
            child = Child.query.get(child_id)
            if child:
                parent.children.append(child)

        db.session.commit()
        flash('Родитель успешно обновлен', 'success')
        return redirect('/parents')

    return render_template('edit_parent.html', parent=parent, children=children)

# =====================================
# Удаление родителя
# =====================================
@app.route('/delete_parent/<int:id>')
def delete_parent(id):
    parent = Parent.query.get_or_404(id)
    # Очищаем связи перед удалением
    parent.children.clear()
    db.session.delete(parent)
    db.session.commit()
    flash('Родитель успешно удален', 'success')
    return redirect('/parents')

# =====================================
# Воспитатели
# =====================================
@app.route('/teachers')
def teachers():
    teachers_list = Educator.query.options(db.joinedload(Educator.groups)).all()
    return render_template(
        'teachers.html',
        teachers=teachers_list
    )


# =====================================
# Добавление воспитателя
# =====================================
@app.route('/add_teacher', methods=['GET', 'POST'])
def add_teacher():
    groups = Group.query.all()

    if request.method == 'POST':
        # Обрабатываем телефон
        phone = request.form.get('phone', '').strip()
        if phone == '':
            phone = None

        # Обрабатываем experience
        experience = request.form.get('experience', '').strip()
        if experience == '':
            experience = None
        else:
            try:
                experience = int(experience)
            except ValueError:
                experience = None

        teacher = Educator(
            full_name=request.form['full_name'],
            phone=phone,  # Будет None, а не строка "None"
            experience=experience,
            hire_date=datetime.strptime(request.form['hire_date'], '%Y-%m-%d')
        )

        db.session.add(teacher)
        db.session.commit()

        # Добавляем выбранные группы
        group_ids = request.form.getlist('group_ids')
        for group_id in group_ids:
            group = Group.query.get(group_id)
            if group:
                teacher.groups.append(group)

        db.session.commit()
        flash('Воспитатель успешно добавлен', 'success')
        return redirect('/teachers')

    return render_template('add_teacher.html', groups=groups)


@app.route('/edit_teacher/<int:id>', methods=['GET', 'POST'])
def edit_teacher(id):
    teacher = Educator.query.get_or_404(id)
    groups = Group.query.all()

    if request.method == 'POST':
        teacher.full_name = request.form['full_name']

        # Обрабатываем телефон
        phone = request.form.get('phone', '').strip()
        teacher.phone = phone if phone else None

        # Обрабатываем experience
        experience = request.form.get('experience', '').strip()
        if experience == '':
            teacher.experience = None
        else:
            try:
                teacher.experience = int(experience)
            except ValueError:
                teacher.experience = None

        teacher.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d')

        # Очищаем старые связи с группами
        teacher.groups.clear()

        # Добавляем выбранные группы
        group_ids = request.form.getlist('group_ids')
        for group_id in group_ids:
            group = Group.query.get(group_id)
            if group:
                teacher.groups.append(group)

        db.session.commit()
        flash('Воспитатель успешно обновлен', 'success')
        return redirect('/teachers')

    return render_template('edit_teacher.html', teacher=teacher, groups=groups)


# =====================================
# Удаление воспитателя
# =====================================
@app.route('/delete_teacher/<int:id>')
def delete_teacher(id):

    teacher = Educator.query.get_or_404(id)

    db.session.delete(teacher)
    db.session.commit()
    flash('Воспитатель успешно удален', 'success')
    return redirect('/teachers')


# =====================================
# Посещаемость
# =====================================
@app.route('/attendance')
def attendance():

    attendance_list = Attendance.query.all()

    return render_template(
        'attendance.html',
        attendance=attendance_list
    )


# =====================================
# Добавление посещаемости
# =====================================
@app.route('/add_attendance', methods=['GET', 'POST'])
def add_attendance():

    children = Child.query.all()

    if request.method == 'POST':

        attendance = Attendance(

            absence_date=datetime.strptime(
                request.form['absence_date'],
                '%Y-%m-%d'
            ),

            reason=request.form['reason'],

            child_id=request.form['child_id']
        )

        db.session.add(attendance)

        db.session.commit()

        return redirect('/attendance')

    return render_template(
        'add_attendance.html',
        children=children
    )


# =====================================
# Платежи
# =====================================
@app.route('/payments')
def payments():

    payments_list = Payment.query.all()

    return render_template(
        'payments.html',
        payments=payments_list
    )


# =====================================
# Добавление платежа
# =====================================
@app.route('/add_payment', methods=['GET', 'POST'])
def add_payment():

    children = Child.query.all()

    if request.method == 'POST':

        payment = Payment(

            amount=request.form['amount'],

            period=request.form['period'],

            child_id=request.form['child_id']
        )

        db.session.add(payment)

        db.session.commit()

        return redirect('/payments')

    return render_template(
        'add_payment.html',
        children=children
    )


# =====================================
# Редактирование платежа
# =====================================
@app.route('/edit_payment/<int:id>', methods=['GET', 'POST'])
def edit_payment(id):
    payment = Payment.query.get_or_404(id)
    children = Child.query.all()

    if request.method == 'POST':
        payment.child_id = request.form['child_id']
        payment.amount = request.form['amount']
        payment.period = request.form['period']

        db.session.commit()
        flash('Платеж успешно обновлен', 'success')
        return redirect('/payments')

    return render_template('edit_payment.html', payment=payment, children=children)


# =====================================
# Удаление платежа
# =====================================
@app.route('/delete_payment/<int:id>')
def delete_payment(id):
    payment = Payment.query.get_or_404(id)
    db.session.delete(payment)
    db.session.commit()
    flash('Платеж успешно удален', 'success')
    return redirect('/payments')

# =====================================
# Запуск
# =====================================
if __name__ == '__main__':

    app.run(debug=True)