import 'globalthis/polyfill';
import { Application, Geometry, Mesh, Shader } from './pixi.js';
import React from 'react';
import ReactDOM from 'react-dom/client';
import './css/index.css';
import TodoApp from './components/todo.jsx';
import reportWebVitals from './reportWebVitals';
import Sketch from "react-p5";
import * as THREE from 'three'
import Stats from 'three/examples/jsm/libs/stats.module'
import vertex from './shaders/mosaic/mosaic.vert';
import fragment from './shaders/mosaic/mosaic.frag';
const root = ReactDOM.createRoot(document.getElementById('root'));



root.render(
    <>
<TodoApp />
<footer>©2024 Ultra Degenerate Labs, No Rights Reserved</footer>
</>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
