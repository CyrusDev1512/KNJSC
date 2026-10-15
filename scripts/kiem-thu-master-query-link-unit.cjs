/* TL-109: link mang bộ lọc lưới (Thống kê, Tải Excel) — chạy chính `navigate` cắt từ master-grid.js với DOM giả. */
const assert=require('node:assert/strict'),fs=require('fs'),vm=require('vm');
const src=fs.readFileSync(process.argv[2]||require.resolve('../app/static/js/master-grid.js'),'utf8');
const a=src.indexOf('  async function navigate('),b=src.indexOf('  // Panel Bộ lọc tải khi người dùng mở lần đầu');
assert(a>0&&b>a,'Không cắt được navigate khỏi master-grid.js');
const thongKe={href:'http://h/thong-ke/?nguon=van_don',dataset:{queryBase:'nguon=van_don'}};
const excel={href:'http://h/bang-tinh/van_don/xuat/?',dataset:{}};
const ctx={URL,URLSearchParams,config:{filterUrl:'/bang-tinh/van_don/'},history:{pushState(){}},
  document:{querySelectorAll:()=>[thongKe,excel]},viewport:{},state:{},reader:{},
  $:id=>({elements:{tim:{}},dataset:{}}),dirty:()=>false,refreshSoft(){},syncScopeButtons(){},repaint(){},invalidate(){},loadFilters(){}};
vm.createContext(ctx);vm.runInContext('let query=new URLSearchParams();'+src.slice(a,b)+';globalThis.navigate=navigate;',ctx);
const q=h=>new URL(h).searchParams;
(async()=>{
  await ctx.navigate(new URLSearchParams('cua_toi=1&tim=Kh%C3%A1ch+0&f_quoc_gia__trong=US&f_quoc_gia__trong=CA'));
  assert.equal(q(thongKe.href).get('nguon'),'van_don','Tôi/Tìm/lọc cột xoá mất nguon của link Thống kê');
  assert.equal(q(thongKe.href).get('cua_toi'),'1');assert.equal(q(thongKe.href).get('tim'),'Khách 0');
  assert.deepEqual(q(thongKe.href).getAll('f_quoc_gia__trong'),['US','CA']);
  assert.equal(q(excel.href).get('nguon'),null,'Tải Excel không có phần riêng — giữ như cũ');assert.equal(q(excel.href).get('cua_toi'),'1');
  await ctx.navigate(new URLSearchParams('sap=ma_don&chieu=giam'),true,true);   // bấm tiêu đề cột (chỉ đổi thứ tự)
  assert.equal(q(thongKe.href).get('nguon'),'van_don');assert.equal(q(thongKe.href).get('cua_toi'),null);
  await ctx.navigate(new URLSearchParams(),false);                              // bỏ hết lọc
  assert.equal(thongKe.href,'http://h/thong-ke/?nguon=van_don');assert.equal(excel.href,'http://h/bang-tinh/van_don/xuat/');
  await ctx.navigate(new URLSearchParams('nguon=khac&tim=a'));                  // URL lưới có nguon lạ không đè nguồn của link
  assert.deepEqual(q(thongKe.href).getAll('nguon'),['van_don']);
  console.log('PASS: link Thống kê giữ nguon sau Tôi/Tìm/lọc/sắp xếp; Tải Excel như cũ');
})().catch(e=>{console.error(e.message);process.exitCode=1;});
