from flask import (
    Flask, render_template, redirect, url_for, request, flash, session, jsonify
)
from flask_login import (
    LoginManager, login_user, logout_user, login_required, current_user
)
from flask_socketio import SocketIO, emit, join_room
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import IntegrityError
from models import db, User, Message, ChatRoom, Keyword
from forms import LoginForm, SignupForm, RenameForm, PasswordResetForm

app = Flask(__name__)
app.config.update(
    SECRET_KEY='hard-to-guess-secret-key',
    SQLALCHEMY_DATABASE_URI='sqlite:///chat.db',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    DEBUG=True
)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def require_role(*roles):
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if current_user.role not in roles:
                flash('Zugriff verweigert.')
                return redirect(url_for('chat'))
            return f(*args, **kwargs)
        return wrapper
    return decorator


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        u = User.query.filter_by(username=form.username.data).first()
        if u and pbkdf2_sha256.verify(form.password.data, u.password):
            login_user(u)
            session['room'] = 'global'
            session.pop('original_user_id', None)
            return redirect(url_for('rooms'))
        flash('Login fehlgeschlagen.')
    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET','POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        try:
            u = User(
                username       = form.username.data,
                password       = pbkdf2_sha256.hash(form.password.data),
                plain_password = form.password.data,
                role           = 'user'
            )
            db.session.add(u)
            db.session.commit()
            login_user(u)
            session['room'] = 'global'
            session.pop('original_user_id', None)
            return redirect(url_for('rooms'))
        except IntegrityError:
            db.session.rollback()
            flash('Benutzername bereits vergeben.')
    return render_template('signup.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('original_user_id', None)
    return redirect(url_for('login'))


@app.route('/rooms', methods=['GET','POST'])
@login_required
def rooms():
    if request.method=='POST':
        rm = request.form.get('room')
        room = ChatRoom.query.filter_by(name=rm, archived=False).first()
        if room:
            if room.password:
                pw = request.form.get('room_password','')
                if pw != room.password:
                    flash('Falsches Raum-Passwort.')
                    return redirect(url_for('rooms'))
            session['room'] = rm
            return redirect(url_for('chat'))
        flash('Raum nicht gefunden.')
    rooms = ChatRoom.query.filter_by(archived=False).all()
    return render_template('choose_room.html', rooms=rooms)


@app.route('/chat')
@login_required
def chat():
    room = session.get('room','global')
    return render_template(
        'chat.html',
        username=current_user.username,
        is_admin=(current_user.role=='admin'),
        is_mod=(current_user.role in ['admin','moderator']),
        room=room
    )


@app.route('/admin', methods=['GET','POST'])
@login_required
@require_role('admin')
def admin_panel():
    form = request.form
    rename_form = RenameForm(prefix='rename')
    pw_form     = PasswordResetForm(prefix='pw')

    # — Impersonate
    if 'impersonate' in form:
        session['original_user_id'] = current_user.id
        u = User.query.get(int(form['impersonate_uid']))
        if u:
            logout_user()
            login_user(u)
            session['room'] = 'global'
            flash(f"Du sprichst jetzt als: {u.username}")
            return redirect(url_for('chat'))

    # — Revert Impersonation (ohne Logout)
    if 'revert_impersonation' in form:
        orig = session.pop('original_user_id', None)
        if orig:
            admin = User.query.get(orig)
            logout_user()
            login_user(admin)
            flash("Zurück zum Admin-Account.")
            return redirect(url_for('admin_panel'))

    # — Delete user
    if 'delete_user' in form:
        u = User.query.get(int(form['delete_uid']))
        if u:
            db.session.delete(u)
            db.session.commit()
            flash('Benutzer gelöscht.')

    # — Rename user
    if rename_form.validate_on_submit() and 'rename' in form:
        u = User.query.get(int(rename_form.user_id.data))
        u.username = rename_form.new_name.data
        db.session.commit()
        flash('Username geändert.')
        # falls du gerade diesen User bist, reloggen
        if current_user.id == u.id:
            login_user(u)

    # — Reset password
    if pw_form.validate_on_submit() and 'reset_pw' in form:
        u = User.query.get(int(pw_form.user_id.data))
        u.password       = pbkdf2_sha256.hash(pw_form.new_pass.data)
        u.plain_password = pw_form.new_pass.data
        db.session.commit()
        flash(f"Passwort zurückgesetzt auf: {u.plain_password}")

    # — Create room
    if 'create_room' in form:
        name = form.get('room_name','').strip()
        pw   = form.get('room_password','').strip() or None
        if name and not ChatRoom.query.filter_by(name=name).first():
            db.session.add(ChatRoom(name=name, password=pw))
            db.session.commit()
            flash(f"Raum '{name}' erstellt.")

    # — Archive / Restore room
    if 'archive_room' in form:
        r = ChatRoom.query.get(int(form['archive_room_id']))
        r.archived = not r.archived
        db.session.commit()
        flash('Raum ' + ('archiviert' if r.archived else 'wiederhergestellt') + '.')

    # — Delete room
    if 'delete_room' in form:
        r = ChatRoom.query.get(int(form['delete_room_id']))
        if r:
            db.session.delete(r)
            db.session.commit()
            flash('Raum gelöscht.')

    # — Add Keyword
    if 'add_keyword' in form:
        kw   = form.get('keyword','').strip()
        act  = form.get('action')
        mt   = form.get('match_type')
        rm   = form.get('kf_room') or None
        if kw and act in ['block','mark'] and mt in ['exact','case_insensitive','regex']:
            db.session.add(Keyword(word=kw, action=act, match_type=mt, room=rm))
            db.session.commit()
            flash('Keyword hinzugefügt.')

    # — Delete Keyword
    if 'delete_keyword' in form:
        k = Keyword.query.get(int(form['delete_keyword_id']))
        if k:
            db.session.delete(k)
            db.session.commit()
            flash('Keyword gelöscht.')

    users    = User.query.all()
    rooms    = ChatRoom.query.all()
    keywords = Keyword.query.all()
    stats    = db.session.query(
                  Message.username, db.func.count(Message.id)
               ).group_by(Message.username).all()

    return render_template(
        'admin.html',
        users=users, rooms=rooms, keywords=keywords, stats=stats,
        rename_form=rename_form, pw_form=pw_form
    )


@app.route('/get_messages/<room>')
@login_required
def get_messages(room):
    pinned = Message.query.filter_by(room=room, pinned=True).all()
    others = Message.query.filter_by(room=room, pinned=False, approved=True).all()
    def ser(ms):
        return [{'id':m.id,'username':m.username,'content':m.content,'timestamp':m.timestamp.strftime('%H:%M')} for m in ms]
    return jsonify(ser(pinned)+ser(others))


@app.route('/delete_message/<int:mid>', methods=['POST'])
@login_required
@require_role('admin','moderator')
def delete_message(mid):
    m = Message.query.get(mid)
    if m:
        rm = m.room
        db.session.delete(m)
        db.session.commit()
        socketio.emit('delete_message', {'id':mid}, room=rm)
    return ('',204)


@socketio.on('join')
def on_join(data):
    join_room(data['room'])
    emit('status', {'msg':f"{data['username']} betritt {data['room']}."}, room=data['room'])


@socketio.on('message')
def on_message(data):
    u = User.query.filter_by(username=data.get('username')).first()
    if not u: return
    msg = data.get('msg','')
    for k in Keyword.query.filter((Keyword.room==data['room'])|(Keyword.room.is_(None))):
        if k.match_type=='exact' and k.word in msg:
            if k.action=='block': return
            msg = msg.replace(k.word, f"<mark>{k.word}</mark>")
    m = Message(username=u.username, content=msg, room=data['room'])
    db.session.add(m)
    db.session.commit()
    emit('message', {
        'id':m.id,'username':m.username,
        'content':m.content,'timestamp':m.timestamp.strftime('%H:%M')
    }, room=data['room'])


if __name__=='__main__':
    with app.app_context():
        db.create_all()
        if not ChatRoom.query.filter_by(name='global').first():
            db.session.add(ChatRoom(name='global'))
        if not User.query.filter_by(username='Felix').first():
            db.session.add(User(
                username='Felix',
                password=pbkdf2_sha256.hash('123'),
                plain_password='123',
                role='admin'
            ))
        db.session.commit()
    socketio.run(app, host='0.0.0.0', port=8080, debug=True)
