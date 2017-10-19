from flask import Flask, render_template, send_file, Response, request, redirect
from flask_pymongo import PyMongo
from pymongo import MongoClient
from bson.objectid import ObjectId
from gridfs import GridFS
from PIL import Image
from functools import wraps
import io

# opens connection to database
client = MongoClient("mongodb://rfhs:wildcat1@veterans-shard-00-00-0nuxa.mongodb.net:27017,"
                     "veterans-shard-00-01-0nuxa.mongodb.net:27017,"
                     "veterans-shard-00-02-0nuxa.mongodb.net:27017/test?ssl=true&replicaSet=Veterans-shard-0&auth"
                     "Source=admin")
db = client.test  # gets actual database
fs = GridFS(db)  # for getting images

app = Flask(__name__)  # inits flask server
mongo = PyMongo(app)  # inits mongo server


def check_auth(uname, pword):
    '''Checks username and password against existing ones'''
    return uname == 'admin' and pword == 'secret'


def authenticate():
    '''Sends 401 response that enables authorization'''
    return Response('Could not verify access level\nYou have to log in with proper credentials', 401,
                    {'WWW-Authenticate': 'Basic realm="Login Required'})


def requires_auth(f):
    '''Wrapper for admin only pages'''
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


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


@app.route('/')
def hello():
    # gets all featured veterans from GridFS in the database
    vets = []
    for vet in db.inventory.find({"featured": True}):
        vets.append(vet)
    return render_template('index.html', ppl=vets)  # renders index template


@app.route('/vets/')
def vets():
    # gets all vets as a list
    vets = []
    for vet in db.inventory.find():
        vets.append(vet)
    return render_template('vets.html', ppl=vets)  # renders vets template


@app.route('/vets/<identifier>/')
def vet(identifier):
    return render_template('vet.html', ppl=db.inventory.find_one({"id": identifier})) # renders page for specific vet


@app.route('/admin/edit/')
@requires_auth
def edit():
    # gets all vets as a list
    vets = []
    for vet in db.inventory.find():
        vets.append(vet)
    return render_template('edit.html', ppl=vets)


@app.route('/admin/edit/<oid>')
def edit_p(oid):
    yrs = []
    for i in range(1900, 2017):
        yrs.append(i)
    if request.method == 'POST':
        name = request.form['name']
        bio = request.form['bio']
        branch = request.form['branch']
        year = request.form['year']
        featured = request.form['featured']
        db.inventory.update_one({'_id': ObjectId(oid)},
                                {"name": name, "bio": bio, "branch": branch, "year": year, "featured": featured})
        return redirect('/admin/edit/')
    else:
        return render_template('edit_p.html', ppl=db.inventory.find_one({"_id": ObjectId(oid)}), yrs=yrs)
