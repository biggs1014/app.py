#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAXXSCAN Terminal v3.1 — Bloomberg-style momentum screener UI
v3.1: $Eff & Chg% moved next to Symbol for mobile-first scanning.
Flags column restored while keeping the new v3.1 column order.
"""

import os
import csv
import glob
import argparse
import traceback
from datetime import datetime
from flask import Flask, render_template_string, jsonify

TERMINAL_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MAXXSCAN Terminal</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
--bg:#0a0e14;--bg2:#0f1318;--bg3:#141a22;--bg4:#1a222c;
--border:#1e2a3a;--border2:#2a3a4e;
--txt:#c8d4e0;--txt2:#8899aa;--txt3:#556677;
--orange:#ff8c00;--orange2:#ffaa33;--green:#00e676;--green2:#00c853;
--red:#ff1744;--red2:#ff5252;--blue:#448aff;--blue2:#82b1ff;
--cyan:#18ffff;--yellow:#ffd600;--purple:#b388ff;
--row-hover:#111820;
}
html,body{height:100%;background:var(--bg);color:var(--txt);font-family:'JetBrains Mono',monospace;font-size:11px;overflow:hidden}
.header{background:linear-gradient(180deg,#0d1117 0%,#0a0e14 100%);border-bottom:1px solid var(--border);padding:6px 16px;display:flex;align-items:center;justify-content:space-between;height:44px}
.header-left{display:flex;align-items:center;gap:16px}
.logo{font-family:'IBM Plex Sans',sans-serif;font-weight:700;font-size:16px;color:var(--orange);letter-spacing:2px;text-transform:uppercase}
.logo span{color:var(--txt3);font-weight:400;font-size:10px;letter-spacing:1px;margin-left:8px}
.header-badge{font-size:9px;font-weight:700;padding:2px 6px;border-radius:2px;letter-spacing:1px}
.badge-live{background:var(--green);color:#000;animation:pulse-live 2s ease-in-out infinite}
.badge-stale{background:var(--yellow);color:#000}
.badge-error{background:var(--red);color:#fff}
@keyframes pulse-live{0%,100%{opacity:1}50%{opacity:.7}}
.header-right{display:flex;align-items:center;gap:12px;color:var(--txt2);font-size:10px}
.header-right .time{color:var(--orange);font-weight:600;font-size:11px}
.session-box{display:flex;align-items:center;gap:6px}
.session-name{font-weight:600;font-size:10px}
.session-countdown{color:var(--txt3);font-size:9px;font-variant-numeric:tabular-nums}
.file-info{color:var(--txt3);font-size:9px;display:flex;align-items:center;gap:6px}
.file-info .dot{width:5px;height:5px;border-radius:50%;background:var(--green);display:inline-block}
.update-ago{color:var(--txt3);font-size:9px}
.toolbar{background:var(--bg2);border-bottom:1px solid var(--border);padding:6px 16px;display:flex;align-items:center;gap:8px;height:36px;flex-wrap:nowrap;overflow-x:auto}
.toolbar label{color:var(--txt3);font-size:9px;text-transform:uppercase;letter-spacing:1px;white-space:nowrap}
.toolbar select,.toolbar input{background:var(--bg3);border:1px solid var(--border);color:var(--txt);font-family:'JetBrains Mono',monospace;font-size:10px;padding:4px 8px;border-radius:2px;outline:none}
.toolbar select:focus,.toolbar input:focus{border-color:var(--orange)}
.toolbar select option{background:var(--bg2)}
.btn{background:var(--bg3);border:1px solid var(--border);color:var(--txt2);font-family:'JetBrains Mono',monospace;font-size:10px;padding:4px 10px;border-radius:2px;cursor:pointer;transition:all .15s;white-space:nowrap}
.btn:hover{background:var(--bg4);border-color:var(--orange);color:var(--orange)}
.btn-refresh{border-color:var(--green);color:var(--green)}
.btn-refresh:hover{background:var(--green);color:#000}
.btn-refresh.loading{opacity:.5;pointer-events:none;animation:spin .8s linear infinite}
@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}
.search-box{width:160px}
.divider{width:1px;height:20px;background:var(--border);flex-shrink:0}
.count-badge{background:var(--bg3);border:1px solid var(--border);color:var(--orange);font-size:10px;padding:2px 8px;border-radius:2px;font-weight:600;white-space:nowrap}
.qf-chips{display:flex;gap:4px;align-items:center}
.qf{padding:2px 7px;border-radius:2px;font-size:8px;font-weight:700;letter-spacing:.5px;cursor:pointer;border:1px solid var(--border);background:var(--bg3);color:var(--txt3);transition:all .15s;user-select:none;white-space:nowrap}
.qf:hover{border-color:var(--orange);color:var(--orange)}
.qf.active{border-color:var(--orange);color:#000;background:var(--orange)}
.qf-gap.active{background:#ff1744;border-color:#ff1744;color:#fff}
.qf-hod.active{background:#ff8c00;border-color:#ff8c00;color:#000}
.qf-exp.active{background:#ff1744;border-color:#ff1744;color:#fff}
.qf-pm.active{background:#00e676;border-color:#00e676;color:#000}
.qf-pin.active{background:#ffd600;border-color:#ffd600;color:#000}
.qf-earn.active{background:#448aff;border-color:#448aff;color:#fff}
.stats-bar{background:var(--bg);border-bottom:1px solid var(--border);padding:4px 16px;display:flex;align-items:center;gap:24px;height:28px;overflow-x:auto}
.stat{display:flex;align-items:center;gap:4px;white-space:nowrap}
.stat-label{color:var(--txt3);font-size:9px;text-transform:uppercase;letter-spacing:1px}
.stat-val{font-size:10px;font-weight:600}
.stat-val.up{color:var(--green)}.stat-val.down{color:var(--red)}
.table-wrap{flex:1;overflow:auto;position:relative}
.table-wrap::-webkit-scrollbar{width:6px;height:6px}
.table-wrap::-webkit-scrollbar-track{background:var(--bg)}
.table-wrap::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}
.table-wrap::-webkit-scrollbar-thumb:hover{background:var(--txt3)}
table{width:100%;border-collapse:collapse;table-layout:fixed}
thead{position:sticky;top:0;z-index:10}
th{background:linear-gradient(180deg,#141a22 0%,#111820 100%);border-bottom:2px solid var(--orange);color:var(--orange);font-weight:600;font-size:9px;text-transform:uppercase;letter-spacing:1px;padding:6px 6px;text-align:left;white-space:nowrap;cursor:pointer;user-select:none}
th:hover{color:var(--orange2);background:var(--bg4)}
th.sorted-asc::after{content:" ▲";font-size:8px}
th.sorted-desc::after{content:" ▼";font-size:8px}
th.no-sort{cursor:default}
th.no-sort:hover{color:var(--orange);background:linear-gradient(180deg,#141a22 0%,#111820 100%)}

/* v3.1 mobile-first widths */
th.col-pin{width:28px;text-align:center}
th.col-rank{width:40px;text-align:center}
th.col-sym{width:68px}
th.col-price{width:66px;text-align:right}
th.col-chg{width:72px;text-align:right}
th.col-links{width:168px}
th.col-name{width:140px}
th.col-sess{width:72px}
th.col-best{width:48px;text-align:center}
th.col-preset{width:110px}
th.col-score{width:54px;text-align:center}
th.col-ml{width:54px;text-align:center}
th.col-arch{width:86px;text-align:center}
th.col-conf{width:56px;text-align:center}
th.col-gap{width:58px;text-align:right}
th.col-hod{width:52px;text-align:right}
th.col-vol{width:70px;text-align:right}
th.col-rvol{width:50px;text-align:right}
th.col-turn{width:56px;text-align:right}
th.col-vwap{width:58px;text-align:right}
th.col-spread{width:52px;text-align:right}
th.col-flags{width:160px}

td{padding:4px 6px;border-bottom:1px solid #111820;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:11px}
tr{transition:background .1s, opacity .15s}
tr:hover{background:var(--row-hover) !important}
tr.even{background:rgba(255,255,255,.01)}
tr.selected{background:#1a2233 !important;outline:1px solid var(--blue);outline-offset:-1px}
tr.pinned{background:rgba(255,214,0,.04) !important}
tr.pinned td.pin-cell .pin-star{color:var(--yellow)}
td.pin-cell{text-align:center;cursor:pointer;font-size:12px}
td.pin-cell .pin-star{color:var(--txt3);transition:color .15s}
td.pin-cell:hover .pin-star{color:var(--yellow)}
td.rank{text-align:center;color:var(--txt3);font-weight:600}
td.rank .rn{display:inline-block;min-width:20px;padding:1px 4px;border-radius:2px;font-size:10px}
tr:nth-child(-n+3) td.rank .rn{background:var(--orange);color:#000;font-weight:700}
tr:nth-child(n+4):nth-child(-n+10) td.rank .rn{background:var(--bg4);color:var(--orange)}
td.sym{font-weight:700;color:var(--cyan);letter-spacing:.5px;cursor:pointer;position:relative}
td.sym:hover{text-decoration:underline}
td.sym .copy-hint{display:none;position:absolute;top:-18px;left:0;background:var(--bg4);color:var(--orange);font-size:8px;padding:1px 4px;border-radius:2px;white-space:nowrap;pointer-events:none;z-index:20}
td.sym:hover .copy-hint{display:block}
td.sym.copied .copy-hint{display:block;background:var(--green);color:#000}
td.name{color:var(--txt2);font-size:10px}
td.price{text-align:right;font-weight:600;font-variant-numeric:tabular-nums}
td.price.above-vwap{color:var(--green)}
td.price.below-vwap{color:var(--red2)}
td.chg{text-align:right;font-weight:700;font-variant-numeric:tabular-nums}
td.chg.up{color:var(--green)}
td.chg.down{color:var(--red)}
td.num{text-align:right;color:var(--txt2);font-variant-numeric:tabular-nums}
td.center{text-align:center}
td.sess{color:var(--txt2);font-size:10px}
.sb{display:inline-block;width:40px;height:14px;background:var(--bg);border:1px solid var(--border);border-radius:2px;position:relative;overflow:hidden;vertical-align:middle}
.sf{height:100%;position:absolute;left:0;top:0;border-radius:1px}
.st{position:relative;z-index:1;display:block;text-align:center;font-size:9px;font-weight:700;line-height:14px;color:#fff;text-shadow:0 0 3px rgba(0,0,0,.8)}
.badge{display:inline-block;padding:1px 4px;border-radius:2px;font-size:8px;font-weight:700;letter-spacing:.5px;margin:0 1px}
.b-ex{background:#ff1744;color:#fff}.b-mo{background:#ff9100;color:#000}.b-ac{background:#448aff;color:#fff}.b-br{background:#00e676;color:#000}.b-vo{background:#ff6d00;color:#000}.b-df{background:var(--bg4);color:var(--txt2)}
.pt{display:inline-block;padding:1px 3px;border-radius:1px;font-size:8px;font-weight:600;margin:0 1px;letter-spacing:.3px}
.pt-FR{background:#1a237e;color:#82b1ff}.pt-VS{background:#1b5e20;color:#69f0ae}.pt-GAP{background:#b71c1c;color:#ff8a80}.pt-HOD{background:#e65100;color:#ffcc02}.pt-SW{background:#4a148c;color:#ce93d8}.pt-BW{background:#004d40;color:#80cbc4}.pt-VR{background:#3e2723;color:#bcaaa4}
.fl{display:inline-block;padding:1px 3px;border-radius:1px;font-size:7px;font-weight:700;margin:0 1px;letter-spacing:.3px}
.fl-h{background:#ff6d00;color:#000}.fl-t{background:#d50000;color:#fff}.fl-b{background:#00c853;color:#000}.fl-g{background:#2979ff;color:#fff}.fl-q{background:#b71c1c;color:#fff}.fl-liq{background:#37474f;color:#fff}.fl-ah{background:#6a1b9a;color:#fff}.fl-earn{background:#283593;color:#fff}.fl-pm{background:#1b5e20;color:#fff}.fl-exh{background:#bf360c;color:#fff}
.lk-wrap{display:flex;gap:2px;align-items:center;flex-wrap:nowrap}
.lk{display:inline-block;padding:2px 4px;border-radius:2px;font-size:7px;font-weight:700;text-decoration:none;letter-spacing:.3px;transition:all .12s;border:1px solid transparent}
.lk-n{background:#1a237e;color:#82b1ff;border-color:#283593}.lk-n:hover{background:#283593;color:#fff}
.lk-s{background:#0d47a1;color:#64b5f6;border-color:#1565c0}.lk-s:hover{background:#1565c0;color:#fff}
.lk-g{background:#1b5e20;color:#81c784;border-color:#2e7d32}.lk-g:hover{background:#2e7d32;color:#fff}
.lk-all{background:var(--bg4);color:var(--orange);border:1px solid var(--border);font-size:7px;font-weight:700;padding:2px 4px;border-radius:2px;cursor:pointer;letter-spacing:.3px;transition:all .12s;text-decoration:none}
.lk-all:hover{background:var(--orange);color:#000;border-color:var(--orange)}
.lk-tv{background:#131722;color:#2962ff;border:1px solid #2962ff;font-size:7px;font-weight:700;padding:2px 4px;border-radius:2px;text-decoration:none;transition:all .12s}
.lk-tv:hover{background:#2962ff;color:#fff}
.load-more-wrap{padding:10px 16px;text-align:center;border-top:1px solid var(--border);background:var(--bg2)}
.load-btn{background:linear-gradient(180deg,var(--bg3),var(--bg));border:1px solid var(--orange);color:var(--orange);font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:600;padding:8px 32px;border-radius:2px;cursor:pointer;letter-spacing:1px;transition:all .15s}
.load-btn:hover{background:var(--orange);color:#000}
.footer{background:var(--bg2);border-top:1px solid var(--border);padding:4px 16px;display:flex;justify-content:space-between;height:24px;align-items:center}
.footer-left,.footer-right{color:var(--txt3);font-size:9px}
.footer-center{color:var(--txt3);font-size:8px;letter-spacing:.5px}
.kbd{display:inline-block;background:var(--bg4);border:1px solid var(--border);border-radius:2px;padding:0 3px;font-size:8px;font-weight:600;color:var(--txt2);margin:0 1px}
.overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.65);z-index:100;backdrop-filter:blur(2px)}
.overlay.open{display:flex;align-items:center;justify-content:center}
.panel{background:var(--bg2);border:1px solid var(--orange);border-radius:4px;width:780px;max-height:85vh;overflow-y:auto;box-shadow:0 0 60px rgba(255,140,0,.12)}
.panel::-webkit-scrollbar{width:5px}.panel::-webkit-scrollbar-thumb{background:var(--border2);border-radius:3px}
.ph{background:linear-gradient(180deg,var(--bg3),var(--bg2));padding:12px 16px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center}
.ph h2{font-family:'IBM Plex Sans',sans-serif;font-size:18px;color:var(--cyan);font-weight:700}
.ph h2 span{color:var(--txt2);font-size:12px;font-weight:400;margin-left:8px}
.close-btn{background:none;border:1px solid var(--border);color:var(--txt2);width:26px;height:26px;border-radius:2px;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center}
.close-btn:hover{border-color:var(--red);color:var(--red)}
.pb{padding:16px}
.price-hero{display:flex;gap:16px;align-items:baseline;margin-bottom:16px}
.price-hero .px{font-size:28px;font-weight:700;font-family:'IBM Plex Sans',sans-serif}
.price-hero .pc{font-size:18px;font-weight:700}
.price-hero .pc.up{color:var(--green)}.price-hero .pc.down{color:var(--red)}
.price-hero .ex{color:var(--txt3);font-size:11px}
.section{margin-top:14px;padding-top:12px;border-top:1px solid #111820}
.section-title{color:var(--orange);font-weight:700;font-size:10px;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px}
.dg{display:grid;grid-template-columns:1fr 1fr;gap:8px 16px}
.dr{display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #111820}
.dr .dl{color:var(--txt3);font-size:10px}.dr .dv{font-weight:600;font-size:11px;max-width:60%;text-align:right;overflow:hidden;text-overflow:ellipsis}
.ah-box{margin-top:12px;padding:8px 12px;background:var(--bg);border:1px solid var(--border);border-radius:2px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.ah-label{color:var(--txt3);font-size:9px;text-transform:uppercase;letter-spacing:1px}
.dl-links{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
.dl-link{display:inline-flex;align-items:center;gap:4px;padding:8px 14px;border-radius:2px;font-size:11px;font-weight:600;text-decoration:none;border:1px solid var(--border);transition:all .15s;color:var(--txt)}
.dl-link:hover{border-color:var(--orange);color:var(--orange);background:var(--bg4)}
.loading-screen{position:fixed;top:0;left:0;width:100%;height:100%;background:var(--bg);z-index:200;display:flex;flex-direction:column;align-items:center;justify-content:center;transition:opacity .3s}
.loading-screen.hidden{opacity:0;pointer-events:none}
.loading-title{font-family:'IBM Plex Sans',sans-serif;font-size:24px;color:var(--orange);font-weight:700;letter-spacing:4px;margin-bottom:16px}
.loading-bar{width:200px;height:3px;background:var(--bg3);border-radius:2px;overflow:hidden}
.loading-fill{height:100%;background:var(--orange);border-radius:2px;animation:load-pulse 1.5s ease-in-out infinite}
@keyframes load-pulse{0%{width:0;margin-left:0}50%{width:70%}100%{width:0;margin-left:100%}}
.loading-sub{color:var(--txt3);font-size:10px;margin-top:12px;letter-spacing:1px}
.app{display:flex;flex-direction:column;height:100vh}
.table-wrap::before{content:"";position:absolute;top:0;left:0;right:0;bottom:0;pointer-events:none;z-index:5;background:repeating-linear-gradient(0deg,rgba(0,0,0,.03) 0px,rgba(0,0,0,.03) 1px,transparent 1px,transparent 2px)}
.toast{position:fixed;bottom:40px;right:20px;background:var(--bg3);border:1px solid var(--orange);color:var(--orange);padding:8px 16px;border-radius:2px;font-size:10px;font-weight:600;z-index:300;opacity:0;transition:opacity .3s;pointer-events:none}
.toast.show{opacity:1}
</style>
</head>
<body>
<div class="loading-screen" id="loadingScreen"><div class="loading-title">MAXXSCAN</div><div class="loading-bar"><div class="loading-fill"></div></div><div class="loading-sub">LOADING SCREENER DATA...</div></div>
<div class="app">
  <div class="header"><div class="header-left"><div class="logo">MAXXSCAN<span>MOMENTUM SCREENER</span></div><div class="header-badge badge-live" id="statusBadge">LIVE</div><div class="file-info" id="fileInfo"><span class="dot" id="statusDot"></span><span id="fileName">&mdash;</span><span class="update-ago" id="updateAgo"></span></div></div><div class="header-right"><div class="session-box"><span class="session-name" id="sessionLabel"></span><span class="session-countdown" id="sessionCountdown"></span></div><span style="display:inline-block;width:1px;height:14px;background:var(--border)"></span><span class="time" id="clock"></span></div></div>
  <div class="toolbar"><label>Show</label><select id="showCount"><option value="25">25</option><option value="50">50</option><option value="100">100</option><option value="200">200</option><option value="99999">All</option></select><div class="divider"></div><label>Type</label><select id="archFilter"><option value="">ALL</option></select><div class="divider"></div><label>Preset</label><select id="presetFilter"><option value="">ALL</option><option value="FR">FR</option><option value="VS">VS</option><option value="GAP">GAP</option><option value="HOD">HOD</option><option value="SW">SW</option><option value="BW">BW</option><option value="VR">VR</option></select><div class="divider"></div><input type="text" id="searchBox" class="search-box" placeholder="&#128269; Symbol / name..."><div class="divider"></div><div class="qf-chips"><span class="qf qf-pin" data-qf="pinned" title="Show pinned only">&#9733; PINS</span><span class="qf qf-gap" data-qf="gap">GAP&gt;5%</span><span class="qf qf-hod" data-qf="hod">@ HOD</span><span class="qf qf-exp" data-qf="explosive">EXPLOSIVE</span><span class="qf qf-pm" data-qf="pm">PM&#10003;</span><span class="qf qf-earn" data-qf="earnings">EARN</span></div><div class="divider"></div><button class="btn btn-refresh" id="refreshBtn" title="Reload CSV (R)">&#10227;</button><button class="btn" id="exportBtn" title="Export filtered view as CSV">&#11015; CSV</button><div class="divider"></div><span class="count-badge" id="countBadge">0 / 0</span></div>
  <div class="stats-bar" id="statsBar"></div>
  <div class="table-wrap" id="tableWrap"><table><thead id="thead"></thead><tbody id="tbody"></tbody></table></div>
  <div class="load-more-wrap" id="loadMoreWrap" style="display:none"><button class="load-btn" id="loadMoreBtn">&#9660; LOAD +25 MORE &#9660;</button></div>
  <div class="footer"><div class="footer-left">MAXXSCAN v3.1 &mdash; <span id="dataTs">&mdash;</span></div><div class="footer-center"><span class="kbd">&uarr;&darr;</span> nav <span class="kbd">Enter</span> detail <span class="kbd">N</span> news <span class="kbd">T</span> chart <span class="kbd">P</span> pin <span class="kbd">R</span> refresh <span class="kbd">/</span> search <span class="kbd">Esc</span> close</div><div class="footer-right">SHOWN: <span id="fShown">0</span> | FILTERED: <span id="fFiltered">0</span> | TOTAL: <span id="fTotal">0</span></div></div>
</div>
<div class="overlay" id="overlay"><div class="panel" id="panel"></div></div>
<div class="toast" id="toast"></div>

<script>
let C={},CSV_COLUMNS=[],ALL_DATA=[],filtered=[],displayCount=25;
let sortColName=null,sortDir='asc';
let lastModified='',dataLoadTime=null;
let selectedIdx=-1;
let pinnedSymbols=new Set();
let activeQF=new Set();

try{const p=JSON.parse(localStorage.getItem('maxxscan_pins')||'[]');p.forEach(s=>pinnedSymbols.add(s))}catch(e){}
function savePins(){try{localStorage.setItem('maxxscan_pins',JSON.stringify([...pinnedSymbols]))}catch(e){}}

/* v3.1 column order: ★ # SYM $EFF CHG% LINKS NAME SESS ... FLAGS */
const TABLE_COLS=[
  {name:'_pin',            key:'PN', label:'★',      cls:'col-pin',    nosort:true},
  {name:'master_rank',     key:'RK', label:'#',      cls:'col-rank'},
  {name:'symbol',          key:'SY', label:'Symbol', cls:'col-sym'},
  {name:'px_eff',          key:'PX', label:'$Eff',   cls:'col-price'},
  {name:'chg_eff',         key:'CH', label:'Chg%',   cls:'col-chg'},
  {name:'_links',          key:'LK', label:'Links',  cls:'col-links',  nosort:true},
  {name:'name',            key:'NM', label:'Name',   cls:'col-name'},
  {name:'session',         key:'SS', label:'Sess',   cls:'col-sess'},
  {name:'best_preset',     key:'BP', label:'Best',   cls:'col-best'},
  {name:'presets_list',    key:'PL', label:'Presets',cls:'col-preset'},
  {name:'composite_score', key:'CS', label:'Score',  cls:'col-score'},
  {name:'ml_final_score',  key:'ML', label:'ML',     cls:'col-ml'},
  {name:'ml_archetype',    key:'AR', label:'Type',   cls:'col-arch'},
  {name:'ml_confidence',   key:'CF', label:'Conf',   cls:'col-conf'},
  {name:'gap_pct',         key:'GA', label:'Gap%',   cls:'col-gap'},
  {name:'hod_distance',    key:'HD', label:'HOD%',   cls:'col-hod'},
  {name:'vol_eff',         key:'VO', label:'Vol',    cls:'col-vol'},
  {name:'rel_volume',      key:'RV', label:'RVol',   cls:'col-rvol'},
  {name:'turnover_rate',   key:'TU', label:'Turn',   cls:'col-turn'},
  {name:'vwap',            key:'VW', label:'VWAP',   cls:'col-vwap'},
  {name:'spread_pct',      key:'SP', label:'Sprd',   cls:'col-spread'},
  {name:'_flags',          key:'FL', label:'Flags',  cls:'col-flags',  nosort:true},
];

function hasCol(n){return Object.prototype.hasOwnProperty.call(C,n)}
function gv(r,c){const i=C[c];return(i===undefined||!Array.isArray(r))?'':r[i]}
function isTrueLike(v){return v===true||String(v).toLowerCase()==='true'||String(v)==='1'}
function num(v,f=0){const n=Number(v);return Number.isFinite(n)?n:f}
function getEffPrice(r){return num(gv(r,'px_eff')||gv(r,'price')||0)}
function getEffChg(r){return num(gv(r,'chg_eff')||gv(r,'change_pct')||0)}
function getEffVol(r){return num(gv(r,'vol_eff')||gv(r,'volume')||0)}
function getSym(r){return(gv(r,'symbol')||'').toString()}

/* Keep only TV + Google News + StockTwits + Google Finance in row links */
function getRowLinks(r){
  const links=[],sym=getSym(r);
  const gn=gv(r,'lnk_Google_News'),st=gv(r,'lnk_StockTwits'),gf=gv(r,'lnk_Google_Finance');
  if(sym)links.push({url:'https://www.tradingview.com/chart/?symbol='+encodeURIComponent(sym),label:'TV',cls:'lk-tv'});
  if(gn)links.push({url:gn,label:'NEWS',cls:'lk-n'});
  if(st)links.push({url:st,label:'STWT',cls:'lk-s'});
  if(gf)links.push({url:gf,label:'GFIN',cls:'lk-g'});
  return links;
}

async function init(){
  buildHeader();updateClock();setInterval(updateClock,1000);setInterval(updateAgo,15000);
  document.getElementById('showCount').addEventListener('change',e=>{displayCount=+e.target.value;render()});
  document.getElementById('archFilter').addEventListener('change',()=>applyFilters());
  document.getElementById('presetFilter').addEventListener('change',()=>applyFilters());
  document.getElementById('searchBox').addEventListener('input',()=>applyFilters());
  document.getElementById('refreshBtn').addEventListener('click',()=>loadData());
  document.getElementById('exportBtn').addEventListener('click',exportCSV);
  document.getElementById('loadMoreBtn').addEventListener('click',()=>{displayCount+=25;render()});
  document.getElementById('overlay').addEventListener('click',e=>{if(e.target===e.currentTarget)closeDetail()});
  document.querySelectorAll('.qf').forEach(el=>{el.addEventListener('click',()=>{const f=el.dataset.qf;if(activeQF.has(f)){activeQF.delete(f);el.classList.remove('active')}else{activeQF.add(f);el.classList.add('active')}applyFilters()})});
  document.addEventListener('keydown',handleKeyboard);
  setInterval(checkForUpdates,30000);
  await loadData();
}

function handleKeyboard(e){
  if(document.activeElement&&document.activeElement.id==='searchBox'){if(e.key==='Escape'){document.activeElement.blur();e.preventDefault()}return}
  const isOpen=document.getElementById('overlay').classList.contains('open');
  if(e.key==='Escape'){if(isOpen){closeDetail();e.preventDefault();return}selectedIdx=-1;renderSelection();return}
  if(e.key==='/'){e.preventDefault();document.getElementById('searchBox').focus();return}
  if((e.key==='r'||e.key==='R')&&!e.ctrlKey&&!e.metaKey){loadData();e.preventDefault();return}
  if(isOpen)return;
  const shown=filtered.slice(0,displayCount);if(!shown.length)return;
  if(e.key==='ArrowDown'){e.preventDefault();selectedIdx=Math.min(selectedIdx+1,shown.length-1);renderSelection();scrollToSelected()}
  else if(e.key==='ArrowUp'){e.preventDefault();selectedIdx=Math.max(selectedIdx-1,0);renderSelection();scrollToSelected()}
  else if(e.key==='Enter'&&selectedIdx>=0){e.preventDefault();openDetail(shown[selectedIdx])}
  else if((e.key==='n'||e.key==='N')&&selectedIdx>=0){e.preventDefault();const news=gv(shown[selectedIdx],'lnk_Google_News');if(news)window.open(news,'_blank')}
  else if((e.key==='t'||e.key==='T')&&selectedIdx>=0){e.preventDefault();const s=getSym(shown[selectedIdx]);if(s)window.open('https://www.tradingview.com/chart/?symbol='+encodeURIComponent(s),'_blank')}
  else if((e.key==='p'||e.key==='P')&&selectedIdx>=0){e.preventDefault();togglePin(getSym(shown[selectedIdx]));render()}
}
function renderSelection(){document.querySelectorAll('#tbody tr').forEach((tr,i)=>{tr.classList.toggle('selected',i===selectedIdx)})}
function scrollToSelected(){const rows=document.querySelectorAll('#tbody tr');if(rows[selectedIdx])rows[selectedIdx].scrollIntoView({block:'nearest',behavior:'smooth'})}
function togglePin(sym){if(!sym)return;sym=sym.toUpperCase();if(pinnedSymbols.has(sym))pinnedSymbols.delete(sym);else pinnedSymbols.add(sym);savePins()}

async function loadData(){
  const btn=document.getElementById('refreshBtn');btn.classList.add('loading');
  try{
    const resp=await fetch('/api/data');const data=await resp.json();
    if(data.error){showToast('⚠ '+data.error);updateStatus('error');return}
    CSV_COLUMNS=Array.isArray(data.columns)?data.columns:[];
    C=data.col_index||{};ALL_DATA=Array.isArray(data.rows)?data.rows:[];
    lastModified=data.modified||'';dataLoadTime=new Date();
    populateFilters();applyFilters();
    document.getElementById('fileName').textContent=data.file||'—';
    document.getElementById('dataTs').textContent=(data.file||'—')+' — '+(data.modified||'—');
    document.getElementById('fTotal').textContent=Number(data.total||0).toLocaleString();
    if(ALL_DATA.length&&hasCol('session')){const sess=(gv(ALL_DATA[0],'session')||'').toString();if(sess)document.getElementById('sessionLabel').textContent=sess}
    updateStatus('live');updateAgo();showToast('✓ '+Number(data.total||0).toLocaleString()+' tickers loaded');
  }catch(err){showToast('⚠ '+err.message);updateStatus('error')}
  finally{btn.classList.remove('loading');document.getElementById('loadingScreen').classList.add('hidden')}
}
async function checkForUpdates(){try{const r=await fetch('/api/status');const s=await r.json();if(s.ok&&s.modified!==lastModified){showToast('🔄 CSV updated…');await loadData()}}catch(e){}}
function updateAgo(){if(!dataLoadTime){document.getElementById('updateAgo').textContent='';return}const s=Math.floor((Date.now()-dataLoadTime.getTime())/1000);let txt;if(s<60)txt='just now';else if(s<3600)txt=Math.floor(s/60)+'m ago';else txt=Math.floor(s/3600)+'h ago';document.getElementById('updateAgo').textContent='· '+txt}
function updateStatus(state){const b=document.getElementById('statusBadge'),d=document.getElementById('statusDot');b.className='header-badge';if(state==='live'){b.classList.add('badge-live');b.textContent='LIVE';d.style.background='var(--green)'}else if(state==='error'){b.classList.add('badge-error');b.textContent='ERROR';d.style.background='var(--red)'}else{b.classList.add('badge-stale');b.textContent='STALE';d.style.background='var(--yellow)'}}
function showToast(m){const t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2800)}

function populateFilters(){
  const archs=new Set();
  ALL_DATA.forEach(r=>{const a=(gv(r,'ml_archetype')||'').toString();if(a)archs.add(a)});
  const af=document.getElementById('archFilter');const prev=af.value;
  af.innerHTML='<option value="">ALL</option>';
  [...archs].sort().forEach(a=>{const o=document.createElement('option');o.value=a;o.textContent=a;af.appendChild(o)});
  af.value=prev;
}

function applyFilters(){
  const arch=document.getElementById('archFilter').value,preset=document.getElementById('presetFilter').value,q=document.getElementById('searchBox').value.toUpperCase();
  filtered=ALL_DATA.filter(r=>{
    const sym=getSym(r).toUpperCase(),name=(gv(r,'name')??'').toString().toUpperCase(),archetype=(gv(r,'ml_archetype')??'').toString(),presetList=(gv(r,'presets_list')??'').toString();
    if(arch&&archetype!==arch)return false;
    if(preset&&!presetList.includes(preset))return false;
    if(q&&!sym.includes(q)&&!name.includes(q))return false;
    if(activeQF.has('pinned')&&!pinnedSymbols.has(sym))return false;
    if(activeQF.has('gap')&&num(gv(r,'gap_pct'),0)<=5)return false;
    if(activeQF.has('hod')&&!isTrueLike(gv(r,'flag_hod')))return false;
    if(activeQF.has('explosive')&&archetype!=='EXPLOSIVE')return false;
    if(activeQF.has('pm')&&!isTrueLike(gv(r,'flag_pm_active')))return false;
    if(activeQF.has('earnings')&&!isTrueLike(gv(r,'flag_has_earnings')))return false;
    return true;
  });
  if(sortColName!==null)doSort();
  else{
    const pinned=[],unpinned=[];filtered.forEach(r=>{if(pinnedSymbols.has(getSym(r).toUpperCase()))pinned.push(r);else unpinned.push(r)});
    filtered=[...pinned,...unpinned];
  }
  selectedIdx=-1;render();
}

function buildHeader(){
  const tr=document.createElement('tr');
  TABLE_COLS.forEach(c=>{
    const th=document.createElement('th');
    th.className=c.cls+(c.nosort?' no-sort':'');
    th.textContent=c.label;
    th.dataset.name=c.name;
    if(!c.nosort&&c.name&&!c.name.startsWith('_')){
      th.addEventListener('click',()=>{
        if(sortColName===c.name)sortDir=sortDir==='asc'?'desc':'asc';
        else{sortColName=c.name;sortDir=c.name==='master_rank'?'asc':'desc'}
        document.querySelectorAll('th').forEach(t=>t.classList.remove('sorted-asc','sorted-desc'));
        th.classList.add(sortDir==='asc'?'sorted-asc':'sorted-desc');
        doSort();render();
      });
    }
    tr.appendChild(th);
  });
  document.getElementById('thead').innerHTML='';
  document.getElementById('thead').appendChild(tr);
}

function sortValue(row,colName){
  if(colName==='px_eff')return getEffPrice(row);
  if(colName==='chg_eff')return getEffChg(row);
  if(colName==='vol_eff')return getEffVol(row);
  const v=gv(row,colName);const n=Number(v);if(v!==''&&Number.isFinite(n))return n;return(v??'').toString();
}
function doSort(){
  const pinned=[],unpinned=[];filtered.forEach(r=>{if(pinnedSymbols.has(getSym(r).toUpperCase()))pinned.push(r);else unpinned.push(r)});
  const cmp=(a,b)=>{const va=sortValue(a,sortColName),vb=sortValue(b,sortColName);if(typeof va==='number'&&typeof vb==='number')return sortDir==='asc'?(va-vb):(vb-va);return sortDir==='asc'?String(va).localeCompare(String(vb)):String(vb).localeCompare(String(va))};
  pinned.sort(cmp);unpinned.sort(cmp);filtered=[...pinned,...unpinned];
}

function fV(v){v=num(v,0);if(!v)return'—';if(v>=1e9)return(v/1e9).toFixed(1)+'B';if(v>=1e6)return(v/1e6).toFixed(1)+'M';if(v>=1e3)return(v/1e3).toFixed(1)+'K';return v.toString()}
function fM(v){v=num(v,0);if(!v)return'—';if(v>=1e9)return'$'+(v/1e9).toFixed(2)+'B';if(v>=1e6)return'$'+(v/1e6).toFixed(1)+'M';if(v>=1e3)return'$'+(v/1e3).toFixed(0)+'K';return'$'+v}
function fP(v){if(v===''||v===null||v===undefined)return'—';v=num(v,NaN);if(!Number.isFinite(v))return'—';return(v>0?'+':'')+v.toFixed(2)+'%'}
function sC(v){v=num(v,0);if(v>=80)return'var(--green)';if(v>=60)return'var(--green2)';if(v>=40)return'var(--yellow)';if(v>=20)return'var(--orange)';return'var(--red)'}
function N(v){const n=num(v,NaN);return Number.isFinite(n)?n.toFixed(2):'—'}
function escAttr(s){return String(s??'').replace(/"/g,'&quot;')}

function archB(v){const m={'EXPLOSIVE':'b-ex','MOMENTUM':'b-mo','ACCUMULATION':'b-ac','BREAKOUT':'b-br','VOLATILE':'b-vo'};const t=(v||'—').toString();return'<span class="badge '+(m[t]||'b-df')+'">'+t+'</span>'}
function presetT(l){if(!l)return'—';return String(l).split('|').filter(Boolean).map(p=>'<span class="pt pt-'+p+'">'+p+'</span>').join('')||'—'}

function flagT(r){
  let h='';
  if(isTrueLike(gv(r,'flag_hod')))h+='<span class="fl fl-h">HOD</span>';
  if(isTrueLike(gv(r,'flag_thin_supply')))h+='<span class="fl fl-t">THIN</span>';
  if(isTrueLike(gv(r,'flag_big_move')))h+='<span class="fl fl-b">BIG</span>';
  if(isTrueLike(gv(r,'flag_gap_up')))h+='<span class="fl fl-g">GAP↑</span>';
  if(isTrueLike(gv(r,'flag_pm_active')))h+='<span class="fl fl-pm">PM✓</span>';
  if(isTrueLike(gv(r,'flag_illiquid')))h+='<span class="fl fl-liq">ILLQ</span>';
  if(isTrueLike(gv(r,'flag_broken_quote')))h+='<span class="fl fl-q">QUOTE</span>';
  if(isTrueLike(gv(r,'flag_no_dollar_vol')))h+='<span class="fl fl-liq">$VOL</span>';
  if(isTrueLike(gv(r,'flag_low_ah_liquidity')))h+='<span class="fl fl-ah">AH-LIQ</span>';
  if(isTrueLike(gv(r,'flag_session_reversal')))h+='<span class="fl fl-q">REV</span>';
  if(isTrueLike(gv(r,'flag_session_exhaustion')))h+='<span class="fl fl-exh">EXH</span>';
  if(isTrueLike(gv(r,'flag_has_earnings')))h+='<span class="fl fl-earn">EARN</span>';
  return h||'<span style="color:var(--txt3)">—</span>';
}

function linkCell(r){
  const links=getRowLinks(r);
  if(!links.length)return'<span style="color:var(--txt3)">—</span>';
  let h='<div class="lk-wrap">';
  links.forEach(l=>{h+='<a href="'+escAttr(l.url)+'" target="_blank" rel="noopener" class="lk '+l.cls+'" onclick="event.stopPropagation()" title="'+escAttr(l.label)+'">'+l.label+'</a>'});
  h+='<span class="lk-all" onclick="event.stopPropagation();openAllLinks(this)" data-sym="'+escAttr(getSym(r))+'" title="Open all links">ALL</span></div>';
  return h;
}
function openAllLinks(el){el.style.background='var(--green)';el.style.color='#000';const sym=el.dataset.sym;const row=ALL_DATA.find(r=>getSym(r)===sym);if(!row)return;getRowLinks(row).forEach(l=>window.open(l.url,'_blank'));setTimeout(()=>{el.style.background='';el.style.color=''},600)}
function copySymbol(td,sym){navigator.clipboard.writeText(sym).then(()=>{td.classList.add('copied');td.querySelector('.copy-hint').textContent='✓ Copied!';setTimeout(()=>{td.classList.remove('copied');td.querySelector('.copy-hint').textContent='Click to copy'},800)})}
function applyRowVisualQuality(tr,r){const broken=isTrueLike(gv(r,'flag_broken_quote')),noDollar=isTrueLike(gv(r,'flag_no_dollar_vol'));const illiq=isTrueLike(gv(r,'flag_illiquid')),spread=num(gv(r,'spread_pct'),0);if(broken||noDollar)tr.style.opacity='0.62';if(broken)tr.style.boxShadow='inset 3px 0 0 rgba(255,23,68,.75)';else if(illiq||spread>3)tr.style.boxShadow='inset 3px 0 0 rgba(255,82,82,.45)';else if(isTrueLike(gv(r,'flag_pm_active')))tr.style.boxShadow='inset 3px 0 0 rgba(0,230,118,.35)'}

function render(){
  const shown=filtered.slice(0,displayCount);
  const tbody=document.getElementById('tbody');
  tbody.innerHTML='';
  shown.forEach((r,i)=>{
    const tr=document.createElement('tr');if(i%2===0)tr.className='even';
    const sym=getSym(r),symUp=sym.toUpperCase();const isPinned=pinnedSymbols.has(symUp);
    if(isPinned)tr.classList.add('pinned');if(i===selectedIdx)tr.classList.add('selected');
    tr.style.cursor='pointer';
    tr.addEventListener('click',()=>{selectedIdx=i;renderSelection();openDetail(r)});
    tr.addEventListener('dblclick',e=>{e.preventDefault();if(sym)window.open('https://www.tradingview.com/chart/?symbol='+encodeURIComponent(sym),'_blank')});

    const px=getEffPrice(r),ch=getEffChg(r),vo=getEffVol(r);
    const rv=num(gv(r,'rel_volume'),0),cs=num(gv(r,'composite_score'),0),ml=num(gv(r,'ml_final_score'),0);
    const ga=num(gv(r,'gap_pct'),0),hd=num(gv(r,'hod_distance'),0);
    const tu=num(gv(r,'turnover_rate'),0),vw=num(gv(r,'vwap'),NaN),sp=num(gv(r,'spread_pct'),NaN);
    const cc=ch>=0?'up':'down';const sw=Math.min(100,Math.max(0,cs)),mw=Math.min(100,Math.max(0,ml));
    let pxCls='price';if(Number.isFinite(vw)&&vw>0){if(px>vw*1.001)pxCls='price above-vwap';else if(px<vw*0.999)pxCls='price below-vwap'}

    tr.innerHTML=
      '<td class="pin-cell" onclick="event.stopPropagation();togglePin(\''+escAttr(sym)+'\');render()"><span class="pin-star">'+(isPinned?'★':'☆')+'</span></td>'+
      '<td class="rank"><span class="rn">'+(gv(r,'master_rank')??'')+'</span></td>'+
      '<td class="sym" onclick="event.stopPropagation();copySymbol(this,\''+escAttr(sym)+'\')">'+sym+'<span class="copy-hint">Click to copy</span></td>'+
      '<td class="'+pxCls+'">$'+px.toFixed(2)+'</td>'+
      '<td class="chg '+cc+'">'+fP(ch)+'</td>'+
      '<td>'+linkCell(r)+'</td>'+
      '<td class="name" title="'+escAttr(gv(r,'name'))+'">'+(gv(r,'name')??'')+'</td>'+
      '<td class="sess">'+(gv(r,'session')??'')+'</td>'+
      '<td class="center">'+(gv(r,'best_preset')||'—')+'</td>'+
      '<td>'+presetT(gv(r,'presets_list'))+'</td>'+
      '<td class="center"><span class="sb"><span class="sf" style="width:'+sw+'%;background:'+sC(cs)+'"></span><span class="st">'+cs.toFixed(0)+'</span></span></td>'+
      '<td class="center"><span class="sb"><span class="sf" style="width:'+mw+'%;background:'+sC(ml)+'"></span><span class="st">'+ml.toFixed(0)+'</span></span></td>'+
      '<td class="center">'+archB(gv(r,'ml_archetype'))+'</td>'+
      '<td class="center">'+(gv(r,'ml_confidence')||'—')+'</td>'+
      '<td class="num" style="color:'+(ga>0?'var(--green)':'var(--txt2)')+'">'+fP(ga)+'</td>'+
      '<td class="num">'+(Number.isFinite(hd)?hd.toFixed(1)+'%':'—')+'</td>'+
      '<td class="num">'+fV(vo)+'</td>'+
      '<td class="num" style="color:'+(rv>=5?'var(--green)':rv>=2?'var(--yellow)':'var(--txt2)')+'">'+rv.toFixed(1)+'x</td>'+
      '<td class="num">'+(Number.isFinite(tu)?tu.toFixed(2)+'x':'—')+'</td>'+
      '<td class="num">'+(Number.isFinite(vw)?'$'+vw.toFixed(2):'—')+'</td>'+
      '<td class="num">'+(Number.isFinite(sp)?fP(sp):'—')+'</td>'+
      '<td>'+flagT(r)+'</td>';

    applyRowVisualQuality(tr,r);
    tbody.appendChild(tr);
  });
  document.getElementById('countBadge').textContent=shown.length+' / '+filtered.length;
  document.getElementById('fShown').textContent=shown.length;
  document.getElementById('fFiltered').textContent=filtered.length;
  document.getElementById('loadMoreWrap').style.display=shown.length<filtered.length?'block':'none';
  updateStats(shown);
}

function updateStats(shown){
  if(!shown.length){document.getElementById('statsBar').innerHTML='<span style="color:var(--txt3)">No results</span>';return}
  const avg=shown.reduce((a,r)=>a+getEffChg(r),0)/shown.length;
  const tv=shown.reduce((a,r)=>a+getEffVol(r),0);
  const as=shown.reduce((a,r)=>a+num(gv(r,'composite_score'),0),0)/shown.length;
  const gp=shown.filter(r=>num(gv(r,'gap_pct'),0)>5).length;
  const ex=shown.filter(r=>(gv(r,'ml_archetype')||'')==='EXPLOSIVE').length;
  const hod=shown.filter(r=>isTrueLike(gv(r,'flag_hod'))).length;
  const pins=shown.filter(r=>pinnedSymbols.has(getSym(r).toUpperCase())).length;
  const risk=shown.filter(r=>isTrueLike(gv(r,'flag_broken_quote'))||isTrueLike(gv(r,'flag_no_dollar_vol'))).length;
  document.getElementById('statsBar').innerHTML=
    '<div class="stat"><span class="stat-label">Avg Chg</span><span class="stat-val '+(avg>=0?'up':'down')+'">'+fP(avg)+'</span></div>'+
    '<div class="stat"><span class="stat-label">Tot Vol</span><span class="stat-val">'+fV(tv)+'</span></div>'+
    '<div class="stat"><span class="stat-label">Avg Score</span><span class="stat-val" style="color:'+sC(as)+'">'+as.toFixed(1)+'</span></div>'+
    '<div class="stat"><span class="stat-label">Gap&gt;5%</span><span class="stat-val up">'+gp+'</span></div>'+
    '<div class="stat"><span class="stat-label">Explosive</span><span class="stat-val" style="color:var(--red)">'+ex+'</span></div>'+
    '<div class="stat"><span class="stat-label">@ HOD</span><span class="stat-val" style="color:var(--orange)">'+hod+'</span></div>'+
    '<div class="stat"><span class="stat-label">★ Pinned</span><span class="stat-val" style="color:var(--yellow)">'+pins+'</span></div>'+
    '<div class="stat"><span class="stat-label">⚠ Risk</span><span class="stat-val" style="color:'+(risk?'var(--red)':'var(--txt2)')+'">'+risk+'</span></div>';
}

/* Export aligned to v3.1 visible order + flags text */
function exportCSV(){
  if(!filtered.length){showToast('Nothing to export');return}
  const headers=['Rank','Symbol','PxEff','ChgEff%','Name','Sector','Session','BestPreset','Presets','Score','ML','Archetype','Conf','Gap%','HOD%','VolEff','RVol','Turn','VWAP','Spread%','Flags'];
  const rows=filtered.map(r=>[
    gv(r,'master_rank'),
    getSym(r),
    getEffPrice(r).toFixed(2),
    getEffChg(r).toFixed(2),
    gv(r,'name'),
    gv(r,'sector'),
    gv(r,'session'),
    gv(r,'best_preset'),
    gv(r,'presets_list'),
    num(gv(r,'composite_score'),0).toFixed(1),
    num(gv(r,'ml_final_score'),0).toFixed(1),
    gv(r,'ml_archetype'),
    gv(r,'ml_confidence'),
    num(gv(r,'gap_pct'),0).toFixed(2),
    num(gv(r,'hod_distance'),0).toFixed(1),
    getEffVol(r),
    num(gv(r,'rel_volume'),0).toFixed(1),
    num(gv(r,'turnover_rate'),0).toFixed(2),
    N(gv(r,'vwap')),
    N(gv(r,'spread_pct')),
    [
      isTrueLike(gv(r,'flag_hod')) ? 'HOD' : '',
      isTrueLike(gv(r,'flag_thin_supply')) ? 'THIN' : '',
      isTrueLike(gv(r,'flag_big_move')) ? 'BIG' : '',
      isTrueLike(gv(r,'flag_gap_up')) ? 'GAP↑' : '',
      isTrueLike(gv(r,'flag_pm_active')) ? 'PM✓' : '',
      isTrueLike(gv(r,'flag_illiquid')) ? 'ILLQ' : '',
      isTrueLike(gv(r,'flag_broken_quote')) ? 'QUOTE' : '',
      isTrueLike(gv(r,'flag_no_dollar_vol')) ? '$VOL' : '',
      isTrueLike(gv(r,'flag_low_ah_liquidity')) ? 'AH-LIQ' : '',
      isTrueLike(gv(r,'flag_session_reversal')) ? 'REV' : '',
      isTrueLike(gv(r,'flag_session_exhaustion')) ? 'EXH' : '',
      isTrueLike(gv(r,'flag_has_earnings')) ? 'EARN' : ''
    ].filter(Boolean).join('|')
  ]);
  let csv=headers.join(',')+'\n';rows.forEach(r=>{csv+=r.map(v=>'"'+String(v).replace(/"/g,'""')+'"').join(',')+'\n'});
  const blob=new Blob([csv],{type:'text/csv'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download='maxxscan_export_'+new Date().toISOString().slice(0,10)+'.csv';
  a.click();
  showToast('✓ Exported '+rows.length+' rows');
}

function buildDetailRow(l,v){return'<div class="dr"><span class="dl">'+l+'</span><span class="dv">'+v+'</span></div>'}

function openDetail(r){
  const ch=getEffChg(r),px=getEffPrice(r),cc=ch>=0?'up':'down',sym=getSym(r);
  const bid=num(gv(r,'bid_price'),NaN),ask=num(gv(r,'ask_price'),NaN),bsz=gv(r,'bid_size'),asz=gv(r,'ask_size');
  const spread=num(gv(r,'spread_pct'),NaN),rv=num(gv(r,'rel_volume'),0),gap=num(gv(r,'gap_pct'),0),hdd=num(gv(r,'hod_distance'),NaN);
  const ahPx=num(gv(r,'after_hours_price'),NaN),ahCh=num(gv(r,'after_hours_chg'),NaN),ahPct=num(gv(r,'after_hours_pct'),NaN),ahVol=num(gv(r,'after_hours_vol'),NaN);
  const pmPx=num(gv(r,'pm_price'),NaN),pmChAmt=num(gv(r,'pm_change_amt'),NaN),pchRatio=num(gv(r,'pch_ratio'),NaN);

  const y=gv(r,'lnk_Yahoo')||(sym?'https://finance.yahoo.com/quote/'+encodeURIComponent(sym):'');
  const fv=gv(r,'lnk_Finviz')||(sym?'https://finviz.com/quote.ashx?t='+encodeURIComponent(sym):'');
  const sec=gv(r,'lnk_SEC_8K')||(sym?'https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company='+encodeURIComponent(sym)+'&type=8-K&dateb=&owner=include&count=10':'');
  const tvUrl=sym?'https://www.tradingview.com/chart/?symbol='+encodeURIComponent(sym):'';
  const isPinned=pinnedSymbols.has(sym.toUpperCase());

  const p=document.getElementById('panel');
  p.innerHTML='<div class="ph"><h2>'+sym+'<span>'+(gv(r,'name')||'')+'</span></h2><div style="display:flex;gap:8px;align-items:center"><button class="close-btn" onclick="togglePin(\''+escAttr(sym)+'\');loadData()" title="Pin/Unpin" style="color:'+(isPinned?'var(--yellow)':'var(--txt2)')+';font-size:16px;border-color:'+(isPinned?'var(--yellow)':'var(--border)')+'">'+(isPinned?'★':'☆')+'</button><button class="close-btn" onclick="closeDetail()">✕</button></div></div>'+
  '<div class="pb"><div class="price-hero"><span class="px">$'+px.toFixed(2)+'</span><span class="pc '+cc+'">'+fP(ch)+'</span><span class="ex">'+(gv(r,'exchange')||'')+' · '+(gv(r,'sector')||'')+' · '+(gv(r,'industry')||'')+' · '+(gv(r,'session')||'')+'</span></div>'+
  '<div class="section"><div class="section-title">Execution Snapshot</div><div class="dg">'+buildDetailRow('RANK','#'+(gv(r,'master_rank')||'—'))+buildDetailRow('VWAP','$'+N(gv(r,'vwap')))+buildDetailRow('PX_EFF','$'+N(gv(r,'px_eff')||gv(r,'price')))+buildDetailRow('CHG_EFF',fP(gv(r,'chg_eff')||gv(r,'change_pct')))+buildDetailRow('VOL_EFF',fV(gv(r,'vol_eff')||gv(r,'volume')))+buildDetailRow('REL VOL',rv.toFixed(1)+'x')+buildDetailRow('TURNOVER',num(gv(r,'turnover_rate'),0).toFixed(2)+'x')+buildDetailRow('SPREAD',Number.isFinite(spread)?fP(spread):'—')+buildDetailRow('BID / ASK',(Number.isFinite(bid)?'$'+bid.toFixed(2):'—')+' / '+(Number.isFinite(ask)?'$'+ask.toFixed(2):'—'))+buildDetailRow('BID / ASK SIZE',fV(bsz)+' / '+fV(asz))+buildDetailRow('GAP %',fP(gap))+buildDetailRow('HOD DIST',Number.isFinite(hdd)?hdd.toFixed(1)+'%':'—')+buildDetailRow('OPEN','$'+N(gv(r,'open')))+buildDetailRow('PREV CLOSE','$'+N(gv(r,'prev_close')))+buildDetailRow('HIGH / LOW','$'+N(gv(r,'high'))+' / $'+N(gv(r,'low')))+buildDetailRow('MKT CAP',fM(gv(r,'mkt_cap')))+'</div></div>'+
  '<div class="section"><div class="section-title">Ranking Thesis</div><div class="dg">'+buildDetailRow('BEST PRESET',gv(r,'best_preset')||'—')+buildDetailRow('BEST SCORE',num(gv(r,'best_score'),0).toFixed(1))+buildDetailRow('PRESETS PASSED',''+(gv(r,'presets_passed')||0))+buildDetailRow('PRESET LIST',presetT(gv(r,'presets_list')))+buildDetailRow('COMPOSITE','<span style="color:'+sC(gv(r,'composite_score'))+'">'+num(gv(r,'composite_score'),0).toFixed(1)+'</span>')+buildDetailRow('ML FINAL','<span style="color:'+sC(gv(r,'ml_final_score'))+'">'+num(gv(r,'ml_final_score'),0).toFixed(1)+'</span>')+buildDetailRow('ARCHETYPE',archB(gv(r,'ml_archetype')))+buildDetailRow('ML CONFIDENCE',gv(r,'ml_confidence')||'—')+buildDetailRow('ML FT COVERAGE',hasCol('ml_feature_coverage')?num(gv(r,'ml_feature_coverage'),0).toFixed(3):'—')+buildDetailRow('INDUSTRY',gv(r,'industry')||'—')+'</div></div>'+
  '<div class="section"><div class="section-title">Risk Flags & Session</div><div class="dg">'+buildDetailRow('FLAGS',flagT(r))+buildDetailRow('EARNINGS',gv(r,'earnings_date')||'—')+buildDetailRow('PM ACTIVE',isTrueLike(gv(r,'flag_pm_active'))?'YES':'NO')+buildDetailRow('PM PRICE',Number.isFinite(pmPx)?'$'+pmPx.toFixed(2):'—')+buildDetailRow('PM CHG $',Number.isFinite(pmChAmt)?pmChAmt.toFixed(4):'—')+buildDetailRow('PCH RATIO',Number.isFinite(pchRatio)?pchRatio.toFixed(4):'—')+buildDetailRow('RAW PRICE','$'+N(gv(r,'price')))+buildDetailRow('RAW CHG %',fP(gv(r,'change_pct')))+buildDetailRow('RAW VOL',fV(gv(r,'volume')))+buildDetailRow('AVG VOL 10D',fV(gv(r,'avg_vol_10d')))+'</div></div>'+
  ((Number.isFinite(ahPx)||Number.isFinite(ahPct)||Number.isFinite(ahVol))?'<div class="ah-box"><span class="ah-label">After Hours</span><span style="font-weight:700;font-size:13px">'+(Number.isFinite(ahPx)?'$'+ahPx.toFixed(2):'—')+'</span><span style="font-weight:700;color:'+(ahPct>=0?'var(--green)':'var(--red)')+'">'+(Number.isFinite(ahPct)?fP(ahPct):'—')+'</span><span style="color:var(--txt2)">Δ '+(Number.isFinite(ahCh)?ahCh.toFixed(4):'—')+'</span><span style="color:var(--txt2)">Vol '+(Number.isFinite(ahVol)?fV(ahVol):'—')+'</span></div>':'')+
  '<div class="section"><div class="section-title">Quick Access</div><div class="dl-links">'+
    (tvUrl?'<a href="'+escAttr(tvUrl)+'" target="_blank" rel="noopener" class="dl-link" style="border-color:#2962ff;color:#2962ff">📊 TradingView</a>':'')+
    (gv(r,'lnk_Google_News')?'<a href="'+escAttr(gv(r,'lnk_Google_News'))+'" target="_blank" rel="noopener" class="dl-link">📰 Google News</a>':'')+
    (gv(r,'lnk_StockTwits')?'<a href="'+escAttr(gv(r,'lnk_StockTwits'))+'" target="_blank" rel="noopener" class="dl-link">💬 StockTwits</a>':'')+
    (gv(r,'lnk_Google_Finance')?'<a href="'+escAttr(gv(r,'lnk_Google_Finance'))+'" target="_blank" rel="noopener" class="dl-link">📊 Google Finance</a>':'')+
    (y?'<a href="'+escAttr(y)+'" target="_blank" rel="noopener" class="dl-link">📈 Yahoo Finance</a>':'')+
    (fv?'<a href="'+escAttr(fv)+'" target="_blank" rel="noopener" class="dl-link">🔍 Finviz</a>':'')+
    (sec?'<a href="'+escAttr(sec)+'" target="_blank" rel="noopener" class="dl-link">📄 SEC 8-K</a>':'')+
    (gv(r,'lnk_Webull')?'<a href="'+escAttr(gv(r,'lnk_Webull'))+'" target="_blank" rel="noopener" class="dl-link">🟣 Webull</a>':'')+
  '</div></div></div>';

  document.getElementById('overlay').classList.add('open');
}
function closeDetail(){document.getElementById('overlay').classList.remove('open')}

function updateClock(){
  const now=new Date();
  const ts=now.toLocaleTimeString('en-US',{hour12:false,timeZone:'America/New_York'});
  document.getElementById('clock').textContent=ts+' ET';
  const [h,m]=ts.split(':').map(x=>parseInt(x,10));const mins=h*60+m;
  let sess='CLOSED',nextMins=0,nextLabel='';
  if(mins>=240&&mins<570){sess='PRE-MKT';nextMins=570;nextLabel='Open'}
  else if(mins>=570&&mins<960){sess='OPEN';nextMins=960;nextLabel='Close'}
  else if(mins>=960&&mins<1200){sess='AFTER-HRS';nextMins=1200;nextLabel='End'}
  else{sess='CLOSED';nextMins=mins<240?240:(240+1440);nextLabel='Pre-Mkt'}
  const el=document.getElementById('sessionLabel');
  if(!el.textContent||el.textContent==='CLOSED'||el.textContent===sess){
    el.textContent=sess;
    el.style.color=sess==='OPEN'?'var(--green)':sess==='PRE-MKT'?'var(--yellow)':sess==='AFTER-HRS'?'var(--purple)':'var(--txt3)';
  }
  let remain=nextMins-mins;if(remain<0)remain+=1440;
  const rh=Math.floor(remain/60),rm=remain%60;
  document.getElementById('sessionCountdown').textContent='→ '+nextLabel+' '+rh+'h'+String(rm).padStart(2,'0')+'m';
}

init();
</script>
</body>
</html>
"""

