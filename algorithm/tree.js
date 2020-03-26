const targetKeys = ['a', 'a-b', 'a-b-c', 'd', 'd-e-f', 'h-j-k', 'm', 'm-n', 'r-s-t', 'r-s-u']
const map = {}

function count(p){
  let cnt = 0
  for (let c of p) {
    if (c === '-')
      cnt++
  }
  return cnt
}

for (let k of targetKeys) {
  const [ root ] = k.split('-');
  if (map[root]){
    const [p] = map[root];
    const ck = count(k), cp = count(p) 
    if (ck < cp) {
      map[root] = [k]
    } else if (ck == cp){
      map[root].push(k);
    }
  } else {
    map[root] = [k]
  }
}
console.log(map)
/*
{
  a: [ 'a' ],
  d: [ 'd' ],
  h: [ 'h-j-k' ],
  m: [ 'm' ],
  r: [ 'r-s-t', 'r-s-u' ]
}
*/
const res = {}
for (let path of Object.values(map)){
  for (let p of path){
    let node = res
    for (let step of p.split('-')) {
      node[step] = node[step] || {}
      node = node[step]
    }
  }
}
console.log(res)
/*
{
  a: {},
  d: {},
  h: { j: { k: {} } },
  m: {},
  r: { s: { t: {}, u: {} } }
}
*/
