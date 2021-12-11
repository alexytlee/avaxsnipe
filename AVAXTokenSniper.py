from web3 import Web3
import datetime
import threading
import json
import asyncio
import requests
import time
import os
import sys

print("AVAX Chain Sniper")

currentTimeStamp = ""


def get_timestamp():
    while True:
        timeStampData = datetime.datetime.now()
        global currentTimeStamp
        currentTimeStamp = "[" + timeStampData.strftime("%H:%M:%S.%f")[:-3] + "]"


# -------------------------------- INITIALISE ------------------------------------------

timeStampThread = threading.Thread(target=get_timestamp)
timeStampThread.start()

numTokensDetected = 0
numTokensBought = 0
walletBalance = 0

avax = "https://api.avax.network/ext/bc/C/rpc"
web3 = Web3(Web3.HTTPProvider(avax))

if web3.isConnected():
    print(currentTimeStamp + " [Info] Web3 successfully connected")

# load json data

configFilePath = os.path.abspath('') + '/config.json'

with open(configFilePath, 'r') as configdata:
    data = configdata.read()

# parse file
obj = json.loads(data)

traderJoeRouterAddress = obj['traderJoeRouterAddress']  # load config data from JSON file into program
traderJoeFactoryAddress = '0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73'  # read from JSON later
walletAddress = obj['walletAddress']
private_key = obj['walletPrivateKey']  # private key is kept safe and only used in the program

snipeAVAXAmount = float(obj['amountToSpendPerSnipe'])
transactionRevertTime = int(obj[
                                'transactionRevertTimeSeconds'])  # number of seconds after transaction processes to cancel it if it hasn't completed
gasAmount = int(obj['gasAmount'])
gasPrice = int(obj['gasPrice'])
snowtraceScanAPIKey = obj['snowtraceScanAPIKey']
observeOnly = obj['observeOnly']

checkSourceCode = obj['checkSourceCode']
checkMintFunction = obj['checkMintFunction']
checkHoneypot = obj['checkHoneypot']
checkTraderJoeRouter = obj['checkTraderJoeRouter']

enableMiniAudit = False


def update_title():
    walletBalance = web3.fromWei(web3.eth.get_balance(walletAddress),
                                 'ether')  # There are references to ether in the code but it's set to AVAX, its just
    # how Web3 was originally designed
    walletBalance = round(walletBalance, -(int("{:e}".format(walletBalance).split('e')[
                                                   1]) - 4))  # the number '4' is the wallet balance significant
    print("Current walletBalance", walletBalance)


update_title()

print(currentTimeStamp + " [Info] Using Wallet Address: " + walletAddress)
print(currentTimeStamp + " [Info] Using Snipe Amount: " + str(snipeAVAXAmount), "AVAX")
nonce = web3.eth.getTransactionCount(walletAddress)

print("The current nonce is", nonce)

