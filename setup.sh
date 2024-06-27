#!/bin/bash

echo "Setup DSO observation tool..."

add2crontab() {
  echo "insert: $1"
  (crontab -l 2>/dev/null; echo "$1") | crontab -
}

echo "Update python installation..."
sudo pip3 install matplotlib --break-system-packages
sudo pip3 install numpy --break-system-packages
sudo pip3 install astropy --break-system-packages
sudo pip3 install bottle --break-system-packages
sudo pip3 install pyephem --break-system-packages
sudo pip3 install skyfield --break-system-packages
sudo pip3 install pytz --break-system-packages
sudo pip3 install astroquery --break-system-packages
sudo pip3 install spaceweather --break-system-packages

echo "Install DSO service."
sudo cp /home/pi/sky/dso/dsoserver.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable dsoserver.service
sudo systemctl start dsoserver.service

echo "Update crontab..."
add2crontab "# check DSO visibility for the actual day"
add2crontab "2 3 * * * python3 /home/pi/sky/dso/DSO_observation_planning.py --catalogue --plot"


echo "DSO observation tool installation succeeded."

read -n1 -p "Create DSO catalogue/plots for today now This will take a while.? [y,n]" doit 
case $doit in
  y|Y) python3 /home/pi/sky/dso/DSO_observation_planning.py --catalogue --plot ;;
  n|N) echo "Nope." ;;
esac

echo "In a browser check:"
echo "DSO visibility tonight plotted: http://101.202.303.4:44444/tonight"
echo "DSO visibility tonight as a list: http://101.202.303.4:44444/tonight/list"
echo "Best DSOs tonight in the South above 10 degrees plotted: http://101.202.303.4:44444/best/S/10.0"
echo "Best DSOs tonight in the South above 10 degrees as a list: http://101.202.303.4:44444/best/S/10.0/list"
echo "DSO visibility on another date: http://101.202.303.4:44444/<dd.mm.yyyy>"
echo "DSO visibility on another date as a list: http://101.202.303.4:44444/<dd.mm.yyyy>/list"


