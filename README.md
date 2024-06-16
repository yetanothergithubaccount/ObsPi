# ObsPi
This is the minimal source code base to run a simple Raspberry Pi based DSO observation planning tool within a WiFi network.

## Requirements
### Hardware
- Raspberry Pi 3/4

### Software
#### Requirements
- Raspberry Pi OS, e.g. Bookworm
- Python3, pip3
```sudo apt install python3-pip```
- suntime
```sudo pip3 install astropy --break-system-packages```
```sudo pip3 install matplotlib --break-system-packages```
```sudo pip3 install numpy --break-system-packages```

## Installation
Run the sky/dso/setup.sh script for basic installation.

This will install the dsoserver which will be launched via systemctl.

## Functionality
The crontab will be extended to run the python script which will create the DSO visibility catalogue and DSO-plots per day. The calculations will take a while, so the cronjob is installed tu run at 3.02 am in the morning. The catalogue and the plots will be stored in /home/pi/sky/dso.
The dsoserver can be accessed in the same WiFi network with a browser:

Display all available DSO visibility plots for tonight:
http://111.222.333.4:44444/tonight
http://101.202.303.4:44444/tonight/list

Display the best visible DSOs in the South which are above 10 degrees altitude
http://111.222.333.4:44444/best/S/10.0
http://111.222.333.4:44444/best/S/10.0/list