# tx = {
# 'chainId': 43114,
# 'nonce': nonce,
# 'to': '0x60aE616a2155Ee3d9A68541Ba4544862310933d4', #traderJoe router address
# 'value': web3.toWei(0.005, 'ether'),
# 'gas': gasAmount,
# 'gasPrice': web3.toWei(30,'gwei'),
# }
# signed_tx = web3.eth.account.sign_transaction(tx, private_key)
# tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
# print(web3.toHex(tx_hash))
traderJoeABI = '[ { "inputs": [ { "internalType": "address", "name": "_factory", "type": "address" }, { "internalType": "address", "name": "_WAVAX", "type": "address" } ], "stateMutability": "nonpayable", "type": "constructor" }, { "inputs": [], "name": "WAVAX", "outputs": [ { "internalType": "address", "name": "", "type": "address" } ], "stateMutability": "view", "type": "function" }, { "inputs": [ { "internalType": "address", "name": "tokenA", "type": "address" }, { "internalType": "address", "name": "tokenB", "type": "address" }, { "internalType": "uint256", "name": "amountADesired", "type": "uint256" }, { "internalType": "uint256", "name": "amountBDesired", "type": "uint256" }, { "internalType": "uint256", "name": "amountAMin", "type": "uint256" }, { "internalType": "uint256", "name": "amountBMin", "type": "uint256" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "addLiquidity", "outputs": [ { "internalType": "uint256", "name": "amountA", "type": "uint256" }, { "internalType": "uint256", "name": "amountB", "type": "uint256" }, { "internalType": "uint256", "name": "liquidity", "type": "uint256" } ], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "address", "name": "token", "type": "address" }, { "internalType": "uint256", "name": "amountTokenDesired", "type": "uint256" }, { "internalType": "uint256", "name": "amountTokenMin", "type": "uint256" }, { "internalType": "uint256", "name": "amountAVAXMin", "type": "uint256" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "addLiquidityAVAX", "outputs": [ { "internalType": "uint256", "name": "amountToken", "type": "uint256" }, { "internalType": "uint256", "name": "amountAVAX", "type": "uint256" }, { "internalType": "uint256", "name": "liquidity", "type": "uint256" } ], "stateMutability": "payable", "type": "function" }, { "inputs": [], "name": "factory", "outputs": [ { "internalType": "address", "name": "", "type": "address" } ], "stateMutability": "view", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountOut", "type": "uint256" }, { "internalType": "uint256", "name": "reserveIn", "type": "uint256" }, { "internalType": "uint256", "name": "reserveOut", "type": "uint256" } ], "name": "getAmountIn", "outputs": [ { "internalType": "uint256", "name": "amountIn", "type": "uint256" } ], "stateMutability": "pure", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountIn", "type": "uint256" }, { "internalType": "uint256", "name": "reserveIn", "type": "uint256" }, { "internalType": "uint256", "name": "reserveOut", "type": "uint256" } ], "name": "getAmountOut", "outputs": [ { "internalType": "uint256", "name": "amountOut", "type": "uint256" } ], "stateMutability": "pure", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountOut", "type": "uint256" }, { "internalType": "address[]", "name": "path", "type": "address[]" } ], "name": "getAmountsIn", "outputs": [ { "internalType": "uint256[]", "name": "amounts", "type": "uint256[]" } ], "stateMutability": "view", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountIn", "type": "uint256" }, { "internalType": "address[]", "name": "path", "type": "address[]" } ], "name": "getAmountsOut", "outputs": [ { "internalType": "uint256[]", "name": "amounts", "type": "uint256[]" } ], "stateMutability": "view", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountA", "type": "uint256" }, { "internalType": "uint256", "name": "reserveA", "type": "uint256" }, { "internalType": "uint256", "name": "reserveB", "type": "uint256" } ], "name": "quote", "outputs": [ { "internalType": "uint256", "name": "amountB", "type": "uint256" } ], "stateMutability": "pure", "type": "function" }, { "inputs": [ { "internalType": "address", "name": "tokenA", "type": "address" }, { "internalType": "address", "name": "tokenB", "type": "address" }, { "internalType": "uint256", "name": "liquidity", "type": "uint256" }, { "internalType": "uint256", "name": "amountAMin", "type": "uint256" }, { "internalType": "uint256", "name": "amountBMin", "type": "uint256" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "removeLiquidity", "outputs": [ { "internalType": "uint256", "name": "amountA", "type": "uint256" }, { "internalType": "uint256", "name": "amountB", "type": "uint256" } ], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "address", "name": "token", "type": "address" }, { "internalType": "uint256", "name": "liquidity", "type": "uint256" }, { "internalType": "uint256", "name": "amountTokenMin", "type": "uint256" }, { "internalType": "uint256", "name": "amountAVAXMin", "type": "uint256" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "removeLiquidityAVAX", "outputs": [ { "internalType": "uint256", "name": "amountToken", "type": "uint256" }, { "internalType": "uint256", "name": "amountAVAX", "type": "uint256" } ], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "address", "name": "token", "type": "address" }, { "internalType": "uint256", "name": "liquidity", "type": "uint256" }, { "internalType": "uint256", "name": "amountTokenMin", "type": "uint256" }, { "internalType": "uint256", "name": "amountAVAXMin", "type": "uint256" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "removeLiquidityAVAXSupportingFeeOnTransferTokens", "outputs": [ { "internalType": "uint256", "name": "amountAVAX", "type": "uint256" } ], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "address", "name": "token", "type": "address" }, { "internalType": "uint256", "name": "liquidity", "type": "uint256" }, { "internalType": "uint256", "name": "amountTokenMin", "type": "uint256" }, { "internalType": "uint256", "name": "amountAVAXMin", "type": "uint256" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" }, { "internalType": "bool", "name": "approveMax", "type": "bool" }, { "internalType": "uint8", "name": "v", "type": "uint8" }, { "internalType": "bytes32", "name": "r", "type": "bytes32" }, { "internalType": "bytes32", "name": "s", "type": "bytes32" } ], "name": "removeLiquidityAVAXWithPermit", "outputs": [ { "internalType": "uint256", "name": "amountToken", "type": "uint256" }, { "internalType": "uint256", "name": "amountAVAX", "type": "uint256" } ], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "address", "name": "token", "type": "address" }, { "internalType": "uint256", "name": "liquidity", "type": "uint256" }, { "internalType": "uint256", "name": "amountTokenMin", "type": "uint256" }, { "internalType": "uint256", "name": "amountAVAXMin", "type": "uint256" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" }, { "internalType": "bool", "name": "approveMax", "type": "bool" }, { "internalType": "uint8", "name": "v", "type": "uint8" }, { "internalType": "bytes32", "name": "r", "type": "bytes32" }, { "internalType": "bytes32", "name": "s", "type": "bytes32" } ], "name": "removeLiquidityAVAXWithPermitSupportingFeeOnTransferTokens", "outputs": [ { "internalType": "uint256", "name": "amountAVAX", "type": "uint256" } ], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "address", "name": "tokenA", "type": "address" }, { "internalType": "address", "name": "tokenB", "type": "address" }, { "internalType": "uint256", "name": "liquidity", "type": "uint256" }, { "internalType": "uint256", "name": "amountAMin", "type": "uint256" }, { "internalType": "uint256", "name": "amountBMin", "type": "uint256" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" }, { "internalType": "bool", "name": "approveMax", "type": "bool" }, { "internalType": "uint8", "name": "v", "type": "uint8" }, { "internalType": "bytes32", "name": "r", "type": "bytes32" }, { "internalType": "bytes32", "name": "s", "type": "bytes32" } ], "name": "removeLiquidityWithPermit", "outputs": [ { "internalType": "uint256", "name": "amountA", "type": "uint256" }, { "internalType": "uint256", "name": "amountB", "type": "uint256" } ], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountOut", "type": "uint256" }, { "internalType": "address[]", "name": "path", "type": "address[]" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "swapAVAXForExactTokens", "outputs": [ { "internalType": "uint256[]", "name": "amounts", "type": "uint256[]" } ], "stateMutability": "payable", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountOutMin", "type": "uint256" }, { "internalType": "address[]", "name": "path", "type": "address[]" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "swapExactAVAXForTokens", "outputs": [ { "internalType": "uint256[]", "name": "amounts", "type": "uint256[]" } ], "stateMutability": "payable", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountOutMin", "type": "uint256" }, { "internalType": "address[]", "name": "path", "type": "address[]" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "swapExactAVAXForTokensSupportingFeeOnTransferTokens", "outputs": [], "stateMutability": "payable", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountIn", "type": "uint256" }, { "internalType": "uint256", "name": "amountOutMin", "type": "uint256" }, { "internalType": "address[]", "name": "path", "type": "address[]" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "swapExactTokensForAVAX", "outputs": [ { "internalType": "uint256[]", "name": "amounts", "type": "uint256[]" } ], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountIn", "type": "uint256" }, { "internalType": "uint256", "name": "amountOutMin", "type": "uint256" }, { "internalType": "address[]", "name": "path", "type": "address[]" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "swapExactTokensForAVAXSupportingFeeOnTransferTokens", "outputs": [], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountIn", "type": "uint256" }, { "internalType": "uint256", "name": "amountOutMin", "type": "uint256" }, { "internalType": "address[]", "name": "path", "type": "address[]" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "swapExactTokensForTokens", "outputs": [ { "internalType": "uint256[]", "name": "amounts", "type": "uint256[]" } ], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountIn", "type": "uint256" }, { "internalType": "uint256", "name": "amountOutMin", "type": "uint256" }, { "internalType": "address[]", "name": "path", "type": "address[]" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "swapExactTokensForTokensSupportingFeeOnTransferTokens", "outputs": [], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountOut", "type": "uint256" }, { "internalType": "uint256", "name": "amountInMax", "type": "uint256" }, { "internalType": "address[]", "name": "path", "type": "address[]" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "swapTokensForExactAVAX", "outputs": [ { "internalType": "uint256[]", "name": "amounts", "type": "uint256[]" } ], "stateMutability": "nonpayable", "type": "function" }, { "inputs": [ { "internalType": "uint256", "name": "amountOut", "type": "uint256" }, { "internalType": "uint256", "name": "amountInMax", "type": "uint256" }, { "internalType": "address[]", "name": "path", "type": "address[]" }, { "internalType": "address", "name": "to", "type": "address" }, { "internalType": "uint256", "name": "deadline", "type": "uint256" } ], "name": "swapTokensForExactTokens", "outputs": [ { "internalType": "uint256[]", "name": "amounts", "type": "uint256[]" } ], "stateMutability": "nonpayable", "type": "function" }, { "stateMutability": "payable", "type": "receive" } ]'
listeningABI = json.loads(
    '[{"inputs":[{"internalType":"address","name":"_feeToSetter","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"token0","type":"address"},{"indexed":true,"internalType":"address","name":"token1","type":"address"},{"indexed":false,"internalType":"address","name":"pair","type":"address"},{"indexed":false,"internalType":"uint256","name":"","type":"uint256"}],"name":"PairCreated","type":"event"},{"constant":true,"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"allPairs","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"allPairsLength","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"}],"name":"createPair","outputs":[{"internalType":"address","name":"pair","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"feeTo","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[],"name":"feeToSetter","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"}],"name":"getPair","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"_feeTo","type":"address"}],"name":"setFeeTo","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"_feeToSetter","type":"address"}],"name":"setFeeToSetter","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"}]')
