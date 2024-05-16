import Header from './Header.jsx';
import Dashboard from './Dashboard.jsx';
import Wallets from './Wallets.jsx';
import React, { Component } from 'react';

let curState = "Dashboard";



class TodoApp extends React.Component{

  constructor(props){
    super(props);
    this.changeState = this.changeState.bind(this);
  }

  components = {
      dashboard: Dashboard,
      wallets: Wallets
  };

  changeState(state){
    curState = state;
    this.forceUpdate();
  }



  render(){
    curState = curState == "" ? Header.HeaderContent[0].title : curState;
    let Component = this.components[this.props.tag || curState.charAt(0).toLowerCase() + curState.slice(1)];

    return (
        <>
        <Header changeState={this.changeState}></Header>
        {React.createElement(Component,null)}
        </>


    );
  }
};
export default TodoApp;
