import random
import string
from datetime import datetime

from flask import Flask, render_template, send_file, Response, request, redirect, url_for, flash, abort, g, session
from flask_pymongo import PyMongo
from flask_uploads import UploadSet, IMAGES, configure_uploads
from pymongo import MongoClient
from bson.objectid import ObjectId
from gridfs import GridFS
from PIL import Image
from werkzeug.utils import secure_filename
import io, os

app = Flask(__name__)
# opens connection to database
client = MongoClient("mongodb://rfhs:wildcat1@veterans-shard-00-00-0nuxa.mongodb.net:27017,"
                    "veterans-shard-00-01-0nuxa.mongodb.net:27017,"
                    "veterans-shard-00-02-0nuxa.mongodb.net:27017/test?ssl=true&replicaSet=Veterans-shard-0&auth"
                    "Source=admin")
# client = MongoClient()
db = client.test  # gets actual database
fs = GridFS(db)  # for getting images

#app = Flask(__name__)  # inits flask server
mongo = PyMongo(app)  # inits mongo server

UPLOADED_PHOTOS_DEST = '/tmp/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOADED_PHOTOS_DEST'] = UPLOADED_PHOTOS_DEST
photos = UploadSet('photos', IMAGES)

configure_uploads(app, (photos,))

now = datetime.now()

with app.app_context():
    login_code = setattr(g, 'user', 0)
    db.inventory.update_one({'account': True}, {'$set': {'id': -1}})

with app.test_request_context():
    rule = request.url_rule

def allowed_file(filename):
    return '.' in filename and filename.split('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/admin/logout/')
def logout():
    session['logged_in'] = False
    session['incorrect'] = False
    return redirect('/')


def check_auth(uname, pword):
    '''Checks username and password against existing ones'''
    return uname == 'admin' and pword == 'secret'


def check_id(id):
    account = db.inventory.find_one({'account': True})
    return id == account['id']


def authenticate():
    '''Sends 401 response that enables authorization'''
    return redirect(request.path + '#openModal')


def serve_pil_image(pil_img):
    img_io = io.BytesIO()  # converts image to binary
    pil_img.save(img_io, 'PNG', quality=70)  # uses PIL to save image to memory
    img_io.seek(0)  # moves to location of image
    return send_file(img_io, mimetype='image/png')  # uses flask to send image back to page


@app.route('/image/<path:filename>')
def get_img(filename):
    im_stream = fs.get_last_version(filename)  # gets latest version of image from GridFS in the database
    im = Image.open(im_stream)  # uses PIL to open image
    return serve_pil_image(im)  # returns image to browser


@app.route('/photo/<id>')
def show(id):
    photo = Image.open(id)
    if photo is None:
        abort(404)
    return serve_pil_image(photo)


@app.route('/')
def home_r():
    return redirect('/home/')


@app.route('/home/', methods=['GET', 'POST'])
def home():
    # gets all featured veterans from GridFS in the database
    if request.method == 'POST':
        uname = request.form['uname']
        pword = request.form['pword']
        print('uname: ' + uname + '\npword: ' + pword)
        if check_auth(uname, pword):
            session['logged_in'] = True
            print(session.get('logged_in'))
            return redirect('/admin/edit/')
        flash('Incorrect Credentials')
        return redirect("/home/#openModal")
    vets = []
    for vet in db.inventory.find({"featured": True}):
        vets.append(vet)
    return render_template('index.html', ppl=vets)  # renders index template


@app.route('/vets/', methods=['GET', 'POST'])
def vets():
    # gets all vets as a list
    vets = []
    for vet in db.inventory.find():
        vets.append(vet)
    if request.method == 'POST':
        uname = request.form['uname']
        pword = request.form['pword']
        print('uname: ' + uname + '\npword: ' + pword)
        if check_auth(uname, pword):
            session['logged_in'] = True
            print(session.get('logged_in'))
            return redirect('/admin/edit/')
        flash('Incorrect Credentials')
        return redirect("/vets/#openModal")
    return render_template('vets.html', ppl=vets)  # renders vets template


