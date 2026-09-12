// Panel event regression tests with a minimal DOM; not a browser layout test.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
function panel() {
  const nodes = new Map();
  const get = key => { if (!nodes.has(key)) nodes.set(key, {}); return nodes.get(key); };
  const formDataValues={name:'Bedroom',device_type:'climate',protocol:'ELECTRA_AC',topic:'zigbee2mqtt/Bedroom/set/ir_code_to_send',transport:'base64',model:'-1',min_temp:'16',max_temp:'30',temp_step:'1',command_map:'{}',hvac_options:'{}'};
  const fields = Object.fromEntries(['name','device_type','protocol','topic','transport','model','min_temp','max_temp','temp_step','address','command_map','hvac_options'].map(name=>[name,{value:''}]));
  fields.device_type.value='climate';
  get('form').elements = {namedItem: name => fields[name]};
  get('form').querySelector=()=>({append:()=>{}});
  let Component;
  const context = vm.createContext({
    document:{createElement:()=>({style:{}})},
    FormData: class { [Symbol.iterator]() { return Object.entries(formDataValues)[Symbol.iterator](); } },
    HTMLElement: class { attachShadow() { this.shadowRoot={querySelector:get,querySelectorAll:()=>[]}; } toggleAttribute() {} },
    customElements: {get:()=>undefined, define:(_,component)=>{Component=component;}},
  });
  const source=readFileSync(path.join(__dirname,'../custom_components/tuya_ir_bridge/www/manager.js'),'utf8')
    .replace(/import '\.\/remote_card\.js\?v=[^']+';/, '')
    .replace(/import \{CSS\} from '\.\/panel\.js\?v=[^']+';/, "const CSS='';")
    .replace(/import \{mountEditor\} from '\.\/editor\.js\?v=[^']+';/, "const mountEditor=()=>{};");
  vm.runInContext(source, context);
  const instance = new Component();
  instance.catalogue={climate:['DAIKIN','ELECTRA_AC','GREE','MITSUBISHI_AC'],send:[{name:'NEC'},{name:'SAMSUNG'},{name:'SONY'},{name:'RC5'},{name:'RC6'}]};
  instance.render();
  const initialHtml=instance.shadowRoot.innerHTML;
  instance.createDevice();
  return {instance,fields,get,initialHtml,formDataValues};
}
test('initial page waits for a device selection and uses the Tasmota-style shell',()=>{
  const {initialHtml}=panel();
  assert.doesNotMatch(initialHtml,/<form/);
  assert.match(initialHtml,/Select a device from the sidebar/);
  assert.match(initialHtml,/Open Home Assistant sidebar/);
  assert.match(initialHtml,/➕ Add/);
});
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

test('selecting an existing device loads editable parameters and keeps type fixed',()=>{
  const {instance,fields}=panel();
  instance.devices=[{id:'one',name:'Bedroom',device_type:'climate',protocol:'electra',topic:'zigbee2mqtt/Bedroom/set/ir_code_to_send',hvac_options:{SwingV:'Auto'}}];
  instance.selectDevice('one');
  assert.equal(fields.name.value,'Bedroom');
  assert.equal(fields.protocol.value,'ELECTRA_AC');
  assert.equal(fields.transport.value,'base64');
  assert.equal(fields.max_temp.value,32);
  assert.equal(fields.device_type.disabled,true);
  assert.match(fields.hvac_options.value,/SwingV/);
  assert.match(instance.shadowRoot.innerHTML,/<h2>Bedroom<\/h2>/);
  assert.match(instance.shadowRoot.innerHTML,/class="btn btn-danger"/);
  assert.match(instance.shadowRoot.innerHTML,/class="btn btn-primary"/);
  assert.match(instance.shadowRoot.innerHTML,/aria-label="Save Changes"/);
});

test('refresh preserves an unsaved draft',async()=>{
  const {instance,fields}=panel();
  instance.devices=[{id:'one',name:'Old',device_type:'climate',protocol:'GREE'}];
  instance.selectedId='one';
  instance.draft={name:'Unsaved',device_type:'climate',protocol:'GREE',command_map:'invalid JSON draft'};
  instance._hass={callWS:async({type})=>type.endsWith('/list')?instance.devices:instance.catalogue};
  await instance.refresh();
  assert.equal(fields.name.value,'Unsaved');
  assert.equal(fields.command_map.value,'invalid JSON draft');
});

test('climate save explicitly persists linked sensors and availability topic',async()=>{
  const {instance,get}=panel();
  instance.devices=[{id:'one',name:'Bedroom',device_type:'climate',protocol:'ELECTRA_AC',topic:'zigbee2mqtt/Bedroom/set/ir_code_to_send',transport:'base64',hvac_options:{}}];
  instance.selectDevice('one');
  instance.editorValues=()=>({
    hvac_modes:['off','cool'],fan_modes:['auto'],swing_modes:[],feature_switches:[],
    initial_hvac_mode:'off',initial_target_temp:24,precision:.1,temperature_unit:'C',away_temp:0,mqtt_delay:0,
    sleep_minutes:0,keep_mode_on_power_on:false,ignore_off_temperature:false,hvac_options:{},
    temperature_sensor:'sensor.room_temperature',humidity_sensor:'sensor.room_humidity',
    power_sensor:'binary_sensor.ac_power',availability_topic:'  zigbee2mqtt/Bedroom/availability  ',
  });
  let update;
  instance._hass={callWS:async message=>{
    if(message.type.endsWith('/update')){update=message;return {...message.device,id:message.device_id};}
    if(message.type.endsWith('/list'))return instance.devices;
    if(message.type.endsWith('/catalogue'))return instance.catalogue;
    throw Error(`Unexpected ${message.type}`);
  }};
  await get('form').onsubmit({preventDefault(){}});
  assert.equal(update.device.temperature_sensor,'sensor.room_temperature');
  assert.equal(update.device.humidity_sensor,'sensor.room_humidity');
  assert.equal(update.device.power_sensor,'binary_sensor.ac_power');
  assert.equal(update.device.availability_topic,'zigbee2mqtt/Bedroom/availability');
});
