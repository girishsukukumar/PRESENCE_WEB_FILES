from flask import Flask, jsonify

from flask_cors import CORS

import threading

import json

import paho.mqtt.client as mqtt

from datetime import datetime

import random

import csv
import os


from google import genai
from google.genai import types
import io
import time

from flask import Flask
import logging

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

CORS(app)





BROKER = "broker.hivemq.com"

# PORT = 8883 1883

PORT = 8883

#TOPIC = "PRESENCE/LD2410/STATUS"

TOPIC = "PRESENCE/BLR/MANSARVOVAR/A4562/STATUS"

TOPIC2 = "PRESENCE/BLR/MANSARVOVAR/A4562/ALERT"





DETECTION_STATUSES = ["DETECTED", "NOT_DETECTED"]

CONNECTIVITY_STATUSES = ["OFF_LINE", "ON_LINE", "KEEP_ALIVE"]

MAX_MESSAGES = 200



# Latest data for React

latest_sensor_data = {}

toiletTimings = [] 
BedRoomTimings= []
LivingRoomTimings= []
KitchenTimings = []


messages = []

next_message_id = 1



# Thread synchronization

data_lock = threading.Lock()




def add_message(text):

    """Append a chat message. Do NOT call while already holding data_lock."""

    global next_message_id

    with data_lock:

        messages.append({

            "id": next_message_id,

            "text": text,

            "timestamp": datetime.now().isoformat(),

        })

        next_message_id += 1

        del messages[:-MAX_MESSAGES]  # keep only the newest MAX_MESSAGES





def on_connect(client, userdata, flags, reason_code, properties=None):



    print("Flask MQTT Connected")



    client.subscribe(TOPIC)

    client.subscribe(TOPIC2)



    add_message("Connected to MQTT broker")





def on_message(client, userdata, msg):



    global latest_sensor_data



    try:



        sensor_data = json.loads(msg.payload.decode())



        #print("\nMQTT Message Received:")

        #print("Topic:", msg.topic)

        #print("sensor_data : ", sensor_data)



        # -------------------------------------------------

        # ALERT TOPIC

        # -------------------------------------------------



        if msg.topic == TOPIC2:

            # Alert message

            # Convert alert payload into text



            if isinstance(sensor_data, dict):



                # Example:

                # {"Message": "Motion detected in Kitchen"}



                if ("Message" not in sensor_data):



                    print("Message not required to print")



                else:



                    alert_text = sensor_data.get("Message")

                    add_message(f"{alert_text}")



            else:

                print("No new Alert")



            return            

        



        if msg.topic == TOPIC:



            # -------------------------------------------------

            # Get sensor room

            # -------------------------------------------------





            sensor = sensor_data.get("sensor_room")



            if not sensor:

                print("sensor_room not found in payload")

                return





            # -------------------------------------------------

            # Get incoming status

            # -------------------------------------------------



            incoming_status = sensor_data.get("status", "").strip().upper()

            #print("incoming_status : ", incoming_status)





            # -------------------------------------------------

            # Timestamp for the latest received message

            # -------------------------------------------------



            timestamp = datetime.now().isoformat()





            # -------------------------------------------------

            # SENSOR STATUS MESSAGE

            #

            # DETECETED / NOT_DETECETED

            # -------------------------------------------------



            if incoming_status in DETECTION_STATUSES:



                with data_lock:



                    # Check whether this sensor already has data

                    existing_sensor_data = latest_sensor_data.get(sensor, {})





                    # Start with the NEW sensor reading

                    updated_sensor_data = sensor_data.copy()





                    # Preserve previously received sensor_status

                    if "sensor_status" in existing_sensor_data:



                        updated_sensor_data["sensor_status"] = (

                            existing_sensor_data["sensor_status"]

                        )




                         # only if status changes, 
                    if "status" in existing_sensor_data:

                        if (existing_sensor_data["status"] != updated_sensor_data["status"]):

                            # Update timestamp

                            updated_sensor_data["timestamp"] = timestamp

                        else:

                            updated_sensor_data["timestamp"] = existing_sensor_data["timestamp"]



                    else:

                        updated_sensor_data["timestamp"] = timestamp





                    # Save updated sensor data

                    latest_sensor_data[sensor] = updated_sensor_data





            # -------------------------------------------------

            # SENSOR STATUS / CONNECTIVITY MESSAGE

            #

            # OFF_LINE / ON_LINE / KEEP_ALIVE

            # -------------------------------------------------



            elif incoming_status in CONNECTIVITY_STATUSES:



                with data_lock:



                    # Get existing data for this sensor

                    existing_sensor_data = latest_sensor_data.get(

                        sensor,

                        {}

                    ).copy()





                    # If there is no previous data,

                    # create the basic sensor record

                    if not existing_sensor_data:



                        existing_sensor_data["sensor_room"] = sensor

                        existing_sensor_data["timestamp"] = timestamp





                    # Add / update sensor_status

                    existing_sensor_data["sensor_status"] = incoming_status





                    # Update timestamp

                    #existing_sensor_data["timestamp"] = timestamp





                    # Save the merged data

                    latest_sensor_data[sensor] = existing_sensor_data





            # -------------------------------------------------

            # UNKNOWN STATUS

            # -------------------------------------------------



            else:



                print(

                    f"Unknown status received from {sensor}: "

                    f"{incoming_status}"

                )



    except Exception as e:



        print("Error processing MQTT message:", e)





mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)



mqtt_client.tls_set()



mqtt_client.on_connect = on_connect



mqtt_client.on_message = on_message



mqtt_client.connect(BROKER, PORT)



mqtt_client.loop_start()





@app.route("/api/sensors")

def sensors():



    with data_lock:



        return jsonify({



            "status": "success",

            "totalSensors": len(latest_sensor_data),

            "data": list(latest_sensor_data.values())



        })


@app.route("/api/transitions", methods=["GET"])
def get_transitions():
    
    CSVfileName = datetime.now().strftime("%Y_%m_%d")  + ".csv"

    if os.path.isfile(CSVfileName):
         with open(CSVfileName, "rb") as f:
               csv_bytes = f.read()  # Locks the file size in memory so it cannot shift
    else:
         lines = ["History of movements is not yet available for the day"]
         return jsonify({"data": lines})

     # 1. Define your API key 
    API_KEY = "yyyyyyyyyy"

     # 2. Initialize the GenAI Client
    client = genai.Client(api_key=API_KEY)

    # 3. Path to your local CSV file
    # Ensure 'room_occupancy.csv' exists in the same directory as your Python script

    # Upload the file using the Files API (stays active temporarily for up to 48 hours)
    #uploaded_csv = client.files.upload(file=csv_file_path)

    #print("Uploading safe static data copy to Gemini...")

    # 2. Use the types config helper to explicitly declare it as plain text
    uploaded_csv = client.files.upload(
                          file=io.BytesIO(csv_bytes),
                          config=types.UploadFileConfig(
                          mime_type="text/plain"  # <--- Gemini reads CSV architecture flawlessly under plain text
                          )  
                        )
    # Optional: Add a brief wait to ensure small metadata processing completes on the cloud
    time.sleep(2)

    # 4. Prepare your prompt text
    # --- TOKEN-OPTIMIZED PROMPT ---
    # We use strict instructions to stop the model from rambling.

    prompt = """Analyze the uploaded CSV.
                -First col of the CSV has room name
                -Second col of the CSV has entry time stamp
                -Third col of the CSV has exit time stamp
                -Remove duplicate entries 
                -Remove entries which has entry time stamp and exit time stamp matches
                -Remove entries where the difference between  entry time stamp and exit time stamp are less than 10 5 seconds 
                -Convert the final content into an HTML table - plain staic HTML no javascript 
                - All fourth column which display the amount of time spend in this, this basically the difference between the exit time time stamp and entry time stamp.
                - if the time spend is more than 60 second it should be expressed in minutes and seconds, mention the time units too
                - if the time spend is less than 60 seconds you can mention in seconds but mention the unit as seconds
                - No need to HTML begin and end table. Just <TABLE> </TABLE> part of the HTML is enough
                While writing into HTML remove the date part of the Data and time stamp write only the time part.
                Constraint: Rely strictly on data facts. No introductory words, no greetings, no 
                conversational padding.
             """

    #print("Processing file analysis via Gemini...")
    # 5. Send both the prompt and the file object in the contents array
    final_response = client.models.generate_content(
                            #model='gemini-pro-latest',
                            model='gemini-3.5-flash-lite',
                            contents=[
                            uploaded_csv,  # Pass the uploaded file reference object directly
                            prompt         # Pass the prompt string
                            ]
                           )

    #print("\n--- Model Output ---")
    #print(final_response.text)

    lines = final_response.text
    return lines
