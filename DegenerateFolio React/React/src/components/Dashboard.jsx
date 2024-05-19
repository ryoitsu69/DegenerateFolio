import '../css/Dashboard.css'
import '../css/Header.css'
import React, { Component } from 'react';

var socketReady = false;
var sorted = '';
var sortedTime = new Date("2019-01-01");
var sortCooldown = 200; // ms
var tokens = [];
var waiting = false;
var weeklyTimeframe = '1 H';
var weeklyLimit = 168;


const socket = new WebSocket("ws://192.168.50.252:13257");

socket.onopen = function () {
  socketReady = true;

  requestBalances();
}

socket.addEventListener("message", async (event) => {
//  constructor(name, price, holdings, value, domElement, h1, h24, d7, chart)
  let type = event.data.split('/')[0];
  let data = event.data.split('/')[1];
  if (type == 'balances'){
    let balances = JSON.parse(data);
    let totalValue = 0;
    document.getElementById("asset_wrap").innerHTML = "";
    for(let i = 0; i < balances.length; i++) {
      let price = balances[i].price != null ? round(balances[i].price,balances[i].decimals) : 0;
      let amount = balances[i].amount != null ? round(balances[i].amount,3) : 0;
      let value = round(price*amount,2);
      let name = balances[i].ticker;
      let token = new Token(name,price,amount,value);
      token.chart = [];
      token.fullname = balances[i].fullname != null ? balances[i].fullname : "";
      token.decimals = balances[i].decimals;
      token.h1Change = balances[i].h1Change;
      token.h24Change = balances[i].h24Change;
      token.d7Change = balances[i].d7Change;
      tokens.push(token);


      requestChart(name,0,weeklyTimeframe,weeklyLimit);


      totalValue+=parseFloat(value);
    }
    updateTotalValue(totalValue);
  }else if(type == 'updateAllBalances'){
      let balances = JSON.parse(data);
      let totalValue = 0;
      for(let i = 0; i < balances.length; i++) {
        let token = getTokenByName(balances[i].ticker);
        token.price = balances[i].price != null ? round(balances[i].price,5) : 0;
        token.holdings = balances[i].amount != null ? round(balances[i].amount,4) : 0;
        token.value = round(token.price*token.holdings,balances[i].decimals);
        token.h1Change = balances[i].h1Change;
        token.h24Change = balances[i].h24Change;
        token.d7Change = balances[i].d7Change;
        totalValue+=token.value;
        updateToken(token.name,'price',token.price);
        updateToken(token.name,'holdings',token.holdings);
        updateToken(token.name,'value',token.value);
        updateToken(token.name,'h1',token.h1Change);
        updateToken(token.name,'h24',token.h24Change);
        updateToken(token.name,'d7',token.d7Change);
        //recalculatePercentages(token.name,false);
      }
      updateTotalValue(totalValue);

  }else if(type == 'chart7D'){
    let token = getTokenByName(event.data.split('/')[1]);
    let priceLastHour,priceLastDay,priceLastWeek;
    var h1,h24,d7;
    var h1Class,h24Class,d7Class;
    token.chart = [];
    let chart = JSON.parse(event.data.split('/')[2]);https://ethereum.org/en/

    if(chart)
    {
      for(var i in chart.open){
        token.chart.push([i, chart.open[i]]);
      }

      //let percentages = recalculatePercentages(token.name, true);
      //console.log(percentages);
      //h1 = percentages[0];
      //h24 = percentages[1];
      //d7 = percentages[2];

    }else{
      //h1 = "-";
      //h24 = "-";
      //d7 = "-";
    }

    h1Class = token.h1Change != "-" ? (token.h1Change > 0 ? 'positive' : (token.h1Change==0 ? "neutral" : 'negative')) : 'undefined';
    h24Class = token.h24Change != "-" ? (token.h24Change > 0 ? 'positive' : (token.h24Change==0 ? "neutral" : 'negative')) : 'undefined';
    d7Class = token.d7Change != "-" ? (token.d7Change > 0 ? 'positive' : (token.d7Change==0 ? "neutral" : 'negative')) : 'undefined';
    let html ="<div id='"+token.name+"' class='asset'><img src='images/logo/"+token.name+".png'"+" class='tokenLogo' ><span class='nameWrap'><span class='fullname'>"+token.fullname+"</span><span class='name'>("+token.name+")</span></span> <span class='h1 "+h1Class+"'>"+token.h1Change+"</span><span class='h24 "+h24Class+"'>"+token.h24Change+"</span><span class='d7 "+d7Class+"'>"+token.d7Change+"</span> <span class='price'>"+token.price+"</span><span class='holdings'>"+token.holdings+"</span> <span class='value'>"+token.value+"</span><canvas class='canvas'></canvas></div>";
    const node = document.createRange().createContextualFragment(html);
    document.getElementById("asset_wrap").appendChild(node);

    draw7dChart(token,true);

  }else if(type == 'update'){
    let token = getTokenByName(event.data.split('/')[1]);
    let update = JSON.parse(event.data.split('/')[2]);
    console.log("update: "+update.open);
    for(var i in update.open){
      token.chart.unshift([i, update.open[i]]);
    }
    token.chart.pop();
    draw7dChart(token);
  }else if(type == 'shaders'){
    var shaders = JSON.parse(data);
    document.getElementById("shaders-content").innerHTML = "";
    for(var i=0;i<shaders.length;i++){
      console.log(shaders[i]);
      var node = document.createElement('a');
      node.setAttribute('class','shader');
      node.innerHTML = shaders[i];
      document.getElementById("shaders-content").appendChild(node);
    }
  }

});

