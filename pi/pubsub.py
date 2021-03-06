#!/usr/bin/python

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import sys
import logging
import time
import getopt
import json
import weather
import traffic
from datetime import datetime

# Custom MQTT message callback

def customCallback(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")


def get_pi_data(peoplecount):
	data = {}
	data['people_count'] = peoplecount
	return data


def get_calendar_data():
	currentdatetime = datetime.now()
	data = {}
	data["id"]= str(currentdatetime)
	data["month"]= currentdatetime.month
	data["weekday"]= currentdatetime.weekday()
	data["hour"]= currentdatetime.hour
	data["minute"]= currentdatetime.minute
	data['day'] = currentdatetime.day
	return data;


def main(host, privateKeyPath,certificatePath, rootCAPath, useWebsocket, peoplecount):
	# Configure logging
	logger = logging.getLogger("AWSIoTPythonSDK.core")
	logger.setLevel(logging.DEBUG)
	streamHandler = logging.StreamHandler(sys.stdout)
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	streamHandler.setFormatter(formatter)
	logger.addHandler(streamHandler)

	# Init AWSIoTMQTTClient
	myAWSIoTMQTTClient = None
	if useWebsocket:
		myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub", useWebsocket=True)
		myAWSIoTMQTTClient.configureEndpoint(host, 443)
		myAWSIoTMQTTClient.configureCredentials(rootCAPath)
	else:
		myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub")
		myAWSIoTMQTTClient.configureEndpoint(host, 8883)
		myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

	# AWSIoTMQTTClient connection configuration
	myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
	myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
	myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
	myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
	myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

	# Connect and subscribe to AWS IoT
	myAWSIoTMQTTClient.connect()
	TOPIC = "sdk/test/Python"
	# myAWSIoTMQTTClient.subscribe(TOPIC, 1, customCallback)
	# time.sleep(2)

	data = {}
	data['time'] = get_calendar_data()
	data['pi'] = get_pi_data(peoplecount)
	data['weather'] = weather.get_weather_data()
	data['traffic'] = traffic.get_traffic_data()

	myAWSIoTMQTTClient.publish(TOPIC, json.dumps(data), 1)

	myAWSIoTMQTTClient.disconnect()

if __name__ == '__main__': 
	# Usage
	usageInfo = """Usage:

	Use certificate based mutual authentication:
	python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>

	Use MQTT over WebSocket:
	python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -w

	Type "python basicPubSub.py -h" for available options.
	"""
	# Help info
	helpInfo = """-e, --endpoint
		Your AWS IoT custom endpoint
	-r, --rootCA
		Root CA file path
	-c, --cert
		Certificate file path
	-k, --key
		Private key file path
	-w, --websocket
		Use MQTT over WebSocket
	-h, --help
		Help information


	"""

	# Read in command-line parameters
	useWebsocket = False
	host = ""
	rootCAPath = ""
	certificatePath = ""
	privateKeyPath = ""
	peoplecount = 0
	try:
		opts, args = getopt.getopt(sys.argv[1:], "hwe:k:c:r:p:", ["help", "endpoint=", "key=","cert=","rootCA=", "websocket", "pi="])
		if len(opts) == 0:
			raise getopt.GetoptError("No input parameters!")
		for opt, arg in opts:
			if opt in ("-h", "--help"):
				print(helpInfo)
				exit(0)
			if opt in ("-e", "--endpoint"):
				host = arg
			if opt in ("-r", "--rootCA"):
				rootCAPath = arg
			if opt in ("-c", "--cert"):
				certificatePath = arg
			if opt in ("-k", "--key"):
				privateKeyPath = arg
			if opt in ("-w", "--websocket"):
				useWebsocket = True
			if opt in ("-pi"):
				peoplecount = int(arg)
	except getopt.GetoptError:
		print(usageInfo)
		exit(1)

	# Missing configuration notification
	missingConfiguration = False
	if not host:
		print("Missing '-e' or '--endpoint'")
		missingConfiguration = True
	if not rootCAPath:
		print("Missing '-r' or '--rootCA'")
		missingConfiguration = True
	if not useWebsocket:
		if not certificatePath:
			print("Missing '-c' or '--cert'")
			missingConfiguration = True
		if not privateKeyPath:
			print("Missing '-k' or '--key'")
			missingConfiguration = True
	if missingConfiguration:
		exit(2)

	main(host, privateKeyPath,certificatePath, rootCAPath, useWebsocket, peoplecount)

