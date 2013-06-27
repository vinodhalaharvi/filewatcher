#===============================================================================
# Script provided by Vinod Halhaarvi, email: vinod.halaharvi@gmail.com, vinod.halaharvi@rtpnet.net
# RTP Network Services, Inc. / 904-236-6993 ( http://www.rtpnet.net )
# DESCRIPTION:
#===============================================================================
import sys, subprocess, shlex, os, time, re, threading, Queue
import smtplib
from email.mime.text import MIMEText
import os
from os.path import getmtime, getctime
from datetime import datetime, timedelta
import glob
import socket
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class UpdateEnviron(object):
	"""ue = UpdateEnviron()"""
	def __init__(self, ):
		super(UpdateEnviron, self).__init__()

	def updateEnv(self):
		"""docstring for printEnv"""
		envstr = """OI_SERVER=TEST-OI
SM_HOME=/opt/local/software/ionix/InCharge/SAM/smarts
HOSTNAME=lnx40012
BROKER=lnx40012
EMWTO_PATH=/opt/local/software/ionix/InCharge8/SAM/smarts/local/script
SM_PERL_HOME=/opt/local/software/ionix/InCharge8/SAM/smarts/bin/"""
		strio = StringIO(envstr)
		for line in strio.readlines():
			try:
				key, value = line.split("=")
				value = value.strip()
				os.environ.update({key:value})
			except:
				pass


class Escalation(object):
	"""docstring for Escalation"""
	def __init__(self, escalationType):
		super(Escalation, self).__init__()
		self.escalationType = escalationType
	def getEscalationType(self):
		"""docstring for getEscalationType"""
		return self.escalationType

class SnmpTrap(Escalation):
	"""docstring for SnmpTrap"""
	def __init__(self,):
		super(SnmpTrap, self).__init__("SnmpTrap")
		self.cmdline = ""

	def sendTrap(self, node, eventDisplayName, eventType, severity, eventName, eventText):
		"""docstring for sendTrap
		assert os.environ["EMWTO_PATH"]
		assert os.environ["SM_HOME"]
		assert os.environ["OI_SERVER"]
		assert os.environ["SM_PERL_HOME"]
		sys.path.append(os.environ["EMWTO_PATH"])
		sys.path.append(os.environ["SM_PERL_HOME"])
		"""
		self.cmdline = "/opt/local/software/ionix/InCharge8/SAM/smarts/bin/sm_perl /opt/local/software/ionix/InCharge8/SAM/smarts/local/script/emwto.pl %s %s %s %s %s %s" % (node, eventDisplayName, eventType, severity, eventName.strip(), eventText.strip())
		print self.cmdline
		self.proc = subprocess.Popen(shlex.split(self.cmdline),
					 stdout = subprocess.PIPE,
					 stderr = subprocess.PIPE,
					 env = os.environ
				)
		stdout, stderr = self.proc.communicate()
		if stderr:
			print stderr
		self.proc.stderr.close()
		self.proc.stdout.close()
		status = self.proc.returncode


class Log(Escalation):
	"""docstring for SysLog"""
	def __init__(self, fileName, ):
		super(SysLog, self).__init__("Log")
		self.fileName = fileName
		try:
			self.log = open(self.fileName, 'a')
		except:
			raise
	def log(self, message):
		"""docstring for log"""
		self.log.write(message)
		
	
class Email(Escalation):
	"""
		docstring for Email
		to, subject, message
		from is set to vinod.halaharvi@rtpnet.net
	"""
	def __init__(self, to, subject, message="" ):
		super(Email, self).__init__("Email")
		assert to
		assert subject
		self.to = to 
		self.subject = subject
		self.message = message
		self.frm = 'vinod.halaharvi@rtpnet.net'
		self.msg = {}
		# Import smtplib for the actual sending function
		# Import the email modules we'll need
		# Open a plain text file for reading.  For this example, assume that
		# the text file contains only ASCII characters.
		# Create a text/plain message
		self.msg = MIMEText(self.message)
		self.msg['Subject'] = self.subject
		self.msg['From'] = self.frm
		self.msg['To'] = self.to

	
	def sendemail(self):
		s = smtplib.SMTP('localhost')
		s.sendmail(self.frm, self.to, self.msg.as_string())
		s.quit()


