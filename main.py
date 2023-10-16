import socket
import os
import sys
import struct
import time
import select
import binascii

ICMP_ECHO_REQUEST = 8

def checksum(str):

  csum = 0
  countTo = (len(str) / 2) * 2

  count = 0
  while count < countTo:
    thisVal = (str[count+1]) * 256 + (str[count])
    csum = csum + thisVal
    csum = csum & 0xffffffff #
    count = count + 2

  if countTo < len(str):
    csum = csum + ord(str[len(str) - 1])
    csum = csum & 0xffffffff #

  csum = (csum >> 16) + (csum & 0xffff)
  csum = csum + (csum >> 16)
  
  answer = ~csum
  answer = answer & 0xffff
  answer = answer >> 8 | (answer << 8 & 0xff00)

  return answer


def receiveOnePing(mySocket, ID, timeout, destAddr):

  timeLeft = timeout

  while 1:
    startedSelect = time.time()
    whatReady = select.select([mySocket], [], [], timeLeft)
    howLongInSelect = (time.time() - startedSelect)
    if whatReady[0] == []:
      return "Request timed out."

    timeReceived = time.time()
    recPacket, addr = mySocket.recvfrom(1024)

    #Fill in start
    #Fetch the ICMP header from the IP packet
    icmph = recPacket[20:28]
    type, code, checksum, pID, sq = struct.unpack("bbHHh", icmph)
    if pID == ID:
      bytesinDbl = struct.calcsize("d")
      timeSent = struct.unpack("d", recPacket[28:28 + bytesinDbl])[0]
      round_time=timeReceived - timeSent
      print ("Reply from:",destAddr, "Time:",round_time*1000)
      return ""
    # Fill in end
    timeLeft = timeLeft - howLongInSelect
    if timeLeft <= 0:
      return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
  # Header is type (8), code (8), checksum (16), id (16), sequence (16)
  myChecksum = 0

  header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)

  data = struct.pack("d", time.time())

  myChecksum = checksum(header + data)

  if sys.platform == 'darwin':
    myChecksum = socket.htons(myChecksum) & 0xffff   #Convert 16-bit integers from host to network byte order.
  else:
    myChecksum = socket.htons(myChecksum)

  header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
  packet = header + data

  mySocket.sendto(packet, (destAddr, 1))
  # Both LISTS and TUPLES consist of a number of objects
  # which can be referenced by their position number within the object.


def doOnePing(destAddr, timeout):
  icmp = socket.getprotobyname("icmp")
  #SOCK_RAW is a powerful socket type. For more details:   http://sock-raw.org/papers/sock_raw

  # Fill in start
  # Create socket here.
  mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
  # Fill in end
  myID = os.getpid() & 0xFFFF 
  sendOnePing(mySocket, destAddr, myID)
  delay = receiveOnePing(mySocket, myID, timeout, destAddr)
  mySocket.close()
  return delay


def ping(host, timeout=1):

  dest = socket.gethostbyname(host)
  print ("Pinging " + dest + " using Python:")
  print ("")

  while 1:
    delay = doOnePing(dest, timeout) 
    print (delay)
    time.sleep(1)
  return delay

ping("www.google.com")
