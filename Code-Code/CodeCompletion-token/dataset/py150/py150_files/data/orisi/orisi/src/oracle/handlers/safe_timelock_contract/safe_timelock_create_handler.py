from basehandler import BaseHandler

import json
import cjson
import logging
import time
import datetime

from contract_util import get_mark_for_address
from oracle.oracle_db import KeyValue
from random import randrange

TIME_FOR_TRANSACTION = 30 * 60
TIME_FOR_CONFIRMATION = 20 * 60
NUMBER_OF_CONFIRMATIONS = 3

class SafeTimelockCreateHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc
    self.kv = KeyValue(self.oracle.db)

  def mark_unavailable(self, mark, addr):
    mark_data = self.kv.get_by_section_key('mark_available', '{}#{}'.format(mark, addr))
    if not mark_data:
      return False

    available = mark_data['available']
    return not available

  def claim_mark(self, mark, addr, return_address, locktime, oracle_fees, miners_fee_satoshi, req_sigs):
    mark_data = self.kv.get_by_section_key('mark_available', '{}#{}'.format(mark, addr))
    if not mark_data:
      self.kv.store('mark_available', '{}#{}'.format(mark, addr), {'available':True})

    self.kv.update('mark_available', '{}#{}'.format(mark, addr), {
      'available': False,
      'return_address': return_address,
      'ts': int(time.mktime(datetime.datetime.utcnow().timetuple())),
      'locktime': locktime,
      'oracle_fees': oracle_fees,
      'miners_fee_satoshi': miners_fee_satoshi,
      'req_sigs': req_sigs
    })
    logging.info("claimed mark {} for addr {}".format(mark, return_address))

  def extend_observed_addresses(self, address):
    observed_addresses = self.kv.get_by_section_key('safe_timelock', 'addresses')
    if not observed_addresses:
      self.kv.store('safe_timelock', 'addresses', {'addresses':[]})

    observed_addresses = self.kv.get_by_section_key('safe_timelock', 'addresses')
    observed_addresses = observed_addresses['addresses']
    if address in observed_addresses:
      return

    observed_addresses.append(address)
    logging.info("extending observed address {}".format(address))
    self.kv.update('safe_timelock', 'addresses', {'addresses':observed_addresses})

  def save_redeem(self, addr, redeem):
    try:
      self.kv.store('safe_timelock_redeem', addr, {'redeem':redeem})
    except AssertionError:
      # Already saved
      pass

  def handle_request(self, request):
    message = request.message

    return_address = message['return_address']
    mark = get_mark_for_address(return_address)
    address_to_pay_on = self.oracle.btc.add_multisig_address(message['req_sigs'], message['pubkey_list'])
    retval = self.oracle.btc.create_multisig_address(message['req_sigs'], message['pubkey_list'])
    redeemScript = retval['redeemScript']

    self.save_redeem(address_to_pay_on, redeemScript)

    self.extend_observed_addresses(address_to_pay_on)

    locktime = int(message['locktime'])
    oracle_fees = message['oracle_fees']
    miners_fee_satoshi = message['miners_fee_satoshi']
    req_sigs = message['req_sigs']

    if self.mark_unavailable(mark, address_to_pay_on):
      reply_msg = {
        'operation': 'safe_timelock_error',
        'in_reply_to': message['message_id'],
        'comment': 'A marker for this address is currently unavailable. Try again in a couple minutes, or try a different return address. See: https://github.com/orisi/orisi/issues/88',
        'contract_id' : '{}#{}'.format(address_to_pay_on, mark),
        'message_id': "%s-%s" % (address_to_pay_on, str(randrange(1000000000,9000000000)))
      }
      logging.info("mark {} unavailable".format(mark))

      self.oracle.broadcast_with_fastcast(json.dumps(reply_msg))
      return

    # For now oracles are running single-thread so there is no race condition
    self.claim_mark(mark, address_to_pay_on, return_address, locktime, oracle_fees, miners_fee_satoshi, req_sigs)

    reply_msg = { 'operation' : 'safe_timelock_created',
        'contract_id' : '{}#{}'.format(address_to_pay_on, mark),
        'comment': 'mark claimed, use {} as value sufix, you have {} minutes to send cash to address {}'.format(mark, int(TIME_FOR_TRANSACTION / 60), address_to_pay_on),
        'in_reply_to' : message['message_id'],
        'message_id': "%s-%s" % (address_to_pay_on, str(randrange(1000000000,9000000000))),
        'mark': mark,
        'addr': address_to_pay_on,
        'time': TIME_FOR_TRANSACTION}

    self.oracle.broadcast_with_fastcast(json.dumps(reply_msg))

    message['contract_id'] = '{}#{}'.format(address_to_pay_on, mark)

    release_time = int(time.time()) + TIME_FOR_TRANSACTION + NUMBER_OF_CONFIRMATIONS * TIME_FOR_CONFIRMATION

    self.oracle.task_queue.save({
        "operation": 'timelock_mark_release',
        "json_data": json.dumps({'mark': mark, 'address': address_to_pay_on}),
        "done": 0,
        "next_check": release_time
    })

  def handle_task(self, task):
    message = cjson.decode(task['json_data'])

    txid = message['txid']
    n = message['n']
    redeemScript = self.kv.get_by_section_key('safe_timelock_redeem', message['address'])['redeem']
    tx = self.btc.get_raw_transaction(txid)
    transaction = self.btc.decode_raw_transaction(tx)
    vout = None
    for v in transaction['vout']:
      if v['n'] == n:
        vout = v
        break

    if not vout:
      logging.info("missing vout for txid {} n {}".format(txid, n))
      return

    sum_satoshi = int(round(vout['value'] * 100000000))
    message['sum_satoshi'] = sum_satoshi

    scriptPubKey = vout['scriptPubKey']['hex']

    prevtx = {
        'txid': txid,
        'vout': n,
        'redeemScript': redeemScript,
        'scriptPubKey': scriptPubKey
    }
    prevtxs = [prevtx,]
    message['prevtxs'] = prevtxs

    message['outputs'] = message['oracle_fees']

    logging.debug('outputs: %r' % message['outputs'])

    try:
      future_transaction = self.try_prepare_raw_transaction(message)
    except:

      msg_id = "%s-%s" % ("timelock_signature", str(randrange(1000000000,9000000000)))
      contract_id = "{}#{}".format(message['address'], message['mark'])

      info_msg = {
        'operation': 'timelock_signing_fail',
        'in_reply_to': '',
        'message_id': msg_id,
        'contract_id' : contract_id,
      }
      self.oracle.broadcast_with_fastcast(json.dumps(info_msg))

      logging.exception('problem signing tx: %r ; %r' % (contract_id, msg_id))
      return

    if not future_transaction:
      return

    logging.info(future_transaction)

    try:
      pwtxid = self.get_tx_hash(future_transaction)
    except:
      logging.error("Failed to create tx hash")
      return

    assert(future_transaction is not None) # should've been verified gracefully in handle_request

    self.oracle.signer.sign(future_transaction, pwtxid, prevtxs, message['req_sigs'])

    info_msg = {
      'operation': 'safe_timelock_signed',
      'in_reply_to': '',
      'message_id': "%s-%s" % ("timelock_signature", str(randrange(1000000000,9000000000))),
      'contract_id' : "{}#{}".format(message['address'], message['mark']),
    }

    self.oracle.broadcast_with_fastcast(json.dumps(info_msg))
