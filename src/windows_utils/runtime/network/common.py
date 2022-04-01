import netifaces
from threading import Thread
import socket
import ipaddress

vuln = dict()

def get_lan() -> set:
    """
    this function should return set of address of "nearby" ip by lan.
    //TODO 20: find better way to to this
    //TODO 21: WHY DA FUCK ONLY 192.168 OR 172.16?
    """
    interfaces = netifaces.interfaces()
    local_ip = set()
    for interface in interfaces:
        if interface == 'lo':
            continue
        iface = netifaces.ifaddresses(interface).get(netifaces.AF_INET)
        if iface:
            for j in iface:
                addr = str(j['addr'])
                if not addr.startswith('169.254') and not addr.startswith('127.0'):
                    local_ip.add(addr)
    return local_ip


def scan(port_range: set, ip: str) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    for port in port_range:
        result = s.connect_ex((str(ip), int(port)))
        if result == 0:
            if vuln.get(ip):
                vuln[ip].add(port)
            else:
                vuln[ip] = {port}
    return True

def get_vuln_ports() -> dict:
    """
    This function should "scan" for open ports from the vuln_ports set.
    this is kind'a fucked up and would probably too noisy.
    the function return dict of {ip: "open_port,open_port"}
    //TODO 22: make it return list of port instead of string.
    //TODO 23: nmap ? XMAS? just find better way
    """
    vuln_ports = {'445', '3389', '5985', '22'}
    threads = []
    local_ip = get_lan()
    for addr in local_ip:
        range = ipaddress.ip_network(f"{addr.strip().split('.')[0]}.{addr.strip().split('.')[1]}.1.0/24")
        for ip in range.hosts():
            threads.append(Thread(target=scan, args=(vuln_ports, ip)))
    for index, thread in enumerate(threads):
        thread.start()
        if index % 555 == 0:
            thread.join()
            # we prevent too much threads by joining one out 9
    return vuln