APP_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

DEFAULT_CSV_PATH = r"C:\Users\Nadir\Desktop\ROKKIE\screener_master.csv"
DEFAULT_FOLDER = None
CSV_PATH = None
CSV_FOLDER = None

COLUMNS = [
    'master_rank','symbol','name','exchange','sector','industry','session',
    'presets_passed','presets_list','best_preset','best_score',
    'composite_score','ml_final_score','ml_archetype','ml_confidence','ml_feature_coverage',
    'px_eff','chg_eff','vol_eff',
    'price','change_pct','open','high','low','prev_close',
    'gap_pct','gap_holding','hod_distance',
    'volume','rel_volume','avg_vol','avg_vol_10d','avg_vol_3m',
    'turnover_rate','mkt_cap','shares_outstanding','total_shares',
    'week52_position','week52_high','week52_low','vwap',
    'bid_price','bid_size','ask_price','ask_size','spread_pct',
    'pm_price','pm_change_amt','pch_ratio','flag_pm_active',
    'after_hours_price','after_hours_chg','after_hours_pct',
    'after_hours_vol','after_hours_high','after_hours_low',
    'flag_hod','flag_thin_supply','flag_rvol5x','flag_big_move',
    'flag_gap_up','flag_wide_range','flag_illiquid',
    'flag_broken_quote','flag_no_dollar_vol',
    'flag_has_earnings','flag_low_ah_liquidity',
    'flag_session_reversal','flag_session_exhaustion',
    'earnings_date','dividend_date',
    'lnk_Yahoo','lnk_StockTwits','lnk_Finviz','lnk_Webull',
    'lnk_SEC_8K','lnk_Google_News','lnk_Google_Finance',
]

