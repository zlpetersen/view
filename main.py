from flask import Flask, render_template, send_file
from flask_pymongo import PyMongo
from pymongo import MongoClient
from gridfs import GridFS
from PIL import Image
import io

client = MongoClient("mongodb://rfhs:wildcat1@veterans-shard-00-00-0nuxa.mongodb.net:27017,veterans-shard-00-01-0nuxa.mongodb.net:27017,veterans-shard-00-02-0nuxa.mongodb.net:27017/test?ssl=true&replicaSet=Veterans-shard-0&authSource=admin")
db = client.test
fs = GridFS(db)

app = Flask(__name__)
mongo = PyMongo(app)


def serve_pil_image(pil_img):
    img_io = io.BytesIO()
    pil_img.save(img_io, 'PNG', quality=70)
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')


@app.route('/image/<path:filename>')
def get_img(filename):
    im_stream = fs.get_last_version(filename)
    im = Image.open(im_stream)
    return serve_pil_image(im)


@app.route('/')
def hello():
    return render_template('index.html', ppl=db.inventory.find_one())


@app.route('/vets/<od>/')
def vet(od):
    print(db.inventory.fine({"name": "John Smith"}).read())
    return render_template('vet.html', ppl=db.inventory.find({'name': 'John Smith'}))


@app.route('/hello/')
@app.route('/hello/<uname>/')
def hi(uname=None):
    return render_template('hello.html', uname=uname)

