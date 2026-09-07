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
  const instance = new Component();
  instance.catalogue={climate:['DAIKIN','ELECTRA_AC','GREE','MITSUBISHI_AC'],send:[{name:'NEC'},{name:'SAMSUNG'},{name:'SONY'},{name:'RC5'},{name:'RC6'}]};
  instance.render();
  return {instance,fields,get};
}
test('switching device type uses the backend protocol catalogue',()=>{
  const {fields,get}=panel();
  for(const value of ['remote','media_player','light']) {
    fields.device_type.value=value; fields.device_type.onchange();
    assert.match(fields.protocol.innerHTML,/value="NEC"/);
    assert.match(fields.protocol.innerHTML,/value="SONY"/);
    assert.match(fields.protocol.innerHTML,/value="RC6"/);
    assert.equal(get('#commands').hidden,false);
  }
  fields.device_type.value='climate'; fields.device_type.onchange();
  assert.match(fields.protocol.innerHTML,/value="ELECTRA_AC"/);
  assert.match(fields.protocol.innerHTML,/value="DAIKIN"/);
  assert.match(fields.protocol.innerHTML,/value="GREE"/);
  assert.doesNotMatch(fields.protocol.innerHTML,/value="NEC"/);
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
  instance._hass={callWS:async({type})=>type.endsWith('/list')?devices:instance.catalogue};
  assert.equal(await instance.refresh(),true);
  assert.equal(instance.devices,devices);
});