class FileHandler(object):
	"""docstring for FileHandler"""
	def __init__(self, alertPattern , clearPattern, escalationType ):
		self.alertPattern = alertPattern
		self.clearPattern = clearPattern
		self.escalationType = escalationType
		super(FileHandler, self).__init__()
	def handle_line(self, configFileName, fileName, line):
		"""docstring for handle_line""" 
		#print "==> %s <==" % fileName
		#print line,
		if self.isalertmatch(line):
			eventType = 'ALERT'
			severity = 'RED'
		elif self.isclearmatch(line):
			eventType = 'CLEAR'
			severity = 'WHITE'
		else:
			return

		if self.escalationType == "Email":
			e = Email("halavin@localhost", "Alert Email", configFileName + "::" + fileName + "::" + line)
			e.sendemail()
			e = None
		elif self.escalationType == "SnmpTrap":
			st = SnmpTrap()
			st.sendTrap(socket.gethostname(), 
					socket.gethostname(),
					eventType,
					severity,
					configFileName+"::"+fileName,
					configFileName+"::"+fileName+"::"+line 
				)
		elif self.escalationType == "Log":
			pass
		else:
			# else just print it on the screen
			print "%s::%s::%s:%s" % ("ALERT", configFileName, fileName, line),


	def isalertmatch(self, line):
	 	"""docstring for  isalertmatch"""
		return re.match(self.alertPattern, line)
	def isclearmatch(self, line):
		"""docstring for isclearmatch"""
		return re.match(self.clearPattern, line)
	def handle_alert(self, fileName, line):
		pass
	def handle_clear(self, fileName, line):
		pass
		

class ConfigFile(object):
	"""docstring for ConfigFile"""
	def __init__(self, configFileName):
		super(ConfigFile, self).__init__()
		self.configFileName = configFileName
		self.fileObjects = []
		self.parseConfigFile()
	
		
	def parseConfigFile(self):
		"""docstring for parseConfigFile"""
		fileObj = {}
		for line in open(self.configFileName, 'r'):
		  if line.strip() != "---" :
		    try:
		      (key, value) = line.split(',,,')
		      (key, value) = (key.strip(), value.strip())
		      fileObj[key] = value
		    except:
		      continue
		  else:
		    self.fileObjects.append(fileObj)
		    fileObj = {}

	def getFileObjects(self):
		"""docstring for getFileObjects"""
		return self.fileObjects

	def printFileObjects(self):
		"""docstring for printFileObjects"""
		for fo in self.fileObjects:
			print fo["fileName"]




class FileWatcher(threading.Thread):
	"""docstring for FileWatcher"""
	def __init__(self, configFileName, fileName, handler,  interval=10):
		super(FileWatcher, self).__init__()
		self.configFileName = configFileName
		self.fileName = fileName
		self.interval = interval
		self.changed = False
		self.fd = open(self.fileName)
		self.handler = handler
		print "Watching %s .. " % self.fileName

	def ischanged(self):
		"""docstring for ischanged"""
		pasttime = datetime.today() - timedelta(seconds=self.interval)
		if pasttime <  datetime.fromtimestamp(getmtime(self.fileName)):
			self.changed = True
			return  True
		self.changed = False
		return False

	def run(self):
		self.fd.seek(os.SEEK_SET,os.SEEK_END)      # Go to the end of the file
		while True:
			line = self.fd.readline()
			if not line:
				time.sleep(10)    # Sleep briefly
				continue
			self.handler.handle_line(self.configFileName, self.fileName, line)
"""
# Sample Usage:
	python minifilewatcher.py filewatcher1.conf filewatcher2.conf
# Sample filewatcher.conf contents are
fileName,,,data/commandlist.1
alertString,,,alertString1
clearString,,,clearString1
---
fileName,,,data/commandlist.2
alertString,,,alertString2
clearString,,,clearString2
---
fileName,,,data/fileregex*.???
alertString,,,anyAlertString
clearString,,,anyClearString
---
"""

if __name__ == '__main__':
	queueLock = threading.Lock()
	threadList = []

	#set up environment for SM_EMS
	#ue = UpdateEnviron()
	#ue.updateEnv()

	# if we have more than one confi file
	for configFileName in sys.argv[1:]:
		cf = ConfigFile(configFileName)

		print "Watching for following files .. " 
		print configFileName
		cf.printFileObjects()
		print 

		queueLock.acquire()
		for fileObj in cf.getFileObjects():
			alertString = fileObj["alertString"]
			clearString = fileObj["clearString"]
			# If there is file regex
			for fileName in glob.glob(fileObj["fileName"]):
				threadList.append(FileWatcher(configFileName, 
							fileName, 
							FileHandler(alertString, clearString, 'SnmpTrap')
							)
						)
		queueLock.release()

	for t in threadList:
		t.start()

	for t in threadList:
		t.join()

