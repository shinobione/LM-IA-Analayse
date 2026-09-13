import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
const source = fs.readFileSync('js/loader.js','utf8');
const loader = source.slice(source.indexOf('function loadCatalogIntelligenceAssets()'), source.indexOf('\nloadFusionAssets();'));
function harness() {
  const nodes = [], errors = [];
  const document = {
    querySelector(selector) { return nodes.find(node => node.selector === selector) || null; },
    createElement(tag) {
      return {tag, dataset:{}, listeners:{}, setAttribute(name) {this.selector = `script[${name}]`;}, addEventListener(event, handler) { (this.listeners[event] ||= []).push(handler); }, fire(event) { for (const fn of this.listeners[event] || []) fn(); }};
    },
    head:{appendChild(node) {nodes.push(node);}},
  };
  const context = vm.createContext({document, console:{error:message => errors.push(message)}});
  vm.runInContext(loader, context);
  return {nodes,errors,run:() => vm.runInContext('loadCatalogIntelligenceAssets()',context)};
}
const h = harness();
h.run();
let scripts = () => h.nodes.filter(node => node.tag === 'script');
assert.equal(scripts().length,1);
assert.match(scripts()[0].src,/catalog-memory/);
scripts()[0].fire('load');
const similarity = scripts()[1];
assert.equal(similarity.type,'module');
assert.equal(similarity.async,false);
assert.match(similarity.src,/^js\/catalog-similarity.js/);
assert.equal(scripts().length,2,'UI waits for module dependency evaluation');
h.run();
assert.equal(scripts().length,2,'Reentrant initialization must not duplicate pending module');
// Exercise the actual local ES module before simulating its browser load event.
globalThis.window = {};
globalThis.document = {dispatchEvent(event) {assert.equal(event.type,'sonictrace:similarity-ready'); assert.ok(window.SonicTraceCatalog.similarity);}};
await import('../js/catalog-similarity.js');
similarity.fire('load');
assert.match(scripts()[2].src,/catalog-ui/);
for (let i=2; i<scripts().length; i++) scripts()[i].fire('load');
assert.equal(scripts().length,8);
h.run();
assert.equal(scripts().length,8,'Loaded assets reused');
const failed = harness(); failed.run();
failed.nodes.find(node => node.tag === 'script').fire('load');
failed.nodes.filter(node => node.tag === 'script')[1].fire('error');
assert.equal(failed.errors.length,1);
assert.equal(failed.nodes.filter(node => node.tag === 'script').length,2,'Module failure must not start dependent UI');
console.log('PASS Build107 loader: local module, ready-before-UI, delayed load, reentry, ordering and failure stop.');
