/* Hình học hàng biến thiên: chỉ lưu phần chênh với 28 px, không cấp mảng theo tổng đơn. */
((scope) => {
  'use strict';
  class MasterRowGeometry {
    // Trần chiều cao một dòng — một chỗ duy nhất; master-grid.js đọc `KNJSCRowGeometry.MAX`.
    // 2000 px thay cho 400 từ 23.09.2026 (AC-11.44): dòng phải giãn đủ cao cho một ghi chú
    // dài, mà vẫn giữ tổng chiều cao bảng trong ngưỡng trình duyệt chịu được.
    static MAX=2000;
    constructor(total=0) { this.reset(total); }
    reset(total) { this.total=Math.max(0,Math.floor(total));this.tree=new Map();this.heights=new Map(); }
    // Đổi tổng số hàng mà giữ chiều cao đã đặt: cây Fenwick phụ thuộc tổng, nên dựng lại
    // từ danh sách hàng khác 28 px (thường rất ít) thay vì xoá sạch như reset().
    resize(total) { const kept=[...this.heights];this.reset(total);for(const [index,height] of kept)this.set(index,height); }
    height(index) { return this.heights.get(index)||28; }
    set(index,height) {
      if(index<0||index>=this.total)return;
      height=Math.max(28,Math.min(MasterRowGeometry.MAX,Math.round(height)));
      const delta=height-this.height(index);if(!delta)return;
      if(height===28)this.heights.delete(index);else this.heights.set(index,height);
      for(let p=index+1;p<=this.total;p+=p&-p){const sum=(this.tree.get(p)||0)+delta;if(sum)this.tree.set(p,sum);else this.tree.delete(p);}
    }
    top(index) {
      index=Math.max(0,Math.min(this.total,Math.floor(index)));let sum=index*28;
      for(let p=index;p>0;p-=p&-p)sum+=this.tree.get(p)||0;
      return sum;
    }
    at(pixel) {
      if(!this.total)return 0;
      let low=0,high=this.total;
      while(low<high){const mid=Math.floor((low+high)/2);if(this.top(mid+1)<=pixel)low=mid+1;else high=mid;}
      return Math.min(this.total-1,low);
    }
  }
  if(typeof module!=='undefined'&&module.exports)module.exports=MasterRowGeometry;
  else scope.KNJSCRowGeometry=MasterRowGeometry;
})(globalThis);
