/* Imperium Detailing — timesheet settings.

   Both pages load this first, so a code or a rate is only ever typed once. */
window.IMP = {

  /* The Google Apps Script web app URL. Everything the crew taps goes through
     it and lands in the Imperium Hours spreadsheet. Setup is in README.md.
     Leave it empty and each phone keeps its own copy, which is no use to
     anybody but does at least stop the page being a dead end. */
  ENDPOINT: 'https://script.google.com/macros/s/AKfycbwkodRGuMD3Myt6K7VtwCNENen6v3n8oFNIVzWRB3pmZ3IcjoKoPbn7eoYLGiomaRt8mw/exec',

  /* The two codes. They live in the page, so anyone who views source can read
     them — this is a lid that keeps the crew out of the pay figures, not a lock
     on the data. The link is the real key. */
  STAFF_CODE: '0000',
  ADMIN_CODE: '1906',

  DEFAULT_RATE: 27,
  DEFAULT_CREW: ['Lucas', 'AJ', 'Nick', 'Gus', 'Ananth'],

  POLL_MS: 20000,          // how often a sheet-backed page re-reads
};

/* A day nobody clocked on for, stored as a plain number of hours.

   It also carries a start and an end spanning the same length from midnight, so
   a total still comes out right anywhere that only knows about start and end —
   a sheet that has not been updated, or a formula somebody writes later. The
   hours field is the truth; the times exist so nothing silently reads zero.
   Both pages build one through here, so the shape cannot drift apart. */
/* Pay weeks run Wednesday to Tuesday. Wednesday is day 3, so (day + 4) % 7 is
   how many days back the week that is running now began. Both pages ask here,
   so the two can never disagree about which week a shift belongs to. */
window.IMP.weekStart = function (offset) {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - ((d.getDay() + 4) % 7) + (offset || 0) * 7);
  return d;
};

/* Calendar arithmetic. Adding 24h of milliseconds is wrong twice a year in
   Canberra: the night daylight saving starts or ends is 23 or 25 hours long, so
   "yesterday" skips or repeats a day and a pay-week boundary lands an hour off.
   setDate() moves by calendar days and lets the clock sort itself out. */
window.IMP.addDays = function (d, n) {
  const x = new Date(d);
  x.setDate(x.getDate() + n);
  return x;
};
window.IMP.daysAgo = function (n) {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - n);
  return d;
};
window.IMP.weekEnd = function (offset) {
  return window.IMP.weekStart((offset || 0) + 1);
};

window.IMP.dayShift = function (o) {
  const h = Math.round(Number(o.hours) * 4) / 4;
  const start = new Date(o.date + 'T00:00:00');     // local midnight, that day
  return {
    id: o.id,
    staffId: o.staffId,
    staffName: o.staffName || 'Unknown',
    start: start.toISOString(),
    end: new Date(start.getTime() + h * 3600000).toISOString(),
    job: o.job || '',
    hours: h,
  };
};
