# *****J1772 EV charge controller config parser*****
# Copyright (C) 2021 Simon Richard Matthews
# Project loaction https://github.com/simat/Variable-J1772-Charger
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import json
from _thread import start_new_thread as start
from time import sleep
from logger import logexception
config = {}
def getconfig():
	global config
	try:
		with open('config.json') as fp:
			config = json.load(fp)
	except (Exception,OSError,ValueError) as err:
		logexception(err)


def loopgetconfig():
	while True:
		getconfig()
		sleep(180)

start(loopgetconfig,())
