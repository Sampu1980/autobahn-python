import sys
import argparse
import os
from binascii import b2a_hex, a2b_hex

import web3
from autobahn import xbr

import eth_keys
from eth_account import Account

from crossbarfx.cfxdb import pack_uint256, unpack_uint256, pack_uint128, unpack_uint128


data1 = {
    'types': {
        'EIP712Domain': [
            {'name': 'name', 'type': 'string'},
            {'name': 'version', 'type': 'string'},
            {'name': 'chainId', 'type': 'uint256'},
            {'name': 'verifyingContract', 'type': 'address'},
        ],
        'Person': [
            {'name': 'name', 'type': 'string'},
            {'name': 'wallet', 'type': 'address'}
        ],
        'Mail': [
            {'name': 'from', 'type': 'Person'},
            {'name': 'to', 'type': 'Person'},
            {'name': 'contents', 'type': 'string'}
        ]
    },
    'primaryType': 'Mail',
    'domain': {
        'name': 'Ether Mail',
        'version': '1',
        'chainId': 1,
        'verifyingContract': '0xCcCCccccCCCCcCCCCCCcCcCccCcCCCcCcccccccC',
    },
    'message': {
        'from': {
            'name': 'Cow',
            'wallet': '0xCD2a3d9F938E13CD947Ec05AbC7FE734Df8DD826',
        },
        'to': {
            'name': 'Bob',
            'wallet': '0xbBbBBBBbbBBBbbbBbbBbbbbBBbBbbbbBbBbbBBbB',
            'foobar': 23,
        },
        'contents': 'Hello, Bob!',
    },
}

data2 = {
    'types': {
        'EIP712Domain': [
            {'name': 'name', 'type': 'string'},
            {'name': 'version', 'type': 'string'},
            {'name': 'chainId', 'type': 'uint256'},
            {'name': 'verifyingContract', 'type': 'address'},
        ],
        'Transaction': [
                # The buyer/seller delegate Ed25519 public key.
                {'name': 'pubkey', 'type': 'uint256'},

                # The UUID of the data encryption key bought/sold in the transaction.
                {'name': 'key_id', 'type': 'uint128'},

                 # Channel transaction sequence number.
                {'name': 'channel_seq', 'type': 'uint32'},

                # Amount paid / earned.
                {'name': 'amount', 'type': 'uint256'},

                # Amount remaining in the payment/paying channel after the transaction.
                {'name': 'balance', 'type': 'uint256'},
        ],
    },
    'primaryType': 'Transaction',
    'domain': {
        'name': 'XBR',
        'version': '1',

        # test chain/network ID
        'chainId': 5777,

        # XBRNetwork contract address
        'verifyingContract': '0x254dffcd3277c0b1660f6d42efbb754edababc2b',
    },
    'message': {
        'pubkey': unpack_uint256(a2b_hex('ebdfef6d225155873355bd4afeb2ed3100b0e0b5fddad12bd3cd498c1e0c1fbd')),
        'key_id': unpack_uint128(a2b_hex('c37ba03c32608744c3c06302bf81d174')),
        'channel_seq': 1,
        'amount': 35000000000000000000,
        'balance': 2000,
    }
}

def main(accounts):
    from py_eth_sig_utils import signing

    data = data2

    # generate a new raw random private key
    if True:
        # maker_key
        # pkey_raw = a2b_hex('6370fd033278c143179d81c5526140625662b8daa446c22ee2d73db3707e620c')

        # consumer_delegate_key
        pkey_raw = a2b_hex('e485d098507f54e7733a205420dfddbe58db035fa577fc294ebd14db90767a52')
    else:
        pkey_raw = os.urandom(32)
    print('Using private key: {}'.format(b2a_hex(pkey_raw).decode()))

    # make a private key object from the raw private key bytes
    pkey = eth_keys.keys.PrivateKey(pkey_raw)

    # make a private account from the private key
    acct = Account.privateKeyToAccount(pkey)

    # get the public key of the account
    addr = pkey.public_key.to_canonical_address()
    print('Account address: {}'.format(b2a_hex(addr).decode()))

    # get the canonical address of the account
    caddr = web3.Web3.toChecksumAddress(addr)
    print('Account canonical address: {}'.format(caddr))

    signature = signing.v_r_s_to_signature(*signing.sign_typed_data(data, pkey_raw))
    assert len(signature) == 32 + 32 + 1
    print('Ok, signed typed data using {}:\nSIGNATURE = 0x{}'.format(caddr, b2a_hex(signature).decode()))

    signer_address = signing.recover_typed_data(data, *signing.signature_to_v_r_s(signature))
    assert signer_address == caddr
    print('Ok, verified signature was signed by {}'.format(signer_address))


if __name__ == '__main__':
    print('using web3.py v{}'.format(web3.__version__))

    parser = argparse.ArgumentParser()

    parser.add_argument('--gateway',
                        dest='gateway',
                        type=str,
                        default=None,
                        help='Ethereum HTTP gateway URL or None for auto-select (default: -, means let web3 auto-select).')

    args = parser.parse_args()

    if args.gateway:
        w3 = web3.Web3(web3.Web3.HTTPProvider(args.gateway))
    else:
        # using automatic provider detection:
        from web3.auto import w3

    # check we are connected, and check network ID
    if not w3.isConnected():
        print('could not connect to Web3/Ethereum at "{}"'.format(args.gateway or 'auto'))
        sys.exit(1)
    else:
        print('connected to network {} at provider "{}"'.format(w3.version.network, args.gateway or 'auto'))

    # set new provider on XBR library
    xbr.setProvider(w3)

    # now enter main ..
    main(w3.eth.accounts)