NUMERIC_COLS = {
    'master_rank','presets_passed','best_score','composite_score','ml_final_score','ml_feature_coverage',
    'px_eff','chg_eff','vol_eff','price','change_pct','open','high','low','prev_close',
    'gap_pct','hod_distance','volume','rel_volume','avg_vol','avg_vol_10d','avg_vol_3m',
    'turnover_rate','mkt_cap','shares_outstanding','total_shares',
    'week52_position','week52_high','week52_low','vwap',
    'bid_price','bid_size','ask_price','ask_size','spread_pct',
    'pm_price','pm_change_amt','pch_ratio',
    'after_hours_price','after_hours_chg','after_hours_pct',
    'after_hours_vol','after_hours_high','after_hours_low',
}

BOOLISH_COLS = {
    'gap_holding','flag_pm_active',
    'flag_hod','flag_thin_supply','flag_rvol5x','flag_big_move',
    'flag_gap_up','flag_wide_range','flag_illiquid',
    'flag_broken_quote','flag_no_dollar_vol',
    'flag_has_earnings','flag_low_ah_liquidity',
    'flag_session_reversal','flag_session_exhaustion',
}

def find_latest_csv(folder):
    files = glob.glob(os.path.join(folder, "*.csv"))
    return max(files, key=os.path.getmtime) if files else None

