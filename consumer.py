import oci #Python OCI SDK github: Allows us to provide Object Storage URL, namespace etc. to specify location to import from
import sys #Provides in inforation about constants, variables and methods of Python interpreter
import time #Provides time-related functions i.e. sleep
from base64 import b64encode, b64decode #Ability to encode string using Base64
import cx_Oracle #Python extension that enables access to Oracle Database (Pre-requisite need client)
from ast import literal_eval #Raises an exception if the input isn't a valid Python datatype, so the code won't be executed if it's not.
from urllib import request, parse
import json
import smashing
from datetime import datetime

STREAM_NAME = "jod"
PARTITIONS = 1

#Create dashboard function and update different parameters with the real-time values gathered from the plug
def dashboard(k, v):
   if k in 'energy':
      power = str(v['power_mw']/1000)
      voltage = str(v['voltage_mv']/1000)
      current = str(v['current_ma']/1000)
      timeNow = str(v['total_wh'])
      smashing.UpdateMeter("power", power)
      smashing.UpdateMeter("voltage", voltage)
      smashing.UpdateMeter("current", current)
      smashing.UpdateMeter("timeNow", timeNow)

#Calculating duration the device has been 'On' since last 'Off' state
   if k in 'deviceRuntime':
       onSince = str(v)
       smashing.UpdateMeter("onSince", onSince)

#Calculating average cost to run the currently connected device since last 'Off' state
   if k in 'avgCost':
       cost = str(v)
       smashing.UpdateMeter("cost", cost)
       
#Function that allows us to connect to the database and insert parameters into the table
#Inserted every 5 seconds (stream time) and viewed through SQL Developer
def insert(v):
    conn = cx_Oracle.connect('user_name','user_password','user_database_name')
    cur = conn.cursor()

#   v = plug.get_emeter_realtime()
#    a = '{\'voltage_mv\':' +  str(v['voltage_mv']) + ',\'current_ma\':' + str(v['current_ma']) + ',\'power_mw\':' + str(v['current_ma']) + ',\'total_wh\':' + str(v['total_wh']) + '}'

    power = str(v['power_mw'])
    voltage = str(v['voltage_mv'])
    current = str(v['current_ma'])
    timeNow = str(v['total_wh'])

#    b = 'Insert into ADMIN.READINGS (VOLTAGES,CURRENTS,POWERS,TOTALS) values (4, \'' + a
    statement = 'Insert into ADMIN.hs110_data (VOLTAGES,CURRENTS,POWERS,TIMENOW) values (:1,:2,:3,:4)'
    cur.execute(statement,(voltage,current,power,timeNow))
    conn.commit()

#Function that gets or creates stream based on input parameters
def get_or_create_stream(client, compartment_id, stream_name, partition, sac_composite):

    list_streams = client.list_streams(compartment_id, name=stream_name,
                                       lifecycle_state=oci.streaming.models.StreamSummary.LIFECYCLE_STATE_ACTIVE)
    if list_streams.data:
        # If we find an active stream with the correct name, we'll use it.
        print("An active stream {} has been found".format(stream_name))
        sid = list_streams.data[0].id
        return get_stream(sac_composite.client, sid)

    print(" No Active stream  {} has been found; Creating it now. ".format(stream_name))
    print(" Creating stream {} with {} partitions.".format(stream_name, partition))

    # Create stream_details object that need to be passed while creating stream.
    stream_details = oci.streaming.models.CreateStreamDetails(name=stream_name, partitions=partition,
                                                              compartment_id=compartment, retention_in_hours=24)

    # Since stream creation is asynchronous; we need to wait for the stream to become active.
    response = sac_composite.create_stream_and_wait_for_state(
        stream_details, wait_for_states=[oci.streaming.models.StreamSummary.LIFECYCLE_STATE_ACTIVE])
    return response

#Reading message send from the stream 'producer.py'
def simple_message_loop(client, stream_id, initial_cursor):
    cursor = initial_cursor
    while True:
        get_response = client.get_messages(stream_id, cursor, limit=1)
#        print(str(get_response.data[0])[35:38])
        # No messages to process. return.
        if not get_response.data:
            return
        
#        if int(str(get_response.data[0])[35:38]) > 500:

        # Process the messages
        print(" Read {} messages".format(len(get_response.data)))
        for message in get_response.data:
            if message.key is not None and message.value is not None:
#                    print("{}".format(b64decode(message.value.encode()).decode()))
#                    print('key is ' + b64decode(message.key.encode()).decode())
                    key_to_validate = b64decode(message.key.encode()).decode()
                    if key_to_validate in 'energy':
                        insert(literal_eval("{}".format(b64decode(message.value.encode()).decode())))
                        dashboard(b64decode(message.key.encode()).decode(), literal_eval("{}".format(b64decode(message.value.encode()).decode())))
                    if key_to_validate in 'deviceRuntime' or key_to_validate in 'avgCost':
                        dashboard(b64decode(message.key.encode()).decode(), "{}".format(b64decode(message.value.encode()).decode()))
        time.sleep(1)
        cursor = get_response.headers["opc-next-cursor"]

def get_stream(admin_client, stream_id):
    return admin_client.get_stream(stream_id)

def get_cursor_by_partition(client, stream_id, partition):
    print("Creating a cursor for partition {}".format(partition))
    cursor_details = oci.streaming.models.CreateCursorDetails(
        partition=partition,
        type=oci.streaming.models.CreateCursorDetails.TYPE_TRIM_HORIZON)
    response = client.create_cursor(stream_id, cursor_details)
    cursor = response.data.value
    return cursor


# Load the default configuration
config = oci.config.from_file()

# Create a StreamAdminClientCompositeOperations for composite operations.
stream_admin_client = oci.streaming.StreamAdminClient(config)
stream_admin_client_composite = oci.streaming.StreamAdminClientCompositeOperations(stream_admin_client)

if len(sys.argv) != 2:
    raise RuntimeError('This example expects an ocid for the compartment in which streams should be created.')

compartment = sys.argv[1]

# We  will reuse a stream if its already created.
# This will utilize list_streams() to determine if a stream exists and return it, or create a new one.
stream = get_or_create_stream(stream_admin_client, compartment, STREAM_NAME,
                              PARTITIONS, stream_admin_client_composite).data

# Streams are assigned a specific endpoint url based on where they are provisioned.
# Create a stream client using the provided message endpoint.
stream_client = oci.streaming.StreamClient(config, service_endpoint=stream.messages_endpoint)
s_id = stream.id

partition_cursor = get_cursor_by_partition(stream_client, s_id, partition="0")
simple_message_loop(stream_client, s_id, partition_cursor)


