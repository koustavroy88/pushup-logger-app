from flask import Flask, redirect, render_template, request, flash, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app=Flask(__name__)
app.config['SECRET_KEY']='secret-key'
app.config['SQLALCHEMY_DATABASE_URI']="sqlite:///todo.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db = SQLAlchemy(app)
app.app_context().push()


login_manager=LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id=db.Column(db.Integer, primary_key=True) 
    email=db.Column(db.String(100), unique=True) 
    password=db.Column(db.String(100)) 
    name=db.Column(db.String(100)) 
    workouts=db.relationship('workout', backref='author', lazy=True)

class workout(db.Model):
    id=db.Column(db.Integer, primary_key=True) 
    pushups=db.Column(db.Integer, nullable=False) 
    data_posted=db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    comment=db.Column(db.Text, nullable=False)
    user_id=db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def get_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html", name=current_user.name)

@app.route("/new")
@login_required
def new_workout():
    return render_template("create_workout.html")

@app.route("/new", methods=["POST"])
@login_required
def new_workout_post():
    pushups =request.form["pushups"]
    comment =request.form["comment"]
    print(pushups,comment)
    Workout = workout(pushups=pushups,comment=comment, author=current_user) 
    db.session.add(Workout)
    db.session.commit()
    
    flash("Your workout has been added")
    return redirect("/all")

@app.route("/all")
@login_required
def user_workouts():
    page= request.args.get('page',1,type=int)
    user=User.query.filter_by(email=current_user.email).first_or_404()
    Workouts=workout.query.filter_by(author=user).paginate(page=page,per_page=3)
    return render_template("all_workouts.html",workouts=Workouts,user=user)

@app.route("/workout/<int:workout_id>/update",methods=["GET","POST"])
@login_required
def update_workouts(workout_id):
    workouts= workout.query.get_or_404(workout_id)
    print(workouts)
    if request.method=="POST":
        workouts.pushups=request.form['pushups']
        workouts.comment=request.form['comment']
        db.session.commit()
        flash("Your workout has been updated")
        return redirect(url_for('user_workouts'))
    
    return render_template("update_workout.html", workouts=workouts)


@app.route("/workout/<int:workout_id>/delete",methods=["GET","POST"])
@login_required
def delete_workouts(workout_id):
    Workout= workout.query.get_or_404(workout_id)
    db.session.delete(Workout)
    db.session.commit()
    flash("Your workout has been deleted")
    return redirect(url_for('user_workouts'))


@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/signup", methods=["POST"])
def signup_post():
    email=request.form["email"]
    name=request.form["name"]
    password=request.form["password"]

    user=User.query.filter_by(email=email).first()
    if user:
        return redirect("/signup")

    new_user=User(email=email,name=name,password=generate_password_hash(password, method="pbkdf2:sha256"))
    db.session.add(new_user)
    db.session.commit()    
    return redirect("/login")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login_post():
    email=request.form["email"]
    password=request.form["password"]

    user=User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        return render_template("login.html")
    
    login_user(user)
    return redirect("/profile")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