tokenNameABI = json.loads(
    '[ { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "owner", "type": "address" }, { "indexed": true, "internalType": "address", "name": "spender", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "value", "type": "uint256" } ], "name": "Approval", "type": "event" }, { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "from", "type": "address" }, { "indexed": true, "internalType": "address", "name": "to", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "value", "type": "uint256" } ], "name": "Transfer", "type": "event" }, { "constant": true, "inputs": [ { "internalType": "address", "name": "_owner", "type": "address" }, { "internalType": "address", "name": "spender", "type": "address" } ], "name": "allowance", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": false, "inputs": [ { "internalType": "address", "name": "spender", "type": "address" }, { "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "approve", "outputs": [ { "internalType": "bool", "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": true, "inputs": [ { "internalType": "address", "name": "account", "type": "address" } ], "name": "balanceOf", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "decimals", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "getOwner", "outputs": [ { "internalType": "address", "name": "", "type": "address" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "name", "outputs": [ { "internalType": "string", "name": "", "type": "string" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "symbol", "outputs": [ { "internalType": "string", "name": "", "type": "string" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": true, "inputs": [], "name": "totalSupply", "outputs": [ { "internalType": "uint256", "name": "", "type": "uint256" } ], "payable": false, "stateMutability": "view", "type": "function" }, { "constant": false, "inputs": [ { "internalType": "address", "name": "recipient", "type": "address" }, { "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "transfer", "outputs": [ { "internalType": "bool", "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" }, { "constant": false, "inputs": [ { "internalType": "address", "name": "sender", "type": "address" }, { "internalType": "address", "name": "recipient", "type": "address" }, { "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "transferFrom", "outputs": [ { "internalType": "bool", "name": "", "type": "bool" } ], "payable": false, "stateMutability": "nonpayable", "type": "function" } ]')


