from pyZcash.rpc.ZDaemon import *

# How to change network settings here?
zd = ZDaemon()

def get_tx(txid):
    print "In get_tx of displaytx"
    # verbose=1 returns json obj
    tx = zd.getrawtransaction(txid, 1)
    print "Tx returned by get_tx", tx
    return tx
