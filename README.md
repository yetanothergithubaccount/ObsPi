# ObsPi
This is the minimal source code base to run a simple Raspberry Pi based DSO observation planning tool within a WiFi network. The DSO visibility tool is based on https://docs.astropy.org/en/stable/generated/examples/coordinates/plot_obs-planning.html .

## Requirements
### Hardware
- Raspberry Pi 3/4

### Software
#### Requirements
- Raspberry Pi OS, e.g. Bookworm
- Python3, pip3
```sudo apt install python3-pip```
- suntime
```sudo pip3 install matplotlib --break-system-packages```
```sudo pip3 install numpy --break-system-packages```
```sudo pip3 install astropy --break-system-packages```
```sudo pip3 install bottle --break-system-packages```

## Installation
Run the /home/pi/setup.sh script for basic installation.

The required python packages will be added if missing.
The dsoserver which will be launched via systemctl will be set up.
On request the DSO visibility catalogue and plots will be created for today.

## Functionality
The crontab will be extended to run the python script which will create the DSO visibility catalogue and DSO-plots per day for your location. The location coordinates are stored in sky/dso/config.py.
The calculations will take a while, so the cronjob is installed tu run at 3.02 am in the morning. The catalogue and the plots for the day will be stored in /home/pi/sky/dso.

The dsoserver can be accessed in the same WiFi network with a browser:

Display all available DSO visibility plots for tonight either as graphs or list:
http://111.222.333.4:44444/tonight
http://111.222.333.4:44444/tonight/list

Display the best visible DSOs in the South which are above 10 degrees altitude
http://111.222.333.4:44444/best/S/10.0
http://111.222.333.4:44444/best/S/10.0/list

![M5 visibility plot](https://github.com/yetanothergithubaccount/ObsPi/blob/master/sky/dso/DSO_M5_16.06.2024.png)

