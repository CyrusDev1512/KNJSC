// Chỉ chạy cùng MARKET_CURRENCY_BROWSER trên PostgreSQL test riêng.
const {chromium} = require('playwright');
const fs = require('fs');
const assert = require('assert/strict');
const folder = 'storage/market-currency', base = 'http://127.0.0.1:8865';
const result = {ok:false, cases:[], errors:[]};

(async () => {
  const ready = JSON.parse(fs.readFileSync(`${folder}/browser-ready.json`));
  const browser = await chromium.launch({channel:'chrome', headless:true});
  try {
    for (const [index,width] of [1440,390].entries()) {
      const context = await browser.newContext({viewport:{width,height:900}});
      context.setDefaultTimeout(15000);
      const page = await context.newPage();
      page.on('pageerror', error => result.errors.push(error.message));
      await page.goto(base+'/dang-nhap/');
      await page.locator('[name=username]').fill('quan_tri');
      await page.locator('[name=password]').fill('matkhau-kiem-thu-1');
      await Promise.all([page.waitForURL(u=>!u.pathname.includes('dang-nhap')),page.locator('button[type=submit]').click()]);
      await page.goto(base+'/van-don/len-don/');
      assert.equal(await page.locator('[name=sub_unit]').count(),0);
      const currency = page.locator('[name=currency]'), market = page.locator('[name=market]');
      assert.equal(await currency.getAttribute('readonly'), '');
      assert.equal(await currency.inputValue(), '');
      assert.deepEqual(await page.locator('[name=payment_method] option').evaluateAll(options=>options.map(o=>o.value)), ['', 'zelle','paypal']);
      await market.selectOption('us');assert.equal(await currency.inputValue(),'USD');
      await page.locator('[name=unit_price]').fill('12.50');
      page.once('dialog', dialog=>dialog.dismiss());
      await market.selectOption('ca');assert.equal(await market.inputValue(),'us');
      page.once('dialog', dialog=>dialog.accept());
      await market.selectOption('ca');assert.equal(await currency.inputValue(),'CAD');
      page.once('dialog', dialog=>dialog.accept());
      await market.selectOption('ph');assert.equal(await currency.inputValue(),'PHP');
      assert.equal(await page.locator('[name=unit_price]').inputValue(),'12.50');
      await page.locator('[name=customer_name]').fill(`Currency QA ${width}`);
      await page.locator('[name=phone]').fill(`097000${width}`);
      await page.locator('[name=payment_method]').selectOption('paypal');
      await page.locator('[name=product]').selectOption(ready.product);
      await page.locator('[name=quantity]').fill('2');
      await page.getByRole('button',{name:'Lưu đơn',exact:true}).click();
      await page.locator('.vd-success').waitFor();
      await page.getByRole('link',{name:'Xem đơn gốc',exact:true}).click();
      assert.equal(await page.getByText('Đơn vị phụ',{exact:true}).count(),0);

      await page.goto(`${base}/bang-tinh/${ready.table}/?f_ma_don=${encodeURIComponent(ready.codes[index])}`);
      await page.locator('.mg-cell[data-r="0"]').first().waitFor();
      // Trên mobile bỏ cố định cột bằng điều khiển có sẵn để sửa cột ở xa.
      async function cell(code) {
        await page.evaluate(code=>{
          const target=document.querySelector(`.mg-cell[data-r="0"][data-code="${code}"]`);
          const viewport=document.getElementById('mg-viewport');
          if(target)viewport.scrollLeft=Math.max(0,parseFloat(target.style.left||0)-Math.min(550,viewport.clientWidth/2));
        },code);
        const target=page.locator(`.mg-cell[data-r="0"][data-code="${code}"]`);
        await target.scrollIntoViewIfNeeded();return target;
      }
      const snapshot=()=>page.evaluate(async()=>{
        const c=JSON.parse(document.getElementById('mg-config').textContent);
        return (await fetch(c.dataUrl+location.search).then(r=>r.json())).rows[0];
      });
      // Dùng điều khiển Cột để đưa ba trường cần kiểm vào cùng vùng nhìn.
      {
        await page.locator('#mg-columns-button').click();
        const toggles=page.locator('#mg-column-list input[type=checkbox]');
        for(let i=0;i<await toggles.count();i++){
          const input=toggles.nth(i), label=await input.locator('..').innerText();
          if(!['Quốc gia','Loại tiền','PTTT thực tế'].includes(label.trim())&&await input.isChecked())await input.uncheck();
        }
        await page.getByRole('button',{name:'Đóng cột hiển thị',exact:true}).click();
      }
      await (await cell('pttt_thuc_te')).dblclick({delay:120});
      assert.equal(await page.locator('#mg-editor select').inputValue(),'Thẻ');
      assert.equal(await page.locator('#mg-editor select option:checked').isDisabled(),true);
      await page.locator('#mg-editor select').press('Enter');
      assert.equal((await snapshot()).cells.pttt_thuc_te.value,'Thẻ');
      await (await cell('quoc_gia')).dblclick({delay:120});
      await page.locator('#mg-editor select').selectOption('Canada');
      page.once('dialog', dialog=>dialog.dismiss());
      await page.locator('#mg-editor select').press('Enter');
      await page.waitForFunction(()=>document.getElementById('mg-message').textContent.includes('Chưa lưu thay đổi quốc gia'));
      assert.equal((await snapshot()).cells.loai_tien.value,'USD');
      page.once('dialog', dialog=>dialog.accept());
      await page.keyboard.press('Control+s');
      await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');
      let row=await snapshot();assert.equal(row.cells.loai_tien.value,'CAD');assert.equal(row.cells.gia_tien.value,'10.00');
      await (await cell('loai_tien')).dblclick({delay:120});
      assert.equal(await page.locator('#mg-editor').isVisible(),false);
      await page.keyboard.press('Escape');
      await (await cell('pttt_thuc_te')).dblclick({delay:120});
      assert.deepEqual(await page.locator('#mg-editor select option').evaluateAll(options=>options.filter(o=>o.value&&!o.disabled).map(o=>o.value)),['Zelle','PayPal']);
      await page.locator('#mg-editor select').selectOption('PayPal');await page.keyboard.press('Enter');
      await page.waitForFunction(()=>document.getElementById('bt-trang-thai').textContent==='Đã lưu');
      row=await snapshot();assert.equal(row.cells.pttt_thuc_te.value,'PayPal');
      await page.screenshot({path:`${folder}/grid-${width}.png`});
      result.cases.push({width,orderCurrencies:true,orderConfirmation:true,gridConfirmation:true,currencyLocked:true,paymentChoices:true});
      await context.close();
    }
    assert.equal(result.errors.length,0);result.ok=true;
  } catch(error){result.errors.push(error.message);process.exitCode=1;}
  finally{await browser.close();fs.writeFileSync(`${folder}/browser-result.json`,JSON.stringify(result,null,2));console.log(JSON.stringify(result));}
})();
