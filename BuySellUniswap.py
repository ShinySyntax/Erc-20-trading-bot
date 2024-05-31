import requests
from web3 import Web3
import time
import json
import datetime
import os
import json, ssl, asyncio, websockets
import eth_abi.packed
from uniswap_universal_router_decoder import FunctionRecipient, RouterCodec
from datetime import timedelta, timezone
from decimal import Decimal, getcontext


class UniSwapV1:
    def __init__(self):
        self.georliRpc = (
            "https://eth-goerli.g.alchemy.com/v2/sgVKVudg1rIPwUU065uEUAgFMaOXnYmc" # testnet 
        )
    
        self.blxrbdnRpc = (
            "https://eth-mainnet.g.alchemy.com/v2/38Gjw7EysPUBxh0MEZ_x8AEgHnfRVwCQ" # free alachemy feel free to change 
        )
        self.alchemy_url = (
            "https://eth-mainnet.g.alchemy.com/v2/xSkilifcxJwzptEKDrJRXpVXkP65kr1O" # free alachemy feel free to change 
        )  #this having RPC Error

        self.blxKey = "MmUxZGUw" # notworking
        self.blxUrl = "https://api.blxrbdn.com" 
        self.ur_address = Web3.to_checksum_address(
            "0xEf1c6E67703c7BD7107eed8303Fbe6EC2554BF6B"  # univ router 
        )
        self.abiV2 = ""
        self.abiV3 = ""
        self.abiErc20 = ""
        self.abiPoolV3 = ""
        self.v2FactoryABI = ""
        self.v3FactoryABI = ""
        self.pricefeed = ""
        self.wrapperEthABI = ""
        self.permit2_abi = ""

        self.uniswapV2RouterAddress = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
        self.uniswapV3RouterAddress = "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45"
        self.v2FactoryContractAddress = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
        self.v3FactoryContractAddress = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
        self.chainlink_price_feed_address = "0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419"
        self.wrapper_eth_address = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
        self.permit2_address = Web3.to_checksum_address(
            "0x000000000022D473030F116dDEE9F6B43aC78BA3"
        )

        current_directory = os.getcwd()
        # file_dir = os.path.join(current_directory, "BasicBuySell", "trading_json")
        file_dir = os.path.join(current_directory, "trading_json")
        with open(f"{file_dir}/uniswapV2Abi.json", "r") as file:
            self.abiV2 = json.load(file)
        with open(f"{file_dir}/erc20ABI.json", "r") as file:
            self.abiErc20 = json.load(file)
        with open(f"{file_dir}/uniswapV3Abi.json", "r") as file:
            self.abiV3 = json.load(file)
        with open(f"{file_dir}/v3PoolABI.json", "r") as file:
            self.abiPoolV3 = json.load(file)
        with open(f"{file_dir}/v2factory.json", "r") as file:
            self.v2FactoryABI = json.load(file)
        with open(f"{file_dir}/v3factory.json", "r") as file:
            self.v3FactoryABI = json.load(file)
        with open(f"{file_dir}/pricefeed.json", "r") as file:
            self.pricefeed = json.load(file)
        with open(f"{file_dir}/v2PoolABI.json", "r") as file:
            self.poolV2 = json.load(file)
        with open(f"{file_dir}/WETH.json", "r") as file:
            self.wrapperEthABI = json.load(file)
        with open(f"{file_dir}/permit2_abi.json", "r") as file:
            self.permit2_abi = json.load(file)
        with open(f"{file_dir}/uni_abi.json", "r") as file:
            self.uni_abi = json.load(file)

    # def eth_conversion():

    def check_uniswap(self, tokenInAddress, tokenOutAddress, eth_amount): ## this is how we find if the token is V2 or V3 
        amount_in = ""
        amount_out = ""
        estimateusd = ""
        version = ""
        with requests.Session() as sess:
            try:
                w3 = Web3(Web3.HTTPProvider(self.alchemy_url))
                if tokenInAddress == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2":
                    wei_amount = Web3.to_wei(eth_amount, "ether")
                else:
                    wei_amount = eth_amount

                params = {
                    "protocols": "v2,v3",
                    "tokenInAddress": tokenInAddress,
                    "tokenInChainId": 1,
                    "tokenOutAddress": tokenOutAddress,
                    "tokenOutChainId": 1,
                    "amount": wei_amount,
                    "type": "exactIn",
                }

                resp = sess.get(
                    f"https://api.uniswap.org/v1/quote",
                    headers={"origin": "https://app.uniswap.org"},
                    params=params,
                )

                if resp.status_code == 200:
                    uniswap_json = json.loads(resp.text)
                    amount_in = uniswap_json["amountDecimals"]
                    amount_out = uniswap_json["quoteDecimals"]
                    estimateusd = uniswap_json["gasUseEstimateUSD"]
                    version = uniswap_json["route"][0][0]["type"]
                    pool_address = uniswap_json["route"][0][0]["address"]
                    if "v2-" in version:
                        version = "V2"
                    if "v3-pool" in version:
                        version = "V3"
                    res_details = {
                        "amount_in": amount_in,
                        "amount_out": amount_out,
                        "estimateusd": estimateusd,
                        "version": version,
                        "pool_address": pool_address,
                        "error": "",
                    }
                else:
                    try:
                        uniswap_json = json.loads(resp.text)
                        error = uniswap_json["detail"]
                    except:
                        error = "need to check uniswap"
                    res_details = {
                        "amount_in": amount_in,
                        "amount_out": amount_out,
                        "estimateusd": estimateusd,
                        "version": version,
                        "error": error,
                        "pool_address": "",
                    }
            except:
                error = "need to check uniswap"
                res_details = {
                    "amount_in": amount_in,
                    "amount_out": amount_out,
                    "estimateusd": estimateusd,
                    "version": version,
                    "error": error,
                    "pool_address": "",
                }
        return res_details


    def sendPrivateTransaction(self, w3, rawTransaction): ## potentially we want to use private tx only, but we are not using it for testing  Ref -https://docs.bloxroute.com/apis/sending-transactions
        headers = {"Content-Type": "application/json", "Authorization": f"{self.blxKey}"}
        # data = {"method": "blxr_tx", "id": "1", "params": {"transaction": rawTransaction}}

        data = {
            "id": 1,
            "method": "blxr_private_tx",
            "params": {
                "transaction": rawTransaction,
                "mev_builders": {
                    "bloxroute": "",
                    "flashbots": "",
                    "beaverbuild": "",
                    "all": "",
                },
            },
        }

        # data = json.dumps(data1)
        print("post data:", data)
        # print("post headers:", headers)
        response = requests.post(self.blxUrl, headers=headers, json=data)
        print("Before Response content:", response.text)
        if response.status_code == 200:
            response_json = json.loads(response.text)
            print(f"response_json['result']===========>{response_json['result']}")
            # txHash=response_json['result']['txHash']
            txHash = response_json["result"]
            tx_recipt = w3.eth.wait_for_transaction_receipt(txHash)
            
            print("-" * 50)
            print("Transaction Recipt blxUrl:", tx_recipt)
            print("-" * 50)
            return tx_recipt
        else:
            print("Request failed with status code:", response.status_code)
            print("Response content:", response.text)
            return False
            



    def get_liquidity_of_a_token_pair_v2( # we dont use it but we use to use it for calc Liq 
        self, pairAddress, tokenAddress
    ):  # SUPER/WETH ,#SUPER
        w3 = Web3(Web3.HTTPProvider(self.alchemy_url))
        contract = w3.eth.contract(
            address=w3.to_checksum_address(pairAddress), abi=self.poolV2
        )
        reserves = contract.functions.getReserves().call()
        decimals = contract.functions.decimals().call()
        token0 = contract.functions.token0().call()
        token1 = contract.functions.token1().call()
        if w3.to_checksum_address(tokenAddress) == token0:
            reserve_0 = reserves[0] / 10**decimals
            reserve_1 = reserves[1] / 10**18
            return reserve_0, reserve_1
        elif w3.to_checksum_address(tokenAddress) == token1:
            reserve_0 = reserves[1] / 10**decimals
            reserve_1 = reserves[0] / 10**18
            return reserve_0, reserve_1  

    def check_mainnet_vsersion(self, tokenId):  ## use this if you need to test 
        self.WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        self.w3 = Web3(Web3.HTTPProvider(self.blxrbdnRpc))
        uniSwapV2Contract = self.w3.eth.contract(
            address=self.uniswapV2RouterAddress, abi=self.abiV2
        )
        uniSwapV3Contract = self.w3.eth.contract(
            address=self.uniswapV3RouterAddress, abi=self.abiV3
        )
        v2FactoryContract = self.w3.eth.contract(
            address=self.v2FactoryContractAddress, abi=self.v2FactoryABI
        )
        v3FactoryContract = self.w3.eth.contract(
            address=self.v3FactoryContractAddress, abi=self.v3FactoryABI
        )
        return self.checkTokenPoolVersion(
            v2FactoryContract, v3FactoryContract, tokenId, self.WETH_ADDRESS
        )




    def getnamesymboldecimalsoferc20(self, tokenAddress):
        w3 = Web3(Web3.HTTPProvider(self.blxrbdnRpc))
        erc20 = w3.eth.contract(
            address=w3.to_checksum_address(tokenAddress), abi=self.abiErc20
        )
        decimals = erc20.functions.decimals().call()
        token_name = erc20.functions.name().call()
        token_symbol = erc20.functions.symbol().call()

        return token_name, token_symbol, decimals

    def getEthPrice(self):
        # Create a contract instance
        _w3 = Web3(Web3.HTTPProvider("https://eth.rpc.blxrbdn.com")) ## we used to use Bloxroute to get this 

        contract = _w3.eth.contract(
            address=self.chainlink_price_feed_address, abi=self.pricefeed
        )

        # Get the latest price data from Chainlink oracle
        latest_price = contract.functions.latestRoundData().call()

        # Extracting Ether price in USD (example, may vary based on specific contract)
        ether_price_usd = (
            latest_price[1] / 10**8
        )  # Adjust this according to the actual structure of price data

        return ether_price_usd

    def checkTokenPoolVersion( 
        self, v2FactoryContract, v3FactoryContract, tokenAddress, WETH_ADDRESS
    ):
        pair = v2FactoryContract.functions.getPair(tokenAddress, WETH_ADDRESS).call()
        if pair != "0x0000000000000000000000000000000000000000":
            return "V2", pair

        pair = v3FactoryContract.functions.getPool(
            WETH_ADDRESS, tokenAddress, 3000
        ).call()
        if pair != "0x0000000000000000000000000000000000000000":
            return "V3", pair
        return None, None

    def getwalletBalance(self, wallet_address, net=False):
        self.WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        self.w3 = Web3(Web3.HTTPProvider(self.blxrbdnRpc))
        wallet_address1 = self.w3.to_checksum_address(wallet_address)
        try:
            balance_wei = self.w3.eth.get_balance(wallet_address1)
            balance_eth = self.w3.from_wei(balance_wei, "ether")
            return balance_eth
        except Exception as e:
            print(f"error in getwalletBalance function {e}")
            return 0



    def getErc20Balance(self, tokenAddress, private_key1=False, net=False):
        if private_key1:
            self.private_key = private_key1
        if net:
            if net == "testnet":
                self.WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"
                self.w3 = Web3(Web3.HTTPProvider(self.georliRpc))
            elif net == "mainnet":
                self.WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
                self.w3 = Web3(Web3.HTTPProvider(self.blxrbdnRpc))
        try:
            erc20 = self.w3.eth.contract(
                address=self.w3.to_checksum_address(tokenAddress),
                abi=self.abiErc20,
            )

            sender_wallet = self.w3.eth.account.from_key(self.private_key)
            balance = erc20.functions.balanceOf(sender_wallet.address).call()
            return balance
        except:
            return 0

    def get_current_gas_price(self):
        return self.w3.eth.gas_price


