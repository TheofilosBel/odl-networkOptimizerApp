#!/usr/bin/python                                                                            
                                                                                             
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel
from mininet.node import RemoteController, OVSKernelSwitch
from mininet.cli import CLI
from time import sleep
import sys                

# Get server ip and port from command line
server_ip = None #'192.168.56.1'
server_port = None #6653
if len(sys.argv) < 3:
    print "[INFO] Wrong usage, try: python tests.py <server-ip> <server-port>"
    exit(0)
else:
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

# Init Mininet / Controller
net = Mininet(topo=None,controller=None,switch=OVSKernelSwitch)
controller = net.addController(name='c0', controller=RemoteController, ip=server_ip, port=server_port);


# Create switches
s1 = net.addSwitch('s1', protocols='OpenFlow13')
s2 = net.addSwitch('s2', protocols='OpenFlow13')
s3 = net.addSwitch('s3', protocols='OpenFlow13')
s4 = net.addSwitch('s4', protocols='OpenFlow13')

# Create hosts
h1 = net.addHost('h1', ip='10.0.0.1')
h2 = net.addHost('h2', ip='10.0.0.2')
h3 = net.addHost('h3', ip='10.0.0.3')
h4 = net.addHost('h4', ip='10.0.0.4')

# Create links
net.addLink(h1, s1)
net.addLink(h2, s2)
net.addLink(h3, s3)
net.addLink(h4, s4)

net.addLink(s1, s2)
net.addLink(s2, s4)
net.addLink(s1, s3)
net.addLink(s3, s4)


# Start the network
net.start()


# Do 2 pingAlls to make sure everything is okay
print "------------\n",
print "PING ALL x 2"
print "------------\n",
net.pingAll()
net.pingAll()

print "\n----------------------------------\n",
print "STARTING TEST: 'Network Optimizer'"
print "----------------------------------\n\n",
print "+ Run iperf without optimizing the network..."

# Run iperf of h1 and get it's pid
print "|-Run iperf on h1 (as server)"
h1.cmd('iperf -s -P 2 > /tmp/h1.out &')
pidh1 = int( h1.cmd('echo $!') )

sleep(0.5)

print "|-Run iperf on h3 (client) to h1 (server)"
print "|-OUTPUT:\n", h3.cmd('iperf -c 10.0.0.1 -t 6 -i 2')

# Run the optimizer

print "+ Run the simple_optimizer.py and press enter..."
raw_input()

print "|-Run iperf again on h3 (client) to h1 (server)"
print "|-OUTPUT:\n", h3.cmd('iperf -c 10.0.0.1 -t 6 -i 2')

# Kill server task
print "|-Kill server...", h1.cmd('kill -9', pidh1)
print "*\n"

print "-----------------------\n",
print "READING SERVER'S OUTPUT"
print "-----------------------\n",
f = open('/tmp/h1.out')    
for line in f.readlines():
    print "%s" % ( line.strip() )        
f.close()


print "\n-----------------------\n",
print "OPENING A CLI"
print "-----------------------\n",
CLI(net)
net.stop()
