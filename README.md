# Energy-Consumption_Oracle

#### Welcome

#### This repository will provide you with an insight into my ability to code with 'Python' through a project I worked on during the time of my internship here in Oracle Dublin as a Solution Engineer.

#### Within this directory you will see a list of folders that contain the contents of my work over the past 3 months.

#### Thanks.

---------------------------------------------------------------------------------------------------------------------------------------Youtube Video: 

![4d94500617bf4979d1099ce63b058b19](https://user-images.githubusercontent.com/36043248/64624320-67db3680-d3e2-11e9-9f16-ebc9d183f2cc.png)

![fb4bde7ef365670e9459ebb53c3380a9](https://user-images.githubusercontent.com/36043248/64599145-cb4c7080-d3b0-11e9-978c-755d521e0b7b.png)

#### Project Concept:

Reducing Energy Consumption in the Workplace through the integration of AI and real-time data diagnostics to better reduce our overall carbon footprint.

#### Project Breakdown:

1. Deploy an instance of an Autonomous Data Warehouse (Database) in our tenancy:
    - This database will store the real-time energy consumption statistics of the device currently connected to the smart plug.
2. Deploy an OCI Streaming instance:
    - This streaming service will give us the ability to stream the information from a VM (Virtual Machine) to the Oracle Cloud.
    - This will then allow us to store the data off-premise in the database which we can then perform analytics upon to reveal trends/
      patterns.
3. TP Link HS110 Smart Plug is connected and configured:
   - The plug is connected to the wall socket and a device of our choosing is then connected to the plug.
   - The HS110 is configured (connected to the Wi-Fi) through the 'Kasa' app available on both the 'Play Store' and 'App Store'.
4. Smashing Dashboard:
   - With the help of the Smashing Dashboard repository (https://smashing.github.io), we had to ability to create a  dashboard via HTML. (#image above#)
   - This repository helped me to update the dashboard and add widgets etc. (https://github.com/AnykeyNL/oci-smashing)
   - It stores information regarding the consumption data of the device via the help of the 'consumer.py' script I will soon discuss in more detail.
   - We have the ability to update the 'workplace-energy-consumption.erb' file which simply gives us the ability to modify the layout and content displayed on the dashboard. This file is stored on a remote server unlike the rest of the files provided above, which are stored locally.
   - The 'smashing.py' file is the script which allows us to associate a URL to the dashboard so we can access it through our browser. (#image above#)
5. Producing Stream
   - A 'producer.py' script extracts the data from the smart plug. 
   - This date consists of power, current, voltage, runtime etc with the help of this repository        (https://github.com/GadgetReactor/pyHS100). 
   - It then transfers this real-time data onto the network to be consumed by another script.
6. Consuming Stream
   - A 'consumer.py' script then extracts the real-time data from the network.
   - It insert the contents of the stream into the Autonomous Data Warehouse we deployed earlier with the help of 'SQL   . 
     Developer' to view and modify its contents.
   - The file also has the ability to update our dashboard with the real-time statistics.



