/*
* @Author: python
* @Date:   2016-02-24 13:29:23
* @Last Modified by:   python
* @Last Modified time: 2016-02-24 15:14:45
*/

'use strict';
var Toy = React.createClass({
    getInitialState () {
        return {show: false}
    },
    render () {
        let stylesClose = {
            color: '#fff',
            backgroundColor:'#999',
            width: '100%',
            height: '30px',
            textAlign: 'center',
            WebkitTransition: 'height .3s ease-out',
                  transition: 'height .3s ease-out',
            },
            stylesOpen = Object.assign({}, stylesClose);
            stylesOpen = Object.assign(stylesOpen, {
                color: '#000',
                backgroundColor: '#eee',
                height: '300px'
            });

        return (<div
                 style={this.state.show ? stylesOpen: stylesClose}
                 // onTouchStart={this.handleTouchStart}
                 onClick={this.handleTouchStart}
                 >{this.state.show? 'close': 'open'}</div>)
    },
    handleTouchStart (e) {
        this.setState({show:!this.state.show})
    }
});ReactDOM.render(<Toy/>, document.getElementById('example'));