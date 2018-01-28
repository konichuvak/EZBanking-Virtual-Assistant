import React from 'react';

const ResponseButton = ({pressResponse, button}) => (
    <button type="submit" className="responseButton" onClick={() => pressResponse(button.title, button.payload)} >{button.title}</button>
);

export default ResponseButton;