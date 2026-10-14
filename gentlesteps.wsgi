#! /usr/bin/python3 

import logging
import sys
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/var/www/gentlesteps')
from  gentlesteps import app as application
application.secret_key = '0x413455aabdff9cd58pfc'
