#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Name: Best Before
# Author: John Peel <john@dgby.org>
# Description: http://www.spotify.com/uk/jobs/tech/best-before/

from calendar import isleap, monthrange

def getDate(input):
	try:
		date = sorted(map(int, input.split('/')))
	except ValueError:
		return '%s is illegal' % input	
	
	if (len(date) != 3):
		return '%s is illegal' % input
	
	year = month = day = 0
	lt12 = lt31 = 0
	
	for item in date:
		if (item < 0) or (item > 2999):
			return '%s is illegal' % input
		if (item <= 12):
			lt12 += 1
		if (item <= 31):
			lt31 += 1
	
	if (lt31 < 2):
		return '%s is illegal' % input
		
	if (lt12 == 3) or ((lt12 == 2) and (lt31 == 3)):
		year, month, day = date
	else:
		if (lt31 == 2):
			month, day, year = date
		if (lt31 == 3):
			month, year, day = date
			
	if (month == 0):
		return '%s is illegal' % input
	
	day_max = monthrange(year + 2000 if year < 1000 else year, month)[1]
	if (day > day_max):
		if (year > day_max) or (year == 0):
			return '%s is illegal' % input
		year, day = day, year
			
	if (year < 1000):
		year += 2000	
	
	return '%04d-%02d-%02d' % (year, month, day)
	
if (__name__ == '__main__'):
	print getDate(raw_input())
