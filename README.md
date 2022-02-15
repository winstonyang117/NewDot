# NewDot

**Step 1: Install Raspberry Pi image and enable wifi and ssh

Set up wifi and ssh in Raspberry Pi without monitor and keyboard: https://desertbot.io/blog/headless-raspberry-pi-4-ssh-wifi-setup

**Step 2: Install pip3, ntp and packages

Raspberry OS has python3 isntalled by default. If your OS does not have python3 installed, then first run "sudo apt install python3 -y".

```
  sudo apt update
  sudo apt install ntp
  sudo apt install python3-pip -y
  sudo pip3 install pyserial
  sudo pip3 install netifaces
```

With Raspberry Pi 0 W, if the serial port is not enabled by default (/dev/ttyS0 does not exist), then run
```
  sudo raspi-config
```

Choose "3. Interface Options" -> "Serial Port" -> enable
```
  sudo raspi-config
```

Now, /dev/ttyS0 should appear. Test this command and you should see the data in the displayed Grafana URL by the code:

```
sudo python3 serialClient_final.py /dev/ttyS0
```

**Step 3: Setup the NewDot service

```
  sudo apt install git
  git clone https://github.com/wsonguga/NewDot.git
  sudo ./setup_service.sh
```