######################################################## Sell on V2 #####################################
    def sellOnV2(
        self,
        w3,
        uniSwapV2Contract, #router 
        tokenAddress,
        amount, # amount in wei 
        slip1, # we are just giving 5 or 10% and for auto we are giving it 50% this is one of our problem 
        privateTransaction, # yes or no 
        gas_price_aggressive_estimate,
        default_limit_expiration_minutes,
        default_bribe_amt,
    ):
        response = {
            "status": False,
            "hash_id": "",
            "gas_price_con": "",
            "etherPrice": "",
            "amountOut": "",
            "slip": "", ## just printing out 
        }
        print(f"amountamount====>{amount}")
        try:
            # slippage = [int(slip1)]
            slip = int(slip1)
            sender_wallet = w3.eth.account.from_key(self.private_key)
            blockNumber = w3.eth.block_number
            block = w3.eth.get_block(blockNumber)

            if default_limit_expiration_minutes:
                deadline = (
                    block["timestamp"] + default_limit_expiration_minutes
                )  # 30 seconds hardcoded
            else:
                deadline = block["timestamp"] + 600
            path = [
                w3.to_checksum_address(tokenAddress),
                w3.to_checksum_address(self.WETH_ADDRESS),
            ]

            try:
                amountOut = uniSwapV2Contract.functions.getAmountsOut(
                    amount, path
                ).call()
            except Exception as e:
                print(f"error in amount=={amount}=>{e}")
                response["error"] = str(e)
                return response
          
            amountOut = amountOut[1]
            response["amountOut"] = amountOut

            print(f"slip==============>{slip}")

            try:
                min_token_expected = amountOut * (1 - (slip / 100))
                estimate = uniSwapV2Contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                    amount,
                    int(min_token_expected),
                    path,
                    w3.to_checksum_address(sender_wallet.address),
                    deadline,
                ).build_transaction(
                    {
                        "from": w3.to_checksum_address(sender_wallet.address),
                        "nonce": w3.eth.get_transaction_count(
                            w3.to_checksum_address(sender_wallet.address)
                        ),
                    }
                )
                etherPrice = self.getEthPrice()

                estimated_gas = w3.eth.estimate_gas(transaction=estimate)
                # maxPriorityFeePerGasfromcustomer=10000000000
                default_max_priority_fee = w3.to_wei(default_bribe_amt, "gwei")
                current_gas_price = self.get_current_gas_price()

                if gas_price_aggressive_estimate:
                    maxPriorityFeePerGasfromcustomer = default_max_priority_fee * 2
                    estimated_gas = round(1.5 * estimated_gas)
                else:
                    maxPriorityFeePerGasfromcustomer = default_max_priority_fee
                adjusted_max_priority_fee = max(
                    maxPriorityFeePerGasfromcustomer,
                    current_gas_price + default_max_priority_fee,
                )

 
                gas_price = w3.eth.gas_price * estimated_gas
                gas_price_in_ether = w3.from_wei(gas_price, "ether")
                print(
                    f"Estimated gas price for the swap: {float(gas_price_in_ether) * etherPrice}"
                )
                gas_price_con = float(gas_price_in_ether) * etherPrice
                swap = uniSwapV2Contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                    amount,
                    int(min_token_expected),
                    path,
                    w3.to_checksum_address(sender_wallet.address),
                    deadline,
                ).build_transaction(
                    {
                        "from": w3.to_checksum_address(sender_wallet.address),
                        "nonce": w3.eth.get_transaction_count(
                            w3.to_checksum_address(sender_wallet.address)
                        ),
                        "gas": estimated_gas,
                        "maxPriorityFeePerGas": default_max_priority_fee,
                        "maxFeePerGas": estimated_gas + adjusted_max_priority_fee,
                    }
                )

                signed_txn = w3.eth.account.sign_transaction(swap, self.private_key)
                hash_id = w3.to_hex(w3.keccak(signed_txn.rawTransaction))
                print("-" * 50)
                print("Transaction Hash:", hash_id)
                if privateTransaction:
                    
                    tx_recipt = self.sendPrivateTransaction(
                        w3, signed_txn.rawTransaction.hex()[2:]
                    )
                else:
                    tx = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    tx_recipt = w3.eth.wait_for_transaction_receipt(tx)
                try:
                    
                    if(tx_recipt):
                        print(f"status for transaction {tx_recipt.status}")
                        if bool(tx_recipt.status):
                            org_status=True
                        else:
                            org_status=False
                    else:
                        org_status=False
                except:
                    org_status=False
                    pass
                try:
                    if not(tx_recipt):
                        hash_id=''
                        error="private transaction failed"
                except:
                    pass
       

                print("-" * 50)
                print("Transaction Recipt:", tx_recipt)
                print("-" * 50)
       
                unwrappEth_status = False
                response = {
                    "status": True,
                    "hash_id": hash_id,
                    "gas_price_con": gas_price_con,
                    "etherPrice": etherPrice,
                    "amountOut": amountOut,
                    "error": "",
                    "slip": slip,
                    "unwrappEth_status": unwrappEth_status,
                    "org_status":org_status,
                }
                return response
            except Exception as e:
                print(e)
                response["error"] = str(e)
                return response
        except Exception as e:
            print(e)
            response["error"] = str(e)
            return response
        return response
    
    ####################################################

    def gas_estimate_sell_v2(self, w3, uniSwapV2Contract, tokenAddress, amount, slip1):
        slip = int(slip1)
        sender_wallet = w3.eth.account.from_key(self.private_key)
        blockNumber = w3.eth.block_number
        block = w3.eth.get_block(blockNumber)
        deadline = block["timestamp"] + 600
        path = [
            w3.to_checksum_address(tokenAddress),
            w3.to_checksum_address(self.WETH_ADDRESS),
        ]

        try:
            amountOut = uniSwapV2Contract.functions.getAmountsOut(amount, path).call()
        except Exception as e:
            print(f"error in amount=={amount}=>{e}")
        amountOut = amountOut[1]
        print(f"slip=11=============>{slip}")
        try:
            min_token_expected = amountOut * (1 - (slip / 100))
            estimate = uniSwapV2Contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                amount,
                int(min_token_expected),
                path,
                w3.to_checksum_address(sender_wallet.address),
                deadline,
            ).build_transaction(
                {
                    "from": w3.to_checksum_address(sender_wallet.address),
                    "nonce": w3.eth.get_transaction_count(
                        w3.to_checksum_address(sender_wallet.address)
                    ),
                }
            )
            etherPrice = self.getEthPrice()
            estimated_gas = w3.eth.estimate_gas(transaction=estimate)
            gas_price = w3.eth.gas_price * estimated_gas
            gas_price_in_ether = w3.from_wei(gas_price, "ether")
            print(
                f"Estimated gas price for the swap: {float(gas_price_in_ether) * etherPrice}"
            )
            gas_price_con = float(gas_price_in_ether) * etherPrice
        except Exception as e:
            print(f"error in sell gas {e}")
            gas_price_con = ""
        return gas_price_con



    def gas_estimate_buy_v2(
        self, w3, uniSwapV2Contract, tokenAddress, ethQuantity, slip1
    ):
        slip = int(slip1)
        sender_wallet = w3.eth.account.from_key(self.private_key)
        blockNumber = w3.eth.block_number
        block = w3.eth.get_block(blockNumber)
        deadline = block["timestamp"] + 180  # 30 seconds hardcoded
        path = [
            w3.to_checksum_address(self.WETH_ADDRESS),
            w3.to_checksum_address(tokenAddress),
        ]
        amountOut = uniSwapV2Contract.functions.getAmountsOut(
            w3.to_wei(ethQuantity, "ether"), path
        ).call()
        amountOut = amountOut[1]
        try:
            print(f"slip==============>{slip}")
            min_eth_expected = amountOut * (1 - (slip / 100))
            estimate = uniSwapV2Contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
                int(min_eth_expected),
                path,
                w3.to_checksum_address(sender_wallet.address),
                deadline,
            ).build_transaction(
                {
                    "from": w3.to_checksum_address(sender_wallet.address),
                    "value": w3.to_wei(ethQuantity, "ether"),  # $2 hardcoded
                    "nonce": w3.eth.get_transaction_count(
                        w3.to_checksum_address(sender_wallet.address)
                    ),
                }
            )
            etherPrice = self.getEthPrice()
            # use change link self.pricefeed function sent on Slack
            estimated_gas = w3.eth.estimate_gas(transaction=estimate)
            gas_price = w3.eth.gas_price * estimated_gas
            gas_price_in_ether = w3.from_wei(gas_price, "ether")
            print(
                f"Estimated gas price for the swap: {float(gas_price_in_ether) * etherPrice}"
            )  # gas price print on console
            gas_price_con = float(gas_price_in_ether) * etherPrice
        except Exception as e:
            print(f"error in buy v2 gas price {e}")
            if "insufficient funds for gas" in str(e):
                gas_price_con = "Insufficient Gas"
            else:
                gas_price_con = ""
        return gas_price_con


    def getwalletBalance(self, wallet_address, net=False):
        self.WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        self.w3 = Web3(Web3.HTTPProvider(self.blxrbdnRpc))
        wallet_address1 = self.w3.to_checksum_address(wallet_address)
        try:
            balance_wei = self.w3.eth.get_balance(wallet_address1)
            balance_eth = self.w3.from_wei(balance_wei, "ether")
            return balance_eth
        except Exception as e:
            print(f"error in getwalletBalance function {e}")
            return 0

    async def send_tx(self, raw_tx):
        async with websockets.connect(
            "wss://api.blxrbdn.com/ws",
            extra_headers=[("Authorization", self.blxrbdn_auth)],
            ssl=ssl.SSLContext(cert_reqs=ssl.CERT_NONE),
        ) as ws:
            request = json.dumps(
                {"id": 1, "method": "blxr_tx", "params": {"transaction": raw_tx}}
            )
            await ws.send(request)
            response = await ws.recv()
            return response
