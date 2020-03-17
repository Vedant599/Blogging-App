from flask import Flask,render_template,redirect,session,logging,request,url_for,flash,session
from wtforms import Form,StringField,PasswordField,validators,TextAreaField
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL
from data import Articles
from functools import wraps
app=Flask(__name__)
articles_app=Articles()
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_USER']='root'
app.config['MYSQL_PASSWORD']=''
app.config['MYSQL_DB']='reviseblogapp'
app.config['MYSQL_CURSORCLASS']='DictCursor'
mysql=MySQL(app)
class RegistrationForm(Form):
    username=StringField('Username',[validators.length(min=4,max=50)])
    email=StringField('Email',[validators.length(min=4,max=50),validators.Email("xyz@email.com")])
    password=PasswordField('Password',[validators.equal_to('confirm',"Passwords Don't Match"),validators.DataRequired("Compulsary")])
    confirm=PasswordField('confirm')
@app.route('/')
def index():
    return render_template('home.html')
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/articles')
def articles():
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles")
    if(result>0):
        data=cur.fetchall()
    else:
        data=dict({})
    return render_template('articles.html',articles=data)
@app.route('/article/<int:id>')
def article(id):
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles WHERE id=%s",[id])
    if(result>0):
        data=cur.fetchone()
    else:
        flash("No articles to view",category="danger")
        return redirect(url_for('articles'))
    return render_template('article.html',article=data)
@app.route('/register',methods=['GET','POST'])
def register():
    form=RegistrationForm(request.form)
    if(request.method=='POST' and form.validate()):
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(str(form.password.data))
        cur=mysql.connection.cursor()
        if cur.execute("INSERT INTO users(username,email,password) VALUES(%s,%s,%s)",(username,email,password)):
            mysql.connection.commit()
            flash("You are Registered",category="success")
            return redirect(url_for('index'))
        else:
            cur.close()
            return render_template('register.html',form=form)

    return render_template('register.html',form=form)  

@app.route('/login',methods=['GET','POST'])
def login():

    if request.method =='POST':
        email=request.form['email']   
        password_candidate=request.form['password']
        cur=mysql.connection.cursor()
        result=cur.execute("SELECT * FROM users WHERE email = %s",[email])
        # mysql.commit()
        if(result>0):
            data=cur.fetchone()
            password=data['password']
            if(sha256_crypt.verify(password_candidate,password)):
                session['logged_in']=True
                session['username']=data['username']
                cur.close()
                flash("You are logged in !",category='success')
                return redirect(url_for('dashboard'))
            else:
                cur.close()
                return render_template('login.html',error="Please enter Correct Password")
        else:
            cur.close()
            return render_template('login.html',error="User No Found")
            
    return render_template('login.html')
def is_logged_in(f):
    @wraps(f)
    def wrap(*args,**kwargs):
        if('logged_in' in session):
            return f(*args,**kwargs)
        else:
            flash("Unauthorized Please log in",category='danger')
            return redirect(url_for('login'))
    return wrap
@app.route('/dashboard')
@is_logged_in
def dashboard():
    cur=mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles WHERE author=%s",[session['username']])
    if(result>0):
        data=cur.fetchall()
    else:
        data=dict({})
    cur.close()
    return render_template('dashboard.html',data=data)

@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash("You are now Logged Out",category="success")
    return redirect(url_for('index'))

class ArticleForm(Form):
    title=StringField('Title',[validators.length(min=1,max=30)])
    body=TextAreaField('Body',[validators.length(min=30)])
@app.route('/add_article', methods=['GET','POST'])
@is_logged_in
def add_article():
    form=ArticleForm(request.form)
    if(request.method =='POST' and form.validate()):
        title=form.title.data
        body=form.body.data
        cur=mysql.connection.cursor()
        cur.execute("INSERT INTO articles(title,body,author) VALUES (%s,%s,%s)",(title,body,session['username']))
        mysql.connection.commit()
        flash("Article Added Successfully",category="success")
        cur.close()
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)

@app.route('/edit_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    form=ArticleForm(request.form)
    cur = mysql.connection.cursor()
    result=cur.execute("SELECT * FROM articles WHERE id=%s",[id])
    if(result>0):
        data=cur.fetchone()
        form.title.data=data['title']
        form.body.data=data['body']
        cur.close()
    else:
        flash("Article Not Found",category="danger")
        return redirect(url_for('articles'))
    if request.method== 'POST' and form.validate():
        title=request.form['title']
        body=request.form['body']
        cur=mysql.connection.cursor()
        cur.execute("UPDATE  articles SET title =%s, body= %s WHERE ID=%s",(title,body,id))
        mysql.connection.commit()
        flash("Article Editted Successfully",category="success")
        return redirect(url_for('dashboard'))

    return render_template("edit_article.html",form=form)

@app.route('/delete_article/<string:id>',methods=['POST'])
@is_logged_in
def delete_article(id):
    cur=mysql.connection.cursor()
    cur.execute("DELETE FROM articles WHERE id = %s",[id])
    mysql.connection.commit()
    flash("Article Deleted Successfully",category="success")
    return redirect(url_for('dashboard'))
if(__name__=='__main__'):
    app.secret_key="some_secret"
    app.run(debug=True)