def get_csv_path():
    if CSV_FOLDER and os.path.isdir(CSV_FOLDER):
        path = find_latest_csv(CSV_FOLDER)
        if path:
            return path
    if CSV_PATH:
        n = os.path.normpath(CSV_PATH)
        if os.path.isfile(n):
            return n
    local = os.path.join(APP_DIR, "screener_master.csv")
    return local if os.path.isfile(local) else None

def _coerce_numeric(col, v):
    if v is None:
        return 0
    s = str(v).strip().strip('\r')
    if s == '' or s.lower() in ('nan','none','null'):
        return 0
    try:
        if col in {'master_rank','presets_passed','volume','vol_eff','avg_vol','avg_vol_10d','avg_vol_3m','bid_size','ask_size','after_hours_vol'}:
            return int(float(s))
        return round(float(s), 6)
    except (ValueError, TypeError):
        return 0

def _coerce_boolish(v):
    if v is None:
        return False
    return str(v).strip().lower() in ('true','1','yes','y','t')

def _empty_api_payload(error_msg=None):
    return {
        "rows": [],
        "columns": COLUMNS,
        "col_index": {c:i for i,c in enumerate(COLUMNS)},
        "schema": {"numeric_cols": sorted(NUMERIC_COLS), "boolish_cols": sorted(BOOLISH_COLS)},
        "total": 0,
        "file": None,
        "modified": None,
        "error": error_msg
    }

