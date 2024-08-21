import csv
import json
from kafka import KafkaProducer
from time import sleep
from datetime import datetime, timedelta

# Function to filter and transform the data into JSON format
def create_json_record(row, start_time):
    # Create the timestamp
    record_time = start_time + timedelta(seconds=int(row['t']))
    record_time_str = record_time.strftime("%d/%m/%Y %H:%M:%S")
    
    # Create the JSON object
    json_record = {
        "name": row['name'],
        "origin": row['orig'],
        "destination": row['dest'],
        "time": record_time_str,
        "link": row['link'],
        "position": float(row['x']),
        "spacing": float(row['s']),
        "speed": float(row['v'])
    }
    
    return json_record

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Start time of the producer
start_time = datetime.now()

# Read the CSV file and send data
with open('output.csv', mode='r') as file:
    csv_reader = csv.DictReader(file)
    
    # Loop through the CSV rows and send data
    for row in csv_reader:
        if float(row['v']) > 0:  # Only send data if the vehicle is moving
            json_record = create_json_record(row, start_time)
            producer.send('vehiclePositions', value=json_record)
            print(f"Sent: {json_record}")
        
        # Wait for N seconds 
        N = 2
        sleep(N)

# Flush and close the producer
producer.flush()
producer.close()
