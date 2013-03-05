'''
Created on Mar 4, 2013

@author: jketterl
'''

import libxml2, datetime, time, re
import gps.fake as gpsfake

class GPXTestload(gpsfake.TestLoad):
    def __init__(self, gpxFile):
        self.name = gpxFile
        self.sentences = []
        self.serial = None
        
        doc = libxml2.parseFile(gpxFile);
        
        ctxt = doc.xpathNewContext();
        ctxt.xpathRegisterNs("gpx", "http://www.topografix.com/GPX/1/1");
        res = ctxt.xpathEval("//gpx:gpx/gpx:trk/gpx:trkseg/gpx:trkpt")
        
        
        for node in res:
            lat = float(node.prop("lat"))
            lon = float(node.prop("lon"))
            lat = '%02d%05.2f' % self.convertCoordinate(lat)
            lon = '%03d%05.2f' % self.convertCoordinate(lon)
            
            ctxt.setContextNode(node)
            time = ctxt.xpathEval("gpx:time")[0].getContent();
            time = datetime.datetime.strptime(time, '%Y-%m-%dT%H:%M:%SZ');
            
            self.outputMessage("GPRMC,%s.000,A,%s,N,%s,E,0,0,%s,0,E" % (
                datetime.datetime.strftime(time, '%H%M%S'),
                lat, lon,
                datetime.datetime.strftime(time, '%d%m%y'),
            ))
            
            self.outputMessage("GPGGA,%s.000,%s,N,%s,E,1,03,0.0,0.0,M,0.0,M,," % (
                datetime.datetime.strftime(time, '%H%M%S'),
                lat, lon
            ))
    
    def convertCoordinate(self, c):
        return (int(c), (c - int(c)) * 60)

    def outputMessage(self, msg):
            checksum = 0
            for char in msg:
                checksum ^= ord(char)
                
            self.sentences.append('$%s*%x\n' % (msg, checksum))

if __name__ == '__main__':
    gpx = "2011-07-25 1955__20110725_1955.gpx"
    testload = GPXTestload(gpx)

    timeRegex = re.compile('^\$(GPRMC|GPGGA),([0-9]{6})')
    
    def progress(line):
        pass

    lastTime = None

    def predicate(x, y):
	nmea = testload.sentences[x]
        now = int(timeRegex.match(nmea).group(2))
	global lastTime
	if lastTime is not None:
        	time.sleep(min(5, now - lastTime))
	lastTime = now
        return True
    
    gps = gpsfake.FakePTY(testload, progress=progress)
    gps.go_predicate = predicate
    gps.exhausted = 0
    session = gpsfake.TestSession(options="")
    session.progress = progress
    
    session.spawn()
    
    session.fakegpslist[gps.byname] = gps
    session.append(gps)
    session.daemon.add_device(gps.byname)
    
    session.run()
