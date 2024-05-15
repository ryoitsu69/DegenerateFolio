import '../css/Header.css'
import React, { Component } from 'react';

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
      </header>
    );
  }
};
export default Header;
