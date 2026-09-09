/* Tabbed editor inspired by Tasmota IR Ready (MIT, copyright 2026 Hollako). */
const esc = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const modes=['off','auto','cool','heat','dry','fan_only'];
const fans=['auto','min','low','medium','high','max'];
const swings=['off','vertical','horizontal','both','highest','high','middle','low','lowest','left max','left','horizontal middle','right','right max','wide'];
const features=['SwingV','SwingH','Quiet','Turbo','Econo','Light','Filter','Clean','Beep','Sleep','iFeel'];
const groups={power:['power','turn_on','turn_off','volume_up','volume_down','mute'],navigation:['up','down','left','right','ok','back','home','menu','settings','info','exit'],playback:['play','pause','play_pause','stop','next','previous','rewind','fast_forward'],channels:['channel_up','channel_down','red','green','yellow','blue'],keypad:Array.from({length:10},(_,i)=>`digit_${i}`)};
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
    const box=document.createElement('div');box.className='choice-group';box.innerHTML=`<h3>${esc(label)}</h3>`;
    const chosen=arrayValue(key,defaults);
    for(const option of options){const labelNode=document.createElement('label');labelNode.className='choice';labelNode.innerHTML=`<input type="checkbox" data-choice="${key}" value="${esc(option)}" ${chosen.includes(option)?'checked':''} ${key==='hvac_modes'&&option==='off'?'disabled':''}> ${esc(option.replaceAll('_',' '))}`;box.append(labelNode);}
    container.append(box);extras[key]=()=>[...box.querySelectorAll('input:checked')].map(input=>input.value);
  }
  if(climate){
    const capabilities=pane('capabilities','Capabilities');
    checklist(capabilities,'hvac_modes','HVAC modes shown in Home Assistant',modes,modes);
    checklist(capabilities,'fan_modes','Fan speeds shown in Home Assistant',fans,fans);
    checklist(capabilities,'swing_modes','Swing positions shown in Home Assistant',swings,[]);
    for(const name of ['min_temp','max_temp','temp_step'])move(name,capabilities);
    const behavior=pane('behavior','Behavior & Switches');
    checklist(behavior,'feature_switches','Create separate Home Assistant switches',features,[]);
    const help=document.createElement('p');help.className='help';help.textContent='Choose features your AC supports. Switches send the current AC state with the changed feature, and retain it for later commands. Unsupported features may be ignored by the protocol. Deselecting a switch makes it unavailable.';behavior.append(help);
    const sleep=document.createElement('label');sleep.className='field-row';sleep.innerHTML='<span class="field-label">Sleep duration (minutes, 0 = protocol default)</span><input class="field-input" name="sleep_minutes" type="number" min="0" max="1440">';behavior.append(sleep);field('sleep_minutes').value=values.sleep_minutes??0;extras.sleep_minutes=()=>Number(field('sleep_minutes').value);
    const defaults=document.createElement('div');defaults.innerHTML='<h3>Initial feature values</h3><p class="help">These seed the first command. Live feature switches can change them afterwards.</p>';
    for(const key of features.filter(k=>!['SwingV','SwingH','Sleep'].includes(k))){const label=document.createElement('label');label.className='choice';const options=JSON.parse(field('hvac_options').value||'{}');label.innerHTML=`<input type="checkbox" data-default="${key}" ${options[key]===true?'checked':''}> ${esc(key)}`;defaults.append(label);}
    defaults.onchange=()=>{try{const options=JSON.parse(field('hvac_options').value||'{}');for(const input of defaults.querySelectorAll('input'))options[input.dataset.default]=input.checked;field('hvac_options').value=JSON.stringify(options,null,2);capture();}catch(error){panel.status(error.message);}};
    behavior.append(defaults);
    if(selected){const controls=document.createElement('div');controls.innerHTML='<h3>Control saved feature switches</h3>';for(const key of selected.feature_switches||[]){for(const enabled of [true,false]){const button=document.createElement('button');button.type='button';button.textContent=`${key} ${enabled?'On':'Off'}`;button.onclick=()=>action('feature',{device_id:selected.id,feature:key,enabled},button);controls.append(button);}}behavior.append(controls);}
  } else {
    let commands={};try{commands=JSON.parse(field('command_map').value||'{}');}catch{/* Advanced draft remains visible. */}
    const known=new Set(Object.values(groups).flat());
    for(const [key,names] of Object.entries(groups)){const section=pane(key,{power:'Power & Volume',navigation:'Navigation',playback:'Playback',channels:'Channels & Colors',keypad:'Keypad'}[key]);for(const name of names)commandRow(section,name,commands[name]);}
    const sources=pane('sources','Sources');sources.innerHTML='<p class="help">Name direct source commands source:HDMI 1, source:TV, etc. Media players expose these in Home Assistant.</p>';
    const custom=pane('custom','Custom Commands');
    for(const [name,command] of Object.entries(commands)){if(!known.has(name))commandRow(name.startsWith('source:')?sources:custom,name,command);}
    for(const [section,isSource] of [[sources,true],[custom,false]]){const wrapper=document.createElement('div');wrapper.innerHTML=`<input aria-label="${isSource?'Source name':'Command name'}" placeholder="${isSource?'HDMI 1':'netflix'}"><button type="button">Add ${isSource?'Source':'Command'}</button>`;wrapper.querySelector('button').onclick=()=>{const name=(isSource?'source:':'')+wrapper.querySelector('input').value.trim();if(!name||name==='source:')return;if([...form.querySelectorAll('[data-command]')].some(n=>n.dataset.command===name)){panel.status('This command already exists.');return;}commandRow(section,name);wrapper.querySelector('input').value='';};section.append(wrapper);}
    if(selected){const remote=pane('remote','Remote Control');remote.innerHTML='<p class="help">Buttons send saved commands. Save edits before using this remote.</p>';for(const name of Object.keys(selected.commands||{})){const b=document.createElement('button');b.type='button';b.className='remote-key';b.textContent=name;b.onclick=()=>action('remote',{device_id:selected.id,command:name},b);remote.append(b);}}
  }
  const advanced=pane('advanced','Advanced');move('hvac_options',advanced);move('address',advanced);move('command_map',advanced);
  field('hvac_options').closest('.field-row').hidden=!climate;
  field('command_map').closest('.field-row').hidden=climate;
  if(climate)field('address').closest('.field-row').hidden=true;
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
    const row=document.createElement('div');row.className='command-row';row.innerHTML=`<div class="command-name">${esc(name)}</div><textarea data-command="${esc(name)}" aria-label="${esc(name)} command" placeholder='{"Bits":32,"Data":"0x20DF10EF"}'></textarea><div class="command-actions"><button type="button" data-learn>Learn</button><button type="button" data-test>Test</button><button type="button" data-clear>Clear</button></div>`;
    const input=row.querySelector('textarea');input.value=values._command_drafts?.[name] ?? (command===undefined?'':JSON.stringify(command));
    const simple=document.createElement('div');simple.className='command-inputs';
    simple.innerHTML='<label>Format <select aria-label="Command format"><option value="irsend">Generated IRsend</option><option value="learned">Learned IR</option><option value="advanced">Advanced / Legacy</option></select></label><label data-bits>Bits <input type="number" min="1" max="4096" value="32"></label><label data-code>Hex Data <input type="text" placeholder="0x20DF10EF"></label><span data-learned></span>';
    const format=simple.querySelector('select'),bits=simple.querySelector('[data-bits] input'),code=simple.querySelector('[data-code] input');
    const details=document.createElement('details');const summary=document.createElement('summary');summary.textContent='Advanced';details.append(summary);details.append(input);
    const toolbar=document.createElement('div');toolbar.className='command-toolbar';row.querySelector('.command-name').after(toolbar);toolbar.append(simple,details,row.querySelector('.command-actions'));
    function loadSimple(){let value;try{value=JSON.parse(input.value||'null');}catch{return;}format.value=value?.Learned?'learned':(value===null||typeof value==='object'&&value.Protocol!=='RAW'?'irsend':'advanced');bits.value=value?.Bits||32;code.value=value?.Data||'';simple.querySelector('[data-learned]').textContent=value?.Learned?'IR code captured. Use Test to check it.':'';display();}
    function display(){simple.querySelector('[data-bits]').hidden=format.value!=='irsend';simple.querySelector('[data-code]').hidden=format.value!=='irsend';details.open=format.value==='advanced';}
    function updateSimple(){if(format.value!=='irsend')return;let previous={};try{const parsed=JSON.parse(input.value||'{}');if(parsed&&typeof parsed==='object'&&!parsed.Learned)previous=parsed;}catch{}input.value=code.value.trim()?JSON.stringify({...previous,Bits:Number(bits.value),Data:code.value.trim()}):'';syncCommands();}
    format.onchange=()=>{display();if(format.value==='irsend')updateSimple();};bits.oninput=updateSimple;code.oninput=updateSimple;
    input.onchange=()=>{try{syncCommands();loadSimple();}catch{}};
    input.addEventListener('learned',loadSimple);loadSimple();
    row.querySelector('[data-clear]').onclick=()=>{input.value='';loadSimple();syncCommands();};
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
            input.value=JSON.stringify({Learned:result.code});input.dispatchEvent(new Event('learned'));syncCommands();
            message.textContent='Command learned. Close this window to test it, then save the device.';close.textContent='Done';
            panel.status('Command learned. Test it, then save the device.');return;
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