function getMinFrom7dChart(token){
  let min = Infinity;
  for(let i=0;i<token.chart.length;i++){
    min = token.chart[i][1] < min ? token.chart[i][1] : min;
  }
  return min;
}

function getMaxFrom7dChart(token){
  let max = -Infinity;
  for(let i=0;i<token.chart.length;i++){
    max = token.chart[i][1] > max ? token.chart[i][1] : max;
  }
  return max;
}

function draw7dChart(token,isNew){
  let canvas = document.getElementById(token.name).getElementsByClassName("canvas")[0];
  let context = canvas.getContext("2d");
  canvas.style.height='10%';
  if(isNew){
    canvas.width  = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight*0.3;
  }
  context.save();

  // Use the identity matrix while clearing the canvas
  context.setTransform(1, 0, 0, 1, 0, 0);
  context.clearRect(0, 0, canvas.width, canvas.height);

  // Restore the transform
  context.restore();

  if(!isEmpty(token.chart)){
    let topOffset = 0.9; //10%
    let bottomOffset = 0.9;
    let height1p = canvas.height/100;
    let width1p = canvas.width/100;
    let candlesAmount = token.chart.length;
    let min = getMinFrom7dChart(token);
    let max = getMaxFrom7dChart(token);
    let open = token.chart[weeklyLimit-1][1];
    let close = token.chart[0][1];
    let height = max-min;

    context.lineWidth = 3;
    context.strokeStyle = close > open ? "green" : "red";

    context.beginPath();
    context.moveTo(0,canvas.height-((open-min)/height)*canvas.height);
    for(let i=0;i<weeklyLimit;i++){
      context.lineTo((canvas.width/candlesAmount)*i,canvas.height-(((token.chart[weeklyLimit-i-1][1]-min)/height)*canvas.height));
    }
    context.stroke();
    context.closePath();
  }
}

function isEmpty(value) {
  for (let prop in value) {
    if (value.hasOwnProperty(prop)) return false;
  }
  return true;
}

