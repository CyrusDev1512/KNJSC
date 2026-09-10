/* Bản đang làm chỉ trong RAM; hàng đợi lưu gửi thay đổi, không lưu khách hàng vào localStorage. */
((scope)=>{
  'use strict';
  const same=(a,b)=>String(a??'')===String(b??'');
  const key=c=>`${c.id}:${c.column}:${c.property||'value'}`;
  class MasterWorkingCopy {
    constructor(){this.entries=new Map();this.undo=[];this.redo=[];this.held=new Set();this.count=0;}
    value(id,column,fallback,property='value'){const e=this.entries.get(key({id,column,property}));return e?e.value:fallback;}
    pending(){return [...this.entries.values()].filter(e=>!same(e.old,e.value)).map(e=>({...e}));}
    observe(rows){
      if(!this.entries.size)return;
      for(const row of rows)for(const [column,cell] of Object.entries(row.cells)){
        for(const property of ['value','fs','c','bg']){
          const k=key({id:row.id,column,property}),e=this.entries.get(k);
          const value=property==='value'?cell.value:cell.style?.[property]??null;
          if(e&&same(e.old,e.value)&&!this.held.has(k))e.old=e.value=value;
        }
      }
    }
    stage(cells,record=true){
      const changes=new Map(),step=[];
      for(const c of cells){
        const k=key(c),identity={id:c.id,column:c.column,...(c.property?{property:c.property}:{})},e={...(changes.get(k)||this.entries.get(k)||{...identity,old:c.old,value:c.old})};
        if(!same(e.value,c.value)){step.push({...identity,old:e.value,value:c.value});e.value=c.value;changes.set(k,e);}
      }
      const combined=new Map([...this.entries,...changes]);
      const count=[...combined.values()].filter(e=>!same(e.old,e.value)).length;
      if(count>2000)throw Error('Tối đa 2.000 ô chưa lưu. Bấm Lưu dữ liệu trước khi sửa thêm; lượt vừa nhập chưa được áp dụng.');
      this.entries=combined;this.count=count;
      if(record&&step.length){this.undo.push(step);if(this.undo.length>100)this.undo.shift();this.redo=[];}
      this.prune();return step.length;
    }
    travel(redo=false){
      const source=redo?this.redo:this.undo,step=source.at(-1);if(!step)return;
      for(const c of step){const current=this.entries.get(key(c));if(!current||!same(current.value,redo?c.old:c.value))throw Error('Không thể hoàn tác vì ô đã thay đổi. Phần đang làm được giữ nguyên.');}
      this.stage(step.map(c=>({...c,value:redo?c.value:c.old})),false);
      source.pop();(redo?this.undo:this.redo).push(step);this.prune();
    }
    hold(cells){cells.forEach(c=>this.held.add(key(c)));}
    acknowledge(cells,rows){
      const byId=new Map(rows.map(row=>[row.id,row]));
      for(const c of cells){
        const k=key(c),e=this.entries.get(k),cell=byId.get(c.id).cells[c.column],value=c.property&&c.property!=='value'?cell.style?.[c.property]??null:cell.value;
        if(e){if(same(e.value,c.value))e.value=value;e.old=value;}
        if(!same(value,c.value))for(const step of [...this.undo,...this.redo])for(const cell of step){
          if(key(cell)!==k)continue;
          if(same(cell.old,c.value))cell.old=value;
          if(same(cell.value,c.value))cell.value=value;
        }
        this.held.delete(k);
      }
      this.count=this.pending().length;this.prune();
    }
    release(cells){cells.forEach(c=>this.held.delete(key(c)));this.prune();}
    resolve(conflicts, choices){
      for(const c of conflicts){const e=this.entries.get(key(c));if(!e)continue;e.old=c.current;if(choices.get(key(c))==='server')e.value=c.current;}
      // Mốc trước/sau cũ không còn hợp lệ sau khi đối chiếu server.
      this.undo=[];this.redo=[];this.count=this.pending().length;this.prune();
    }
    forget(ids){
      for(const [k,e] of this.entries)if(ids.has(e.id)){this.entries.delete(k);this.held.delete(k);}
      this.undo=this.undo.filter(step=>!step.some(c=>ids.has(c.id)));this.redo=this.redo.filter(step=>!step.some(c=>ids.has(c.id)));
      this.count=this.pending().length;
    }
    prune(){
      const keep=new Set([...this.held,...this.undo.flat().map(key),...this.redo.flat().map(key)]);
      for(const [k,e] of this.entries)if(same(e.old,e.value)&&!keep.has(k))this.entries.delete(k);
    }
  }
  MasterWorkingCopy.same=same;
  MasterWorkingCopy.key=key;
  if(typeof module!=='undefined'&&module.exports)module.exports=MasterWorkingCopy;
  else scope.KNJSCWorkingCopy=MasterWorkingCopy;
})(globalThis);