@app.route('/vets/<identifier>/')
def vet(identifier):
    return render_template('vet.html', ppl=db.inventory.find_one({"id": identifier})) # renders page for specific vet


@app.route('/admin/edit/')
def edit():
    print(session.get('logged_in'))
    if not session.get('logged_in'): return redirect('/admin/login/')
    # gets all vets as a list
    vets = []
    for vet in db.inventory.find():
        vets.append(vet)
    return render_template('edit.html', ppl=vets)


@app.route('/admin/edit/<oid>/')
def edit_p(oid):
    if not session.get('logged_in'): return redirect('/admin/login/')
    yrs = []
    print(now.year)
    for i in range(1887, now.year + 1):
        yrs.append(i)
    branches = ["Air Force", "Army", "Coast Guard", "Marines", "Navy"]
    return render_template('edit_p.html', ppl=db.inventory.find_one({"_id": ObjectId(oid)}), yrs=yrs, branches=branches)


@app.route('/admin/edit/save/<oid>', methods=['GET', 'POST'])
def save(oid):
    if not session.get('logged_in'): return redirect('/admin/login/')
    if request.method == 'POST':
        if not session.get('logged_in'): return redirect('/admin/login/')
        name = request.form['name']
        bio = request.form['bio']
        branch = request.form['branch']
        year = request.form['year']
        if request.form.get('feat', False): featured = True
        else: featured = False
        if request.files.get('file', None):
            filename = photos.save(request.files['file'])
            with open(app.config['UPLOADED_PHOTOS_DEST'] + filename, 'rb') as file:
                file = file.read()
                fs.put(file, filename=filename)
            db.inventory.update_one({'_id': ObjectId(oid)}, {'$set': {'img': filename}})
        db.inventory.update_one({'_id': ObjectId(oid)},
                                {'$set': {"name": name, "bio": bio, "branch": branch, "year": year,
                                          "featured": featured}})
    return redirect('/admin/edit/')


@app.route('/admin/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['uname']
        pword = request.form['pword']
        if not check_auth(uname, pword):
            flash('Incorrect Credentials')
        session['logged_in'] = True
        print(session.get('logged_in'))
        return redirect('/admin/edit/')
    return redirect('/')


@app.route('/admin/delete/<oid>')
def delete(oid):
    if not session.get('logged_in'): return redirect('/admin/login/')
    fs.delete(db.inventory.find_one({'_id': ObjectId(oid)})['img'])
    db.inventory.delete_one({'_id': ObjectId(oid)})
    return redirect('/admin/edit/')


@app.route('/admin/new/', methods=['GET', 'POST'])
def new():
    print(session.get('logged_in'))
    if not session.get('logged_in'): return redirect('/admin/login/')
    if request.method == 'POST':
        if not session.get('logged_in'): return redirect('/admin/login/')
        vets = []
        for vet in db.inventory.find():
            vets.append(vet)
        name = request.form['name']
        bio = request.form['bio']
        branch = request.form['branch']
        year = request.form['year']
        if request.form.get('feat', False): featured = True
        else: featured = False
        id = str(int(vets[-1]['id'])+1)
        db.inventory.insert_one({'name': name, 'bio': bio, 'branch': branch, 'year': year, 'featured': featured,
                                 'id': id, 'img': ''})
        if request.files.get('file', None):
            filename = photos.save(request.files['file'])
            with open(app.config['UPLOADED_PHOTOS_DEST'] + filename, 'rb') as file:
                file = file.read()
                fs.put(file, filename=filename)
            db.inventory.update_one({'name': name, 'bio': bio, 'branch': branch, 'year': year, 'featured': featured, 'id': id},
                                    {'$set': {'img': filename}})
        return redirect('/admin/edit/')
    yrs = []
    print(now.year)
    for i in range(1887, now.year + 1):
        yrs.append(i)
    branches = ["Air Force", "Army", "Coast Guard", "Marines", "Navy"]
    return render_template('new.html', yrs=yrs, branches=branches)


app.secret_key = "verysecret.jpg"
if __name__ == '__main__':
    app.debug = False
    port = int(os.environ.get('PORT', 5000))
    app.run('0.0.0.0', port)
    # app.run('localhost', 5000)
