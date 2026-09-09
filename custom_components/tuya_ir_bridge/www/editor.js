/* Tabbed editor inspired by Tasmota IR Ready (MIT, copyright 2026 Hollako). */
const esc = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const modes=['off','auto','cool','heat','dry','fan_only'];
const fans=['auto','min','low','medium','high','max'];
const swings=['off','vertical','horizontal','both','highest','high','middle','low','lowest','left max','left','horizontal middle','right','right max','wide'];
const features=['SwingV','SwingH','Quiet','Turbo','Econo','Light','Filter','Clean','Beep','Sleep','iFeel'];
const groups={power:['power','turn_on','turn_off','volume_up','volume_down','mute'],navigation:['up','down','left','right','ok','back','home','menu','settings','info','exit'],playback:['play','pause','play_pause','stop','next','previous','rewind','fast_forward'],channels:['channel_up','channel_down','red','green','yellow','blue'],keypad:Array.from({length:10},(_,i)=>`digit_${i}`)};
const commandLabel=name=>({power:'Power Toggle',turn_on:'Power On',turn_off:'Power Off',play_pause:'Play / Pause',volume_up:'Volume Up',volume_down:'Volume Down',channel_up:'Channel Up',channel_down:'Channel Down',fast_forward:'Fast Forward'}[name]||name.replace(/^source:/,'').replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase()));
export function mountEditor(panel,form,selected,values,capture) {
  const root=panel.shadowRoot, field=name=>form.elements.namedItem(name);
  let advancedEdited=false;
  field('command_map').addEventListener('input',()=>{advancedEdited=true;});
  const climate=field('device_type').value==='climate';
  const tabs=document.createElement('div'); tabs.className='editor-tabs'; tabs.setAttribute('role','tablist');
  form.before(tabs);
  const panes=new Map();
  function pane(id,label) {
    const section=document.createElement('section'); section.dataset.pane=id; section.setAttribute('role','tabpanel');
    const button=document.createElement('button'); button.type='button'; button.textContent=label; button.setAttribute('role','tab');button.dataset.tab=id;
    button.onclick=()=>show(id);tabs.append(button);form.querySelector('fieldset').insertBefore(section,form.querySelector('.form-actions'));
    panes.set(id,section);return section;
  }
  function show(id){panel.activeTab=id;for(const [key,node] of panes)node.hidden=key!==id;for(const b of tabs.children)b.setAttribute('aria-selected',String(b.dataset.tab===id));}
  function move(name,to){const node=field(name)?.closest('.field-row');if(node)to.append(node);}
  const connection=pane('connection','Connection');
  for(const name of ['name','device_type','topic','transport','protocol','model'])move(name,connection);
  const protocolNote=root.querySelector('#protocol_note');connection.append(protocolNote);
  const connectionHelp=document.createElement('p');connectionHelp.className='help';connectionHelp.textContent='Use the exact Zigbee2MQTT topic, including capitalization. Learning uses the same blaster. Zosung requires a converter accepting full IR messages; Legacy Base64 uses 38 kHz.';connection.append(connectionHelp);for(const help of form.querySelectorAll(':scope > fieldset > p.help'))help.remove();
  const extras={};
  const arrayValue=(name,defaults)=>{let value=values[name]??defaults;return typeof value==='string'?JSON.parse(value):value;};
  function checklist(container,key,label,options,defaults) {
    const box=document.createElement('div');box.className='choice-group';box.innerHTML=`<span class="choice-title">${esc(label)}</span><div class="choice-box"></div>`;
    const chosen=arrayValue(key,defaults);
    for(const option of options){const labelNode=document.createElement('label');labelNode.className='choice';labelNode.innerHTML=`<input type="checkbox" data-choice="${key}" value="${esc(option)}" ${chosen.includes(option)?'checked':''} ${key==='hvac_modes'&&option==='off'?'disabled':''}><span>${esc(option.replaceAll('_',' '))}</span>`;box.querySelector('.choice-box').append(labelNode);}
    container.append(box);extras[key]=()=>[...box.querySelectorAll('input:checked')].map(input=>input.value);
  }
  function addField(container,name,label,type='text',settings={}){
    const row=document.createElement('label');row.className='field-row';row.innerHTML=`<span class="field-label">${esc(label)}</span>`;let control;
    if(settings.options){control=document.createElement('select');for(const option of settings.options){const item=document.createElement('option');item.value=typeof option==='string'?option:option[0];item.textContent=typeof option==='string'?option:option[1];control.append(item);}}
    else {control=document.createElement('input');control.type=type;for(const [key,value] of Object.entries(settings.attrs||{}))control.setAttribute(key,value);}
    control.className='field-input';control.name=name;control.value=values[name]??settings.default??'';row.append(control);container.append(row);extras[name]=()=>type==='number'?Number(control.value):control.value;return control;
  }
  function addToggle(container,name,label){const row=document.createElement('label');row.className='toggle-row';row.innerHTML=`<span class="field-label">${esc(label)}</span><input type="checkbox" name="${name}" ${values[name]?'checked':''}><span class="toggle-track"></span><span data-toggle-value>${values[name]?'Yes':'No'}</span>`;const input=row.querySelector('input');input.onchange=()=>row.querySelector('[data-toggle-value]').textContent=input.checked?'Yes':'No';container.append(row);extras[name]=()=>input.checked;}
  function addEntity(container,name,label,domains){const options=[['','— None —'],...Object.values(panel._hass.states||{}).filter(state=>domains.includes(state.entity_id.split('.')[0])).sort((a,b)=>a.entity_id.localeCompare(b.entity_id)).map(state=>[state.entity_id,state.attributes?.friendly_name||state.entity_id])];return addField(container,name,label,'text',{options});}
  if(climate){
    addField(connection,'mqtt_delay','MQTT Delay (seconds)','number',{default:0,attrs:{min:0,max:60,step:.1}});
    addEntity(connection,'temperature_sensor','Temperature Sensor',['sensor','input_number']);
    addEntity(connection,'humidity_sensor','Humidity Sensor',['sensor','input_number']);
    addEntity(connection,'power_sensor','Power Sensor',['binary_sensor','switch','input_boolean']);
    addEntity(connection,'availability_sensor','Availability Sensor',['binary_sensor','sensor','input_boolean']);
    const capabilities=pane('capabilities','Capabilities');
    checklist(capabilities,'hvac_modes','HVAC Modes',modes,modes);
    checklist(capabilities,'fan_modes','Fan Speeds',fans,fans);
    checklist(capabilities,'swing_modes','Swing Positions',swings,[]);
    for(const name of ['min_temp','max_temp','temp_step'])move(name,capabilities);
    field('min_temp').max=122;field('max_temp').max=122;
    addField(capabilities,'initial_hvac_mode','Initial Operation Mode','text',{default:'off',options:modes.map(mode=>[mode,mode.replaceAll('_',' ')])});
    addField(capabilities,'initial_target_temp','Default Target Temperature','number',{default:24,attrs:{min:1,max:122,step:.1}});
    addField(capabilities,'precision','Display Precision','number',{default:.1,options:[[.1,'0.1°'],[.5,'0.5°'],[1,'1°']]});
    addField(capabilities,'temperature_unit','Temperature Unit','text',{default:'C',options:[['C','Celsius (°C)'],['F','Fahrenheit (°F)']]});
    addField(capabilities,'away_temp','Away Temperature (0 = disabled)','number',{default:0,attrs:{min:0,max:122,step:.5}});
    const behavior=pane('behavior','Behavior');
    checklist(behavior,'feature_switches','Toggle Features',features,[]);
    const help=document.createElement('p');help.className='help';help.textContent='Choose features your AC supports. Switches send the current AC state with the changed feature, and retain it for later commands. Unsupported features may be ignored by the protocol. Deselecting a switch makes it unavailable.';behavior.append(help);
    addField(behavior,'sleep_minutes','Sleep Value (minutes, 0 = default)','number',{default:0,attrs:{min:0,max:1440}});
    const vertical=addField(behavior,'default_swing_v','Default Vertical Swing','text',{default:'Off',options:['Off','Auto','Highest','High','Middle','Low','Lowest']});
    const horizontal=addField(behavior,'default_swing_h','Default Horizontal Swing','text',{default:'Off',options:['Off','Auto','Left Max','Left','Middle','Right','Right Max','Wide']});
    const defaults=document.createElement('div');defaults.className='choice-group';defaults.innerHTML='<span class="choice-title">Initial Feature Values</span><div class="choice-box"></div>';
    const hvacOptions=JSON.parse(field('hvac_options').value||'{}');vertical.value=hvacOptions.SwingV??'Off';horizontal.value=hvacOptions.SwingH??'Off';
    for(const key of features.filter(k=>!['SwingV','SwingH','Sleep'].includes(k))){const label=document.createElement('label');label.className='choice';label.innerHTML=`<input type="checkbox" data-default="${key}" ${hvacOptions[key]===true?'checked':''}><span>${esc(key)}</span>`;defaults.querySelector('.choice-box').append(label);}
    behavior.append(defaults);
    extras.hvac_options=()=>{const options={...hvacOptions,SwingV:vertical.value,SwingH:horizontal.value};for(const input of defaults.querySelectorAll('input'))options[input.dataset.default]=input.checked;return options;};
    addToggle(behavior,'keep_mode_on_power_on','Keep Mode on Power On');
    addToggle(behavior,'ignore_off_temperature','Ignore Temperature When Off');
    if(selected?.feature_switches?.length){const controls=document.createElement('div');controls.innerHTML='<h3>Control saved feature switches</h3>';for(const key of selected.feature_switches){for(const enabled of [true,false]){const button=document.createElement('button');button.type='button';button.textContent=`${key} ${enabled?'On':'Off'}`;button.onclick=()=>action('feature',{device_id:selected.id,feature:key,enabled},button);controls.append(button);}}behavior.append(controls);}
  } else {
    let commands={};try{commands=JSON.parse(field('command_map').value||'{}');}catch{/* Validation reports malformed stored data. */}
    const known=new Set(Object.values(groups).flat());
    for(const [key,names] of Object.entries(groups)){const section=pane(key,{power:'Power & Volume',navigation:'Navigation',playback:'Playback',channels:'Channels & Colors',keypad:'Keypad'}[key]);for(const name of names)commandRow(section,name,commands[name]);}
    const sources=pane('sources','Sources');sources.innerHTML='<p class="help">Name direct source commands source:HDMI 1, source:TV, etc. Media players expose these in Home Assistant.</p>';
    const custom=pane('custom','Custom Commands');
    for(const [name,command] of Object.entries(commands)){if(!known.has(name))commandRow(name.startsWith('source:')?sources:custom,name,command);}
    for(const [section,isSource] of [[sources,true],[custom,false]]){const wrapper=document.createElement('div');wrapper.innerHTML=`<input aria-label="${isSource?'Source name':'Command name'}" placeholder="${isSource?'HDMI 1':'netflix'}"><button type="button">Add ${isSource?'Source':'Command'}</button>`;wrapper.querySelector('button').onclick=()=>{const name=(isSource?'source:':'')+wrapper.querySelector('input').value.trim();if(!name||name==='source:')return;if([...form.querySelectorAll('[data-command]')].some(n=>n.dataset.command===name)){panel.status('This command already exists.');return;}commandRow(section,name);wrapper.querySelector('input').value='';};section.append(wrapper);}
    if(selected){const remote=pane('remote','Remote Control');remote.innerHTML='<p class="help">Buttons send saved commands. Save edits before using this remote.</p>';for(const name of Object.keys(selected.commands||{})){const b=document.createElement('button');b.type='button';b.className='remote-key';b.textContent=name;b.onclick=()=>action('remote',{device_id:selected.id,command:name},b);remote.append(b);}}
  }
  // JSON storage and legacy address fields are implementation details. The
  // visual controls above are the single source of truth for users.
  field('hvac_options').closest('.field-row').hidden=true;
  field('command_map').closest('.field-row').hidden=true;
  field('address').closest('.field-row').hidden=true;
  root.querySelector('#commands').hidden=true;root.querySelector('#climate_note').hidden=true;
  // All visible editor controls remain in the same form, preserving drafts.
  const previousChange=field('device_type').onchange;
  field('device_type').onchange=()=>{previousChange();capture();panel.activeTab='connection';panel.render();};
  panel.editorValues=()=>Object.fromEntries(Object.entries(extras).map(([key,get])=>[key,get()]));
  panel.validateEditor=()=>{if(!climate&&!advancedEdited)syncCommands();};
  show(panes.has(panel.activeTab)?panel.activeTab:'connection');
  async function action(name,data,button){if(button)button.disabled=true;try{await panel._hass.callWS({type:'tuya_ir_bridge/action',action:name,data});panel.status('Command sent.');}catch(error){panel.status(error.message||String(error));}finally{if(button)button.disabled=false;}}
  function syncCommands(){try{const map={};for(const input of form.querySelectorAll('[data-command]')){if(input.value.trim())map[input.dataset.command]=JSON.parse(input.value);}field('command_map').value=JSON.stringify(map,null,2);capture();return map;}catch(error){panel.status('Command must be an IRsend JSON object or a learned code object.');throw error;}}
  function commandRow(section,name,command){
    const row=document.createElement('div');row.className='command-row';row.innerHTML=`<span class="command-name">${esc(commandLabel(name))}</span><input class="command-code" type="text" aria-label="${esc(commandLabel(name))} IR code" spellcheck="false" autocomplete="off" placeholder="0x20DF10EF"><textarea data-command="${esc(name)}" aria-label="${esc(name)} stored command" hidden></textarea><button type="button" data-learn>Learn</button><button type="button" data-test>Test</button>`;
    const input=row.querySelector('textarea'),code=row.querySelector('.command-code');
    input.value=values._command_drafts?.[name] ?? (command===undefined?'':JSON.stringify(command));
    const defaultBits=()=>panel.catalogue.send.find(item=>item.name===field('protocol').value)?.bits||32;
    function loadCode(){
      let value;try{value=JSON.parse(input.value||'null');}catch{return;}
      code.dataset.stored=input.value;
      if(value?.Learned)code.value=`RAW:${value.Learned}`;
      else if(value&&typeof value==='object'&&typeof value.Data==='string'){code.value=value.Data;code.dataset.protocol=value.Protocol||field('protocol').value;code.dataset.bits=value.Bits||defaultBits();}
      else if(typeof value==='number')code.value=`0x${value.toString(16).toUpperCase()}`;
      else if(value)code.value='Raw timing signal';
      else code.value='';
    }
    function updateCode(){
      const value=code.value.trim();delete code.dataset.stored;
      if(!value)input.value='';
      else if(value.startsWith('RAW:'))input.value=JSON.stringify({Learned:value.slice(4)});
      else {
        if(!/^(?:0x)?[0-9a-f]+$/i.test(value)){panel.status('Enter a hexadecimal IR code, for example 0x20DF10EF.');return;}
        input.value=JSON.stringify({Protocol:code.dataset.protocol||field('protocol').value,Bits:Number(code.dataset.bits||defaultBits()),Data:value});
      }
      syncCommands();
    }
    code.oninput=updateCode;
    input.addEventListener('learned',loadCode);loadCode();
    row.querySelector('[data-test]').onclick=async()=>{try{const map=syncCommands();if(!map[name])throw Error('Enter or learn this command first.');const device={name:field('name').value||'Test',device_type:'remote',topic:field('topic').value.trim(),transport:field('transport').value,protocol:field('protocol').value,commands:{[name]:map[name]},address:Number(field('address').value||0)};await action('test',{device,command:name},row.querySelector('[data-test]'));}catch(error){panel.status(error.message);}};
    row.querySelector('[data-learn]').onclick=()=>learn(input);
    section.append(row);
  }
  async function learn(input){
    if(panel.learning)return;panel.learning=true;
    const overlay=document.createElement('div');overlay.className='learning-overlay';
    overlay.innerHTML='<div role="dialog" aria-modal="true" aria-label="Learn IR command"><h2>Learn IR command</h2><p role="status"></p><button type="button" data-retry hidden>Retry</button><button type="button" data-close>Cancel</button></div>';
    root.append(overlay);
    const message=overlay.querySelector('[role=status]'),retry=overlay.querySelector('[data-retry]'),close=overlay.querySelector('[data-close]');
    let token,closed=false,running=false;
    const stop=async()=>{const current=token;token=null;if(current)await panel._hass.callWS({type:'tuya_ir_bridge/action',action:'learn_cancel',data:{session:current}}).catch(()=>{});};
    const dismiss=async()=>{closed=true;overlay.remove();await stop();panel.learning=false;if(panel.cancelLearning===dismiss)panel.cancelLearning=null;};
    panel.cancelLearning=dismiss;close.onclick=dismiss;
    async function attempt(){
      if(running||closed)return;running=true;retry.hidden=true;close.textContent='Cancel';
      message.textContent='Starting learning…';
      try{
        const started=await panel._hass.callWS({type:'tuya_ir_bridge/action',action:'learn_start',data:{topic:field('topic').value.trim()}});token=started.session;
        if(closed){await stop();return;}
        for(let count=0;count<65&&!closed;count++){
          message.textContent=`Point the original remote at the blaster and press the button. Waiting… ${Math.max(0,30-Math.floor(count/2))} seconds remaining.`;
          await new Promise(resolve=>setTimeout(resolve,500));
          if(closed)break;
          const result=await panel._hass.callWS({type:'tuya_ir_bridge/action',action:'learn_status',data:{session:token}});
          if(closed)break;
          if(result.status==='learned'){
            input.value=JSON.stringify(result.command||{Learned:result.code});input.dispatchEvent(new Event('learned'));syncCommands();
            const decoded=result.command?.Data?`${result.command.Protocol}, ${result.command.Bits} bits: ${result.command.Data}`:'raw timing signal';
            message.textContent=`Command learned as ${decoded}. Close this window to test it, then save the device.`;close.textContent='Done';
            panel.status(`Command learned as ${decoded}. Test it, then save the device.`);return;
          }
          if(result.status!=='waiting')throw Error(result.error||`Learning ${result.status}. Try again.`);
        }
        if(!closed)throw Error('No IR command received. Check the blaster topic and try again.');
      }catch(error){
        if(!closed){const detail=error?.error||error;const text=detail?.message||String(detail);message.textContent=`Learning failed: ${text}`;panel.status(`Learning failed: ${text}`);retry.hidden=false;close.textContent='Close';}
      }finally{await stop();running=false;}
    }
    retry.onclick=attempt;await attempt();
  }
}
