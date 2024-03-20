from flask import Flask, request, json
import os
import psycopg2
from dotenv import load_dotenv
import datetime

CREATE_ROOMS_TABLE = (
    "CREATE TABLE IF NOT EXISTS rooms (id SERIAL PRIMARY KEY, name TEXT);"
)
CREATE_TEMPS_TABLE = """CREATE TABLE IF NOT EXISTS temperatures (room_id INTEGER, temperature REAL, 
                        date TIMESTAMP, FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE CASCADE);"""

INSERT_ROOM_RETURN_ID = "INSERT INTO rooms (name) VALUES (%s) RETURNING id;"
INSERT_TEMP = (
    "INSERT INTO temperatures (room_id, temperature, date) VALUES (%s, %s, %s);"
)
GLOBAL_NUMBER_OF_DAYS = (
    """SELECT COUNT(DISTINCT DATE(date)) AS days FROM temperatures;"""
)
GLOBAL_AVG = """SELECT AVG(temperature) as average FROM temperatures;"""

ROOM_NAME = """SELECT name FROM rooms WHERE id = (%s)"""
ROOM_NUMBER_OF_DAYS = """SELECT COUNT(DISTINCT DATE(date)) AS days FROM temperatures WHERE room_id = (%s);"""
ROOM_ALL_TIME_AVG = (
    "SELECT AVG(temperature) as average FROM temperatures WHERE room_id = (%s);"
)

load_dotenv()

app = Flask(__name__)
url = os.getenv("DATABASE_URL")
connection = psycopg2.connect(url)


@app.post("/api/room")
def create_room():
    data = request.json
    name = data["name"]
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_ROOMS_TABLE)
            cursor.execute(INSERT_ROOM_RETURN_ID, (name,))
            room_id = cursor.fetchone()[0]
    return {"id": room_id, "message": f"Room {name} created."}, 201


@app.post("/api/temperature")
def add_temp():
    data = request.json
    temperature = data["temperature"]
    room_id = data["room"]
    try:
        date = datetime.datetime.strptime(data["date"], "%m-%d-%Y %H-%M-%S")
    except KeyError:
        date = datetime.datetime.now(datetime.timezone.utc)
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_TEMPS_TABLE)
            cursor.execute(INSERT_TEMP, (room_id, temperature, date))
    return {"message": "Temperature added."}, 201


@app.get("/api/average")
def get_global_avg():
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(GLOBAL_AVG)
            average = cursor.fetchone()[0]
            cursor.execute(GLOBAL_NUMBER_OF_DAYS)
            days = cursor.fetchone()[0]
    return {"average": round(average, 2), "days": days}


@app.get("/api/room/<int:room_id>")
def get_room_all(room_id):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(ROOM_NAME, (room_id,))
            name = cursor.fetchone()[0]
            cursor.execute(ROOM_ALL_TIME_AVG,(room_id,))
            average = cursor.fetchone()[0]
            cursor.execute(ROOM_NUMBER_OF_DAYS, (room_id, ))
            days = cursor.fetchone()[0]
    return {"name": name, "average": round(average,2), "days": days}



if __name__ == "__main__":
    app.run()