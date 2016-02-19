//import React from 'react';

ReactDOM.render(
  <h1>Hello, world!</h1>,
  document.getElementById('example')
);
var play = (term) => {
  return 'play ' + term;
}
// 
var FlexBox = React.createClass({
    render: () => {
        return (<div>A Flexible Box</div>)
    }
});
ReactDOM.render(<FlexBox/>, document.getElementById('flex-box'));
console.log('test223')