from flask import render_template, redirect, url_for, flash, request, current_app
from app import app, db
from app.forms import LoginForm, RegistrationForm, AlbumForm
from flask_login import current_user, login_user, logout_user, login_required
import os
from werkzeug.utils import secure_filename
from app.models import Album, Photo, User

@app.route('/')
def home():
    return redirect(url_for('login'))

# --- MINIMALIST HOME PAGE ---
@app.route('/index')
@login_required
def index():
    # Only show the welcome message and a link to the albums page
    return render_template('index.html', user=current_user)

# --- NEW DEDICATED ALBUMS PAGE ---
@app.route('/albums_list')
@login_required
def albums_list():
    # This page will now hold all the "VIEW ALBUM" buttons
    albums = current_user.albums.all()
    return render_template('albums_list.html', albums=albums)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for("index"))
    return render_template("login.html", title="LOGIN", form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"Account created successfully!", "success")
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/create_album', methods=['GET', 'POST'])
@login_required
def create_album():
    form = AlbumForm()
    if form.validate_on_submit():
        new_album = Album(title=form.title.data, owner=current_user)
        db.session.add(new_album)
        db.session.commit()

        files = request.files.getlist('pictures')
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.root_path, 'static/uploads', filename)
                file.save(filepath)
                photo = Photo(filename=filename, album=new_album)
                db.session.add(photo)

        db.session.commit()
        flash('Album and photos created!')
        return redirect(url_for('albums_list'))
    
    # FIX: Ensure we use the template meant for creating new albums, 
    # not the one that requires an existing 'album' variable.
    return render_template('create_album.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/my_album/<int:album_id>')
@login_required
def my_album(album_id):
    albums = current_user.albums.all()
    selected_album = Album.query.get_or_404(album_id)
    return render_template('my_album.html', albums=albums, selected_album=selected_album)

@app.route('/album/<int:album_id>/add_photo', methods=['GET', 'POST'])
@login_required
def add_photo(album_id):
    album = Album.query.get_or_404(album_id)
    if request.method == 'POST':
        files = request.files.getlist('pictures')
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.root_path, 'static/uploads', filename)
                file.save(filepath)
                photo = Photo(filename=filename, album=album)
                db.session.add(photo)
        db.session.commit()
        return redirect(url_for('my_album', album_id=album.id))
    return render_template('add_photo_direct.html', album=album)

@app.route('/album/<int:album_id>/delete_photos', methods=['POST'])
@login_required
def delete_photos(album_id):
    album = Album.query.get_or_404(album_id)
    
    # Only the owner can delete
    if album.owner != current_user:
        return redirect(url_for('index'))

    photo_ids = request.form.getlist('photo_ids')
    for photo_id in photo_ids:
        photo = Photo.query.get(photo_id)
        if photo and photo.album_id == album.id:
            # Delete physical file
            file_path = os.path.join(app.root_path, 'static/uploads', photo.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            # Delete database record
            db.session.delete(photo)
            
    db.session.commit()
    return redirect(url_for('my_album', album_id=album.id))