def load_csv_data():
    path = get_csv_path()
    if not path or not os.path.isfile(path):
        return _empty_api_payload(f"CSV not found. path: {CSV_PATH}, folder: {CSV_FOLDER}, app: {APP_DIR}")
    try:
        mod_time = datetime.fromtimestamp(os.path.getmtime(path))
        file_size = os.path.getsize(path)

        content, used_encoding = None, None
        for enc in ('utf-8-sig','utf-8','cp1252','latin-1'):
            try:
                with open(path, 'r', encoding=enc, errors='replace') as f:
                    content = f.read()
                used_encoding = enc
                break
            except Exception:
                continue

        if content is None:
            p = _empty_api_payload("Could not read CSV")
            p["file"] = os.path.basename(path)
            p["modified"] = mod_time.strftime("%Y-%m-%d %H:%M:%S")
            return p

        if content.startswith('\ufeff'):
            content = content[1:]

        reader = csv.DictReader(content.splitlines())
        if reader.fieldnames:
            reader.fieldnames = [str(f).strip().strip('\r').strip('\ufeff') for f in reader.fieldnames]

        rows = []
        for raw in reader:
            row = []
            for col in COLUMNS:
                v = raw.get(col, '')
                if col in NUMERIC_COLS:
                    v = _coerce_numeric(col, v)
                elif col in BOOLISH_COLS:
                    v = _coerce_boolish(v)
                else:
                    v = '' if v is None else str(v).strip().strip('\r')
                row.append(v)
            rows.append(row)

        return {
            "rows": rows,
            "columns": COLUMNS,
            "col_index": {c:i for i,c in enumerate(COLUMNS)},
            "schema": {"numeric_cols": sorted(NUMERIC_COLS), "boolish_cols": sorted(BOOLISH_COLS)},
            "total": len(rows),
            "file": os.path.basename(path),
            "full_path": path,
            "modified": mod_time.strftime("%Y-%m-%d %H:%M:%S"),
            "size_kb": round(file_size/1024, 1),
            "encoding": used_encoding,
            "error": None
        }

    except Exception as e:
        print(f"\n!!! ERROR loading CSV: {e}")
        traceback.print_exc()
        p = _empty_api_payload(f"{type(e).__name__}: {e}")
        p["file"] = os.path.basename(path) if path else None
        return p