#    return jsonify({"data": lines})






@app.route("/api/history", methods=["GET"])

def get_history():
    
    CSVfileName = datetime.now().strftime("%Y_%m_%d")  + ".csv"

    if os.path.isfile(CSVfileName):
         with open(CSVfileName, "rb") as f:
               csv_bytes = f.read()  # Locks the file size in memory so it cannot shift
    else:
         lines = ["History of movements is not yet available for the day"]
         return jsonify({"data": lines})

     # 1. Define your API key 
    API_KEY = "xxxxxxxxxxxxx"

     # 2. Initialize the GenAI Client
    client = genai.Client(api_key=API_KEY)

    # 3. Path to your local CSV file
    # Ensure 'room_occupancy.csv' exists in the same directory as your Python script

    # Upload the file using the Files API (stays active temporarily for up to 48 hours)
    #uploaded_csv = client.files.upload(file=csv_file_path)

    #print("Uploading safe static data copy to Gemini...")

    # 2. Use the types config helper to explicitly declare it as plain text
    uploaded_csv = client.files.upload(
                          file=io.BytesIO(csv_bytes),
                          config=types.UploadFileConfig(
                          mime_type="text/plain"  # <--- Gemini reads CSV architecture flawlessly under plain text
                          )  
                        )
    # Optional: Add a brief wait to ensure small metadata processing completes on the cloud
    time.sleep(2)

    # 4. Prepare your prompt text
    # --- TOKEN-OPTIMIZED PROMPT ---
    # We use strict instructions to stop the model from rambling.

    prompt = """Analyze the uploaded CSV.
                 - Provide  summary of room by room transitions
                 - In case the number of transations are less, list all of them otherwise provide a summary 
                 - Provide a summary using this exact format:
                 - Busiest: [Room Name] ([Total Entries] entries)
                 - Max Stay: [Room Name] ([Duration])
                 - Room Totals: [Room]: [Duration] | [Room]: [Duration]
                 Constraint: Rely strictly on data facts. No introductory words, no greetings, no 
                 conversational padding.
                 Also prepare summary of the percentage time spend in each room against the total """

    #print("Processing file analysis via Gemini...")
    # 5. Send both the prompt and the file object in the contents array
    final_response = client.models.generate_content(
                            #model='gemini-pro-latest',
                            model='gemini-3.5-flash-lite',
                            contents=[
                            uploaded_csv,  # Pass the uploaded file reference object directly
                            prompt         # Pass the prompt string
                            ]
                           )

    #print("\n--- Model Output ---")
    #print(final_response.text)

    lines = [final_response.text]
    return jsonify({"data": lines})

@app.route("/api/msg_clear", methods=["POST"])

def clear_messages():

    # replace with your real storage, e.g. MESSAGES.clear()
    messages.clear() 

    return jsonify({"status": "ok"}), 200


@app.route("/api/messages")

def get_messages():

    with data_lock:

        return jsonify({

            "status": "success",

            "data": list(messages),

        })





if __name__ == "__main__":



    app.run(host="0.0.0.0", port=5000)
