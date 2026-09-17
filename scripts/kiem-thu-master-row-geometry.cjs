const assert=require('assert/strict'),Geometry=require('../app/static/js/master-row-geometry.js');
const g=new Geometry(300000);assert.equal(g.top(300000),8400000);assert.equal(g.tree.size,0);
g.set(0,160);g.set(99,400);g.set(100,120);g.set(299999,300);
assert.equal(g.top(1),160);assert.equal(g.top(100),28*100+132+372);assert.equal(g.at(159),0);assert.equal(g.at(160),1);
assert.equal(g.at(g.top(100)),100);assert.equal(g.at(g.top(300000)-1),299999);assert.equal(g.at(-100),0);
assert(g.tree.size<80);g.set(99,28);assert.equal(g.top(100),28*100+132);
// Đối chiếu với tổng tuyến tính trên dữ liệu nhỏ gồm nhiều lần đổi cùng hàng.
let seed=42;const rnd=()=>{seed=(seed*1664525+1013904223)>>>0;return seed;};
const small=new Geometry(500),expected=Array(500).fill(28);
for(let n=0;n<1000;n++){const i=rnd()%500,h=28+rnd()%373;small.set(i,h);expected[i]=h;}
let y=0;for(let i=0;i<500;i++){assert.equal(small.top(i),y);assert.equal(small.at(y),i);assert.equal(small.at(y+expected[i]-1),i);y+=expected[i];}assert.equal(small.top(500),y);
g.reset(0);assert.equal(g.at(100),0);assert.equal(g.top(5),0);assert.equal(g.tree.size,0);
console.log('PASS row geometry: boundaries, sparse 300k, 1000 updates, reset');
