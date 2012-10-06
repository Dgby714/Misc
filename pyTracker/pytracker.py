#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request

from bencode import bencode
from urlparse import parse_qs
from struct import pack
from socket import AF_INET, AF_INET6, inet_pton
import pprint
import sys
import random

app = Flask(__name__)
app.config['PUBLIC_TRACKER'] = True
app.config['TRACKER_ID'] = 'Hmm, wtf is this?'
app.config['MAX_PEERS'] = 55
app.debug = True

torrents = {}

def parseip(ip, default_port):
	new_ip = ip.rsplit(':', 1)
	if (':' in new_ip[0]) and (not new_ip[0].startswith('[')):
		new_ip = [ip]

	if (len(new_ip) > 1):
		ip, port = new_ip
	else:
		ip, port = new_ip[0], default_port

	return ':' in ip, ip.strip('[]'), port

def gen_peer_list(peer_list, numwant, compact):
	keys = peer_list.keys()
	random.shuffle(keys)
	ret_ipv4, ret_ipv6  = [], None
	if (compact):
		ret_ipv4, ret_ipv6 = '', ''

	for peer in keys[0:numwant]:
		for ip in peer_list[peer]['ip']:
			is_ipv6, ip, port = parseip(ip, peer_list[peer]['port'])

			if (compact):
				if (is_ipv6):
					ret_ipv6 += (inet_pton(AF_INET6, ip) + pack('>H', port))
				else:
					ret_ipv4 += (inet_pton(AF_INET, ip) + pack('>H', port))
			else:
				new_peer = {'ip': ip, 'port': port}
				if not (peer_list[peer]['no_peer_id']):
					new_peer['peer_id'] = peer
				ret_ipv4.append(new_peer)
	
	return ret_ipv4,ret_ipv6

@app.route('/info')
def info():
	return "<!doctype html>\n<pre>\n%s\n</pre>" % pprint.pformat(torrents)

@app.route('/announce')
def announce():
	if ('info_hash' not in request.args): return bencode({'failure reason': 'Missing info_hash.', 'failure code': 101})
	if ('peer_id' not in request.args): return bencode({'failure reason': 'Missing peer_id.', 'failure code': 102})
	if ('port' not in request.args): return bencode({'failure reason': 'Missing port.', 'failure code': 103})
	if ('left' not in request.args): return bencode({'failure reason': 'Missing left.', 'failure code': 900})

	info_hash, peer_id = [(value[0]) for key, value in parse_qs(request.query_string).iteritems() if (key in {'peer_id', 'info_hash'})]
	
	if (len(info_hash) != 20): return bencode({'failure reason': 'Invalid info_hash: < 20 bytes long.', 'failure code': 150})
	if (len(peer_id) != 20): return bencode({'failure reason': 'Invalid peer_id: < 20 bytes long.', 'failure code': 151})

	left = int(request.args.get('left'))
	port = int(request.args.get('port'))

	event = request.args.get('event', '')
	compact = bool(request.args.get('compact', '1') == '1')
	ip = [request.args.get('ip', request.remote_addr)]
	if ('ipv4' in request.args): ip.append(request.args.get('ipv4'))
	if ('ipv6' in request.args): ip.append(request.args.get('ipv6'))

	tracker_id = request.args.get('trackerid', app.config['TRACKER_ID'])
	if (tracker_id != app.config['TRACKER_ID']): return bencode({'failure reason': 'Invalid tracker id.', 'failure code': 900})

	numwant = int(request.args.get('numwant', 30))
	if (numwant > app.config['MAX_PEERS']): return bencode({'failure reason': 'Invalid numwant. Client requested more peers than allowed by tracker.', 'failure code': 152})

	no_peer_id = bool(request.args.get('no_peer_id', '0') == '1')

	if (info_hash not in torrents):
		if (app.config['PUBLIC_TRACKER']):
			torrents[info_hash] = {'complete': 0, 'incomplete': 0, 'peer_list': {}}
		else:
			return bencode({'failure reason': 'torrent not found in the database.', 'failure code': 200})

	if (peer_id not in torrents[info_hash]):
		torrents[info_hash]['peer_list'][peer_id] = {'ip': ip, 'port': port, 'no_peer_id': no_peer_id}
		torrents[info_hash]['complete'] += (left == 0)
		torrents[info_hash]['incomplete'] += (left > 0)

	if (event == 'completed'):
		torrents[info_hash]['complete'] += 1
		torrents[info_hash]['incomplete'] -= 1
	if (event == 'stopped'):
		if (peer_id in torrents[info_hash]['peer_list']):
			del torrents[info_hash]['peer_list'][peer_id]
			torrents[info_hash]['complete'] -= (left == 0)
			torrents[info_hash]['incomplete'] -= (left > 0)
	
	ret = {
		'tracker id': tracker_id.encode('UTF-8'),
		'interval': 30,
		'min interval': 15,
		'complete': torrents[info_hash]['complete'],
		'incomplete': torrents[info_hash]['incomplete']
	}

	ret['peers'],ret['peers6'] = gen_peer_list(torrents[info_hash]['peer_list'], numwant, compact)
	if not (compact):
		del ret['peers6']
	
	return bencode(ret)

if (__name__ == '__main__'):
	app.run(host='0.0.0.0')

