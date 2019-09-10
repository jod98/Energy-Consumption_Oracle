import oci #Python OCI SDK github: Allows us to provide Object Storage URL, namespace etc. to specify location to import from
import sys #Provides in information about constants, variables and methods of Python interpreter
import time #Provides time-related functions i.e. sleep
from base64 import b64encode, b64decode #Ability to encode string using Base64
from pyHS100 import SmartPlug, SmartBulb #Provide Smart Plug and Bulb repository (made visible)
from pprint import pformat as pf #PrettyPrint: 
from datetime import datetime
from ast import literal_eval #Raises an exception if the input isn't a valid Python datatype, so the code won't be executed if it's not.

STREAM_NAME = "jod"
PARTITIONS = 1

#Function that gets or creates stream based on input parameters
def get_or_create_stream(client, compartment_id, stream_name, partition, sac_composite):

    list_streams = client.list_streams(compartment_id, name=stream_name,
                                 	lifecycle_state=oci.streaming.models.StreamSummary.LIFECYCLE_STATE_ACTIVE)

#If no stream found, a stream in then created i.e. always have an active stream
    if list_streams.data:
        #If we find an active stream with the correct name, we'll use it.
        print("An active stream {} has been found".format(stream_name))
        sid = list_streams.data[0].id
        return get_stream(sac_composite.client, sid)

    print(" No Active stream  {} has been found; Creating it now. ".format(stream_name))
    print(" Creating stream {} with {} partitions.".format(stream_name, partition))

#Create stream_details object that need to be passed while creating stream.
    stream_details = oci.streaming.models.CreateStreamDetails(name=stream_name, partitions=partition,
                                                              compartment_id=compartment, retention_in_hours=24)

#Since stream creation is asynchronous; we need to wait for the stream to become active.
    response = sac_composite.create_stream_and_wait_for_state(
        stream_details, wait_for_states=[oci.streaming.models.StreamSummary.LIFECYCLE_STATE_ACTIVE])
    return response

#Publishing messages to stream i.e. energy monitoring data from 'plug.get_emeter_realtime()' func
def publish_example_messages(client, stream_id):
    # Build up a PutMessagesDetails and publish some messages to the stream
    message_list = []

    #Get Current Runtime (Length of Time its Running)
    timestamp = str(plug.get_emeter_daily).split("datetime.datetime(",1)[1]

    #Getting onSince time
    hour = str(timestamp[12:13])
    minu = str(timestamp[16:17])
    sec = str(timestamp[19:20]) #Alter these current_time - runtime doesn't work sometimes if single digit/double digit
    arr = [hour, minu, sec]

    i = 0
    while i < 3:
        if len(arr[i]) < 2:
            arr[i] = arr[i].rjust(2, '0') 
        i += 1

    hour = arr[0]; minu = arr[1]; sec = arr[2]
    onSince = hour + ":" + minu + ":" + sec

    #Print current time
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    #print(current_time)

    #Print diff in time
    FMT = '%H:%M:%S'
    diffHours = ((datetime.strptime(current_time, FMT) - datetime.strptime(onSince, FMT)).total_seconds())/60
    diffHours = diffHours/60
    #print(diffHours)

    #Average cost so far of keeping that appliance on for that length of time, varies
    power = plug.get_emeter_realtime()["power"]
    myCurrentkWhCost = (power * diffHours * 0.1451)/100 # energia
    myCurrentkWhCost = round(myCurrentkWhCost, 2)    
    myCurrentkWhCost = str(myCurrentkWhCost)
    #print(myCurrentkWhCost)

    ####################################################################
    key = "energy"
    key1 = "deviceRuntime" 
    key2 = "avgCost"

    now1 = datetime.now()
#    current_time1 = now1.strftime("%H:%M:%S")
    updatedEnergy = literal_eval(str(plug.get_emeter_realtime()))
    updatedEnergy['total_wh'] = str(now1)
    
    value_eneregy = str(updatedEnergy)
    value_onSince = hour + ":" + minu + ":" + sec    
    value_cost = myCurrentkWhCost
    
    print(value_eneregy)
    print(onSince)
    print(myCurrentkWhCost)

    encoded_key = b64encode(key.encode()).decode()
    encoded_key1 = b64encode(key1.encode()).decode()
    encoded_key2 = b64encode(key2.encode()).decode()
    
    encoded_value = b64encode(value_eneregy.encode()).decode()
    encoded_value1 = b64encode(value_onSince.encode()).decode()
    encoded_value2 = b64encode(value_cost.encode()).decode()
    
    message_list.append(oci.streaming.models.PutMessagesDetailsEntry(key=encoded_key, value=encoded_value))
    message_list.append(oci.streaming.models.PutMessagesDetailsEntry(key=encoded_key1, value=encoded_value1))
    message_list.append(oci.streaming.models.PutMessagesDetailsEntry(key=encoded_key2, value=encoded_value2))

    messages = oci.streaming.models.PutMessagesDetails(messages=message_list)
    put_message_result = client.put_messages(stream_id, messages)
    
    ######################################################################
#The put_message_result can contain some useful metadata for handling failures
    for entry in put_message_result.data.entries:
        if entry.error:
            print("Error ({}) : {}".format(entry.error, entry.error_message))
        else:
            print("Published message to partition {} , offset {}".format(entry.partition, entry.offset))

def get_stream(admin_client, stream_id):
    return admin_client.get_stream(stream_id)


# Load the default configuration. User credentials
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

#Smart Plug IP address
plug = SmartPlug("192.168.43.127")

#If remains connected to smart plug, stream messages every 5 seconds (real time)
while True:
    publish_example_messages(stream_client, s_id)
    time.sleep(1)



