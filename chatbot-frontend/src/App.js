// code used from here (with modifications): https://medium.freecodecamp.org/lets-build-a-react-chatroom-component-ed353982d826 and https://github.com/WigoHunter/react-chatapp
// https://www.youtube.com/watch?v=82GDkSFmEJc was useful for setting up ws client connections

import React, { Component } from 'react';
import './App.css';


import Chatroom from './Chatroom.js';
 
class App extends Component {
  render() {
    return (
      <div className="App">
        <Chatroom /*{... this.state }*/ />
      </div>
    );
  }
}

export default App;
