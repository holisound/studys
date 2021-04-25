/*
html模板转换成vue格式的工具
输入：index.html 以及依赖的静态文件js, css等
输出: vue 中的 main.js 和 App.vue
*/
const fs = require('fs');

const jsdom = require("jsdom");
const process = require('process');
const args = require('minimist')(process.argv.slice(2))

fs.readFile(args.filepath, 'utf8' , (err, data) => {
  if (err) {
    console.error(err)
    return
  }
  // 抽取静态文件路径
  const dom = new jsdom.JSDOM(data);
  const $ = require('jquery')(dom.window)
  const elemScripts = $('script');
  console.log(elemScripts.eq(0).attr('src'))

})
