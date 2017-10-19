from pymongo import MongoClient
import json
import gridfs

# opens connection to db
client = MongoClient("mongodb://rfhs:wildcat1@veterans-shard-00-00-0nuxa.mongodb.net:27017,veterans-shard-00-01-0"
                     "nuxa.mongodb.net:27017,veterans-shard-00-02-0nuxa.mongodb.net:27017/test?ssl=true&replicaSet="
                     "Veterans-shard-0&authSource=admin")
db = client.test  # gets actual db
db.inventory.delete_many({})  # clears db
fs = gridfs.GridFS(db)  # for storing images

# gets info from vets.json
with open('vets.json') as vets:
    data = json.loads(vets.read())

print(data)


def upload_img(img):
    with open('img/' + img, 'rb') as image:  # opens image as binary
        image = image.read()  # gets data
        fs.put(image, filename=img)  # uploads image


# uploads all images in /img folder
for p in data:
    upload_img(p['img'])

# uploads vet data from vets.json to db
db.inventory.insert(data)
print(db.inventory.find_one())