@app.route('/')
def index():
    try:
        return render_template_string(TERMINAL_HTML)
    except Exception:
        return f"<html><body style='background:#111;color:#f90;font-family:monospace;padding:40px'><h1>Render Error</h1><pre style='color:#ff5252'>{traceback.format_exc()}</pre></body></html>", 500

@app.route('/api/data')
def api_data():
    try:
        return jsonify(load_csv_data())
    except Exception as e:
        traceback.print_exc()
        return jsonify(_empty_api_payload(f"{type(e).__name__}: {e}")), 500

@app.route('/api/status')
def api_status():
    try:
        path = get_csv_path()
        if not path:
            return jsonify({"ok":False,"error":"No CSV found"})
        mt = datetime.fromtimestamp(os.path.getmtime(path))
        return jsonify({"ok":True,"file":os.path.basename(path),"modified":mt.strftime("%Y-%m-%d %H:%M:%S"),"size_kb":round(os.path.getsize(path)/1024,1)})
    except Exception as e:
        return jsonify({"ok":False,"error":str(e)}), 500

@app.route('/api/debug')
def api_debug():
    path = get_csv_path()
    info = {
        "csv_path": CSV_PATH,
        "csv_folder": CSV_FOLDER,
        "resolved": path,
        "exists": os.path.isfile(path) if path else False,
        "app_dir": APP_DIR,
        "columns": len(COLUMNS),
        "template": "embedded"
    }
    try:
        data = load_csv_data()
        info["rows"] = data["total"]
        info["error"] = data["error"]
    except Exception as e:
        info["error"] = str(e)
    return jsonify(info)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MAXXSCAN Terminal')
    parser.add_argument('--csv', type=str, default=DEFAULT_CSV_PATH)
    parser.add_argument('--folder', type=str, default=DEFAULT_FOLDER)
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--host', type=str, default='127.0.0.1')
    parser.add_argument('--debug', action='store_true', default=False)
    parser.add_argument('--reloader', action='store_true', default=False)
    args = parser.parse_args()

    CSV_PATH = args.csv
    CSV_FOLDER = args.folder
    path = get_csv_path()

    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║           MAXXSCAN TERMINAL v3.1                 ║")
    print("  ╠══════════════════════════════════════════════════╣")
    if path and os.path.isfile(path):
        print(f"  ║  CSV:  {os.path.basename(path)} ({round(os.path.getsize(path)/1024,1)} KB)")
    else:
        print(f"  ║  ⚠  CSV NOT FOUND — {args.csv}")
    print(f"  ║  URL:  http://{args.host}:{args.port}")
    print(f"  ╚══════════════════════════════════════════════════╝")
    print()

    extra = {}
    if args.reloader:
        extra['use_reloader'] = True
        extra['reloader_type'] = 'stat'

    app.run(host=args.host, port=args.port, debug=args.debug, **extra)
