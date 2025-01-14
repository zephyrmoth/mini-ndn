#!/usr/bin/python

""" This program used to build ad hoc network.
propagation Model function must be call just before
calling of function for configuring wifi node.
So, need to this program. """
import sys
import datetime
import random # This line for graph
from functools import partial
from subprocess import call
from mn_wifi.net import Mininet_wifi
from ndn.ndn_host import NdnHost, CpuLimitedNdnHost
from ndnwifi_host import NdnStation
from mininet.link import TCLink
from mininet.node import Controller
from mininet.log import setLogLevel, output, info
from mininet.examples.cluster import MininetCluster, RoundRobinPlacer, ClusterCleanup
from mn_wifi.link import Association, adhoc
from ndnwifi.wifiutil import MiniNdnWifiCLI
import matplotlib.pyplot as plt
from ndn.nfd import Nfd
from ndnwifi import WifiExperimentManager

def build_adhocnet(adhocTopo, isManet, isAdhoc, ssid, channel, mode, wmediumd, interference,
                   cluster, placement, servers, tunnelType, ctime, nPings, pctTraffic, experimentName, nlsrSecurity):
    """Create an ad hoc network from a topology object
       At the end of this function, everything should be connected
       and up..
       adhocTopo:topology object that be builded according to a file of network topology configure;
       isManet: mobile ad hoc network;
       isAdhoc: stationary ad hoc network;
       channel: channel parames;
       ssid: service set identifier;
       wmedimd:param for 802.11 simulation tool;
       interference: param for 802.11 simulation tool;
       placement:
       servers:
       tunnelType:
       the following paramters are for experiments.
       ctime: specific time that the nentwork covergence;
       nPings: number that perform
    """
    t = datetime.datetime.now()
    cls = Association
    cls.printCon = False
    #build a wire network or a wirelesswork network.
    #topology object adhocTopo can't make as  params in Mininet object definination.
    if adhocTopo.isTCLink == True and adhocTopo.isLimited == True:
        adhocnet = Mininet_wifi(host=CpuLimitedNdnHost, station=NdnStation, link=wmediumd ,controller=Controller,
                           ssid=ssid, channel=channel, mode=mode,
                           wmediumd_mode=interference)
    elif adhocTopo.isTCLink == True and adhocTopo.isLimited == False:
        if cluster is not None:
            mn = partial(MininetCluster, servers=servers, placement=placement)
            adhocnet = mn(host=NdnHost, station=NdnStation, link=wmediumd ,controller=Controller,
                          ssid=ssid, channel=channel, mode=mode,
                          wmediumd_mode=interference)
        else:
            adhocnet = Mininet_wifi(host=NdnHost, station=NdnStation, link=wmediumd, controller=Controller,
                                    ssid=ssid, channel=channel, mode=mode, wmediumd_mode=interference)

    elif adhocTopo.isTCLink == False and adhocTopo.isLimited == True:
        adhocnet = Mininet_wifi(host=CpuLimitedNdnHost, station=NdnStation, controller=Controller, ssid=ssid, channel=channel,
                                mode=mode, link=wmediumd, wmediumd_mode=interference)

    else:
        adhocnet = Mininet_wifi(host=NdnHost, station=NdnStation, controller=Controller, ssid=ssid, channel=channel,
                                mode=mode, link=wmediumd, wmediumd_mode=interference)

    info('*** Creating adhoc network\n')
    if not adhocnet.controllers and adhocnet.controller:
        # Add a default controller
        info('*** Adding controller\n')
        classes = adhocnet.controller
        if not isinstance(classes, list):
            classes = [ classes ]
        for i, cls in enumerate(classes):
            # Allow Controller objects because nobody understands partial()
            if isinstance(cls, Controller):
                adhocnet.addController(cls)
            else:
                adhocnet.addController('c%d' % i, cls)
            info('c%d' %i)

    info('\n*** Adding hosts and stations:\n')
    if isAdhoc: # build a stationary ad hoc network
        for hostName in adhocTopo.hosts():
            pos_x=random.randrange(0,100,10)
            pos_y=random.randrange(0,100,10)
            pos_z=0 #modify this coordinate if you need to 3D space
            posStr='%f,%f,%f' %(pos_x, pos_y, pos_z)
            if 'sta' in str(hostName):
                adhocnet.addStation(hostName, position=posStr, **adhocTopo.nodeInfo(hostName))
            else:
                adhocnet.addHost(hostName, position=posStr, **adhocTopo.nodeInfo(hostName))
            info(hostName + ' ')
    else: # build a mobile ad hoc network
        for hostName in adhocTopo.hosts():
            if 'sta' in str(hostName):
                adhocnet.addStation(hostName, **adhocTopo.nodeInfo(hostName))
            else:
                adhocnet.addHost(hostName, **adhocTopo.nodeInfo(hostName))
            info(hostName + ' ')

    info('\n*** Configuring propagation model...\n')
    # this code line must be put here
    adhocnet.propagationModel(model="logDistance", exp=5)
    #Only can use this propagation model

    info('\n*** Configuring wifi nodes...\n')
    adhocnet.configureWifiNodes()

    info('\n*** Adding link(s):\n')
    for station in adhocnet.stations:
        adhocnet.addLink(station, cls=adhoc, ssid=ssid, mode=mode)
    t2 = datetime.datetime.now()
    delta = t2 - t
    info('Setup time: ' + str(delta.seconds) + '\n')
    print "*** Starting network"
    adhocnet.plotGraph(max_x=100, max_y=100, max_z=0)

    if isManet:
        adhocnet.seed(random.randint(0, 100))
        # this code line must be put here
        adhocnet.startMobility(time=0,  model='RandomWayPoint', max_x=100, max_y=100, max_z=0, min_v=0.5, max_v=0.8)
    adhocnet.build()

    # Load experiment

    if experimentName is not None:
        print("Loading experiment: %s" % experimentName)

        experimentArgs = {
            "isWiFi":True,
            "net": adhocnet,
            "ctime": ctime,
            "nPings": nPings,
            "strategy": Nfd.STRATEGY_BEST_ROUTE,
            "pctTraffic": pctTraffic,
            "nlsrSecurity": nlsrSecurity
        }

        experiment = WifiExperimentManager.create(experimentName, experimentArgs)

        if experiment is not None:
            experiment.start()
        else:
            print("ERROR: Experiment '%s' does not exist" % experimentName)
            return


    """Running CLI....."""
    MiniNdnWifiCLI(adhocnet)

    print "*** Stopping network"
    adhocnet.stop()

    print('Cleaning up...')
    call(["nfd-stop"])
    call(["sudo", "mn", "--clean"])
    sys.exit(1)
