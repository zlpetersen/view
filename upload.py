from pymongo import MongoClient
import json
import gridfs

client = MongoClient("mongodb://rfhs:wildcat1@veterans-shard-00-00-0nuxa.mongodb.net:27017,veterans-shard-00-01-0nuxa.mongodb.net:27017,veterans-shard-00-02-0nuxa.mongodb.net:27017/test?ssl=true&replicaSet=Veterans-shard-0&authSource=admin")
db = client.test
db.inventory.delete_many({})
fs = gridfs.GridFS(db)

with open('vets.json') as vets:
    data = json.loads(vets.read())

print(data)


def upload_img(img):
    with open('img/' + img, 'rb') as image:
        image = image.read()
        id = fs.put(image, filename=img)
    return id


for p in data:
    id = upload_img(p['image'])
    p['image'] = id

db.inventory.insert(data)
print(db.inventory.find_one())