############################################################## Buy on V2 #################################
    def buyOnV2(
        self,
        w3,
        uniSwapV2Contract,
        tokenAddress,
        ethQuantity,
        slip1,
        privateTransaction,
        gas_price_aggressive_estimate,
        default_limit_expiration_minutes,
        default_bribe_amt,
    ):

        response = {
            "status": False,
            "hash_id": "",
            "gas_price_con": "",
            "etherPrice": "",
            "amountOut": "",
            "slip": "",
        }
        try:
            # slippage = [int(slip1)]
            slip = int(slip1)
            sender_wallet = w3.eth.account.from_key(self.private_key)
            blockNumber = w3.eth.block_number
            block = w3.eth.get_block(blockNumber)
            if default_limit_expiration_minutes:
                deadline = (
                    block["timestamp"] + default_limit_expiration_minutes
                )  # 30 seconds hardcoded
            else:
                deadline = block["timestamp"] + 180  # 30 seconds hardcoded
            path = [
                w3.to_checksum_address(self.WETH_ADDRESS),
                w3.to_checksum_address(tokenAddress),
            ]
            amountOut = uniSwapV2Contract.functions.getAmountsOut(
                w3.to_wei(ethQuantity, "ether"), path
            ).call()
            amountOut = amountOut[1]
            # Define slippage tolerance (e.g., 1%)
            # slippage = [5, 10,100]

            # for slip in slippage:
            try:
                print(f"slip==============>{slip}")
                min_eth_expected = amountOut * (1 - (slip / 100))
                estimate = uniSwapV2Contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
                    int(min_eth_expected),
                    path,
                    w3.to_checksum_address(sender_wallet.address),
                    deadline,
                ).build_transaction(
                    {
                        "from": w3.to_checksum_address(sender_wallet.address),
                        "value": w3.to_wei(ethQuantity, "ether"),  # $2 hardcoded
                        "nonce": w3.eth.get_transaction_count(
                            w3.to_checksum_address(sender_wallet.address)
                        ),
                    }
                )
                etherPrice = self.getEthPrice()
                # use change link self.pricefeed function sent on Slack
                estimated_gas = w3.eth.estimate_gas(transaction=estimate)
                default_max_priority_fee = w3.to_wei(default_bribe_amt, "gwei")
                current_gas_price = self.get_current_gas_price()

                if gas_price_aggressive_estimate:
                    maxPriorityFeePerGasfromcustomer = default_max_priority_fee * 2
                    # estimated_gas = 1.5 * estimated_gas
                    estimated_gas = round(1.5 * estimated_gas)
                else:
                    maxPriorityFeePerGasfromcustomer = default_max_priority_fee
                adjusted_max_priority_fee = max(
                    maxPriorityFeePerGasfromcustomer,
                    current_gas_price + default_max_priority_fee,
                )
                gas_price = w3.eth.gas_price * estimated_gas
                gas_price_in_ether = w3.from_wei(gas_price, "ether")
                print(
                    f"Estimated gas price for the swap: {float(gas_price_in_ether) * etherPrice}"
                )  # gas price print on console
                gas_price_con = float(gas_price_in_ether) * etherPrice
                swap = uniSwapV2Contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
                    int(min_eth_expected),
                    path,
                    w3.to_checksum_address(sender_wallet.address),
                    deadline,
                ).build_transaction(
                    {
                        "from": w3.to_checksum_address(sender_wallet.address),
                        "value": w3.to_wei(ethQuantity, "ether"),  # $2 hardcoded
                        "nonce": w3.eth.get_transaction_count(
                            w3.to_checksum_address(sender_wallet.address)
                        ),
                        "gas": estimated_gas,
                        "maxPriorityFeePerGas": default_max_priority_fee,
                        "maxFeePerGas": estimated_gas + adjusted_max_priority_fee,
                    }
                )
                signed_txn = w3.eth.account.sign_transaction(swap, self.private_key)
                hash_id = w3.to_hex(w3.keccak(signed_txn.rawTransaction))
                print("-" * 50)
                print("Transaction Hash:", hash_id)
                # raw_tx = signed_txn.rawTransaction.hex()
                if privateTransaction:
                    tx_recipt = self.sendPrivateTransaction(
                        w3, signed_txn.rawTransaction.hex()[2:]
                    )
                else:
                    tx = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    tx_recipt = w3.eth.wait_for_transaction_receipt(tx)
                try:
                    
                    if(tx_recipt):
                        print(f"status for transaction {tx_recipt.status}")
                        if bool(tx_recipt.status):
                            org_status=True
                        else:
                            org_status=False
                    else:
                        org_status=False
                except:
                    org_status=False
                    pass
                try:
                    if not(tx_recipt):
                        hash_id=''
                        error="private transaction failed"
                except:
                    pass
                print("-" * 50)
                print("Transaction Recipt:", tx_recipt)
                print("-" * 50)
                response = {
                    "status": True,
                    "hash_id": hash_id,
                    "gas_price_con": gas_price_con,
                    "etherPrice": etherPrice,
                    "amountOut": amountOut,
                    "error": "",
                    "slip": slip,
                    "org_status":org_status,
                }
                return response
            except Exception as e:
                print(e)
                response["error"] = str(e)
                return response
        except Exception as e:
            print(e)
            response["error"] = str(e)
            return response
        return response

    def get_current_time_utc(self):
        return datetime.datetime.now(timezone.utc)