function recalculatePercentages(tokenName, init){

  let token = getTokenByName(tokenName);

  if(!isEmpty(token.chart)){
    let priceLastHour = token.chart[parseInt(weeklyLimit/168)][1];
    let priceLastDay = token.chart[parseInt(weeklyLimit/7)][1];
    let priceLastWeek = token.chart[weeklyLimit-1][1];
    let h1 = round(((token.price/priceLastHour)-1)*100,2);
    let h24 = round(((token.price/priceLastDay)-1)*100,2);
    let d7 = round(((token.price/priceLastWeek)-1)*100,2);

    if(init == false){
      updateToken(token.name,'h1',h1);
      updateToken(token.name,'h24',h24);
      updateToken(token.name,'d7',d7);
    }
    return [h1,h24,d7];
  }

  return ["-","-","-"];

}

function updateTotalValue(value){
  console.log("yo: "+value)
  document.getElementById("total_value").innerHTML=round(value,3)+"$";
}

function getTokenByName(name){
  for (var i=0;i<tokens.length;i++){
    if(tokens[i].name == name){
      return tokens[i];
    }
  }
}

function round(x,to){
  return parseFloat(Number.parseFloat(x).toFixed(to));
}

function requestChart(token,has,timeframe,limit){
  request('chart/'+token+'/'+has+'/'+timeframe+'/'+limit);
}

function request(message){
  if(socketReady){
    socket.send(message);
  }else{
    console.log("Socket is not ready yet");
  }
}

function requestBalances() {
  request('getAllBalances/');
}

function updateToken(tokenName,attribute,value){
  document.getElementById(tokenName).getElementsByClassName(attribute)[0].innerHTML = value;
}

function sort(how){

  if((new Date().getTime() - sortedTime.getTime()) > sortCooldown)
  {
    sortedTime = new Date();

    let assets = document.getElementsByClassName('asset');
    let assetWrap = document.querySelector("#asset_wrap");
    let swapped;
    let order = false;

    const reverse = () => {
      for (let i = 0; i <= assets.length-1; i++) {
          assetWrap.appendChild(assets[assets.length-1-i]);
      }
    }
    console.log(how);
    if(how == 'name'){
      if(sorted != 'name'){
        sorted = 'name';
        for (let i = 0; i < assets.length; i++) {
          swapped = false;
          for (let ii = 0; ii < assets.length-i-1; ii++) {
            //compare 1st character
            if(assets[ii].getElementsByClassName('nameWrap')[0].getElementsByClassName('name')[0].innerHTML.charCodeAt(1) > assets[ii+1].getElementsByClassName('nameWrap')[0].getElementsByClassName('name')[0].innerHTML.charCodeAt(1)){
              assets[ii+1].after(assets[ii]);

            }
          }
        }
      }else{
        reverse.call();
      }
    }else if(how == 'h1'){
      if(sorted != 'h1'){
        sorted = 'h1';
        for (let i = 0; i < assets.length; i++) {
          swapped = false;
          for (let ii = 0; ii < assets.length-1; ii++) {
            //compare 1st character
            let cur = assets[ii].getElementsByClassName('h1')[0].innerHTML != "-" ? parseFloat(assets[ii].getElementsByClassName('h1')[0].innerHTML) : -Infinity;
            let next = parseFloat(assets[ii+1].getElementsByClassName('h1')[0].innerHTML);
            if(cur < next){
              assets[ii+1].after(assets[ii]);
            }
          }
        }
      }else{
      }
    }else if(how == 'h24'){
      if(sorted != 'h24'){
        sorted = 'h24';
        for (let i = 0; i < assets.length; i++) {
          swapped = false;
          for (let ii = 0; ii < assets.length-1; ii++) {
            //compare 1st character
            let cur = assets[ii].getElementsByClassName('h24')[0].innerHTML != "-" ? parseFloat(assets[ii].getElementsByClassName('h24')[0].innerHTML) : -Infinity;
            let next = parseFloat(assets[ii+1].getElementsByClassName('h24')[0].innerHTML);
            if(cur < next){
              assets[ii+1].after(assets[ii]);
            }
          }
        }
      }else{
        reverse.call();
      }
    }else if(how == 'd7'){
      if(sorted != 'd7'){
        sorted = 'd7';
        for (let i = 0; i < assets.length; i++) {
          swapped = false;
          for (let ii = 0; ii < assets.length-1; ii++) {
            //compare 1st character
            let cur = assets[ii].getElementsByClassName('d7')[0].innerHTML != "-" ? parseFloat(assets[ii].getElementsByClassName('d7')[0].innerHTML) : -Infinity;
            let next = parseFloat(assets[ii+1].getElementsByClassName('d7')[0].innerHTML);
            if(cur < next){
              assets[ii+1].after(assets[ii]);
            }
          }
        }
      }else{
        reverse.call();
      }
    }else if(how == 'price'){
      if(sorted != 'price'){
        sorted = 'price';
        for (let i = 0; i < assets.length; i++) {
          swapped = false;
          for (let ii = 0; ii < assets.length-1; ii++) {
            //compare 1st character
            if(parseFloat(assets[ii].getElementsByClassName('price')[0].innerHTML) < parseFloat(assets[ii+1].getElementsByClassName('price')[0].innerHTML)){
              assets[ii+1].after(assets[ii]);
            }
          }
        }<canvas class="canvas"></canvas>
      }else{
        reverse.call();
      }
    }else if(how == 'holdings'){
      if(sorted != 'holdings'){
        sorted = 'holdings';
        for (let i = 0; i < assets.length; i++) {
          swapped = false;
          for (let ii = 0; ii < assets.length-1; ii++) {
            //compare 1st character
            if(parseFloat(assets[ii].getElementsByClassName('holdings')[0].innerHTML) < parseFloat(assets[ii+1].getElementsByClassName('holdings')[0].innerHTML)){
              assets[ii+1].after(assets[ii]);
            }
          }
        }
      }else{
        reverse.call();
      }
    }else if(how == 'value'){
      if(sorted != 'value'){
        sorted = 'value';
        for (let i = 0; i < assets.length; i++) {
          swapped = false;
          for (let ii = 0; ii < assets.length-1; ii++) {
            if(parseFloat(assets[ii].getElementsByClassName('value')[0].innerHTML) < parseFloat(assets[ii+1].getElementsByClassName('value')[0].innerHTML)){
              assets[ii+1].after(assets[ii]);
            }
          }
        }
      }else{
        reverse.call();
      }
    }
  }
}

