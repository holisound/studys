/*
Prefix & Tree
*/
const targetKeys = ['a', 'a-b', 'a-b-c', 'd', 'd-e-f', 'h-j-k', 'm', 'm-n', 'r-s-t', 'r-s-u', 'r-v']

function count(p){
  let cnt = 0
  for (let c of p) {
    if (c === '-')
      cnt++
  }
  return cnt
}

targetKeys.sort((a,b) => count(a)-count(b))

console.log(targetKeys)

const keys = []
for (let k of targetKeys) {
  let flag = 0, s = ''
  for (let c of k) {
    s += c
    if (keys.indexOf(s) !== -1) {
      flag = 1
      break;
    }
  }
  if (!flag) {
    keys.push(k)
  }
}
console.log(keys)
const res = {}
for (let path of keys){
  let node = res
  for (let step of path.split('-')) {
    node[step] = node[step] || {}
    node = node[step]
  }
}
console.log(res)
