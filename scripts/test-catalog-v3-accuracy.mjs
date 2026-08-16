import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const accuracySource = fs.readFileSync(new URL('../js/catalog-v3-accuracy.js', import.meta.url), 'utf8');
const maintenanceSource = fs.readFileSync(new URL('../js/catalog-maintenance.js', import.meta.url), 'utf8');
const sitecustomizeSource = fs.readFileSync(new URL('../sitecustomize.py', import.meta.url), 'utf8');

const catalog = {
  styleFamilies: { analyze() { return { count:0, groups:[], assignments:{} }; } },
  capture: {},
  memory: {},
};
const context = {
  window: {
    SonicTraceCatalog: catalog,
    setInterval(fn) { fn(); return 1; },
    clearInterval() {},
    setTimeout() { return 1; },
  },
  document: {
    documentElement: { dataset:{} },
    addEventListener() {},
  },
  console,
  structuredClone: value => JSON.parse(JSON.stringify(value)),
};
vm.createContext(context);
vm.runInContext(accuracySource, context, { filename:'catalog-v3-accuracy.js' });

const api = catalog.catalogAccuracy;
assert.ok(api?.analyze, 'catalog V3 accuracy API must be exposed');

const tinh = {
  id:'tinh',
  title:'Tinh Bolero Cho Trân',
  neural:{
    genres:[
      { label:'Nhạc Vàng', score:0.69 },
      { label:'Vietnamese Pop Ballad', score:0.63 },
      { label:'Vietnamese Bolero', score:0.51 },
      { label:'Neo Soul', score:0.49 },
      { label:'Country', score:0.39 },
    ],
    genreAnalysis:{
      dimensions:{
        family:{ label:'Vietnamese / Asian', evidence:{ score:0.69 } },
        style:{ primary:{ label:'Vietnamese Bolero' } },
        tradition:{ primary:{ label:'Nhạc Vàng' } },
        form:{ primary:{ label:'Sentimental Ballad' } },
      },
    },
  },
};
const legacyTinh = {
  id:'tinh-legacy',
  title:'Tinh legacy',
  neural:{ genres:tinh.neural.genres },
};
const rnb = {
  id:'rnb',
  title:'RNB song',
  neural:{ genres:[{ label:'Contemporary R&B', score:0.82 }, { label:'Pop Ballad', score:0.48 }] },
};

assert.equal(api.primaryFamily(tinh).id, 'vietnamese-asian');
assert.equal(api.primaryFamily(tinh).source, 'v3-dimensions');
assert.equal(api.primaryFamily(legacyTinh).id, 'vietnamese-asian', 'legacy raw ranking must prefer the top Vietnamese evidence instead of secondary Neo Soul');
assert.equal(api.primaryFamily(rnb).id, 'rnb-soul');

const result = api.analyze([tinh, legacyTinh, rnb]);
assert.equal(result.assignments.tinh.length, 1, 'role-aware catalog family assignment must not spray one track into every secondary resemblance');
assert.equal(result.assignments.tinh[0].id, 'vietnamese-asian');
assert.equal(result.assignments['tinh-legacy'][0].id, 'vietnamese-asian');
assert.equal(result.assignments.rnb[0].id, 'rnb-soul');
assert.equal(result.groups.find(group => group.id === 'vietnamese-asian')?.count, 2);
assert.equal(result.groups.find(group => group.id === 'rnb-soul')?.count, 1);
assert.ok(!result.assignments.tinh.some(item => item.id === 'rnb-soul'), 'Neo Soul secondary evidence must not place Tinh Bolero in R&B/Soul');
assert.ok(!result.assignments.tinh.some(item => item.id === 'pop-electronic-pop'), 'Vietnamese Pop Ballad form evidence must not place Tinh Bolero in generic Pop family');

assert.match(maintenanceSource, /data-delete-catalog-track/);
assert.match(maintenanceSource, /NS\.memory\?\.deleteTrack/);
assert.match(maintenanceSource, /window\.confirm/);
assert.match(maintenanceSource, /Seule l’entrée locale IndexedDB sera supprimée/);

assert.match(sitecustomizeSource, /Cache-Control/);
assert.match(sitecustomizeSource, /no-store/);
assert.match(sitecustomizeSource, /X-SonicTrace-Frontend/);

console.log('Catalog V3 family authority + local deletion + no-cache frontend regression: PASS');