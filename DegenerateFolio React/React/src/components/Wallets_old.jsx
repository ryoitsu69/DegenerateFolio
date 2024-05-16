import React, { Component } from 'react';
const {Web3} = require('web3');
const { ApiPromise, WsProvider } = require('@polkadot/api');
const { Builder, Browser, By, Key, until } = require('selenium-webdriver');

const cosmosAddress = "cosmos1d6j4xs7l55s2lsy2vqdalj25ef9rj72y05ne0m";
const cosmosApi = "https://cosmos.api.explorers.guru/api/accounts/"+cosmosAddress+"/balance";

const seiAddress = "sei1nk77dnzkesy2dju74n3lj4ru0h8pac0hq6kaz9";
const seiApi = "https://sei.api.explorers.guru/api/accounts/"+seiAddress+"/balance";


const ethRPC = new Web3(new Web3.providers.HttpProvider("https://mainnet.infura.io/v3/ff42bd19bf6e4ca9a401fbf0a8a36f15"));
const optRPC = new Web3(new Web3.providers.HttpProvider("https://optimism-mainnet.infura.io/v3/ff42bd19bf6e4ca9a401fbf0a8a36f15"));
const arbRPC = new Web3(new Web3.providers.HttpProvider("https://arbitrum-mainnet.infura.io/v3/ff42bd19bf6e4ca9a401fbf0a8a36f15"));
const starkRPC = new Web3(new Web3.providers.HttpProvider("https://starknet-mainnet.g.alchemy.com/v2/eDTvRiR7UGc1vibC0sQviDBnqHmlCnKz"));
const bscRPC = new Web3(new Web3.providers.HttpProvider("https://bnb-mainnet.g.alchemy.com/v2/Wflh86IAxtX-p7SFc--_YxhsIINWRfPR"));

/*const provider =new WsProvider('wss://rpc.polkadot.io');
const dotApi = await ApiPromise.create({provider});
const chain = await dotApi.rpc.system.chain();
const dotAddr = "13gBrKGMhttuNjywbmEfK5NFeNbHpbQGbJtFVRMmUWHaSNZf";
  const [{ nonce: accountNonce }, now, validators, locked] = await Promise.all([
    dotApi.query.system.account(dotAddr),
    dotApi.query.timestamp.now(),
    dotApi.query.session.validators(),
    dotApi.query.balances.locks(dotAddr)
  ]);
*/



class Chain{
  constructor(rpc, tokenName, mainTokenAddress){
    this.rpc = rpc;
    this.tokenName = tokenName;
    this.mainTokenAddress = mainTokenAddress;
  }
}

class balanceEntry{
  constructor(tokenName, amount, chain, address, price){
    this.tokenName = tokenName;
    this.amount = amount;
    this.chain = chain;
    this.address = address;
    this.price = price;
  }
}

// The minimum ABI required to get the ERC20 Token balance
const minABI = [
  // balanceOf
  {
    constant: true,
    inputs: [{ name: '_owner', type: 'address' }],
    name: 'balanceOf',
    outputs: [{ name: 'balance', type: 'uint256'}],
    type: 'function',
  },
  // decimals
  {
    "constant":true,
    "inputs":[],
    "name":"decimals",
    "outputs":[{"name":"","type":"uint8"}],
    "type":"function"
  }

];

class Wallets extends React.Component{



  constructor(props){
    super(props);
    this.chains = new Map();
    this.balances = [];
    this.chains.set('ETH', new Chain(ethRPC, 'ETH', null));
    this.chains.set('OPT', new Chain(optRPC, 'OPT', "0x4200000000000000000000000000000000000042"));
    this.chains.set('ARB', new Chain(arbRPC, 'ARB', "0x912ce59144191c1204e64559fe8253a0e49e6548"));
    this.chains.set('STRK', new Chain(starkRPC, 'STRK', '0x04718f5a0Fc34cC1AF16A1cdee98fFB20C31f5cD61D6Ab07201858f4287c938D'));
    this.chains.set('BSC', new Chain(bscRPC, 'BNB', null));
    this.getBalanceGasToken.bind(this);
    this.getERC20Balance.bind(this);
    this.getCosmosBalance.bind(this);
  }

    async callApi(url) {
      const api_call = await fetch(url);
      const data = await api_call.json();
      return data;
    }

  async getCosmosBalance(){
    let data = await this.callApi(cosmosApi);
    let total = (data.delegated.amount+data.reward.amount+data.spendable.amount).toString().split(".")[0];
    let decimals = total.slice(-6);
    let whole = total.split(decimals)[0];
    let result = parseFloat(whole+"."+decimals);
    this.balances.push(new balanceEntry("ATOM",result,"COSMOS",cosmosAddress,0.5));
    console.log("Total Atom = "+whole+"."+decimals);
  }

  async getSeiBalance(){
    let data = await this.callApi(seiApi);
    let total = (data.delegated.amount+data.reward.amount+data.spendable.amount).toString().split(".")[0];
    let decimals = total.slice(-6);
    let whole = total.split(decimals)[0];
    let result = parseFloat(whole+"."+decimals);
    this.balances.push(new balanceEntry("SEI",result,"SEI",seiAddress,0.5));
    console.log("Total Sei = "+result);
  }

  async getERC20Balance(wallet,tokenAddr,chain,tokenName){
    const contract = new chain.rpc.eth.Contract(minABI, tokenAddr);
    let result = await contract.methods.balanceOf(wallet).call();
    result = this.fromWei(result);
    this.balances.push(new balanceEntry(tokenName,result,chain.tokenName,wallet,0.5));
    console.log(this.balances);
  }

  getBalanceGasToken(address, chain){
    chain.rpc.eth.getBalance(address).then((balance) => console.log(bscRPC.utils.fromWei(balance, "ether") + chain.tokenName));
  }

  fromWei(balance){
    let decimals = balance.toString().slice(-18);
    let whole = balance.toString().split(decimals)[0];
    return parseFloat(whole+"."+decimals);
  }


  render(){
{this.getSeiBalance(); this.getCosmosBalance(); this.getERC20Balance("0x4AE673F8898408d39966dE7ECC0BD7128b4b912E","0x4200000000000000000000000000000000000042", this.chains.get('OPT'), "OPT");}
  {this.getERC20Balance("0x4AE673F8898408d39966dE7ECC0BD7128b4b912E","0x912ce59144191c1204e64559fe8253a0e49e6548", this.chains.get('ARB'), "ARB");}
    return (
      <div></div>

    );
  }
};
export default Wallets;
