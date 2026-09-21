/**
 * Imperium Detailing — timesheet backend.
 *
 * A Google Apps Script web app in front of one Google Sheet. The crew's phones
 * talk to it; the hours land in a spreadsheet Pat can read, fix and hand to an
 * accountant. Free, no card, and nobody needs an account to clock on.
 *
 * Setup is in README.md. Short version: paste this into Extensions > Apps
 * Script on a new Sheet, deploy as a web app with access set to "Anyone", and
 * put the deployment URL into ENDPOINT at the top of app.js.
 */

var SHIFTS = 'Shifts';
var STAFF = 'Staff';
var SETTINGS = 'Settings';

// 'hours' is set only for a day nobody clocked on for, logged as a number
// because there are no real times to keep. See dayShift() in config.js.
var SHIFT_COLS = ['id', 'staffId', 'staffName', 'start', 'end', 'job', 'hours'];
var STAFF_COLS = ['id', 'name', 'rate'];

/** Writes from different phones can land in the same instant, so every write
 *  takes a short document lock. Without it two people clocking together can
 *  each read the same last row and overwrite one another. */
function withLock(fn) {
  var lock = LockService.getDocumentLock();
  lock.waitLock(20000);
  try { return fn(); } finally { lock.releaseLock(); }
}

function sheet(name, cols) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    if (cols) sh.appendRow(cols);
    sh.setFrozenRows(1);
  }
  if (cols && sh.getLastRow() === 0) sh.appendRow(cols);
  // A sheet made before a column existed is missing it from the header row.
  // Put the full header back so a person reading the tab knows what is what.
  if (cols && sh.getLastColumn() < cols.length) {
    sh.getRange(1, 1, 1, cols.length).setValues([cols]);
  }
  return sh;
}

function readRows(name, cols) {
  var sh = sheet(name, cols);
  var last = sh.getLastRow();
  if (last < 2) return [];
  var values = sh.getRange(2, 1, last - 1, cols.length).getValues();
  var out = [];
  for (var i = 0; i < values.length; i++) {
    var row = values[i];
    if (!row[0]) continue;                       // blank or deleted line
    var obj = {};
    for (var c = 0; c < cols.length; c++) {
      var v = row[c];
      // Dates come back as Date objects; the app wants ISO strings.
      obj[cols[c]] = v instanceof Date ? v.toISOString() : v;
    }
    if (obj.end === '' || obj.end === null) obj.end = null;
    if (cols === STAFF_COLS) obj.rate = Number(obj.rate) || 0;
    if (cols === SHIFT_COLS) obj.hours = Number(obj.hours) || 0;
    out.push(obj);
  }
  return out;
}

function findRow(sh, id) {
  var last = sh.getLastRow();
  if (last < 2) return 0;
  var ids = sh.getRange(2, 1, last - 1, 1).getValues();
  for (var i = 0; i < ids.length; i++) {
    if (String(ids[i][0]) === String(id)) return i + 2;
  }
  return 0;
}

function upsert(name, cols, value) {
  return withLock(function () {
    var sh = sheet(name, cols);
    var row = [];
    for (var c = 0; c < cols.length; c++) {
      var v = value[cols[c]];
      // Every string is written with a leading apostrophe, which Sheets reads
      // as "this is text" and does not store. Without it a job note beginning
      // with "=" becomes a live formula, a phone number becomes a number, and
      // an ISO timestamp becomes a Date that reads back an hour off.
      row.push(v === null || v === undefined ? '' : (typeof v === 'string' ? "'" + v : v));
    }
    var at = findRow(sh, value.id);
    if (at) sh.getRange(at, 1, 1, cols.length).setValues([row]);
    else sh.appendRow(row);
    return true;
  });
}

function remove(name, cols, id) {
  return withLock(function () {
    var sh = sheet(name, cols);
    var at = findRow(sh, id);
    if (at) sh.deleteRow(at);
    return true;
  });
}

function readSettings() {
  var sh = sheet(SETTINGS, ['key', 'value']);
  var last = sh.getLastRow();
  var out = {};
  if (last < 2) return out;
  var rows = sh.getRange(2, 1, last - 1, 2).getValues();
  for (var i = 0; i < rows.length; i++) {
    if (rows[i][0]) out[String(rows[i][0])] = String(rows[i][1]);
  }
  return out;
}

function writeSettings(value) {
  return withLock(function () {
    var sh = sheet(SETTINGS, ['key', 'value']);
    if (sh.getLastRow() > 1) sh.getRange(2, 1, sh.getLastRow() - 1, 2).clearContent();
    var rows = [];
    for (var k in value) {
      if (Object.prototype.hasOwnProperty.call(value, k)) rows.push([k, "'" + String(value[k])]);
    }
    if (rows.length) sh.getRange(2, 1, rows.length, 2).setValues(rows);
    return true;
  });
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function doGet() {
  try {
    return json({
      ok: true,
      staff: readRows(STAFF, STAFF_COLS),
      shifts: readRows(SHIFTS, SHIFT_COLS),
      settings: readSettings(),
    });
  } catch (err) {
    return json({ ok: false, error: String(err) });
  }
}

function doPost(e) {
  try {
    var body = JSON.parse(e.postData.contents);
    if (body.action === 'settings') {
      writeSettings(body.value || {});
    } else if (body.action === 'upsert') {
      if (body.kind === 'staff') upsert(STAFF, STAFF_COLS, body.value);
      else upsert(SHIFTS, SHIFT_COLS, body.value);
    } else if (body.action === 'remove') {
      var id = body.value ? body.value.id : body.id;
      if (body.kind === 'staff') remove(STAFF, STAFF_COLS, id);
      else remove(SHIFTS, SHIFT_COLS, id);
    } else {
      return json({ ok: false, error: 'unknown action' });
    }
    return json({ ok: true });
  } catch (err) {
    return json({ ok: false, error: String(err) });
  }
}
