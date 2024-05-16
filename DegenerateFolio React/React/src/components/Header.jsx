import '../css/Header.css'
import Cookies from 'js-cookie'
import React, { Component } from 'react';

document.addEventListener('click', function(e) {
  e = e || window.event;
  var target = e.target || e.srcElement,
  text = target.textContent || target.innerText;
  if(target.getAttribute('class') == 'shader'){
    console.log(text);
    Cookies.set('shader',text);
    window.location.reload();
  }
}, false);

class NavigationUnit{
  constructor(title, subMenu){
    this.title = title;
    this.subMenu = subMenu;
  }




}

const HeaderContent = [new NavigationUnit("Dashboard",null), new NavigationUnit("Wallets",null)];

class Header extends React.Component{
  constructor(props){
    super(props);
  }

  render(){

    return (
      <header>
      {HeaderContent.map((unit) => (<div onClick={() => this.props.changeState(unit.title)} key={unit.title} className="navUnit">{unit.title}</div>))}
      <div id="shadersChoice">
      <button class="shadersButton">Shaders</button>
      <div id="shaders-content">
      </div>
      </div>
      </header>
    );
  }
};
export default Header;
