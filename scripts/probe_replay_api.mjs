#!/usr/bin/env node
// PROBE — enumerate TradingView's internal replay/trading API surface. READ-ONLY.
//
// WHY: TradingView's Replay trading natively supports limit / stop / stop-limit
// orders and TP/SL brackets (tradingview.com/support/solutions/43000691889, and
// the "Brackets are now available in Replay trading" release note). The MCP wraps
// only five methods of window.TradingViewApi._replayApi (buy/sell/closePosition/
// position/realizedPL) — the order-ticket API underneath has never been mapped.
// This prints every method name on the suspects, so the local session can extend
// the MCP with a real replay_limit_order tool instead of simulating fills.
//
// RUN (on the Mac, TradingView running with CDP, MCP installed):
//     node scripts/probe_replay_api.mjs
//
// Run it TWICE: once on a normal chart, and once INSIDE replay mode with the
// replay trading panel open and a (tiny, practice) position or order ticket
// touched — TradingView lazy-loads services, and the order API may not exist on
// the page until the panel has been opened once.
//
// SAFETY: enumeration only. Property NAMES are listed via descriptors — getters
// are reported as 'getter' and never invoked, functions are never called. This
// script cannot place, modify, or cancel anything.

import { pathToFileURL } from 'url';
import { homedir } from 'os';

const MCP = process.env.TRADINGVIEW_MCP_PATH || `${homedir()}/tradingview-mcp`;
let conn;
try {
  conn = await import(pathToFileURL(`${MCP}/src/connection.js`));
} catch (e) {
  console.error(`Cannot import ${MCP}/src/connection.js — is the MCP installed there?`);
  console.error('Set TRADINGVIEW_MCP_PATH or run scripts/setup_local_mac.sh first.');
  console.error(String(e));
  process.exit(1);
}

const PAGE = `
  (function () {
    var SUSPECT = /order|trade|broker|position|bracket|limit|stop|qty|quantity|execut|replay/i;
    var HIT = /order|bracket|limit|stop|modify|cancel|qty|quantity/i;

    function describe(obj, maxProtoLevels) {
      var rows = [], cur = obj, level = 0;
      while (cur && cur !== Object.prototype && level <= maxProtoLevels) {
        Object.getOwnPropertyNames(cur).forEach(function (n) {
          var d;
          try { d = Object.getOwnPropertyDescriptor(cur, n) || {}; } catch (e) { d = {}; }
          var kind = d.get ? 'getter'
            : (typeof d.value === 'function' ? 'fn' : typeof d.value);
          rows.push({ name: n, kind: kind, proto_level: level });
        });
        cur = Object.getPrototypeOf(cur);
        level++;
      }
      return rows;
    }

    function scanRoot(root, label, out) {
      if (!root) { out.push({ key: label, err: 'missing' }); return; }
      var names;
      try { names = Object.getOwnPropertyNames(root); }
      catch (e) { out.push({ key: label, err: String(e) }); return; }
      names.forEach(function (k) {
        if (!SUSPECT.test(k)) return;
        var d;
        try { d = Object.getOwnPropertyDescriptor(root, k) || {}; } catch (e) { d = {}; }
        var entry = { key: label + '.' + k, kind: d.get ? 'getter' : typeof d.value };
        if (d.value && typeof d.value === 'object') {
          try {
            entry.fn_members = describe(d.value, 1)
              .filter(function (m) { return m.kind === 'fn'; })
              .map(function (m) { return m.name; })
              .slice(0, 120);
          } catch (e) { entry.members_err = String(e); }
        }
        out.push(entry);
      });
    }

    var report = { replayApi: null, suspects: [], hits: [] };

    try {
      var rp = window.TradingViewApi && window.TradingViewApi._replayApi;
      report.replayApi = rp ? describe(rp, 2) : 'MISSING';
    } catch (e) { report.replayApi = 'ERR ' + String(e); }

    scanRoot(window.TradingViewApi, 'TradingViewApi', report.suspects);
    scanRoot(window.TradingView, 'TradingView', report.suspects);

    // flatten every function name that smells like order placement
    if (Array.isArray(report.replayApi)) {
      report.replayApi.forEach(function (m) {
        if (m.kind === 'fn' && HIT.test(m.name))
          report.hits.push('_replayApi.' + m.name);
      });
    }
    report.suspects.forEach(function (s) {
      (s.fn_members || []).forEach(function (n) {
        if (HIT.test(n)) report.hits.push(s.key + '.' + n);
      });
    });
    return report;
  })()
`;

let report;
try {
  report = await conn.evaluate(PAGE);
} catch (e) {
  console.error('CDP evaluate failed — is TradingView Desktop running with');
  console.error('--remote-debugging-port=9222? (tv_launch, or re-run');
  console.error('scripts/setup_local_mac.sh).');
  console.error(String(e?.message || e));
  process.exit(1);
}

console.log('=== FULL REPORT (save this into the run log) ===');
console.log(JSON.stringify(report, null, 2));

console.log('\n=== LIMIT-SHAPED HITS ===');
if (report && Array.isArray(report.hits) && report.hits.length) {
  report.hits.forEach((h) => console.log('  ' + h));
  console.log('\nNext: read the winning object in DevTools, confirm the order-'
    + 'placement signature on a THROWAWAY replay session, then wrap it as a '
    + 'replay_limit_order MCP tool (fork the MCP; src/tools/replay.js is the '
    + 'pattern to copy).');
} else {
  console.log('  none found on this pass.');
  console.log('  If this was the normal-chart pass: enter replay mode, open the');
  console.log('  replay trading panel, place+cancel one practice order by hand,');
  console.log('  and run the probe again — the service may lazy-load.');
  console.log('  If it stays empty after that: the order ticket runs outside the');
  console.log("  page API we can reach, and the runbook's simulated-limit path");
  console.log('  (drawn lines + market mirror, log fills at the limit price) is');
  console.log('  the fallback — already specced, no slippage in the scored log.');
}
process.exit(0);
