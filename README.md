# unifi-client-list-to-pihole
I wanted to solve for pihole having no awareness of my client names and only showing me IPs, so this periodically pulls them in from unifi controller.

On the unifi controller, add a local-only user.

On the pi, install dependencies   
sudo apt-get install python3 python3-pip -y
sudo pip install netaddr unifi python-hosts

Then edit cron:
crontab -e

Add an entry such as this, with your unifi's IP and user/pass info:
*/15 * * * * python3 /home/pi/unifi-to-pihole.py -c 192.168.1.1 -u unifi -p password -f /etc/pihole/lan.list

Works with pihole 5 and unifiOS 4