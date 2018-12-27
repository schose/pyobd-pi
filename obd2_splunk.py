import obd_io
import serial
import platform
import obd_sensors
from datetime import datetime
import time
import getpass
import os
import socket
import sys
import logging
from obd_utils import scanSerial
import requests
import json


def add_log_item(llogitems):
    
    lsensorlist = []

    for logitem in llogitems:
        for index, e in enumerate(obd_sensors.SENSORS):
            if(logitem == e.shortname):
                    logging.debug("adding Logging item..: %s", e.name)
                    lsensorlist.append(index)
                    break

    return lsensorlist

def connect_port(lsensorlist):
    logging.debug("in connect_port ")
    #portnames = scanSerial()
    
    portnames = ['/dev/rfcomm0']
    logging.info("using port %s", portnames)
    lport = ""

    if debug != 1:
        for port in portnames:
            lport = obd_io.OBDPort(port, None, 2, 2)

            # if(self.port.State == 0):
            #     self.port.close()
            #     self.port = None
            # else:
            #     break


        if(lport):
            logging.debug("Connected to %s", lport.port.name)

    testme = [
    ("pids"                  , "Supported PIDs"				, "0100" , "100",""       ), 
    ("dtc_status"            , "S-S DTC Cleared"				, "0101" , "100",""       ),    
    ("dtc_ff"                , "DTC C-F-F"					, "0102" , "100",""       ),      
    ("fuel_status"           , "Fuel System Stat"				, "0103" , "100",""       ),
    ("load"                  , "Calc Load Value"				, "01041", "100",""       ),    
    ("temp"                  , "Coolant Temp"					, "0105" , "100","F"      ),
    ("short_term_fuel_trim_1", "S-T Fuel Trim"				, "0106" , "100","%"      ),
    ("long_term_fuel_trim_1" , "L-T Fuel Trim"				, "0107" , "100","%"      ),
    ("short_term_fuel_trim_2", "S-T Fuel Trim"				, "0108" , "100","%"      ),
    ("long_term_fuel_trim_2" , "L-T Fuel Trim"				, "0109" , "100","%"      ),
    ("fuel_pressure"         , "FuelRail Pressure"			, "010A" , "100",""       ),
    ("manifold_pressure"     , "Intk Manifold"				, "010B" , "100","psi"    ),
    ("rpm"                   , "Engine RPM"					, "010C1", "100",""       ),
    ("speed"                 , "Vehicle Speed"				, "010D1", "33","MPH"    ),
    ("timing_advance"        , "Timing Advance"				, "010E" , "100","degrees"),
    ("intake_air_temp"       , "Intake Air Temp"				, "010F" , "100","F"      ),
    ("maf"                   , "AirFlow Rate(MAF)"			, "0110" , "100","lb/min" ),
    ("throttle_pos"          , "Throttle Position"			, "01111", "100","%"      ),
    ("secondary_air_status"  , "2nd Air Status"				, "0112" , "100",""       ),
    ("o2_sensor_positions"   , "Loc of O2 sensors"			, "0113" , "100",""       ),
    ("o211"                  , "O2 Sensor: 1 - 1"				, "0114" , "100","%"      ),
    ("o212"                  , "O2 Sensor: 1 - 2"				, "0115" , "100","%"      ),
    ("o213"                  , "O2 Sensor: 1 - 3"				, "0116" , "100","%"      ),
    ("o214"                  , "O2 Sensor: 1 - 4"				, "0117" , "100","%"      ),
    ("o221"                  , "O2 Sensor: 2 - 1"				, "0118" , "100","%"      ),
    ("o222"                  , "O2 Sensor: 2 - 2"				, "0119" , "100","%"      ),
    ("o223"                  , "O2 Sensor: 2 - 3"				, "011A" , "100","%"      ),
    ("o224"                  , "O2 Sensor: 2 - 4"				, "011B" , "100","%"      ),
    ("obd_standard"          , "OBD Designation"				, "011C" , "100",""       ),
    ("o2_sensor_position_b"  , "Loc of O2 sensor" 			, "011D" , "100",""       ),
    ("aux_input"             , "Aux input status"				, "011E" , "100",""       ),
    ("engine_time"           , "Engine Start MIN"				, "011F" , "100","min"    ),
    ("engine_mil_time"       , "Engine Run MIL"				, "014D" , "100","min"    ),
        ]

    while 1:

        outresults = {}

        for index in lsensorlist:
            #(name, value, unit) = lport.sensor(index)
            
            if debug == 1: 
                name = testme[index][1]
                value = testme[index][3]
                unit = testme[index][4]
            else:
                (name, value, unit) = lport.sensor(index)

            logging.debug("name:%s value:%s unit:%s", name, value, unit)

            if name == "Vehicle Speed": 
                value = (round(float(value)*1.609,2))
            if name == "Calc Load Value": 
                value = round(float(value),2)

            outresults[name] = value; 

        url = 'http://splunk.batchworks.de:8890/services/collector/raw'
        payload = json.dumps(outresults)
        headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8', 'Authorization': 'Splunk d8d17157-a4d3-4bb2-98cd-e636c5ebc088'}
        r = requests.post(url, data=payload, headers=headers)

        logging.debug("do the curl request")
        time.sleep(1)

if __name__ == "__main__":
    try: 
        dp0 = os.path.dirname(__file__)
        logdir = ""

        debug = 1

        # init logging
        if not logdir:
            logdir = os.path.join(dp0, "logs")
        else:
            logdir = os.path.join(dp0, logdir)

        if not os.path.exists(logdir):
            os.mkdir(logdir)

        tmp = datetime.now()
        logfilename = os.path.join(logdir, ("obd2_splunk_" + tmp.strftime("%Y%d%m-%H%M%S") +".log" ) )

        logging.basicConfig(format='%(asctime)s %(message)s', filename=logfilename, level=logging.DEBUG )

        log = logging.getLogger('')
        ch = logging.StreamHandler(sys.stdout)
        log.addHandler(ch)

        logging.debug("logfile started at %s", logfilename)

        logitems = ["rpm", "speed", "load"]
        
        sensorlist = []
        sensorlist = add_log_item(logitems)

        connect_port(sensorlist)
        #get_data()

    except Exception:
        import traceback
        traceback.print_exc(file=sys.stdout)