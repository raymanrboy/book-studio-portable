// Book Studio pictograms — 24×24 grid, 1.6 stroke, round joins.
// One meaning per glyph: a function always has the same icon, and no icon means two things.
const FOLDER = 'M3 7.5A1.5 1.5 0 0 1 4.5 6H9l2 2h8.5A1.5 1.5 0 0 1 21 9.5v8a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 17.5z';
const SERVICE = '<rect x="3.5" y="3.5" width="17" height="17" rx="4.5"/>';
const P = {
  // ---- places
  shelf: '<path d="M3.5 20.5h17"/><rect x="5" y="5" width="3.6" height="15.5" rx=".8"/><rect x="9.8" y="7.5" width="3.6" height="13" rx=".8"/><path d="M14.9 8.7l3.4-.9 3 11.6-3.4.9z"/>',
  printer: '<path d="M7 9V3.5h10V9"/><rect x="3.5" y="9" width="17" height="7.5" rx="1.8"/><path d="M7 14h10v6.5H7z"/><path d="M17 12h.01"/>',
  sliders: '<path d="M4 6.5h8.5M16.5 6.5H20M4 12h3M11 12h9M4 17.5h10.5M18.5 17.5H20"/><circle cx="14.5" cy="6.5" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="16.5" cy="17.5" r="2"/>',
  chart: '<path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/>',

  // ---- generic actions
  plus: '<path d="M12 5v14M5 12h14"/>',
  search: '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.4-4.4"/>',
  x: '<path d="M18 6L6 18M6 6l12 12"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
  chevDown: '<path d="M6 9l6 6 6-6"/>',
  chevLeft: '<path d="M15 18l-6-6 6-6"/>',
  chevRight: '<path d="M9 6l6 6-6 6"/>',
  arrowLeft: '<path d="M19 12H5M11 18l-6-6 6-6"/>',
  more: '<circle cx="5" cy="12" r="1.3"/><circle cx="12" cy="12" r="1.3"/><circle cx="19" cy="12" r="1.3"/>',
  sort: '<path d="M4 7h9M4 12h6M4 17h3"/><path d="M17 5v14M14 16l3 3 3-3"/>',
  copy: '<rect x="8.5" y="8.5" width="12" height="12" rx="2"/><path d="M15.5 8.5V6a2 2 0 0 0-2-2h-7.5a2 2 0 0 0-2 2v7.5a2 2 0 0 0 2 2h2.5"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
  trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3"/>',
  upload: '<path d="M12 15.5V4M7.5 8.5L12 4l4.5 4.5"/><path d="M4 15v3.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V15"/>',
  download: '<path d="M12 4v11.5M7.5 11l4.5 4.5 4.5-4.5"/><path d="M4 15v3.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V15"/>',
  sync: '<path d="M19.5 10.5A7.7 7.7 0 0 0 5.6 7"/><path d="M4.5 13.5A7.7 7.7 0 0 0 18.4 17"/><path d="M5 3.5V7.2h3.7M19 20.5v-3.7h-3.7"/>',
  expand: '<path d="M14 4h6v6M20 4l-6.5 6.5M10 20H4v-6M4 20l6.5-6.5"/>',
  external: '<path d="M13.5 4H20v6.5"/><path d="M20 4l-8.5 8.5"/><path d="M18 14v4.5a1.5 1.5 0 0 1-1.5 1.5h-11A1.5 1.5 0 0 1 4 18.5v-11A1.5 1.5 0 0 1 5.5 6H10"/>',
  link: '<path d="M10 14a4 4 0 0 0 5.66 0l3-3a4 4 0 0 0-5.66-5.66l-1 1"/><path d="M14 10a4 4 0 0 0-5.66 0l-3 3a4 4 0 0 0 5.66 5.66l1-1"/>',
  unlink: '<path d="M18.8 5.2a4 4 0 0 0-5.7 0l-1 1M5.2 18.8a4 4 0 0 0 5.7 0l1-1M15 9l1-1M9 15l-1 1M4 4l16 16"/>',
  send: '<path d="M20.5 3.5L10 14"/><path d="M20.5 3.5L14 20.5l-4-6.5-6.5-4z"/>',
  swap: '<path d="M7 7.5h13M16 3.5l4 4-4 4M17 16.5H4M8 12.5l-4 4 4 4"/>',
  scan: '<path d="M4 8.5V5.5A1.5 1.5 0 0 1 5.5 4h3M15.5 4h3A1.5 1.5 0 0 1 20 5.5v3M20 15.5v3a1.5 1.5 0 0 1-1.5 1.5h-3M8.5 20h-3A1.5 1.5 0 0 1 4 18.5v-3"/><path d="M4 12h16"/>',
  pulse: '<path d="M3 12h4l2.5-6.5 5 13L17 12h4"/>',
  template: '<rect x="3.5" y="3.5" width="17" height="17" rx="2"/><path d="M3.5 9h17M9 9v11.5"/>',
  receipt: '<path d="M6 3.5h12v17l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6"/>',
  key: '<circle cx="8" cy="15" r="4"/><path d="M11 12l8.5-8.5M16.5 6.5l3 3"/>',
  login: '<path d="M10 17l5-5-5-5M15 12H3"/><path d="M14 4h5a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-5"/>',
  unplug: '<path d="M9 3.5v4M15 3.5v4M7 7.5h10v3.5a5 5 0 0 1-10 0z"/><path d="M12 16v4.5"/><path d="M3.5 3.5l17 17"/>',
  lock: '<rect x="5" y="11" width="14" height="9.5" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',

  // ---- files & folders
  folderPick: `<path d="M20.5 11V9.5A1.5 1.5 0 0 0 19 8h-8L9 6H4.5A1.5 1.5 0 0 0 3 7.5v10A1.5 1.5 0 0 0 4.5 19h6"/><circle cx="16.5" cy="15.5" r="3"/><path d="M21 20l-2.4-2.4"/>`,
  folderIn: `<path d="${FOLDER}"/><path d="M12 10.5v5.5M9.5 13.5L12 16l2.5-2.5"/>`,
  folderOpen: '<path d="M3 17.5V6.5A1.5 1.5 0 0 1 4.5 5h4l2 2h7A1.5 1.5 0 0 1 19 8.5V10"/><path d="M3 17.5L6 10h15l-3 7.5z"/>',
  filesPlus: '<rect x="8" y="3.5" width="12.5" height="12.5" rx="2"/><path d="M4 8v10.5A1.5 1.5 0 0 0 5.5 20H16"/><path d="M14.2 6.8v6M11.2 9.8h6"/>',
  braces: '<path d="M9 4C7 4 6 5 6 7v2c0 1.5-.8 2.5-2.5 3C5.2 12.5 6 13.5 6 15v2c0 2 1 3 3 3"/><path d="M15 4c2 0 3 1 3 3v2c0 1.5.8 2.5 2.5 3-1.7.5-2.5 1.5-2.5 3v2c0 2-1 3-3 3"/>',
  fileOpen: '<path d="M14 3.5H6.5A1.5 1.5 0 0 0 5 5v14a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 19V8.5z"/><path d="M14 3.5v5h5M9.5 15.5l5-5M11 10.5h3.5V14"/>',
  archive: '<rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v10.5A1.5 1.5 0 0 0 6.5 20h11a1.5 1.5 0 0 0 1.5-1.5V8M10 12h4"/>',
  restore: '<rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v10.5A1.5 1.5 0 0 0 6.5 20h11a1.5 1.5 0 0 0 1.5-1.5V8"/><path d="M12 17.5V11M9.5 13.5L12 11l2.5 2.5"/>',
  stack: '<path d="M4 7.5L12 4l8 3.5-8 3.5z"/><path d="M4 12l8 3.5 8-3.5"/><path d="M4 16.5L12 20l8-3.5"/>',

  // ---- book parts
  book: '<path d="M5 4.5A1.5 1.5 0 0 1 6.5 3H19v15H6.5A1.5 1.5 0 0 0 5 19.5z"/><path d="M5 19.5A1.5 1.5 0 0 0 6.5 21H19v-3"/>',
  image: '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><circle cx="9" cy="10" r="1.8"/><path d="M20.5 16l-5-5-8.5 8.5"/>',
  images: '<rect x="7" y="3.5" width="13.5" height="12" rx="2"/><path d="M4 7.5v11A1.5 1.5 0 0 0 5.5 20H16"/><path d="M20.5 12.5l-3.5-3.5-6 6"/>',
  imageDown: '<path d="M20.5 13v5.5a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2h5.5"/><path d="M3.5 17l4.5-4.5 3.5 3.5"/><path d="M17.5 3v7.5M14.5 7.5l3 3 3-3"/>',
  imageOff: '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><path d="M3.5 3.5l17 17"/>',
  text: '<path d="M6 3.5h9l4 4v13H6z"/><path d="M14.5 3.5V8H19M9 12.5h7M9 16.5h7"/>',
  textOff: '<path d="M5 7h14M5 12h9M5 17h6"/><path d="M4 3.5l16 17"/>',
  grid: '<rect x="4" y="4" width="7" height="7" rx="1.5"/><rect x="13" y="4" width="7" height="7" rx="1.5"/><rect x="4" y="13" width="7" height="7" rx="1.5"/><rect x="13" y="13" width="7" height="7" rx="1.5"/>',
  spread: '<path d="M12 6.5C9.5 5 6.5 4.5 3.5 5v13.5c3-.5 6 0 8.5 1.5 2.5-1.5 5.5-2 8.5-1.5V5c-3-.5-6 0-8.5 1.5z"/><path d="M12 6.5V20"/>',

  // ---- services (letter marks, one shape family)
  etsy: `${SERVICE}<path d="M14.8 8H9.5v8h5.3M9.5 12h4.3"/>`,
  canva: `${SERVICE}<path d="M15 9.6a3.6 3.6 0 1 0 0 4.8"/>`,
  printify: `${SERVICE}<path d="M10 16.5v-9h3.2a2.5 2.5 0 0 1 0 5H10"/>`,
  gelato: `${SERVICE}<path d="M15.4 9.2a3.8 3.8 0 1 0 .8 3.3h-3.4"/>`,

  // ---- status & feedback
  checkCircle: '<circle cx="12" cy="12" r="8.5"/><path d="M8.2 12.4l2.7 2.7 5-5.6"/>',
  alert: '<path d="M12 3.8l8.7 15.2H3.3z"/><path d="M12 10v4.2M12 16.9v.01"/>',
  alertCircle: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.8v5M12 16.2v.01"/>',
  info: '<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5.5M12 7.8v.01"/>',
  clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5v4.8l3 1.8"/>',
  shield: '<path d="M12 3.5l7.5 2.8v5.6c0 4.3-3.2 7.6-7.5 8.6-4.3-1-7.5-4.3-7.5-8.6V6.3z"/><path d="M9 12l2 2 4-4"/>',
  globe: '<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.4 2.4 3.6 5.2 3.6 8.5s-1.2 6.1-3.6 8.5c-2.4-2.4-3.6-5.2-3.6-8.5S9.6 5.9 12 3.5z"/>',
  layers: '<path d="M12 3.5l8.5 4.7L12 13 3.5 8.2z"/><path d="M3.5 12.8L12 17.5l8.5-4.7"/>',
  database: '<ellipse cx="12" cy="5.5" rx="7.5" ry="2.8"/><path d="M4.5 5.5v13c0 1.6 3.4 2.8 7.5 2.8s7.5-1.2 7.5-2.8v-13M4.5 12c0 1.6 3.4 2.8 7.5 2.8s7.5-1.2 7.5-2.8"/>',
  calendar: '<rect x="3.5" y="5" width="17" height="15.5" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
  sparkle: '<path d="M12 3.5l1.8 5.2 5.2 1.8-5.2 1.8L12 17.5l-1.8-5.2L5 10.5l5.2-1.8z"/>',
  guide: '<rect x="5" y="4.5" width="14" height="16.5" rx="2"/><path d="M9.2 4.5V3.5h5.6v1"/><path d="M8.5 10h7M8.5 13.5h7M8.5 17h4.3"/>',
  inbox:'<path d="M3.5 13.5l2.4-6.8A1.8 1.8 0 0 1 7.6 5.5h8.8a1.8 1.8 0 0 1 1.7 1.2l2.4 6.8v4.7a1.8 1.8 0 0 1-1.8 1.8H5.3a1.8 1.8 0 0 1-1.8-1.8z"/><path d="M3.5 13.5h4.6l1.3 2.3h5.2l1.3-2.3h4.6"/>',
  eraser:'<path d="M9 20.5h11"/><path d="M4.7 15.2l9.5-9.5a2 2 0 0 1 2.8 0l3.3 3.3a2 2 0 0 1 0 2.8l-8.2 8.2a2.5 2.5 0 0 1-1.8.7H9.4a2.5 2.5 0 0 1-1.8-.7l-2.9-2.9a1.3 1.3 0 0 1 0-1.9z"/><path d="M9.6 10.3l6.1 6.1"/>',
  textScan: '<path d="M4 5.5h13M4 10h9M4 14.5h5"/><circle cx="15.2" cy="15.2" r="3.8"/><path d="M18 18l2.7 2.7"/>',
  hourglass:'<path d="M6.5 3.5h11M6.5 20.5h11"/><path d="M8 3.5v2.4a3.6 3.6 0 0 0 1.5 2.9L12 10.6l2.5-1.8A3.6 3.6 0 0 0 16 5.9V3.5M8 20.5v-2.4a3.6 3.6 0 0 1 1.5-2.9l2.5-1.8 2.5 1.8a3.6 3.6 0 0 1 1.5 2.9v2.4"/>',

  // ---- viewer
  zoomIn: '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.4-4.4M11 8.2v5.6M8.2 11h5.6"/>',
  zoomOut: '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.4-4.4M8.2 11h5.6"/>',
  fit: '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
  captions: '<rect x="3.5" y="5" width="17" height="14" rx="2"/><path d="M7 11h4M7 15h6.5M14 11h3"/>',

  // ---- appearance
  sun: '<circle cx="12" cy="12" r="3.8"/><path d="M12 2.5v2M12 19.5v2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M2.5 12h2M19.5 12h2M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
  moon: '<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',
  monitor: '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
  motion: '<path d="M3 12c1.8-3.6 3.7-3.6 5.5 0s3.7 3.6 5.5 0 3.7-3.6 5.5 0"/><path d="M3 17h18" opacity=".45"/>',

  // ---- order archive: books sent to print, kept for a while (a page with a clock); "keep" (a pin)
  orderArchive: '<path d="M14.5 10V5A1.5 1.5 0 0 0 13 3.5H5.5A1.5 1.5 0 0 0 4 5v14a1.5 1.5 0 0 0 1.5 1.5H10"/><path d="M7 7.5h4.5M7 11h3"/><circle cx="16.5" cy="16.5" r="4.5"/><path d="M16.5 14.3v2.4l1.7 1"/>',
  pin: '<path d="M9.5 3.5h5l-.8 5.2 3 3v1.8H7.3v-1.8l3-3z"/><path d="M12 13.5V20.5"/>',

  // ---- send journal (what went to Printify / Gelato)
  sendLog: '<circle cx="5" cy="7" r="1.1"/><circle cx="5" cy="12" r="1.1"/><circle cx="5" cy="17" r="1.1"/><path d="M9 7h11M9 12h11M9 17h7.5"/>',

  // ---- profit (page hidden for now)
  dollar: '<path d="M12 3v18M16.5 7.5c-.8-1.3-2.4-2-4.5-2-2.5 0-4 1.2-4 3s1.5 2.6 4 3.2 4.5 1.4 4.5 3.3-1.8 3.2-4.5 3.2c-2.3 0-4-.9-4.8-2.4"/>',
  bag: '<path d="M5 8h14l-1 12H6z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
  trending: '<path d="M3 17l6-6 4 4 8-8"/><path d="M14 7h7v7"/>',
  package: '<path d="M21 8l-9-5-9 5 9 5 9-5z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/>',

  // ---- shipping: the printer has sent the book (tracking number)
  truck: '<path d="M4.6 17H2.5V6h11.5v11H8.4"/><path d="M14 9.5h4l3.5 3.8V17h-2.6M15.1 17H14"/><circle cx="6.5" cy="17.2" r="1.9"/><circle cx="17" cy="17.2" r="1.9"/>',

  // ---- listing mockups: the utility (a book in a picture frame); "the owner fits this by hand" (a hand)
  mockup: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M12 9.3c-1.6-.9-3.4-1.1-5.2-.8v7.3c1.8-.3 3.6-.1 5.2.8 1.6-.9 3.4-1.1 5.2-.8V8.5c-1.8-.3-3.6-.1-5.2.8z"/><path d="M12 9.3v7.3"/>',
  hand: '<path d="M8.5 12.5V6.2a1.5 1.5 0 0 1 3 0V11"/><path d="M11.5 10.5V4.8a1.5 1.5 0 0 1 3 0v5.7"/><path d="M14.5 10.5V6.5a1.5 1.5 0 0 1 3 0v8a6 6 0 0 1-6 6h-.6a6 6 0 0 1-4.6-2.2l-2.7-3.4a1.6 1.6 0 0 1 2.4-2.1l2 1.9"/>',
};

// Older names still used by the (hidden) profit page map onto the same meanings.
const ALIAS = { refresh: 'sync', folder: 'folderOpen', logo: 'book', laptop: 'monitor', wallet: 'dollar' };

export function icon(name, cls = '') {
  const body = P[name] || P[ALIAS[name]] || P.info;
  const filled = name === 'more' ? ' style="fill:currentColor"' : '';
  return `<svg class="icon ${cls}" viewBox="0 0 24 24" aria-hidden="true"${filled}>${body}</svg>`;
}
