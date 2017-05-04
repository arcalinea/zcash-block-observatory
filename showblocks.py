#!/usr/bin/python3
# -*- coding: utf-8 -*-

from functools import wraps
from flask import Flask, g, abort, jsonify, render_template, request, Response, session, redirect
import config, json, os, re, sqlite3, sys, time
from werkzeug.contrib.cache import SimpleCache
from displaytx import get_tx

db_file = 'blocks.sqlite'
app = Flask(__name__)
app.config.from_object(config.FlaskConfig)

txtest = 'ed3a82da9ec2c12ff7e05debf6fe849f6c91e442a844ddbc52048627a27a51e1'

def find_block_by_tx(txid):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT hash FROM tx WHERE tx=:txid', {"txid": txid})
    block_hash = c.fetchone()
    return str(block_hash['hash'])


def get_single_block(block_hash):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM blocks WHERE hash=:hash', {"hash": block_hash})
    block = dict(c.fetchone())
    txs = get_txs(block['hash'])
    block['tx'] = txs
    return block

def get_blocks(query={}):
    print "in get blocks"
    if query.get('height'):
        height = query['height']
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    # if height == 'top':
    #     c.execute('SELECT hash, height, size, time FROM blocks ORDER by height DESC LIMIT 20')
    # else:
    #     bottom = height - 20
    #     c.execute('SELECT hash, height, size, time FROM blocks WHERE height<=:top AND height>:bottom ORDER by height DESC', {"top":height, "bottom":bottom})
    c.execute('SELECT hash, height, size, time FROM blocks ORDER by height DESC LIMIT 200')
    # return retrieved blocks as a dict, with transactions
    blocks = [dict(block) for block in c.fetchall()]
    for block in blocks:
        txs = get_txs(block['hash'])
        block['txs'] = txs
    return blocks

def get_txs(block_hash):
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT tx FROM tx WHERE hash=:hash', {"hash": block_hash})
    txs = [dict(tx) for tx in c.fetchall()]
    return txs

def validate_input(search_string):
    if len(search_string) != 64:
        return None
    m = re.match(r"[A-Fa-f0-9]{64}", search_string)
    if m and m.span()[1] == len(search_string):
        return search_string
    else:
        return None

@app.template_filter('timestamp')
def _jinja2_filter_timestamp(unix_epoch):
    return time.ctime(unix_epoch)

# @app.route('/', defaults={'height': 'top'})
# @app.route('/height/<int:height>')
@app.route('/')
def index(height='top'):
    query = {"height":height}
    try:
        blocks = get_blocks(query)
        # blocks = cache.get('blocks')
    except:
        pass
    return render_template('blocks.html', blocks = blocks)

@app.route('/search', methods = ['POST'])
def search():
    print 'search: ', request.values.get('search')
    search_string = validate_input(request.values.get('search').strip().lower())
    if search_string is None:
        print "Search returned nothing"
        return ('', 204)
    if search_string[:3] == '000':
        return redirect('/block?hash=' + search_string)
    else:
        return redirect('/tx?id=' + search_string)


@app.route('/block', methods = ['GET'])
def show_block():
    block_hash = request.values.get('hash')
    block = get_single_block(block_hash)
    return render_template('block.html', block = block)

@app.route('/tx', methods = ['GET'])
def show_tx():
    txid = request.values.get('id')
    print 'txid: ', txid
    # search_string = validate_input(request.values.get('id').strip().lower())
    if txid is None:
        print 'tx search none'
        return ('', 204)
    try:
        tx = find_tx(txid)
        return render_template('tx.html', tx = tx)
    except:
        print 'except'
        return ('', 204)

def find_tx(txid):
    print "In find_tx:", request.args.get
    print "In find_tx:", request.values
    tx = get_tx(txtest)
    print "TX in FIND_TX", dict(tx)
    return tx
    # Will have to query the rpc interface for tx info


@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    cache = SimpleCache()
    cache.set('blocks', get_blocks(), timeout=3600)
    app.run(host='0.0.0.0', port=int('8201'), debug=True)
