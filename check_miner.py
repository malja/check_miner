import requests
import psutil
import dns.resolver
import smtplib
from threading import Timer
import subprocess
from datetime import datetime

PROCESS_NAME = "EthDcrMiner64.exe"
MINER_ADDRESS = ""
PATH_TO_EXECUTABLE = ""
INTERVAL = 60*60

EMAIL_FROM = ""
EMAIL_TO = ""
EMAIL_SUBJECT = "Miner Watch"
EMAIL_MESSAGE = "Miner prestal tezit a byl restartovan."

class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

def send_rest_request( miner_address ):

    print("Getting response from server...")

    api_address = "https://api.ethermine.org/miner/" + miner_address + "/currentStats"
    
    response = requests.get( api_address )

    json_data = None

    try:
        json_data = response.json()
    except ValueError as e:
        print("Connection error...")

    if ( json_data == None ):
        return False
    elif ( json_data["status"] == "OK" and len( json_data["data"] ) != 0 ):
        return json_data["data"]
    else:
        return False

def find_process_and_kill( process_name ):

    print("Searching for specified process to be killed...")
    for proc in psutil.process_iter():
        if proc.name() == process_name:
            print("Process found ...")
            proc.kill()
            return True

    return False

def start_new_process( path ):
    subprocess.Popen( [ path ] )

def resolve_server_address( server ):
	
	answers = dns.resolver.query(server, 'MX')

	if len(answers) <= 0:
		return False

	return str(answers[0].exchange)

def send_email( address_to, address_from, subject, message ):
	
	server = ""
	
	try:
		server = resolve_server_address( address_to[address_to.find("@")+1:] )
	except dns.resolver.NXDOMAIN:
		return False

	mailer = smtplib.SMTP(host=server)

	message = "From: {}\nTo: {}\nSubject:{}\n{}".format( address_from, address_to, subject, message)

	try:
		mailer.sendmail(address_from, address_to, message)
	except smtplib.SMTPException as e:
		return False

	return True

def run():

    print("Checking response from API server...")
    response = send_rest_request( MINER_ADDRESS )

    if ( response == False ):
        print( datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Worker is not mining...")
        find_process_and_kill( PROCESS_NAME )
        start_new_process( PATH_TO_EXECUTABLE )
        send_email( EMAIL_TO, EMAIL_FROM, EMAIL_SUBJECT, EMAIL_MESSAGE )
    else:
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " Everything is fine...")

###############################################################################
## CODE ITSELF
###############################################################################

print("Starting...")
rt = RepeatedTimer( INTERVAL , run )

try:

    while True:
        user_input = input()
        if ( user_input == "q" or user_input == "exit" or user_input == "quit" ):
            print("Quiting")
            rt.stop()
            break

finally:
    rt.stop()
