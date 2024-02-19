# PNEUMOS_SW

INSTRUCTION
1. start audio_patch.pd
2. connect dac~ 1 2 to myosc 1 and 2
3. set Audio Output in preferences
4. start python getApy.py using:
    -   python getApi.py
    It will automatically (and locally on 127.0.0.1:12345) sends the distances and breath function
4.1 for test and debug, use:
    -   python getApi_fake.py (argument integer)
    where argument is the interval (in minutes)
    It will use a local dictionary ("scpdump.json")
    
REQUIREMENTS
Python 3.11
libraries:
-   numpy
-   scipy
-   pythonosc
-   schedule

PureData
libraries:
-   cyclone
-   else
-   comport

UPDATES
-  Pure Data patch update:
-   -   nw it uses noise~ and cyclone/reson~ instead of osc~
-   -   new abstfraction for sound generator (noise_reson)

-  Python script update:
    -  getApi_fake.py takes 1 input argument = interval (in minutes) between outputs (udp)
    -  getApi.py working with synced API DARE datas every 30 minutes
