import { ethers, BigNumber } from 'ethers';
import {
  PERMIT2_ADDRESS,
  SignatureTransfer,
  AllowanceTransfer,
  AllowanceProvider
} from '@uniswap/permit2-sdk';
import { AlphaRouter, SwapType } from '@uniswap/smart-order-router';
import { CurrencyAmount, TradeType, Percent, Ether } from '@uniswap/sdk-core';
import erc20Abi from './erc20ABI.json' assert { type: 'json' };
import {
  DAI,
  USDT,
  WETH,
  chainId,
  getSigner,
  walletAddress,
  getEthersProvider,
  uniswapRouterAddress,
  UNI
} from './constants.js';

const ethersProvider = getEthersProvider();
const ethersSigner = getSigner();
async function approvePermit2Contract(erc20Address, amount) {
  const erc20 = new ethers.Contract(erc20Address, erc20Abi, ethersSigner);
  const approveTx = await erc20.approve(PERMIT2_ADDRESS, amount);
  console.log('approve tx hash:', approveTx.hash);
  // wait for approve transaction confirmation
  const receipt = await approveTx.wait();
  if (receipt.status === 1) console.log('approve transaction confirmed');
  else throw new Error(receipt);
}

async function getAllowanceAmount(erc20TokenAddress, spender) {
  const erc20 = new ethers.Contract(erc20TokenAddress, erc20Abi, ethersSigner);
  const allowance = await erc20.allowance(walletAddress, spender);
  return allowance;
}

async function getSwapRoute(
  sourceToken,
  destToken,
  amountInWei,
  permit,
  signature
) {
  const inputAmount = CurrencyAmount.fromRawAmount(
    sourceToken,
    amountInWei.toString()
  );

  const router = new AlphaRouter({ chainId, provider: ethersProvider });
  const route = await router.route(
    inputAmount,
    destToken,
    TradeType.EXACT_INPUT,
    {
      recipient: walletAddress,
      slippageTolerance: new Percent(5, 1000),
      // type: SwapType.SWAP_ROUTER_02,
      // deadline: Math.floor(Date.now() / 1000 + 1800),

      type: SwapType.UNIVERSAL_ROUTER,
      deadlineOrPreviousBlockhash: Math.floor(Date.now() / 1000 + 1800),

      inputTokenPermit: {
        ...permit,
        signature
      }
    }
  );
  console.log(`Quote Exact In: ${amountInWei}  -> ${route.quote.toExact()}`);
  return route;
}

async function executeSwap() {
  // swap basic info
  // NOTE: not handling native currency swaps here
  const sourceToken = UNI; //USDT;
  // const destToken = WETH;
  const destToken = Ether.onChain(1);
  const amount = 0.8;

  const amountInWei = ethers.utils.parseUnits(
    amount.toString(),
    sourceToken.decimals
  );
  // expiry for permit & tx confirmation, 30 mins
  const expiry = Math.floor(Date.now() / 1000 + 1800);

  // check if we have approved enough amount
  // for PERMIT2 in source token contract
  const allowance = await getAllowanceAmount(
    sourceToken.address,
    PERMIT2_ADDRESS
  );
  console.log('current allowance:', allowance.toString());
  if (allowance.eq(0) || allowance.lt(amountInWei)) {
    // approve permit2 contract for source token
    // NOTE: amount is set to max here
    // NOTE: this will send out approve tx
    // and wait for confirmation
    console.log('sending approve tx to add more allowance');
    await approvePermit2Contract(
      sourceToken.address,
      ethers.constants.MaxInt256
    );
  }

  // allowance provider is part of permit2 sdk
  // using it to get nonce value of last permit
  // we signed for this source token
  const allowanceProvider = new AllowanceProvider(
    ethersProvider,
    PERMIT2_ADDRESS
  );

  // for allowance based transfer we can just use
  // next nonce value for permits.
  // for signature transfer probably it has to be
  // a prime number or something. checks uniswap docs.
  // const nonce = 1;
  const nonce = await allowanceProvider.getNonce(
    sourceToken.address,
    walletAddress,
    uniswapRouterAddress
  );
  console.log('nonce value:', nonce);

  
  // create permit with AllowanceTransfer
  const permit = {
    details: {
      token: sourceToken.address,
      amount: amountInWei,
      expiration: expiry,
      nonce
    },
    spender: uniswapRouterAddress,
    sigDeadline: expiry
  };
  const { domain, types, values } = AllowanceTransfer.getPermitData(
    permit,
    PERMIT2_ADDRESS,
    chainId
  );


  // create signature for permit
  const signature = await ethersSigner._signTypedData(domain, types, values);
  console.log('signature: ', signature);

  // NOTE: optionally verify the signature
  const address = ethers.utils.verifyTypedData(
    domain,
    types,
    values,
    signature
  );

  if (address !== walletAddress)
    throw new Error('signature verification failed');
  else console.log(`signature verified, signed by: ${address}`);

  // get swap route for tokens

  const route = await getSwapRoute(
    sourceToken,
    destToken,
    amountInWei,
    permit,
    signature
  );

  const txArguments = {
    data: route.methodParameters.calldata,
    to: uniswapRouterAddress,
    value: BigNumber.from(route.methodParameters.value),
    from: walletAddress,
    gasPrice: route.gasPriceWei,
    gasLimit: BigNumber.from('1000000')
  };
  // send out swap transaction
  const transaction = await ethersSigner.sendTransaction(txArguments);
  console.log('swap transaction', transaction.hash);
}

executeSwap(); // executes the V3 Sell only 