class Token{
  constructor(name, price, holdings, value, domElement, h1, h24, d7, chart, fullname, decimals,h1Change,h24Change,d7Change){
    this.name = name;
    this.h1 = h1;
    this.h24 = h24;
    this.d7 = d7;
    this.price = price;
    this.holdings = holdings;
    this.value = value;
    this.chart = chart;
    this.domElement = domElement;
    this.h1Change = h1Change;
    this.h24Change = h24Change;
    this.d7Change = d7Change;
  }
}

class Dashboard extends React.Component{

  constructor(props){
    super(props);
  }

  render(){

    return (
      <>
      <div id="content_wrap">
        <div id='accounts_wrap'>testttt</div>
        <div id="assets_wrap">
          <div id='total_value'>1000$</div>
          <div class='label'><span>Assets</span></div>
          <div id='asset_table_rows'>
          <span class='nameWrap'><span class='fullname'></span><span class='name' onClick={() => sort('name')}>Name</span></span> <span class='h1' onClick={() => sort('h1')}>1h%</span><span class='h24' onClick={() => sort('h24')}>24h%</span><span class='d7' onClick={() => sort('d7')}>7d%</span> <span class='price' onClick={() => sort('price')}>Price</span> <span class='holdings' onClick={() => sort('holdings')}>Holdings</span> <span class='value' onClick={() => sort('value')}>Value</span><span class='weeklyCHart'>Last 7 Days</span>
          </div>
          <div id='asset_wrap'>

          </div>
        </div>
      </div>
      </>
    );

  }
};
export default Dashboard;


