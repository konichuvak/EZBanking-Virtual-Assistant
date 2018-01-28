import React from 'react';
import ReactDOM from 'react-dom';
import './App.css';
import Message from './Message.js';
import ResponseButton from './ResponseButton.js';

class Chatroom extends React.Component {
    constructor(props) {
        super(props);

        //const sock = new WebSocket('ws://d072764.corp.ads:9001/'); //prod
        const sock = new WebSocket('ws://10.0.1.8:10000'); //dev

        sock.onopen = () => {
            console.log('connection open');
        };

        sock.onmessage = async e => { // Need async for sleep(); see https://stackoverflow.com/questions/951021/what-is-the-javascript-version-of-sleep
            var payload = JSON.parse(e.data);
            var responses = payload.responses;
            for (var i = 0; i < responses.length; i++) {
                var chat_response = responses[i];
                console.log(chat_response);
                await this.sleep(500 + chat_response.response.length * 5); // simulate bot typing
                var innerHTML = {__html: chat_response.response};
                this.setState({
                    chats: this.state.chats.concat([{
                        username: chat_response.sender,
                        content: <div dangerouslySetInnerHTML={innerHTML} />, // Read more: https://reactjs.org/docs/dom-elements.html
                        img: "https://i.imgur.com/KJJ5w8D.png",
                }]),
                }, () => {
                    ReactDOM.findDOMNode(this.refs.msg).value = "";
                });
            }
            this.setState({
                buttons: payload.buttons
            })

        };

        sock.onclose = () => {
          console.log('close');
        };

        this.state = {
            chats: [{
                username: "EZ Chatbot",
                content: <p>Hi! I am EZ Banking personal assistant. Please enter your account number.</p>,
                img: "https://i.imgur.com/KJJ5w8D.png",
            }],
            actions: {ws: sock},
            buttons: []
        };

        this.submitMessage = this.submitMessage.bind(this);
        this.pressResponseButton = this.pressResponseButton.bind(this);
    }

    componentDidMount() {
        this.scrollToBot();
    }

    componentDidUpdate() {
        this.scrollToBot();
    }

    scrollToBot() {
        ReactDOM.findDOMNode(this.refs.chats).scrollTop = ReactDOM.findDOMNode(this.refs.chats).scrollHeight;
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    submitMessage(e) {
        e.preventDefault();
        if (this.refs.msg.value.length > 0 && this.state.buttons.length === 0) { //don't allow empty input or input when response buttons are available
            this.state.actions.ws.send(this.refs.msg.value);
            this.setState({
                chats: this.state.chats.concat([
                {
                    username: "Client",
                    content: <p>{ReactDOM.findDOMNode(this.refs.msg).value}</p>,
                    img: "http://i.imgur.com/Tj5DGiO.jpg",
                }
                ])
            }, () => {
                ReactDOM.findDOMNode(this.refs.msg).value = "";
            });
        }
    }

    submitMicSignal(e) {
        e.preventDefault();
        this.state.actions.ws.send(this.refs.mic.value);
    }

    pressResponseButton(message, payload) {
        this.state.actions.ws.send(payload);
        this.setState({
                chats: this.state.chats.concat([
                {
                    username: "Client",
                    content: <p>{message}</p>,
                    img: "http://i.imgur.com/Tj5DGiO.jpg",
                }
                ])
            }, () => {
                ReactDOM.findDOMNode(this.refs.msg).value = "";
            });
    }

    render() {
        let username = "Client";
        let chats  = this.state.chats;
        let buttons = this.state.buttons;
        let pressResponse = this.pressResponseButton;
        let chatsHeight = () => { return (buttons.length > 0 ? 495 : 540) } // make it seem like buttons push chat messages up when they appear
        let ShowButtons = () => { return (buttons.length > 0 ?  //show buttons if present in this state
            buttons.map(button => <ResponseButton pressResponse={pressResponse} button={button} key={button.id}/>) : null) }

        return (
            <div className="chatroom" >
                <h3>EZ Banking Personal Assistant</h3>
                <ul className="chats" ref="chats" style={{height : chatsHeight()} }>
                    {
                        chats.map(chat => 
                          <Message chat={chat} user={username} />
                        )
                    }
                </ul>
                <div className="responseButtons" ref="buttons">
                    <ShowButtons buttons/>
                </div>
                <div className="userInput">
                    <form className="input" onSubmit={(e) => this.submitMessage(e)}>
                        <input type="text" ref="msg" />
                        <input type="submit" value="Send" />
                    </form>
                    <form className="mic" onSubmit={(e) => this.submitMicSignal(e)}>
                        <input type="text" type="hidden" value="*mic_on*" ref="mic"/>
                        <input type="submit" value="🎤" />
                    </form>
                </div>
            </div>
        );
    }
}
export default Chatroom;
