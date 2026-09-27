"""Renders the dashboard: one self-contained, interactive HTML file."""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CSS = """
:root{
  --bg:#FFFFFF; --panel:#F2F5FC; --line:#DCE3F2;
  --ink:#080B14; --muted:#5A6480;
  --blue:#1B4DFF; --blue-soft:#E4EAFF;
  --green:#00A24A; --green-soft:#DBF7E7;
  --red:#E01B1B; --red-soft:#FFE3E3;
  --amber:#E07C00; --amber-soft:#FFF0D6;
}
*{box-sizing:border-box;margin:0;padding:0}
html{-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--ink);
  font-family:Manrope,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  font-size:16px;line-height:1.45;font-variant-numeric:tabular-nums;
  padding-bottom:80px}
.wrap{max-width:1040px;margin:0 auto;padding:0 18px}
button{font-family:inherit;cursor:pointer;border:none;background:none;color:inherit}

/* masthead */
.mast{display:flex;align-items:center;flex-wrap:wrap;padding:24px 0 14px}
.mast h1{font-size:22px;font-weight:800;letter-spacing:-.03em}
.mast .stamp{margin-left:auto;font-size:13px;font-weight:600;color:var(--muted)}

/* regime */
.regime{border-radius:14px;padding:22px 22px 18px;color:#fff;background:var(--blue)}
.regime.warn{background:var(--amber)} .regime.bad{background:var(--red)}
.regime .kicker{font-size:13px;font-weight:800;letter-spacing:.04em;opacity:.85}
.regime .line{font-size:clamp(20px,4.2vw,28px);font-weight:800;line-height:1.2;
  letter-spacing:-.025em;margin-top:6px;max-width:32ch}
.regime .facts{display:flex;flex-wrap:wrap;margin-top:16px;padding-top:14px;
  border-top:1.5px solid rgba(255,255,255,.3)}
.regime .fact{margin-right:32px;margin-bottom:4px}
.regime .fact b{display:block;font-size:20px;font-weight:800}
.regime .fact span{font-size:12px;font-weight:600;opacity:.85}

/* tabs */
.tabs{display:flex;gap:6px;overflow-x:auto;margin:22px 0 0;padding-bottom:4px;
  -webkit-overflow-scrolling:touch}
.tab{white-space:nowrap;font-size:14px;font-weight:700;padding:9px 15px;
  border-radius:999px;background:var(--panel);color:var(--muted);
  transition:background .15s,color .15s}
.tab:hover{background:var(--blue-soft);color:var(--blue)}
.tab[aria-selected=true]{background:var(--ink);color:#fff}
.tab .pill{display:inline-block;margin-left:7px;font-size:12px;font-weight:800;
  padding:1px 7px;border-radius:999px;background:rgba(0,0,0,.09)}
.tab[aria-selected=true] .pill{background:rgba(255,255,255,.22)}
.tab .pill.hot{background:var(--red);color:#fff}

.panel{display:none;margin-top:18px}
.panel.on{display:block}
.lede{font-size:14px;font-weight:600;color:var(--muted);margin-bottom:12px}

/* controls */
.controls{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px}
.controls input{flex:1 1 190px;min-width:0;font-size:15px;font-weight:600;
  padding:10px 13px;border:2px solid var(--line);border-radius:10px;background:var(--bg)}
.controls input:focus{outline:none;border-color:var(--blue)}
.sortbtn{font-size:13px;font-weight:700;padding:9px 13px;border-radius:10px;
  background:var(--panel);color:var(--muted)}
.sortbtn.on{background:var(--blue);color:#fff}

/* rows */
.row{display:flex;align-items:flex-start;width:100%;text-align:left;
  padding:14px 12px;border-radius:12px;transition:background .12s}
.row+.row{margin-top:2px}
.row:hover{background:var(--panel)}
.row .rk{flex:0 0 34px;font-size:14px;font-weight:800;color:var(--muted);padding-top:3px}
.row .bd{flex:1 1 auto;min-width:0;padding-right:12px}
.row .rt{flex:0 0 auto;text-align:right}
.sym{font-size:17px;font-weight:800;letter-spacing:-.02em}
.sub{font-size:13px;font-weight:600;color:var(--muted);margin-top:2px}
.stats{font-size:12.5px;font-weight:700;color:var(--muted);margin-top:5px}
.stats b{color:var(--ink);font-weight:800}
.cat{display:inline-block;margin-top:6px;font-size:12.5px;font-weight:800;
  color:var(--amber);background:var(--amber-soft);padding:3px 9px;border-radius:7px}
.big{font-size:19px;font-weight:800;letter-spacing:-.02em}
.up{color:var(--green)} .down{color:var(--red)}
.tag{display:inline-block;margin-top:6px;font-size:12px;font-weight:800;
  padding:3px 10px;border-radius:999px}
.tag.buy{background:var(--green-soft);color:var(--green)}
.tag.hold{background:var(--blue-soft);color:var(--blue)}
.tag.sell{background:var(--red-soft);color:var(--red)}
.tag.wait{background:var(--panel);color:var(--muted)}
.spine{height:6px;border-radius:99px;background:var(--blue-soft);margin-top:8px;max-width:300px}
.spine i{display:block;height:100%;border-radius:99px;background:var(--blue)}

/* exit cards — loudest thing after the regime */
.exit{display:flex;align-items:center;padding:16px;border-radius:12px;
  background:var(--red-soft);border-left:6px solid var(--red)}
.exit+.exit{margin-top:8px}
.exit .bd{flex:1 1 auto;min-width:0}
.exit .sym{color:var(--red)}
.exit .sub{color:#8A1414;font-weight:700}

/* detail drawer */
.detail{display:none;padding:2px 12px 14px 46px}
.detail.on{display:block}
.grid{display:flex;flex-wrap:wrap}
.kv{margin:0 26px 10px 0}
.kv b{display:block;font-size:16px;font-weight:800}
.kv span{font-size:11.5px;font-weight:700;color:var(--muted)}

/* sectors */
.sect{display:flex;align-items:center;padding:11px 12px;border-radius:10px;font-weight:700}
.sect:hover{background:var(--panel)}
.sect .n{flex:0 0 30px;font-size:14px;font-weight:800;color:var(--muted)}
.sect .nm{flex:1 1 auto;min-width:0;font-size:15px;padding-right:10px}
.sect .bar{flex:0 0 110px;height:9px;border-radius:99px;background:var(--panel);margin-right:12px}
.sect .bar i{display:block;height:100%;border-radius:99px;background:var(--blue)}
.sect .pct{flex:0 0 52px;text-align:right;font-size:14px;font-weight:800}
.sect.out{opacity:.4}
.sect.out .bar i{background:var(--muted)}

.tag.obv{background:#EFE6FF;color:#6A2BD9}
.tag.ipo{background:var(--amber-soft);color:var(--amber)}
.tag.entry{background:var(--green-soft);color:var(--green)}
.tag.ended{background:var(--panel);color:var(--muted)}
.logdate{font-size:12px;font-weight:800;color:var(--muted);letter-spacing:.03em;
  text-transform:uppercase;margin:18px 12px 4px}
/* date-wise board: one column per trading day, newest on the left */
.board{display:flex;gap:10px;overflow-x:auto;padding:2px 2px 12px;
  scroll-snap-type:x proximity;-webkit-overflow-scrolling:touch}
.dcol{flex:0 0 212px;background:var(--panel);border-radius:12px;padding:10px 8px;
  scroll-snap-align:start;align-self:flex-start}
.dcol.today{box-shadow:inset 0 0 0 2px var(--blue)}
.dcol h4{font-size:14.5px;font-weight:800;letter-spacing:-.01em;padding:0 4px}
.dcol .cnt{font-size:11.5px;font-weight:700;color:var(--muted);padding:0 4px 8px}
.dcell{display:flex;align-items:center;background:var(--bg);border-radius:8px;
  padding:7px 8px;margin-top:4px}
.dcell .l{flex:1 1 auto;min-width:0}
.dcell .s{font-size:14px;font-weight:800;letter-spacing:-.01em;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.dcell .m{font-size:11px;font-weight:700;color:var(--muted);white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis}
.dcell .r{flex:0 0 auto;text-align:right;font-size:12.5px;font-weight:800;padding-left:6px}
.dcell.lo{opacity:.55}
.dcell.hit{box-shadow:inset 0 0 0 2px var(--amber)}
.dcol .none{font-size:12.5px;font-weight:700;color:var(--muted);padding:8px 4px}
.tag.big50{background:var(--panel);color:var(--muted);margin:0 0 0 6px;vertical-align:2px;
  font-size:10.5px;padding:2px 7px}
.dsplit{font-size:10.5px;font-weight:800;color:var(--muted);letter-spacing:.04em;
  text-transform:uppercase;padding:10px 4px 0}
.chartchip{display:inline-block;margin-left:8px;padding:2px 9px;border-radius:999px;
  background:var(--panel);color:var(--blue);font-size:11.5px;font-weight:800;vertical-align:2px;cursor:pointer}
.chartchip:hover{background:var(--blue);color:#fff}
.dcell[data-chart]{cursor:pointer}.dcell[data-chart]:hover{box-shadow:inset 0 0 0 2px var(--line)}
.cx{position:fixed;inset:0;background:rgba(8,11,20,.55);display:none;z-index:50;
  align-items:center;justify-content:center;padding:18px}
.cx.on{display:flex}
.cxp{background:var(--bg);border-radius:16px;width:100%;max-width:1020px;height:min(86vh,680px);
  display:flex;flex-direction:column;padding:14px 16px 10px;box-shadow:0 20px 60px rgba(0,0,0,.25)}
.cxh{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.cxh .t{font-size:20px;font-weight:800;letter-spacing:-.02em;margin-right:4px}
.cxh .n{font-size:13px;font-weight:700;color:var(--muted);flex:1 1 140px;min-width:0;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cxh a{font-size:12.5px;font-weight:800;color:var(--blue);text-decoration:none;padding:6px 4px}
.cxh .x{margin-left:auto;font-size:22px;font-weight:700;color:var(--muted);padding:2px 8px;border-radius:8px}
.cxh .x:hover{background:var(--panel)}
.cxc{margin-top:8px}.cxc a{margin-left:auto}
.cxlg{font-size:12px;font-weight:600;color:var(--muted);padding:8px 2px 6px;min-height:34px;line-height:1.6}
.cxlg b{color:var(--ink);font-weight:800}.cxlg b.up{color:var(--green)}.cxlg b.down{color:var(--red)}
.cxl{white-space:nowrap;margin-left:6px}.cxl i{display:inline-block;width:12px;height:3px;border-radius:2px;
  vertical-align:3px;margin-right:4px}
.cxbox{flex:1 1 auto;min-height:0;position:relative}
.cxmsg{padding:40px 10px;text-align:center;font-weight:700;color:var(--muted)}
@media(max-width:560px){.cx{padding:0}.cxp{border-radius:0;height:100%;max-width:none;padding:12px 10px 6px}}
.empty{padding:20px 12px;border-radius:12px;background:var(--panel);
  font-size:15px;font-weight:700;color:var(--muted)}
footer{margin-top:40px;padding-top:16px;border-top:2px solid var(--line);
  font-size:12.5px;font-weight:600;color:var(--muted);line-height:1.6}
@media(max-width:560px){
  .row{padding:13px 8px}.row .rk{flex-basis:26px}
  .sect .bar{flex-basis:64px}.detail{padding-left:34px}
}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = r"""
var F={
  pct:function(x,d){d=d==null?1:d;return x==null||isNaN(x)?'--':(x*100).toFixed(d)+'%';},
  spct:function(x,d){d=d==null?0:d;return x==null||isNaN(x)?'--':((x>=0?'+':'')+(x*100).toFixed(d)+'%');},
  num:function(x,d){d=d==null?0:d;return x==null||isNaN(x)?'--':Number(x).toFixed(d);},
  rs:function(x){return x==null||isNaN(x)?'--':'\u20b9'+Math.round(x).toLocaleString('en-IN');},
  cr:function(x){if(!x)return '--';return x>=1000?'\u20b9'+(x/1000).toFixed(1)+'k cr':'\u20b9'+Math.round(x)+' cr';}
};
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){
  return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function dirOf(x){return (x||0)>=0?'up':'down';}
function big50(mc){
  return (mc!=null&&DATA.priority_mcap&&mc>=DATA.priority_mcap)
    ?'<span class="tag big50">\u20b950K+ cr \u00b7 lower priority</span>':'';
}
function kv(v,l){return '<div class="kv"><b>'+v+'</b><span>'+l+'</span></div>';}

function tabs(){
  var ts=document.querySelectorAll('.tab');
  for(var i=0;i<ts.length;i++){
    ts[i].onclick=function(){
      var all=document.querySelectorAll('.tab');
      for(var j=0;j<all.length;j++){all[j].setAttribute('aria-selected','false');}
      var ps=document.querySelectorAll('.panel');
      for(var k=0;k<ps.length;k++){ps[k].className='panel';}
      this.setAttribute('aria-selected','true');
      document.getElementById(this.getAttribute('data-panel')).className='panel on';
      window.scrollTo(0,0);
    };
  }
}

function drawer(host){
  var rows=host.querySelectorAll('.row[data-i]');
  for(var i=0;i<rows.length;i++){
    rows[i].onclick=function(){
      var d=host.querySelector('.detail[data-i="'+this.getAttribute('data-i')+'"]');
      if(d){d.className=(d.className.indexOf('on')>-1)?'detail':'detail on';}
    };
  }
}

function rowHTML(x,i,o){
  o=o||{};
  var tag=o.tag?'<span class="tag '+o.tag[0]+'">'+o.tag[1]+'</span>':'';
  var spine=(o.spine!=null)?'<div class="spine"><i style="width:'+o.spine+'%"></i></div>':'';
  var cat=x.catalyst?'<div class="cat">'+esc(x.catalyst)+'</div>':'';
  var stats='';
  if(x.weekly_rsi!=null||x.ext20!=null||x.price||x.rs_days!=null){
    var rs=(x.rs_days==null||x.rs_days>900)?'':(' \u00b7 RS high <b>'
      +(x.rs_days===0?'today':x.rs_days+'d ago')+'</b>');
    var qq='';
  if(x.eps_qoq!=null||x.sales_qoq!=null){
    qq='<div class="stats">QoQ earnings <b>'+F.spct(x.eps_qoq)+'</b> \u00b7 sales <b>'
      +F.spct(x.sales_qoq)+'</b>'+(x.quarter?' \u00b7 quarter to '+esc(x.quarter):'')+'</div>';
  }
  var sc='';
    if(x.sector_score!=null||x.earnings_score!=null||x.growth_score!=null||x.emergence_score!=null){
      sc='<div class="stats">Emergence <b>'+F.num(x.emergence_score)+'</b> \u00b7 Sector <b>'
        +F.num(x.sector_score)+'</b> \u00b7 Earnings <b>'+F.num(x.earnings_score)
        +'</b> \u00b7 Growth <b>'+F.num(x.growth_score)+'</b></div>';
    }
    stats='<div class="stats">RSI <b>'+F.num(x.weekly_rsi)+'</b> \u00b7 20-day <b>'+F.spct(x.ext20)+'</b>'
      +rs+(o.weight!=null?' \u00b7 weight <b>'+F.pct(o.weight)+'</b>':'')
      +(x.price?' \u00b7 <b>'+F.rs(x.price)+'</b>':'')+'</div>';
  }
  var ret='';
  if(x.eps_growth!==undefined||x.sales_growth!==undefined){
    ret='<div class="big '+dirOf(x.eps_growth)+'">'+F.spct(x.eps_growth)+'</div>'
       +'<div class="sub">earnings YoY</div>'
       +'<div class="big '+dirOf(x.sales_growth)+'" style="margin-top:6px">'+F.spct(x.sales_growth)+'</div>'
       +'<div class="sub">sales YoY</div>';
  }else if(x.r12m!=null){
    ret='<div class="big '+dirOf(x.r12m)+'">'+F.spct(x.r12m)+'</div><div class="sub">1 year</div>';
  }
  var det='<div class="grid">'
    +kv(F.spct(x.r12m),'1 year')+kv(F.spct(x.r6m),'6 months')+kv(F.spct(x.r3m),'3 months')
    +kv(F.pct(x.ann_vol,0),'volatility')+kv(F.num(x.composite,2),'score')
    +kv(F.cr(x.market_cap_cr),'market cap')
    +kv(x.quality_score!=null?x.quality_score+' of 5':'--','fundamentals')
    +kv(F.num(x.sector_score),'sector score')
    +kv(F.num(x.earnings_score),'earnings score')
    +kv(F.num(x.emergence_score),'emergence score')
    +kv(F.num(x.growth_score),'growth score')
    +(x.eps_accel!=null?kv(F.spct(x.eps_accel),'earnings acceleration'):'')
    +(x.eps_qoq!=null?kv(F.spct(x.eps_qoq),'earnings QoQ'):'')
    +(x.sales_qoq!=null?kv(F.spct(x.sales_qoq),'sales QoQ'):'')
    +(x.stop?kv(F.rs(x.stop),'stop price'):'')
    +(x.blocked?kv(esc(x.blocked),'blocked by'):'')+'</div>';
  return '<button class="row" data-i="'+i+'"><div class="rk">'+(x.rank||'')+'</div><div class="bd">'
    +'<div class="sym">'+esc(x.symbol)+big50(x.market_cap_cr)+chip(x.symbol,x.name)+'</div>'
    +'<div class="sub">'+esc(x.sector||'')+(x.name?' \u00b7 '+esc(x.name):'')+'</div>'
    +stats+sc+qq+cat+(x.obv_cross&&!o.noObv?'<div><span class="tag obv">OBV cross '+esc(x.obv_month||'')+'</span></div>':'')
    +spine+'</div><div class="rt">'+ret+tag+'</div></button>'
    +'<div class="detail" data-i="'+i+'">'+det+'</div>';
}

function list(host,arr,opts,emptyMsg){
  if(!arr||!arr.length){host.innerHTML='<div class="empty">'+emptyMsg+'</div>';return;}
  var out=[];
  for(var i=0;i<arr.length;i++){
    out.push(rowHTML(arr[i],i,(typeof opts==='function')?opts(arr[i]):opts));
  }
  host.innerHTML=out.join('');
  drawer(host);
}

function candidates(){
  var host=document.getElementById('candList');
  var box=document.getElementById('candSearch');
  var key='rank';
  function render(){
    var q=(box.value||'').toLowerCase();
    var a=[];
    for(var i=0;i<DATA.candidates.length;i++){
      var c=DATA.candidates[i];
      var hay=(c.symbol+' '+(c.sector||'')).toLowerCase();
      if(!q||hay.indexOf(q)>-1){a.push(c);}
    }
    if(key==='ready'){
      a=a.filter(function(x){return x.buyable;});
    }else{
      a=a.slice().sort(function(p,n){
        return key==='rank'?(p.rank-n.rank):((n[key]||0)-(p[key]||0));});
    }
    list(host,a,function(x){
      return {tag:x.held?['hold','In book']:(x.buyable?['buy','Ready']:['wait','Too extended'])};
    },'Nothing matches that search.');
  }
  var bs=document.querySelectorAll('.candbtn');
  for(var i=0;i<bs.length;i++){
    bs[i].onclick=function(){
      var all=document.querySelectorAll('.candbtn');
      for(var j=0;j<all.length;j++){all[j].className='sortbtn candbtn';}
      this.className='sortbtn candbtn on';
      key=this.getAttribute('data-key');render();
    };
  }
  box.oninput=render;render();
}

function signalLog(){
  var host=document.getElementById('logList');
  var box=document.getElementById('logSearch');
  var kind='all';
  var L=DATA.signal_log||[];
  var cls={Entry:'entry',OBV:'obv',IPO:'ipo'};
  var lbl={Entry:'Entry',OBV:'OBV cross',IPO:'IPO'};
  function fmt(d){var p=d.split('-');var m=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    return (+p[2])+' '+m[+p[1]-1]+' '+p[0];}
  function render(){
    var q=(box.value||'').toLowerCase(),out=[],last='',n=0;
    for(var i=0;i<L.length;i++){
      var r=L[i];
      if(kind==='active'&&!r.active)continue;
      if(kind!=='all'&&kind!=='active'&&r.type!==kind)continue;
      if(q&&(r.symbol+' '+(r.sector||'')+' '+(r.name||'')).toLowerCase().indexOf(q)<0)continue;
      if(r.date!==last){out.push('<div class="logdate">'+fmt(r.date)+'</div>');last=r.date;}
      n++;
      out.push('<div class="row"><div class="bd">'
        +'<div class="sym">'+esc(r.symbol)+' <span class="tag '+cls[r.type]+'" style="margin:0 0 0 6px;vertical-align:3px">'+lbl[r.type]+'</span>'+chip(r.symbol,r.name)+'</div>'
        +'<div class="sub">'+esc(r.sector||'')+(r.name&&r.name!==r.symbol?' \u00b7 '+esc(r.name):'')+'</div>'
        +'<div class="stats">'+esc(r.detail||'')+'</div>'
        +'<div class="stats">flagged at <b>'+F.rs(r.price)+'</b> \u00b7 now <b>'+F.rs(r.last_price)+'</b> \u00b7 '
        +(r.active?'<b class="up">still active</b>':'ended '+fmt(r.ended||r.last_seen))+'</div></div>'
        +'<div class="rt"><div class="big '+dirOf(r.since)+'">'+F.spct(r.since,1)+'</div>'
        +'<div class="sub">since signal</div>'
        +(r.active?'':'<span class="tag ended">Ended</span>')+'</div></div>');
    }
    host.innerHTML=n?out.join(''):'<div class="empty">'+(L.length?'Nothing matches that filter.':
      'No signals recorded yet. From today, every signal is saved here with its date.')+'</div>';
  }
  var bs=document.querySelectorAll('.logbtn');
  for(var i=0;i<bs.length;i++){
    bs[i].onclick=function(){
      var all=document.querySelectorAll('.logbtn');
      for(var j=0;j<all.length;j++){all[j].className='sortbtn logbtn';}
      this.className='sortbtn logbtn on';kind=this.getAttribute('data-kind');render();
    };
  }
  box.oninput=render;render();
}

function dateWise(){
  var host=document.getElementById('dayBoard');
  var box=document.getElementById('daySearch');
  var note=document.getElementById('dayNote');
  var kind='Entry';
  var D=DATA.daily||[];
  var M=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var W=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  function head(d){var p=d.split('-');var dt=new Date(+p[0],+p[1]-1,+p[2]);
    return W[dt.getDay()]+' '+(+p[2])+' '+M[+p[1]-1]+' '+p[0];}
  function match(r,q){return (r.symbol+' '+(r.name||'')).toLowerCase().indexOf(q)>=0;}
  function cell(r,q){
    return '<div class="dcell'+(r.pri?'':' lo')+(q&&match(r,q)?' hit':'')+'" title="'+esc(r.name||'')+'"'
      +(DATA.charts?' data-chart="'+esc(r.symbol)+'" data-name="'+esc(r.name||'')+'" role="button" tabindex="0"':'')+'>'
      +'<div class="l"><div class="s">'+esc(r.symbol)+'</div>'
      +'<div class="m">'+esc(r.sector||'')+(r.mcap?' \u00b7 '+F.cr(r.mcap):'')+'</div></div>'
      +'<div class="r"><div class="'+dirOf(r.since)+'">'+F.spct(r.since,1)+'</div>'
      +'<div class="m">'+F.rs(r.price)+'</div></div></div>';
  }
  function render(){
    var q=(box.value||'').toLowerCase().trim(),out=[],days=0;
    for(var i=0;i<D.length;i++){
      var rows=D[i][kind]||[];
      if(q){var any=false;for(var j=0;j<rows.length;j++){if(match(rows[j],q)){any=true;break;}}
        if(!any)continue;}
      days++;
      var hi=[],lo=[];
      for(var k=0;k<rows.length;k++){(rows[k].pri?hi:lo).push(cell(rows[k],q));}
      out.push('<div class="dcol'+(i===0?' today':'')+'"><h4>'+head(D[i].date)+'</h4>'
        +'<div class="cnt">'+rows.length+' passed'+(lo.length?' \u00b7 '+hi.length+' under \u20b950K cr':'')+'</div>'
        +(rows.length?hi.join('')+(lo.length?'<div class="dsplit">\u20b950K cr and above</div>'+lo.join(''):'')
          :'<div class="none">Nothing passed.</div>')+'</div>');
    }
    host.innerHTML=out.length?out.join(''):'<div class="empty">'+(D.length
      ?(q?'That symbol did not pass this screen on any day in the last six months.':'Nothing recorded for this screen yet.')
      :'No days recorded yet. From the next run, every trading day gets its own column here and stays for six months.')+'</div>';
    note.innerHTML=(q&&days)?'<b>'+esc(box.value)+'</b> passed on <b>'+days+'</b> of the '+D.length+' days on record.':
      (D.length?D.length+' trading day'+(D.length>1?'s':'')+' on record. Scroll sideways for older days.':'');
  }
  var bs=document.querySelectorAll('.daybtn');
  for(var i=0;i<bs.length;i++){
    bs[i].onclick=function(){
      var all=document.querySelectorAll('.daybtn');
      for(var j=0;j<all.length;j++){all[j].className='sortbtn daybtn';}
      this.className='sortbtn daybtn on';kind=this.getAttribute('data-kind');render();
    };
  }
  box.oninput=render;render();
}

// ------------------------------------------------------------ charts
function chip(sym,name){
  if(!DATA.charts)return '';
  return ' <span class="chartchip" role="button" tabindex="0" data-chart="'+esc(sym)
    +'" data-name="'+esc(name||'')+'" aria-label="Candlestick chart for '+esc(sym)+'">Chart</span>';
}
var CH={chart:null,data:null,tf:'D',sym:'',name:''};
function chartFile(sym){return 'charts/'+encodeURIComponent(String(sym).replace(/[^A-Za-z0-9\-_&]/g,''))+'.json';}
function chartMsg(t){document.getElementById('cxBox').innerHTML='<div class="cxmsg">'+t+'</div>';}
function loadLib(ok,bad){
  if(window.LightweightCharts){ok();return;}
  var s=document.createElement('script');s.src='charts/lightweight-charts.js';
  s.onload=ok;s.onerror=bad;document.head.appendChild(s);
}
function openChart(sym,name){
  CH.sym=sym;CH.name=name||'';CH.data=null;
  document.getElementById('cxSym').textContent=sym;
  document.getElementById('cxName').textContent=CH.name&&CH.name!==sym?CH.name:'';
  document.getElementById('cxTv').href='https://www.tradingview.com/chart/?symbol=NSE%3A'+encodeURIComponent(sym);
  document.getElementById('cxLegend').innerHTML='';
  document.getElementById('cx').className='cx on';
  document.body.style.overflow='hidden';
  chartMsg('Loading chart\u2026');
  loadLib(function(){
    fetch(chartFile(sym)).then(function(r){if(!r.ok)throw 0;return r.json();})
      .then(function(d){if(CH.sym!==sym)return;CH.data=d;drawChart();})
      .catch(function(){chartMsg('No chart for '+esc(sym)+' yet. Charts are rebuilt on every run.');});
  },function(){chartMsg('The chart library did not load. Check your connection and try again.');});
}
function closeChart(){
  document.getElementById('cx').className='cx';document.body.style.overflow='';
  if(CH.chart){CH.chart.remove();CH.chart=null;}
}
function weekKey(t){var p=t.split('-');var d=new Date(Date.UTC(+p[0],+p[1]-1,+p[2]));
  d.setUTCDate(d.getUTCDate()-((d.getUTCDay()+6)%7));return d.toISOString().slice(0,10);}
function aggBars(d,tf){
  var out=[],cur=null,key=null;
  for(var i=0;i<d.t.length;i++){
    var k=tf==='D'?d.t[i]:(tf==='W'?weekKey(d.t[i]):d.t[i].slice(0,7));
    if(tf==='D'||k!==key){
      if(cur)out.push(cur);key=k;
      cur={time:d.t[i],open:d.o[i],high:d.h[i],low:d.l[i],close:d.c[i],volume:d.v[i]};
    }else{
      if(d.h[i]>cur.high)cur.high=d.h[i];
      if(d.l[i]<cur.low)cur.low=d.l[i];
      cur.close=d.c[i];cur.volume+=d.v[i];
    }
  }
  if(cur)out.push(cur);return out;
}
function smaLine(b,n){var o=[],s=0;for(var i=0;i<b.length;i++){s+=b[i].close;if(i>=n)s-=b[i-n].close;
  if(i>=n-1)o.push({time:b[i].time,value:+(s/n).toFixed(2)});}return o;}
function emaVals(vals,n){ // seeded with a simple average of the first n, as TradingView does
  var o=[];if(vals.length<n)return o;var a=2/(n+1),p=0;for(var i=0;i<n;i++)p+=vals[i];p/=n;
  for(i=0;i<vals.length;i++){if(i<n-1){o.push(null);continue;}if(i>=n)p=a*vals[i]+(1-a)*p;o.push(p);}return o;}
function emaLine(b,n){var e=emaVals(b.map(function(x){return x.close;}),n),o=[];
  for(var i=0;i<b.length;i++)if(e[i]!=null)o.push({time:b[i].time,value:+e[i].toFixed(2)});return o;}
var CX_COL={up:'#00A24A',down:'#E01B1B',a:'#E08A00',b:'#1F4FFF',c:'#7A3FE0',obv:'#1F4FFF',obvE:'#E08A00'};
function drawChart(){
  var host=document.getElementById('cxBox');host.innerHTML='';
  if(CH.chart){CH.chart.remove();CH.chart=null;}
  var bars=aggBars(CH.data,CH.tf);
  if(!bars.length){chartMsg('No price history.');return;}
  var LC=window.LightweightCharts;
  var chart=LC.createChart(host,{autoSize:true,
    layout:{background:{type:'solid',color:'#FFFFFF'},textColor:'#5A6480',fontSize:11,
      fontFamily:'Manrope,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif'},
    grid:{vertLines:{color:'#F0F3FA'},horzLines:{color:'#F0F3FA'}},
    rightPriceScale:{borderColor:'#DCE3F2',scaleMargins:{top:0.06,bottom:0.3}},
    timeScale:{borderColor:'#DCE3F2',rightOffset:4},
    crosshair:{mode:0},
    localization:{locale:'en-IN',priceFormatter:function(p){return Math.abs(p)>=1e5?Math.round(p).toLocaleString('en-IN'):p.toFixed(2);}}});
  CH.chart=chart;
  var candle=chart.addCandlestickSeries({upColor:CX_COL.up,downColor:CX_COL.down,borderUpColor:CX_COL.up,
    borderDownColor:CX_COL.down,wickUpColor:CX_COL.up,wickDownColor:CX_COL.down,priceLineVisible:true});
  candle.setData(bars.map(function(x){return {time:x.time,open:x.open,high:x.high,low:x.low,close:x.close};}));
  var lines=[],L=function(data,color,label){
    if(!data.length)return;
    var s=chart.addLineSeries({color:color,lineWidth:1.5,priceLineVisible:false,lastValueVisible:false,
      crosshairMarkerVisible:false});s.setData(data);lines.push({s:s,label:label,color:color});};
  if(CH.tf==='D'){L(smaLine(bars,20),CX_COL.a,'20-day');L(smaLine(bars,50),CX_COL.b,'50-day');L(smaLine(bars,200),CX_COL.c,'200-day');}
  else if(CH.tf==='W'){L(emaLine(bars,21),CX_COL.b,'21-week EMA');L(smaLine(bars,40),CX_COL.c,'40-week');}
  var lower=null,lowerE=null;
  if(CH.tf==='M'){
    // Monthly OBV and its 21-month EMA, built the same way as the screen
    var obv=[],run=0;
    for(var i=0;i<bars.length;i++){if(i>0){var dc=bars[i].close-bars[i-1].close;run+=dc>0?bars[i].volume:(dc<0?-bars[i].volume:0);}obv.push(run);}
    var e=emaVals(obv,21);
    lower=chart.addLineSeries({priceScaleId:'low',color:CX_COL.obv,lineWidth:2,priceLineVisible:false,
      lastValueVisible:false,crosshairMarkerVisible:false,priceFormat:{type:'volume'}});
    lower.setData(bars.map(function(b,i){return {time:b.time,value:obv[i]};}));
    lowerE=chart.addLineSeries({priceScaleId:'low',color:CX_COL.obvE,lineWidth:1.5,priceLineVisible:false,
      lastValueVisible:false,crosshairMarkerVisible:false,priceFormat:{type:'volume'}});
    lowerE.setData(bars.map(function(b,i){return e[i]==null?null:{time:b.time,value:e[i]};}).filter(Boolean));
  }else{
    lower=chart.addHistogramSeries({priceScaleId:'low',priceFormat:{type:'volume'},priceLineVisible:false,lastValueVisible:false});
    lower.setData(bars.map(function(b){return {time:b.time,value:b.volume,
      color:b.close>=b.open?'rgba(0,162,74,.35)':'rgba(224,27,27,.35)'};}));
  }
  chart.priceScale('low').applyOptions({scaleMargins:{top:0.76,bottom:0}});
  var narrow=host.clientWidth<600;
  var n=bars.length,show=CH.tf==='D'?(narrow?110:180):(CH.tf==='W'?(narrow?70:110):n);
  chart.timeScale().setVisibleLogicalRange({from:Math.max(0,n-show),to:n+3});

  var byTime={};for(var j=0;j<n;j++)byTime[bars[j].time]=j;
  var obvV=null,obvEV=null;
  if(CH.tf==='M'){obvV=[];var r2=0;for(j=0;j<n;j++){if(j>0){var d2=bars[j].close-bars[j-1].close;r2+=d2>0?bars[j].volume:(d2<0?-bars[j].volume:0);}obvV.push(r2);}obvEV=emaVals(obvV,21);}
  function legend(k){
    var b=bars[k],p=k>0?bars[k-1].close:b.open,ch=p?b.close/p-1:0;
    var h='<b>'+b.time+'</b> O <b>'+F.rs(b.open)+'</b> H <b>'+F.rs(b.high)+'</b> L <b>'+F.rs(b.low)
      +'</b> C <b>'+F.rs(b.close)+'</b> <b class="'+dirOf(ch)+'">'+F.spct(ch,1)+'</b>';
    for(var q=0;q<lines.length;q++)h+=' <span class="cxl"><i style="background:'+lines[q].color+'"></i>'+lines[q].label+'</span>';
    if(CH.tf==='M'&&obvV){var above=obvEV[k]!=null&&obvV[k]>obvEV[k];
      h+=' <span class="cxl"><i style="background:'+CX_COL.obv+'"></i>OBV</span><span class="cxl"><i style="background:'+CX_COL.obvE+'"></i>21-month EMA</span> '
        +(obvEV[k]==null?'':'<b class="'+(above?'up':'down')+'">OBV '+(above?'above':'below')+' EMA</b>');}
    else h+=' <span class="cxl">Vol <b>'+(b.volume>=1e7?(b.volume/1e7).toFixed(2)+' cr':(b.volume/1e5).toFixed(1)+' L')+'</b></span>';
    document.getElementById('cxLegend').innerHTML=h;
  }
  legend(n-1);
  chart.subscribeCrosshairMove(function(pm){
    if(!pm||pm.time==null){legend(n-1);return;}
    var t=typeof pm.time==='string'?pm.time:(pm.time.year+'-'+String(pm.time.month).padStart(2,'0')+'-'+String(pm.time.day).padStart(2,'0'));
    legend(byTime[t]!=null?byTime[t]:n-1);
  });
}
function chartSetup(){
  document.addEventListener('click',function(e){
    var el=e.target&&e.target.closest?e.target.closest('[data-chart]'):null;
    if(!el)return;e.preventDefault();e.stopPropagation();
    openChart(el.getAttribute('data-chart'),el.getAttribute('data-name'));
  },true);
  document.addEventListener('keydown',function(e){
    if(e.key==='Escape')closeChart();
    var el=document.activeElement;
    if((e.key==='Enter'||e.key===' ')&&el&&el.getAttribute&&el.getAttribute('data-chart')){e.preventDefault();el.click();}
  });
  document.getElementById('cxClose').onclick=closeChart;
  document.getElementById('cx').onclick=function(e){if(e.target===this)closeChart();};
  var tb=document.querySelectorAll('.cxtf');
  for(var i=0;i<tb.length;i++)tb[i].onclick=function(){
    for(var j=0;j<tb.length;j++)tb[j].className='sortbtn cxtf';
    this.className='sortbtn cxtf on';CH.tf=this.getAttribute('data-tf');if(CH.data)drawChart();
  };
}

function boot(){
  chartSetup();

  tabs();
  list(document.getElementById('exitList'),DATA.exits,{tag:['sell','Sell']},
    'Nothing to sell. Every holding is above its 21-week EMA and inside its stop.');
  var buys=DATA.book.filter(function(x){return x.action==='buy';});
  list(document.getElementById('entryList'),buys,function(x){
    return {tag:['buy','Buy'],weight:x.weight};},
    'Nothing to buy today. The next scheduled rebalance is '+DATA.next_rebalance+'.');
  list(document.getElementById('signalList'),DATA.new_signals,{tag:['buy','New']},
    'Nothing new cleared the entry rules since the last run.');
  var top=1;
  for(var i=0;i<DATA.book.length;i++){top=Math.max(top,Math.abs(DATA.book[i].composite||0));}
  list(document.getElementById('bookList'),DATA.book,function(x){
    return {tag:[x.action,x.action==='buy'?'Buy':'Hold'],weight:x.weight,
            spine:Math.min(100,Math.max(5,(x.composite/top)*100))};},
    'No positions yet. Run a rebalance.');
  var sh=[];
  for(var s=0;s<DATA.sectors.length;s++){
    var sec=DATA.sectors[s];
    sh.push('<div class="sect'+(sec.rank<=DATA.top_sectors?'':' out')+'">'
      +'<span class="n">'+sec.rank+'</span><span class="nm">'+esc(sec.sector)+'</span>'
      +'<span class="bar"><i style="width:'+Math.max(3,sec.breadth*100).toFixed(0)+'%"></i></span>'
      +'<span class="pct">'+(sec.breadth*100).toFixed(0)+'%</span></div>');
  }
  document.getElementById('sectList').innerHTML=sh.join('');
  var ip=[];
  for(var q=0;q<DATA.ipos.length;q++){
    var o=DATA.ipos[q];
    ip.push('<button class="row"><div class="rk">'+(q+1)+'</div><div class="bd">'
      +'<div class="sym">'+esc(o.symbol)+big50(o.market_cap_cr)+chip(o.symbol,o.name)+'</div>'
      +'<div class="sub">'+esc(o.sector)+' \u00b7 listed '+esc(o.listed_date)
      +' ('+o.age_days+' days ago) \u00b7 '+F.cr(o.market_cap_cr)+'</div>'
      +'<div class="stats">listing-day high <b>'+F.rs(o.listing_high)+'</b> \u00b7 now <b>'
      +F.rs(o.price)+'</b> \u00b7 since listing <b>'+F.spct(o.since_listing)+'</b>'
      +(o.vs_market!=null?' \u00b7 vs market <b>'+F.spct(o.vs_market)+'</b>':'')+'</div>'
      +'<div class="stats">'+(o.from_peak<0.005?'<b>at its high</b>':'<b>'+F.pct(o.from_peak,1)+'</b> off its high')
      +' \u00b7 above '+o.avg_days+'-day average \u00b7 traded <b>'+F.cr(o.adv_cr)+'</b>/day</div>'
      +'<div class="stats">sales <b>'+F.spct(o.sales_growth)+'</b> \u00b7 profit <b>'+F.spct(o.eps_growth)
      +'</b> \u00b7 ROE <b>'+F.pct(o.roe,0)+'</b> \u00b7 ROCE <b>'+F.pct(o.roce,0)+'</b>'
      +(o.sector_rank?' \u00b7 sector rank <b>'+o.sector_rank+'</b>':'')+'</div>'
      +(o.eps_qoq!=null?'<div class="stats">QoQ profit <b>'+F.spct(o.eps_qoq)
        +'</b> \u00b7 sales <b>'+F.spct(o.sales_qoq)+'</b>'
        +(o.quarter?' \u00b7 quarter to '+esc(o.quarter):'')+'</div>':'')+'</div>'
      +'<div class="rt"><div class="big up">'+F.spct(o.above_listing_high,1)+'</div>'
      +'<div class="sub">above listing high</div></div></button>');
  }
  document.getElementById('ipoList').innerHTML=ip.length?ip.join(''):
    '<div class="empty">No listing under six months old passes every test today. Past qualifiers stay in the Signal log.</div>';
  list(document.getElementById('obvList'),DATA.obv||[],function(x){
      return {noObv:true,tag:x.held?['hold','In book']:(x.buyable?['buy','Ready']:['wait','Not ready'])};},
    'No name that clears the momentum gates has a fresh monthly OBV cross today. Past crosses stay in the Signal log.');
  signalLog();
  dateWise();
  candidates();
}
if(document.readyState==='loading'){
  document.addEventListener('DOMContentLoaded',boot);
}else{boot();}
"""

TEMPLATE = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Momentum book</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@500;700;800&display=swap" rel="stylesheet">
<style>__CSS__</style>
</head><body><div class="wrap">

<div class="mast">
  <h1>Momentum book</h1>
  <div class="stamp">__STAMP__ &nbsp;&middot;&nbsp; __UNIVERSE__ screened &nbsp;&middot;&nbsp; __ELIGIBLE__ qualified</div>
</div>

<div class="regime __RCLASS__">
  <div class="kicker">__RSTATE__</div>
  <div class="line">__RDETAIL__</div>
  <div class="facts">
    <div class="fact"><b>__INVESTED__</b><span>capital deployed</span></div>
    <div class="fact"><b>__POSN__</b><span>positions to run</span></div>
    <div class="fact"><b>__GAP__</b><span>index vs 200-day</span></div>
    <div class="fact"><b>__VIX__</b><span>India VIX</span></div>
  </div>
</div>

<div class="tabs" role="tablist">
  <button class="tab" role="tab" aria-selected="true" data-panel="p-exit">Exiting<span class="pill __EHOT__">__NEXIT__</span></button>
  <button class="tab" role="tab" aria-selected="false" data-panel="p-entry">Entering<span class="pill">__NBUY__</span></button>
  <button class="tab" role="tab" aria-selected="false" data-panel="p-signal">New signals<span class="pill">__NSIG__</span></button>
  <button class="tab" role="tab" aria-selected="false" data-panel="p-book">The book<span class="pill">__NBOOK__</span></button>
  <button class="tab" role="tab" aria-selected="false" data-panel="p-cand">Candidates<span class="pill">__NCAND__</span></button>
  <button class="tab" role="tab" aria-selected="false" data-panel="p-obv">OBV cross<span class="pill">__NOBV__</span></button>
  <button class="tab" role="tab" aria-selected="false" data-panel="p-ipo">IPOs<span class="pill">__NIPO__</span></button>
  <button class="tab" role="tab" aria-selected="false" data-panel="p-day">Date-wise<span class="pill">__NDAY__</span></button>
  <button class="tab" role="tab" aria-selected="false" data-panel="p-log">Signal log<span class="pill __LHOT__">__NLOG__</span></button>
  <button class="tab" role="tab" aria-selected="false" data-panel="p-sect">Sectors</button>
</div>

<div class="panel on" id="p-exit">
  <p class="lede">Sell these on the next open. Checked daily, independent of the rebalance calendar.</p>
  <div id="exitList"></div>
</div>

<div class="panel" id="p-entry">
  <p class="lede">Buy these at the weight shown, and place the stop with your broker the same day.</p>
  <div id="entryList"></div>
</div>

<div class="panel" id="p-signal">
  <p class="lede">Names that cleared every entry rule since the last run. Not instructions &mdash; they enter the book at the next rebalance or when a seat opens.</p>
  <div id="signalList"></div>
</div>

<div class="panel" id="p-book">
  <p class="lede">Everything you hold. Tap any row for the full detail.</p>
  <div id="bookList"></div>
</div>

<div class="panel" id="p-cand">
  <p class="lede">Every name that cleared the gates, ranked. Search by symbol or sector.</p>
  <div class="controls">
    <input id="candSearch" type="search" placeholder="Search symbol or sector" aria-label="Search candidates">
    <button class="sortbtn candbtn on" data-key="rank">Rank</button>
    <button class="sortbtn candbtn" data-key="ready">Ready only</button>
    <button class="sortbtn candbtn" data-key="r12m">1-year return</button>
    <button class="sortbtn candbtn" data-key="r3m">3-month return</button>
  </div>
  <div id="candList"></div>
</div>

<div class="panel" id="p-obv">
  <p class="lede">Names that clear the momentum gates and whose monthly on-balance volume has crossed above its 21-month EMA within the last two months &mdash; buying volume turning up on the monthly chart. Tap a row for detail.</p>
  <div id="obvList"></div>
</div>

<div class="panel" id="p-day">
  <p class="lede">Every stock that passed each screen, day by day, for the last six months. One column per trading day, newest on the left. Under &#8377;50,000 cr is listed first; larger names sit underneath, faded. The % is the move from that day&rsquo;s close to the latest close.</p>
  <div class="controls">
    <input id="daySearch" type="search" placeholder="Find a symbol across all days" aria-label="Search date-wise record">
    <button class="sortbtn daybtn on" data-kind="Entry">Momentum</button>
    <button class="sortbtn daybtn" data-kind="OBV">OBV cross</button>
    <button class="sortbtn daybtn" data-kind="IPO">IPO</button>
  </div>
  <p class="lede" id="dayNote" style="margin-top:-4px"></p>
  <div class="board" id="dayBoard"></div>
</div>

<div class="panel" id="p-log">
  <p class="lede">Every signal the system has raised, with the date it first fired and the price that day. Nothing is deleted &mdash; a signal that stops qualifying is marked ended, not removed. __NEWSIG__</p>
  <div class="controls">
    <input id="logSearch" type="search" placeholder="Search symbol or sector" aria-label="Search signal log">
    <button class="sortbtn logbtn on" data-kind="all">All</button>
    <button class="sortbtn logbtn" data-kind="active">Active</button>
    <button class="sortbtn logbtn" data-kind="Entry">Entry</button>
    <button class="sortbtn logbtn" data-kind="OBV">OBV</button>
    <button class="sortbtn logbtn" data-kind="IPO">IPO</button>
  </div>
  <div id="logList"></div>
</div>

<div class="panel" id="p-ipo">
  <p class="lede">Mainboard listings under six months old, ₹1,000&ndash;60,000 cr, closing above their listing-day high, above their 20-day average, within 15% of their post-listing high and ahead of the market since listing &mdash; with sales growth above 15% and rising profits. Too young for the momentum screen: watch these, do not buy them blind.</p>
  <div id="ipoList"></div>
</div>

<div class="panel" id="p-sect">
  <p class="lede">Ranked by six-month median return and breadth. Only the top __TOPSECT__ are eligible; the bar shows the share of the sector above its 200-day average.</p>
  <div id="sectList"></div>
</div>

<footer>
Next rebalance __NEXTREB__. Scores rebuild every trading day; the book changes on a rebalance or an exit.<br>
End-of-day prices, adjusted for splits and dividends. A screening output, not advice.
</footer>
</div>
<script>const DATA=__DATA__;</script>
<script>__JS__</script>
<div class="cx" id="cx" role="dialog" aria-modal="true" aria-label="Candlestick chart">
  <div class="cxp">
    <div class="cxh">
      <span class="t" id="cxSym"></span><span class="n" id="cxName"></span>
      <button class="x" id="cxClose" aria-label="Close chart">&times;</button>
    </div>
    <div class="cxh cxc">
      <button class="sortbtn cxtf on" data-tf="D">Daily</button>
      <button class="sortbtn cxtf" data-tf="W">Weekly</button>
      <button class="sortbtn cxtf" data-tf="M">Monthly</button>
      <a id="cxTv" href="#" target="_blank" rel="noopener">TradingView &#8599;</a>
    </div>
    <div class="cxlg" id="cxLegend"></div>
    <div class="cxbox" id="cxBox"></div>
  </div>
</div>
</body></html>"""


def render(payload: dict, out_path: str) -> str:
    reg = payload["regime"]
    gap = "--"
    if reg.get("last") and reg.get("sma200"):
        gap = f'{(reg["last"] / reg["sma200"] - 1) * 100:+.1f}%'

    # The exit list is what the alerts already are; give it its own key so the
    # front end never has to know they were called alerts.
    payload = dict(payload)
    payload.setdefault("ipos", [])
    payload.setdefault("obv", [])
    payload.setdefault("signal_log", [])
    payload.setdefault("daily", [])
    payload.setdefault("charts", False)
    payload["exits"] = [
        {"symbol": a["symbol"], "sector": a["kind"], "name": a["detail"],
         "rank": "", "r12m": None, "catalyst": ""}
        for a in payload.get("alerts", [])
    ]

    if payload.get("warming"):
        reg = dict(reg)
        reg["state"] = "loading"
        reg["detail"] = (f'Still loading the market — {payload["pending"]} companies '
                         'left. Rebalancing is held back until the whole universe '
                         'is in; exits still run. Re-run the workflow to continue.')
        payload["regime"] = reg

    n_exit = len(payload["exits"])
    n_buy = sum(1 for b in payload["book"] if b["action"] == "buy")

    html = TEMPLATE
    for k, v in {
        "__CSS__": CSS,
        "__JS__": JS,
        "__DATA__": json.dumps(payload, default=str),
        "__STAMP__": payload["stamp"],
        "__UNIVERSE__": str(payload["universe_n"]),
        "__ELIGIBLE__": str(payload["eligible_n"]),
        "__RCLASS__": {"risk-off": "bad", "defensive": "bad",
                       "caution": "warn", "loading": "warn"}.get(reg["state"], ""),
        "__RSTATE__": reg["state"].replace("-", " ").upper(),
        "__RDETAIL__": reg["detail"],
        "__INVESTED__": f'{reg["invested"] * 100:.0f}%',
        "__POSN__": str(reg["positions"]),
        "__GAP__": gap,
        "__VIX__": f'{reg["vix"]:.1f}' if reg.get("vix") else "--",
        "__EHOT__": "hot" if n_exit else "",
        "__NEXIT__": str(n_exit),
        "__NBUY__": str(n_buy),
        "__NSIG__": str(len(payload.get("new_signals", []))),
        "__NBOOK__": str(len(payload["book"])),
        "__NCAND__": str(len(payload.get("candidates", []))),
        "__NIPO__": str(len(payload.get("ipos", []))),
        "__NOBV__": str(len(payload.get("obv", []))),
        "__NDAY__": str(len(payload.get("daily", []))),
        "__NLOG__": str(sum(1 for r in payload["signal_log"] if r.get("active"))),
        "__LHOT__": "hot" if payload.get("new_sig_today") else "",
        "__NEWSIG__": (f'<b>{payload["new_sig_today"]} new today.</b>'
                       if payload.get("new_sig_today") else ""),
        "__TOPSECT__": str(payload["top_sectors"]),
        "__NEXTREB__": payload["next_rebalance"],
    }.items():
        html = html.replace(k, v)

    out_dir = os.path.dirname(out_path)
    os.makedirs(out_dir, exist_ok=True)
    # Tells GitHub Pages to serve these files as-is instead of running them
    # through Jekyll, which chokes on a plain HTML page.
    open(os.path.join(out_dir, ".nojekyll"), "a").close()
    with open(out_path, "w") as fh:
        fh.write(html)
    with open(os.path.join(os.path.dirname(out_path), "data.json"), "w") as fh:
        json.dump(payload, fh, indent=2, default=str)
    return out_path
