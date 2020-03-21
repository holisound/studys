const isArray = require('lodash/isArray');
const toPlainObject = require('lodash/toPlainObject');
const sample = {
    a: [1,2],
    b: {c: [3,4]}
}
const result=[]
function dfs(data){
    if (isArray(data)){
        for (let i of data){
            result.push(i)
        }
        return;
    }
    for (let k in data){
        dfs(data[k])
    }
}
dfs(sample)
console.log(result)

function bfs(data) {
    const que = Object.values(data)
    let res = []
    while (que.length !== 0) {
        const node = que.shift();
        if (isArray(node)){
            res = res.concat(node)
        } else {
            for (let k in node) {
                que.push(node[k])
            }
        }
    }
    return res;
}


console.log(bfs(sample));