############################################################# Buy on V3 #######################################
    def buyOnV3UniversalRouter(
        self,
        w3,
        uniSwapV3Contract,
        tokenAddress,
        poolAdress,
        ethQuantity,
        slip1,
        privateTransaction,
        gas_price_aggressive_estimate,
        default_limit_expiration_minutes,
        default_bribe_amt,
    ):
        response = {
            "status": False,
            "hash_id": "",
            "gas_price_con": "",
            "etherPrice": "",
            "amountOut": "",
            "slip": "",
        }
        try:
            slip = int(slip1)
            sender_wallet = w3.eth.account.from_key(self.private_key)
            poolInformation = self.getV3PoolInformation(w3, poolAdress)

            amountOut = self.getAmountsOut(
                w3,
                [poolAdress],
                [self.WETH_ADDRESS, tokenAddress],
                w3.to_wei(ethQuantity, "ether"),
            )
            amountOut = amountOut[1]
            try:
                min_token_expected = int(amountOut * (1 - slip / 100))

                path = [self.WETH_ADDRESS, poolInformation["fee"], tokenAddress]
                codec = RouterCodec()
               
                encoded_input = (
                    codec.encode.chain()
                    .wrap_eth(FunctionRecipient.ROUTER, w3.to_wei(ethQuantity, "ether"))
                    .v3_swap_exact_in(
                        FunctionRecipient.SENDER,
                        w3.to_wei(ethQuantity, "ether"),
                        min_token_expected,
                        path,
                        payer_is_sender=False,
                    )
                    .build(codec.get_default_deadline())
                )
                trx_params = {
                    "from": sender_wallet.address,
                    "to": self.ur_address,
                    # "gas": 500_000,
                    # "maxPriorityFeePerGas": w3.eth.max_priority_fee,
                    # "maxFeePerGas": 100 * 10**9,
                    "type": "0x2",
                    "chainId": 1,
                    "value": w3.to_wei(ethQuantity, "ether"),
                    "nonce": w3.eth.get_transaction_count(sender_wallet.address),
                    "data": encoded_input,
                }
                estimate_gas = w3.eth.estimate_gas(trx_params)
                etherPrice = self.getEthPrice()

                default_max_priority_fee = w3.to_wei(default_bribe_amt, "gwei")
                current_gas_price = self.get_current_gas_price()
                if gas_price_aggressive_estimate:
                    maxPriorityFeePerGasfromcustomer = default_max_priority_fee * 2
                    # estimate_gas = 1.5 * estimate_gas
                    estimate_gas = round(1.5 * estimate_gas)
                else:
                    maxPriorityFeePerGasfromcustomer = default_max_priority_fee
                adjusted_max_priority_fee = max(
                    maxPriorityFeePerGasfromcustomer,
                    current_gas_price + default_max_priority_fee,
                )
                gas_price = w3.eth.gas_price * estimate_gas
                gas_price_in_ether = w3.from_wei(gas_price, "ether")
                print(
                    f"Estimated gas price for the swap: {float(gas_price_in_ether) * etherPrice}"
                )
                gas_price_con = float(gas_price_in_ether) * etherPrice
                trx_params = {
                    "from": sender_wallet.address,
                    "to": self.ur_address,
                    "gas": estimate_gas,
                    "maxPriorityFeePerGas": default_max_priority_fee,
                    "maxFeePerGas": estimate_gas + adjusted_max_priority_fee,
                    # "gas": estimate_gas + adjusted_max_priority_fee,
                    # "maxPriorityFeePerGas": w3.eth.max_priority_fee,
                    # "maxFeePerGas": 100 * 10**9,
                    "type": "0x2",
                    "chainId": 1,
                    "value": w3.to_wei(ethQuantity, "ether"),
                    "nonce": w3.eth.get_transaction_count(sender_wallet.address),
                    "data": encoded_input,
                }

                signed_txn = w3.eth.account.sign_transaction(
                    trx_params, self.private_key
                )
                hash_id = w3.to_hex(w3.keccak(signed_txn.rawTransaction))
                print("-" * 50)
                print("Transaction Hash:", hash_id)
                if privateTransaction:
                    tx_recipt=self.sendPrivateTransaction(w3, signed_txn.rawTransaction.hex()[2:])
                else:
                    tx = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    tx_recipt = w3.eth.wait_for_transaction_receipt(tx)

                    print("-" * 50)
                    print("Transaction Recipt:", tx_recipt)
                    print("-" * 50)
                try:
                    
                    if(tx_recipt):
                        print(f"status for transaction {tx_recipt.status}")
                        if bool(tx_recipt.status):
                            org_status=True
                        else:
                            org_status=False
                    else:
                        org_status=False
                except:
                    org_status=False
                    pass
                try:
                    if not(tx_recipt):
                        hash_id=''
                        error="private transaction failed"
                except:
                    pass
                response = {
                    "status": True,
                    "hash_id": hash_id,
                    "gas_price_con": gas_price_con,
                    "etherPrice": etherPrice,
                    "amountOut": amountOut,
                    "error": "",
                    "slip": slip,
                    "org_status":org_status,
                }
                return response
            except Exception as e:
                response["error"] = str(e)
                print(e)
                return response
        except Exception as e:
            print(e)
            response["error"] = str(e)
            return response
