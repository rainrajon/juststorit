import logging
import os
from dotenv import load_dotenv
load_dotenv()

try:
   logfilelocation = os.environ['LOGFILELOCATION']
except KeyError:
   print("Environment Variable Not Found LOGFILELOCATION. Exiting...")
   exit(6)

try:
   os.makedirs(os.path.abspath(os.path.dirname(logfilelocation)))
except FileExistsError:
   # directory already exists
   pass
print("Creating logs at: " + os.path.abspath(logfilelocation))
logging.basicConfig(filename=os.path.abspath(logfilelocation), filemode='a', format = '%(asctime)s:%(levelname)s:%(message)s',level=logging.INFO)