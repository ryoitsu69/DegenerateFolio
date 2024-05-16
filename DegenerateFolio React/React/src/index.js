import React from 'react';
import ReactDOM from 'react-dom/client';
import ShadertoyReact from "shadertoy-react";
import './css/index.css';
import Cookies from 'js-cookie'
import TodoApp from './components/todo.jsx';
import reportWebVitals from './reportWebVitals';
var fragmentShader = require('./shaders/'+(Cookies.get('shader') !== undefined ? Cookies.get('shader') : 'exit_the_matrix')+'/'+(Cookies.get('shader') !== undefined ? Cookies.get('shader') : 'exit_the_matrix')+'.js');

const root = ReactDOM.createRoot(document.getElementById('root'));


/* function setFrag(){
    fragmentShader = require('./shaders/cyber_fuji/cyber_fuji.js');
    const canvas = document.getElementById("root").getElementsByTagName('canvas')[0];
    canvas.remove();
    React.createElement(ShadertoyReact, {fs:fragmentShader});
    console.log("sup");
}
*/

root.render(
    <>
    <ShadertoyReact fs={fragmentShader} />
<TodoApp />
<footer>©2024 Ultra Degenerate Labs, No Rights Reserved</footer>
</>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