##################################################### Sell on V3 wqe use to use this, but since we got a lot of errors we stopped using it and we rewrote this function inside Node.js######################################
    def sellOnV3UniversalRouter(
        self,
        w3,
        uniSwapV3Contract,
        tokenAddress,
        poolAdress,
        amount,
        slip1,
        privateTransaction,
        gas_price_aggressive_estimate,
        default_limit_expiration_minutes,
        default_bribe_amt,
    ):
        response = {
            "status": False,
            "hash_id": "",
            "gas_price_con": "",
            "etherPrice": "",
            "amountOut": "",
            "slip": "",
        }
        try:
            # slippage = [int(slip1)]

            slip = int(slip1)
            sender_wallet = w3.eth.account.from_key(self.private_key)
            poolInformation = self.getV3PoolInformation(w3, poolAdress)
            amountOut = self.getAmountsOut(
                w3,
                [poolAdress],
                [
                    tokenAddress,
                    self.WETH_ADDRESS,
                ],
                amount,
            )
            amountOut = amountOut[1]
            # slippage = [5, 10,100]
            try:
                min_token_expected = int(amountOut * (1 - slip / 100))
          
                permit2_contract = w3.eth.contract(
                    address=self.permit2_address, abi=self.permit2_abi
                )
                (
                    p2_amount,
                    p2_expiration,
                    p2_nonce,
                ) = permit2_contract.functions.allowance(
                    sender_wallet.address, tokenAddress, self.ur_address
                ).call()
                codec = RouterCodec()
                # permit message
                allowance_amount = 2**160 - 1  # max/infinite
                permit_data, signable_message = codec.create_permit2_signable_message(
                    tokenAddress,
                    allowance_amount,
                    codec.get_default_expiration(),  # 30 days
                    p2_nonce,
                    self.ur_address,
                    codec.get_default_deadline(),  # 180 seconds
                    1,
                )

                # Signing the message
                signed_message = sender_wallet.sign_message(signable_message)

                path = [tokenAddress, poolInformation["fee"], self.WETH_ADDRESS]
                encoded_input = (
                    codec.encode.chain()
                    .permit2_permit(permit_data, signed_message)
                    .v3_swap_exact_in(
                        FunctionRecipient.ROUTER,
                        amount,
                        min_token_expected,
                        path,
                        payer_is_sender=True,
                    )
                    .unwrap_weth(FunctionRecipient.SENDER, min_token_expected)
                    .build(codec.get_default_deadline())
                )

                trx_params = {
                    "from": sender_wallet.address,
                    "to": self.ur_address,

                    "type": "0x2",
                    "chainId": 1,
                    "value": 0,
                    "nonce": w3.eth.get_transaction_count(sender_wallet.address),
                    "data": encoded_input,
                }
                estimated_gas = w3.eth.estimate_gas(trx_params)
 
                etherPrice = self.getEthPrice()
                default_max_priority_fee = w3.to_wei(default_bribe_amt, "gwei")
                current_gas_price = self.get_current_gas_price()

                if gas_price_aggressive_estimate:
                    maxPriorityFeePerGasfromcustomer = default_max_priority_fee * 2
                    # estimated_gas = 1.5 * estimated_gas
                    estimated_gas = round(1.5 * estimated_gas)
                else:
                    maxPriorityFeePerGasfromcustomer = default_max_priority_fee
                adjusted_max_priority_fee = max(
                    maxPriorityFeePerGasfromcustomer,
                    current_gas_price + default_max_priority_fee,
                )
                gas_price = w3.eth.gas_price * estimated_gas
                gas_price_in_ether = w3.from_wei(gas_price, "ether")
                gas_price_con = float(gas_price_in_ether) * etherPrice
                print(
                    f"Estimated gas price for the swap: {float(gas_price_in_ether) * etherPrice}"
                )

                trx_params = {
                    "from": sender_wallet.address,
                    "to": self.ur_address,
                    "gas": estimated_gas,
                    "maxPriorityFeePerGas": default_max_priority_fee,
                    "maxFeePerGas": estimated_gas + adjusted_max_priority_fee,
                    "type": "0x2",
                    "chainId": 1,
                    "value": 0,
                    "nonce": w3.eth.get_transaction_count(sender_wallet.address),
                    "data": encoded_input,
                }
                signed_txn = w3.eth.account.sign_transaction(
                    trx_params, self.private_key
                )
                hash_id = w3.to_hex(w3.keccak(signed_txn.rawTransaction))
                print("-" * 50)
                print("Transaction Hash:", hash_id)
                if privateTransaction:
                    tx_recipt=self.sendPrivateTransaction(w3, signed_txn.rawTransaction.hex()[2:])
                else:
                    tx = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
                    tx_recipt = w3.eth.wait_for_transaction_receipt(tx)

                    print("-" * 50)
                    print("Transaction Recipt:", tx_recipt)
                    print("-" * 50)
                try:
                    
                    if(tx_recipt):
                        print(f"status for transaction {tx_recipt.status}")
                        if bool(tx_recipt.status):
                            org_status=True
                        else:
                            org_status=False
                    else:
                        org_status=False
                except:
                    org_status=False
                    pass
                try:
                    if not(tx_recipt):
                        hash_id=''
                        error="private transaction failed"
                except:
                    pass
                
                # try:
                # unwrappEth_status=self.unwrappEth(w3, amount,self.private_key)
                # except:
                unwrappEth_status = False
                response = {
                    "status": True,
                    "hash_id": hash_id,
                    "gas_price_con": gas_price_con,
                    "etherPrice": etherPrice,
                    "amountOut": amountOut,
                    "error": "",
                    "slip": slip,
                    "unwrappEth_status": unwrappEth_status,
                    "org_status":org_status,
                }
                return response
            except Exception as e:
                print(e)
                response["error"] = str(e)
                return response
        except Exception as e:
            print(e)
            response["error"] = str(e)
            return response

  
    def getV3PoolInformation(self, w3, poolAddress):
        try:
            pool = w3.eth.contract(address=poolAddress, abi=self.abiPoolV3)
            slot = pool.functions.slot0().call()
            fee = pool.functions.fee().call()
            sqrtPriceX96 = slot[0]
            tick = slot[1]
            observationIndex = slot[2]
            observationCardinality = slot[3]
            observationCardinalityNext = slot[4]
            feeProtocol = slot[5]
            unlocked = slot[6]
            return {
                "sqrtPriceLimitX96": sqrtPriceX96,
                "tick": tick,
                "observationIndex": observationIndex,
                "observationCardinality": observationCardinality,
                "observationCardinalityNext": observationCardinalityNext,
                "feeProtocol": feeProtocol,
                "unlocked": unlocked,
                "fee": fee,
            }
        except:
            return 0

    def getAmountsOut(self, w3, pool, path, amountIn):
        assert len(path) >= 2, "INVALID_PATH"
        amounts = [0] * len(path)
        amounts[0] = amountIn

        for i in range(len(pool)):
            IPool = w3.eth.contract(address=pool[i], abi=self.abiPoolV3)
            sqrtPriceX96, _, _, _, _, _, unlocked = IPool.functions.slot0().call()
            assert unlocked, "Pool is Locked!"
            # squaredPrice = (sqrtPriceX96 * sqrtPriceX96) // 2**96
            squaredPrice = (
                Decimal(sqrtPriceX96) * Decimal(sqrtPriceX96) / Decimal(2**96)
            )

            if path[i] == IPool.functions.token0().call():
                numerator = squaredPrice
                # denominator = 2**96
                denominator = Decimal(2**96)
            else:
                # numerator = 2**96
                numerator = Decimal(2**96)
                denominator = squaredPrice

            amounts[i + 1] = int((Decimal(amounts[i]) * numerator) // denominator)
            assert amounts[i + 1] != 0, "Output Zero"

        return amounts

    def approveToken(self, w3, router, tokenAddress, amount):
        sender_wallet = w3.eth.account.from_key(self.private_key)
        try:
            erc20 = w3.eth.contract(
                address=w3.to_checksum_address(tokenAddress),
                abi=self.abiErc20,
            )
            approval = erc20.functions.approve(router, int(amount)).build_transaction(
                {
                    "from": w3.to_checksum_address(sender_wallet.address),
                    "nonce": w3.eth.get_transaction_count(
                        w3.to_checksum_address(sender_wallet.address)
                    ),
                }
            )
            signed_txn = w3.eth.account.sign_transaction(approval, self.private_key)
            hash = w3.to_hex(w3.keccak(signed_txn.rawTransaction))
            print("-" * 50)
            print("Transaction Hash For Approval:", hash)
            tx = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_recipt = w3.eth.wait_for_transaction_receipt(tx)
            return True
        except Exception as e:
            print(e)
            return False

############# we find the V2 or V3 then call the function written above ####
    def trade(
        self,
        tradeType,
        tokenId_org,
        Quantity,
        net,
        secret_key,
        uniswap_version_geckoterminal, ## we are getting from Uniswap 
        pool_address_geckoterminal,
        slippage,
        privateTransaction=False,
        pre_approved=False,
        gas_price_aggressive_estimate=False,
        default_limit_expiration_minutes=600,
        default_bribe_amt=10,
        approve_status_already=False,
    ):
        self.private_key = secret_key
        # self.blxrbdn_auth = blxrbdn_auth
        self.WETH_ADDRESS = ""
        try:
            tokenId = Web3.to_checksum_address(tokenId_org)
            print(f"tokenId==========>{tokenId}")
            print(f"net==========>{net}")
            print(f"default_bribe_amt==========>{default_bribe_amt}")
            print(
                f"default_limit_expiration_minutes==========>{default_limit_expiration_minutes}"
            )
            if net == "testnet":
                self.WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"
                self.w3 = Web3(Web3.HTTPProvider(self.georliRpc))
            elif net == "mainnet":
                self.WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
                self.w3 = Web3(Web3.HTTPProvider(self.blxrbdnRpc))
            uniSwapV2Contract = self.w3.eth.contract(
                address=self.uniswapV2RouterAddress, abi=self.abiV2
            )
            uniSwapV3Contract = self.w3.eth.contract(
                address=self.uniswapV3RouterAddress, abi=self.abiV3
            )
            v2FactoryContract = self.w3.eth.contract(
                address=self.v2FactoryContractAddress, abi=self.v2FactoryABI
            )
            v3FactoryContract = self.w3.eth.contract(
                address=self.v3FactoryContractAddress, abi=self.v3FactoryABI
            )

            uniswapProtocol = "V2"  ##################### ExpertEureka  hard coded #######################################################################

            if net == "mainnet":
                if uniswapProtocol:
                    if not (uniswapProtocol == uniswap_version_geckoterminal):
                        uniswapProtocol = uniswap_version_geckoterminal
                        pool = Web3.to_checksum_address(pool_address_geckoterminal)
                elif uniswap_version_geckoterminal:
                    uniswapProtocol = uniswap_version_geckoterminal
                    pool = Web3.to_checksum_address(pool_address_geckoterminal)

            if uniswapProtocol:
                if uniswapProtocol == "V2":
                    if tradeType == "buy":
                        print("2buy function called")
                        button_clicktime_stamp1 = self.get_current_time_utc()
                        tran_status = self.buyOnV2(
                            self.w3,
                            uniSwapV2Contract,
                            tokenId,
                            Quantity,
                            slippage,
                            privateTransaction,
                            gas_price_aggressive_estimate,
                            default_limit_expiration_minutes,
                            default_bribe_amt,
                        )
                        button_clicktime_stamp2 = self.get_current_time_utc()
                        time_difference = (
                            button_clicktime_stamp2 - button_clicktime_stamp1
                        ).total_seconds()
                        tran_status["time_difference"] = time_difference
                        if tran_status.get("status"):
                            if (pre_approved and not(approve_status_already)):
                                Quantity = self.getErc20Balance(tokenId)
                                if Quantity:
                                    # Quantity_1=Quantity*100
                                    Quantity_1 = 2**256 - 1 ## going for Infinity approval 
                                    approved = self.approveToken(
                                        self.w3,
                                        self.uniswapV2RouterAddress,
                                        tokenId,
                                        Quantity_1,
                                    )
                                    if approved:
                                        tran_status["approved_quantity"] = Quantity_1
                        return tran_status

                    elif tradeType == "sell":
                        print("v2 sell function called")
                        # Quantity = self.getErc20Balance(tokenId)
                        approved = ""
                        if not (pre_approved):
                            approved = self.approveToken(
                                self.w3,
                                self.uniswapV2RouterAddress,
                                tokenId,
                                2**256 - 1,
                            )
                            print("Token Approved")
                            if approved:
                                time.sleep(2)
                                pre_approved = True
                                # tran_status["approved_quantity"] = Quantity
                        if pre_approved:
                            button_clicktime_stamp1 = self.get_current_time_utc()
                            tran_status = self.sellOnV2(
                                self.w3,
                                uniSwapV2Contract,
                                tokenId,
                                Quantity,
                                slippage,
                                privateTransaction,
                                gas_price_aggressive_estimate,
                                default_limit_expiration_minutes,
                                default_bribe_amt,
                            )
                            button_clicktime_stamp2 = self.get_current_time_utc()
                            time_difference = (
                                button_clicktime_stamp2 - button_clicktime_stamp1
                            ).total_seconds()
                            tran_status["time_difference"] = time_difference
                            if approved:
                                tran_status["approved_quantity"] = Quantity
                            return tran_status
                elif uniswapProtocol == "V3":
                    if tradeType == "buy":
                        print("v3 buy function called")
                        button_clicktime_stamp1 = self.get_current_time_utc()
                        tran_status = self.buyOnV3UniversalRouter(
                            self.w3,
                            uniSwapV3Contract,
                            tokenId,
                            pool,
                            Quantity,
                            slippage,
                            privateTransaction,
                            gas_price_aggressive_estimate,
                            default_limit_expiration_minutes,
                            default_bribe_amt,
                        )
                        button_clicktime_stamp2 = self.get_current_time_utc()
                        time_difference = (
                            button_clicktime_stamp2 - button_clicktime_stamp1
                        ).total_seconds()
                        tran_status["time_difference"] = time_difference
                        if tran_status.get("status"):
                            # if pre_approved:
                            if (pre_approved and not(approve_status_already)):
                                Quantity = self.getErc20Balance(tokenId)
                                # Quantity_1=Quantity*1000
                                if Quantity:
                                    Quantity_1 = 2**256 - 1
                                    approved = self.approveToken(
                                        self.w3,
                                        self.permit2_address,
                                        tokenId,
                                        Quantity_1,
                                    )
                                    if approved:
                                        tran_status["approved_quantity"] = Quantity_1
                        return tran_status
                    elif tradeType == "sell":
                        print("v3 sell function called")
                        # balance = self.getErc20Balance(tokenId)
                        # print("balance", balance)
                        approved = ""
                        if not (pre_approved):
                            approved = self.approveToken(
                                self.w3, self.permit2_address, tokenId, 2**256 - 1
                            )
                            if approved:
                                time.sleep(2)
                                pre_approved = True
                        if pre_approved:
                            print("Token Approved")
                            # tran_status = self.sellOnV3(
                            button_clicktime_stamp1 = self.get_current_time_utc()
                            tran_status = self.sellOnV3UniversalRouter(
                                self.w3,
                                uniSwapV3Contract,
                                tokenId,
                                pool,
                                Quantity,
                                slippage,
                                privateTransaction,
                                gas_price_aggressive_estimate,
                                default_limit_expiration_minutes,
                                default_bribe_amt,
                            )
                            button_clicktime_stamp2 = self.get_current_time_utc()
                            time_difference = (
                                button_clicktime_stamp2 - button_clicktime_stamp1
                            ).total_seconds()
                            tran_status["time_difference"] = time_difference
                            if approved:
                                tran_status["approved_quantity"] = Quantity
                            return tran_status
                else:
                    try:
                        uniswapProtocol1, pool = self.check_mainnet_vsersion(tokenId)
                        if uniswapProtocol1:
                            response = {
                                "status": False,
                                "hash_id": "",
                                "gas_price_con": "",
                                "etherPrice": "",
                                "amountOut": "",
                                "error": f"couldnt find the pair in testnet v2 and v3, but found in mainet(vesrion {uniswapProtocol1} and pool address {pool}",
                            }
                        else:
                            response = {
                                "status": False,
                                "hash_id": "",
                                "gas_price_con": "",
                                "etherPrice": "",
                                "amountOut": "",
                                "error": "Could not find the pair and version",
                            }
                        return response
                    except Exception as e:
                        pass
        except Exception as e:
            response = {
                "status": False,
                "hash_id": "",
                "gas_price_con": "",
                "etherPrice": "",
                "amountOut": "",
                "error": e,
            }
            print(f"error in above function buy {e}")
            return response


######################### We need to optimize the below in terms of slippage and Gas settings and avoid getting all those annoying errors 

# trade(
#         self,
#         tradeType,
#         tokenId_org,
#         Quantity,
#         net,
#         secret_key,
#         uniswap_version_geckoterminal, ## we are getting from Uniswap 
#         pool_address_geckoterminal,
#         slippage,
#         privateTransaction=False,
#         pre_approved=False,
#         gas_price_aggressive_estimate=False,
#         default_limit_expiration_minutes=600,
#         default_bribe_amt=10,
#         approve_status_already=False,
#     )


#################### Common Errors that we got ###############