# Buy Token
def Buy(token_address, token_symbol):
    if token_address is not None:
        token_to_buy = web3.toChecksumAddress(token_address)
        spend = web3.toChecksumAddress("0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7")  # wavax contract address
        contract = web3.eth.contract(address=traderJoeRouterAddress, abi=traderJoeABI)
        nonce = web3.eth.get_transaction_count(walletAddress)
        start = time.time()
        traderjoe_txn = contract.functions.swapExactETHForTokens(
            0,
            # Set to 0 or specify min number of tokens - setting to 0 just buys X amount of token at its current
            # price for whatever AVAX specified
            [spend, token_to_buy],
            walletAddress,
            (int(time.time()) + transactionRevertTime)
        ).buildTransaction({
            'from': walletAddress,
            'value': web3.toWei(float(snipeAVAXAmount), 'ether'),
            # This is the Token(AVAX) amount you want to Swap from
            'gas': gasAmount,
            'gasPrice': web3.toWei(gasPrice, 'gwei'),
            'nonce': nonce,
        })

        try:
            signed_txn = web3.eth.account.sign_transaction(traderjoe_txn, private_key)
            tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)  # BUY THE TOKEN
        except:
            print("")  # line break: move onto scanning for next token

        txHash = str(web3.toHex(tx_token))

        # TOKEN IS BOUGHT

        check_transaction_success_url = "https://api.snowtrace.io/api?module=transaction&action=gettxreceiptstatus&txhash=" + txHash + "&apikey=" + snowtraceScanAPIKey
        check_transaction_result = requests.get(url=check_transaction_success_url)
        tx_result = check_transaction_result.json()['status']

        if tx_result == "1":
            print(currentTimeStamp + " Successfully bought $" + token_symbol + " for " + str(
                snipeAVAXAmount) + " AVAX - TX ID: ", txHash)

        else:
            print(currentTimeStamp + " Transaction failed: likely not enough gas.")

        update_title()


