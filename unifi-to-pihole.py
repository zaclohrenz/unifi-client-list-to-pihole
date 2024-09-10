#!/usr/bin/env python3

import argparse, string, os, sys
import json
from netaddr import *
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# Suppress only the single InsecureRequestWarning from urllib3
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

parser = argparse.ArgumentParser(description="Fetch list of hosts from UniFi controller and update Pi-hole DNS")
parser.add_argument('-v', '--verbose', action='store_true', help="print additional information")
parser.add_argument('-f', '--hostfile', help="hosts file to use", default="/etc/pihole/lan.list")
parser.add_argument('-c', '--controller', help="controller IP or hostname")
parser.add_argument('-u', '--user', help="username")
parser.add_argument('-p', '--password', help="password")
args = parser.parse_args()

print("Script started")

if args.verbose:
    print(f"Arguments: {args}")

controllerIP = args.controller or os.getenv("UNIFI_CONTROLLER") or input('Controller: ')
userName = args.user or os.getenv("UNIFI_USER") or input('Username: ')
password = args.password or os.getenv("UNIFI_PASSWORD") or input('Password: ')

print(f"Using controller IP {controllerIP}")
print(f"Using username {userName}")

login_url = f"https://{controllerIP}:443/api/auth/login"
query_url = f"https://{controllerIP}:443/proxy/network/api/s/default/rest/user"

session = requests.Session()
login_data = {"username": userName, "password": password}

print("Attempting to login to UniFi Controller...")
try:
    response = session.post(login_url, json=login_data, verify=False)
    response.raise_for_status()
    print("Login successful")
    if args.verbose:
        print(f"Login response: {response.text}")
except requests.exceptions.RequestException as e:
    print(f"Error connecting to UniFi Controller: {e}")
    sys.exit(1)

print("Querying UniFi Controller for client data...")
try:
    response = session.get(query_url, verify=False)
    response.raise_for_status()
    data = response.json()
    print("Query successful")
    if args.verbose:
        print(f"Query response: {json.dumps(data, indent=2)}")
    clients = data.get('data', [])
    print(f"Number of clients returned: {len(clients)}")
except requests.exceptions.RequestException as e:
    print(f"Error querying UniFi Controller: {e}")
    sys.exit(1)

dns_entries = []

print("Processing client data...")
for client in clients:
    ip = client.get('last_ip')
    name = client.get('name')
    hostname = client.get('hostname')
    mac = client.get('mac')

    if ip:
        if name:
            dns_name = name.lower().replace(" ", "-")
        elif hostname:
            dns_name = hostname.lower().replace(" ", "-")
        else:
            dns_name = mac.replace(":", "").lower()

        dns_entries.append(f"{ip} {dns_name}")
        if args.verbose:
            print(f"Added entry: {ip} {dns_name}")

print(f"Using hosts file {args.hostfile}")
print(f"Found {len(dns_entries)} DNS entries")

if dns_entries:
    print("Attempting to write DNS entries to file...")
    try:
        with open(args.hostfile, 'w') as f:
            for entry in dns_entries:
                f.write(f"{entry}\n")
        print("Hosts file updated successfully")

        # Restart Pi-hole DNS
        print("Restarting Pi-hole DNS...")
        os.system("pihole restartdns")
        print("Pi-hole DNS restarted")
    except PermissionError:
        print(f"Error: You need root permissions to write to {args.hostfile}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")
        sys.exit(1)
else:
    print("No DNS entries found to update")

print("Script completed")