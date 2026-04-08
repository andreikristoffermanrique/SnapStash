from flask import render_template, redirect, url_for, flash, request
from app import app, db
from app.forms import LoginForm, RegistrationForm, AlbumForm
from flask_login import current_user, login_user, logout_user, login_required
import os
from werkzeug.utils import secure_filename
from flask import current_app
from app.models import Album, Photo


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    albums = current_user.albums.all()
    return render_template('index.html', user=current_user, albums=albums)

@app.route("/login", methods=["GET", "POST"])
def login():
    from app.models import User 
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
    from app.models import User
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"Account created successfully for {form.username.data}!", "success")
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
                filepath = os.path.join('app/static/uploads', filename)
                file.save(filepath)

                photo = Photo(filename=filename, album=new_album)
                db.session.add(photo)

        db.session.commit()

        flash('Album and photos created!')
        return redirect(url_for('index'))
    return render_template('create_album.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/album/<int:album_id>')
@login_required
def view_album(album_id):
    # Fetch the album by ID, or return a 404 error if it doesn't exist
    album = Album.query.get_or_404(album_id)
    
    # Optional: Security check to ensure the current user owns this album
    if album.owner != current_user:
        flash("You do not have permission to view this album.")
        return redirect(url_for('index'))
        
    return render_template('view_album.html', album=album)

@app.route('/my_album/<int:album_id>')
@login_required
def my_album(album_id):
    from app.models import Album
    # Get all albums for the sidebar list
    albums = current_user.albums.all()
    # Get the specific album the user clicked on
    selected_album = Album.query.get_or_404(album_id)
    
    # Send both to the template
    return render_template('my_album.html', albums=albums, selected_album=selected_album)