buyTokenThread = threading.Thread(target=Buy(None, None))
buyTokenThread.start()

# Listen for Token
contract = web3.eth.contract(address=traderJoeFactoryAddress, abi=listeningABI)

print(currentTimeStamp + " [Info] Scanning for new tokens...")
print("")  # line break


def found_token(event):
    try:
        jsonEventContents = json.loads(Web3.toJSON(event))
        if (jsonEventContents['args'][
            'token1'] == "0xb31f66aa3c1e785363f0875a1b74e27b85fd66c7"):  # check if pair is WAVAX, if not then ignore it
            token_address = jsonEventContents['args']['token0']

            getTokenName = web3.eth.contract(address=token_address,
                                             abi=tokenNameABI)  # code to get name and symbol from token address
            print("getTokenName is", getTokenName)

            tokenName = getTokenName.functions.name().call()
            token_symbol = getTokenName.functions.symbol().call()
            print(
                currentTimeStamp + " [Token] New potential token detected: " + tokenName + " (" + token_symbol + "): " + token_address)
            global numTokensDetected
            global numTokensBought
            numTokensDetected = numTokensDetected + 1
            update_title()

            # --------------------------------------------MINI AUDIT FEATURE-------------------------------------------------------

            if (
                    enableMiniAudit == True):  # enable mini audit feature: quickly scans token for potential
                # features that make it a scam / honeypot / rugpull etc
                print("[Token] Starting Mini Audit...")
                contractCodeGetRequestURL = "https://api.snowtrace.io/api?module=contract&action=getsourcecode&address=" + token_address + "&apikey=" + snowtraceScanAPIKey
                contractCodeRequest = requests.get(url=contractCodeGetRequestURL)
                tokenContractCode = contractCodeRequest.json()

                if (str(tokenContractCode['result'][0][
                            'ABI']) == "Contract source code not verified") and checkSourceCode == "True":  # check if source code is verified
                    print("[FAIL] Contract source code isn't verified.")

                elif "mint" in str(tokenContractCode['result'][0][
                                       'SourceCode']) and checkMintFunction == "True":  # check if any mint function enabled
                    print("[FAIL] Contract has mint function enabled.")

                elif (
                        "function transferFrom(address sender, address recipient, uint256 amount) public override returns (bool)" in str(
                    tokenContractCode['result'][0][
                        'SourceCode']) or "function _approve(address owner, address spender, uint256 amount) internal" in str(
                    tokenContractCode['result'][0]['SourceCode']) or "newun" in str(tokenContractCode['result'][0][
                                                                                        'SourceCode'])) and checkHoneypot == "True":  # check if token is honeypot
                    print("[FAIL] Contract is a honeypot.")

                else:
                    print("[SUCCESS] Token has passed mini audit.")  # now you can buy
                    numTokensBought = numTokensBought + 1
                    if (observeOnly == "False"):
                        Buy(token_address, token_symbol)
                        update_title()





            else:  # we dont care about audit, just buy it
                if (observeOnly == "False"):
                    Buy(token_address, token_symbol)
                    numTokensBought += 1
                    update_title()

            print("")  # line break: move onto scanning for next token

    except:
        pass

    # ------------------------------------END OF MINI AUDIT FEATURE---------------------------------------------------------------


# -----------------------------------------TOKEN SCANNER BACKGROUND CODE----------------------------------------------------------------------

async def token_loop(event_filter, poll_interval):
    while True:
        try:
            for PairCreated in event_filter.get_new_entries():
                print("looping in PairCreated...")
                found_token(PairCreated)
            await asyncio.sleep(poll_interval)
        except:
            pass


def listen_for_tokens():
    event_filter = contract.events.PairCreated.createFilter(fromBlock='latest')
    print("In the listening loop...")
    # block_filter = web3.eth.filter('latest')
    # tx_filter = web3.eth.filter('pending')
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(
            asyncio.gather(
                token_loop(event_filter, 0)))
        # log_loop(block_filter, 2),
        # log_loop(tx_filter, 2)))

    finally:
        # close loop to free up system resources
        # loop.close()
        # print("loop close")
        listen_for_tokens()

        # beware of valueerror code -32000 which is a glitch. make it ignore it and go bakc to listening


listen_for_tokens()

input("")
# ------------------------------------------END OF TOKEN SCANNER BACKGROUND CODE---------------------------------------------------------------------
