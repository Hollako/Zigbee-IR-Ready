// Panel event regression tests with a minimal DOM; not a browser layout test.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
function panel() {
  const nodes = new Map();
  const get = key => { if (!nodes.has(key)) nodes.set(key, {}); return nodes.get(key); };
  const fields = {device_type: {value:'climate'}, protocol:{}};
  get('form').elements = {namedItem: name => fields[name]};
  let Component;
  const context = vm.createContext({
    HTMLElement: class { attachShadow() { this.shadowRoot={querySelector:get}; } },
    customElements: {get:()=>undefined, define:(_,component)=>{Component=component;}},
  });
  const source=readFileSync(path.join(__dirname,'../custom_components/tuya_ir_bridge/www/manager.js'),'utf8')
    .replace("import {CSS} from './panel.js';", "const CSS='';");
  vm.runInContext(source, context);
  const instance = new Component(); instance.render();
  return {instance,fields,get};
}
test('switching device type offers command protocols and returns to Electra',()=>{
  const {fields,get}=panel();
  for(const value of ['remote','media_player','light']) {
    fields.device_type.value=value; fields.device_type.onchange();
    assert.match(fields.protocol.innerHTML,/value="nec"/);
    assert.match(fields.protocol.innerHTML,/value="samsung"/);
    assert.equal(get('#commands').hidden,false);
  }
  fields.device_type.value='climate'; fields.device_type.onchange();
  assert.match(fields.protocol.innerHTML,/value="electra"/);
  assert.doesNotMatch(fields.protocol.innerHTML,/value="nec"/);
  assert.equal(get('#commands').hidden,true);
});
test('unknown backend errors provide recovery guidance',async()=>{
  const {instance,get}=panel();
  instance._hass={callWS:async()=>{throw {code:'unknown_error',message:'Unknown error'};}};
  assert.equal(await instance.refresh(),false);
  assert.match(get('.statusbar').textContent,/System → Logs/);
});
test('successful list request refreshes device data',async()=>{
  const {instance}=panel();
  const devices=[{name:'AC',device_type:'climate'}];
  instance._hass={callWS:async()=>devices};
  assert.equal(await instance.refresh(),true);
  assert.equal(instance.devices,devices);
});
