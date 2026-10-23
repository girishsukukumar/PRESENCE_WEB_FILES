import json
import paho.mqtt.client as mqtt
from datetime import datetime


BROKER = "broker.hivemq.com"
PORT = 8883
# TOPIC = "factory/motion"
# TOPIC = "HP/CONSUMER_NO/+/+"
#TOPIC = "PRESENCE/LD2410/STATUS"
TOPIC = "PRESENCE/BLR/MANSARVOVAR/A4562/STATUS"


toiletTimings =  [] 
BedRoomTimings = []
LivingRoomTimings = []
KitchenTimings = [] 

def on_connect(client, userdata, flags, rc):
    print("Connected")
    client.subscribe(TOPIC)



def AppendToLogFile(csv_line):

    #fileName = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")  + ".csv"
    fileName = datetime.now().strftime("%Y_%m_%d")  + ".csv"

    with open(fileName,"a") as file :
        file.write(",".join(str(item) for item in csv_line) + "\n" )
    return


def on_message(client, userdata, msg):
    global toiletTimings 
    global BedRoomTimings
    global LivingRoomTimings
    global KitchenTimings  

    try:

        data = json.loads(msg.payload.decode())
        print(data)


        status = data.get("status", "")

        if status in ["DETECTED", "NOT_DETECTED"]:

           room =  data.get("sensor_room","") 
           status = data.get("status", "") 
           #currentDateTime = datetime.now().strftime("%B %d, %Y at %I:%M %p")
           currentDateTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

           if (room == "Toilet-1"):
               if (status == "DETECTED"):
                  toiletTimings = [] 
                  toiletTimings.append("Toilet-1")
                  toiletTimings.append(currentDateTime) 
               elif (status == "NOT_DETECTED"):
                   if toiletTimings:  
                      toiletTimings.append(currentDateTime)
                      AppendToLogFile(toiletTimings)
                   toiletTimings = [] 

           if (room == "BedRoom"):
               if (status == "DETECTED"):
                  BedRoomTimings = []
                  BedRoomTimings.append("BedRoom")
                  BedRoomTimings.append(currentDateTime)
               elif (status == "NOT_DETECTED"):
                  if BedRoomTimings:
                     BedRoomTimings.append(currentDateTime)
                     AppendToLogFile(BedRoomTimings)
                  BedRoomTimings = []
           if (room == "LivingRoom"):
               if (status == "DETECTED"):
                  LivingRoomTimings = []
                  LivingRoomTimings.append("LivingRoom")
                  LivingRoomTimings.append(currentDateTime)
               elif (status == "NOT_DETECTED"):
                  if LivingRoomTimings :
                     LivingRoomTimings.append(currentDateTime)
                     AppendToLogFile(LivingRoomTimings)
                  LivingRoomTimings = []
           if (room == "Kitchen"):
               if (status == "DETECTED"):
                  KitchenTimings = []
                  KitchenTimings.append("KitchenRoom")
                  KitchenTimings.append(currentDateTime)
               elif (status == "NOT_DETECTED"):
                  if KitchenTimings:
                     KitchenTimings.append(currentDateTime)
                     AppendToLogFile(KitchenTimings)
                  KitchenTimings = []


    except json.JSONDecodeError:

        print("Invalid JSON received")


    except Exception as e:

        print(f"Error processing MQTT message: {e}")



client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)

client.tls_set()

client.on_connect = on_connect
client.on_message = on_message


client.connect(BROKER, PORT)

client.loop_forever()
