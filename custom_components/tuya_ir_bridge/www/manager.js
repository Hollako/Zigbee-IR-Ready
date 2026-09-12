/* Device manager; CSS reused under MIT from Tasmota IR Ready. */
// Register the Lovelace card whenever the manager is opened as a fallback for
// browsers that started before Home Assistant injected the global module URL.
import './remote_card.js?v=0.4.7';
import {CSS} from './panel.js?v=0.4.7';
import {mountEditor} from './editor.js?v=0.4.7';
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const errorText = error => {
  const detail = error?.error || error;
  if (detail?.code === 'unknown_error') return 'Home Assistant could not complete the request. Check Settings → System → Logs for tuya_ir_bridge, and ensure the integration is updated and Home Assistant has restarted.';
  if (detail?.code === 'unauthorized') return 'Sign in with a Home Assistant administrator account to manage IR devices.';
  return detail?.message || String(detail || 'Request failed. Please try again.');
};
class ZigbeeIRPanel extends HTMLElement {
  constructor() { super(); this.attachShadow({mode:'open'}); this.devices=[]; this.catalogue={climate:[],send:[]}; this.selectedId=null; this.creating=false; this.draft=null; this._narrow=false; }
  set hass(value) {
    this._hass=value;
    this.toggleAttribute('dark',value.themes?.darkMode===true);
    if (!this.started) { this.started=true; this.render(); this.refresh(); }
  }
  set narrow(value) {
    this._narrow=value;
    const menu=this.shadowRoot.querySelector('.menu-button');
    if(menu)menu.narrow=value;
  }
  selectDevice(id) {
    if (this.saving || this.learning) return;
    this.selectedId=id; this.creating=false; this.draft=null; this.render();
  }
  createDevice() {
    if (this.saving || this.learning) return;
    this.selectedId=null; this.creating=true; this.draft=null; this.activeTab='connection'; this.render();
  }
  async refresh() {
    if(this.learning)return false;
    try {
      const [devices,catalogue]=await Promise.all([
        this._hass.callWS({type:'tuya_ir_bridge/list'}),
        this._hass.callWS({type:'tuya_ir_bridge/catalogue'}),
      ]);
      this.devices=devices; this.catalogue=catalogue; this.render(); return true;
    }
    catch(error) { this.status(errorText(error)); return false; }
  }
  status(message) { this.shadowRoot.querySelector('.statusbar').textContent=message; }
  disconnectedCallback() { this.cancelLearning?.(); }
  async deleteDevice(device) {
    if(this.saving || this.learning)return;
    const dialog=document.createElement('dialog');
    dialog.innerHTML=`<h2>Delete ${esc(device.name)}?</h2><p>This removes the saved configuration, learned commands, and all its Home Assistant entities, including feature switches and companion remotes.</p><p>The physical Zigbee IR blaster and other virtual devices will remain.</p><p role="alert"></p><button type="button" data-cancel>Cancel</button><button type="button" data-confirm>Delete permanently</button>`;
    this.shadowRoot.append(dialog);dialog.showModal();
    dialog.querySelector('[data-cancel]').onclick=()=>dialog.close();
    dialog.onclose=()=>dialog.remove();
    dialog.oncancel=event=>{if(this.saving)event.preventDefault();};
    dialog.querySelector('[data-confirm]').onclick=async()=>{
      this.saving=true;dialog.querySelector('[data-confirm]').disabled=true;
      dialog.querySelector('[data-cancel]').disabled=true;
      try{
        await this._hass.callWS({type:'tuya_ir_bridge/delete',device_id:device.id});
        this.devices=this.devices.filter(d=>d.id!==device.id);this.selectedId=null;this.creating=false;this.draft=null;this.activeTab='connection';
        dialog.close();this.render();this.status('Device deleted, including its related Home Assistant entities.');
      }catch(error){dialog.querySelector('[role=alert]').textContent=errorText(error);dialog.querySelector('[data-confirm]').disabled=false;dialog.querySelector('[data-cancel]').disabled=false;}
      finally{this.saving=false;}
    };
  }
  render() {
    const selected=this.devices.find(device=>device.id===this.selectedId);
    const editing=!!selected;
    const showingEditor=editing || this.creating;
    const menuButton=customElements.get('ha-menu-button')
      ? '<ha-menu-button class="menu-button"></ha-menu-button>'
      : '<button class="menu-fallback" id="menu" title="Open Home Assistant sidebar" aria-label="Open Home Assistant sidebar">☰</button>';
    const typeLabels={climate:'Climate',media_player:'Media Player',remote:'Remote',light:'Light'};
    const sidebarHtml=Object.entries(typeLabels).map(([type,label])=>{
      const devices=this.devices.filter(device=>device.device_type===type);
      if(!devices.length)return '';
      return `<div class="sidebar-section"><div class="sidebar-section-title">${label}</div>${devices.map(device=>`<button type="button" class="sidebar-item${device.id===this.selectedId?' active':''}" data-device-id="${esc(device.id)}" aria-label="Edit ${esc(device.name)}"><span>${esc(device.name)}</span><small>Edit</small></button>`).join('')}</div>`;
    }).join('') || '<div class="sidebar-empty">No IR devices found.<br>Use Add to create one.</div>';
    this.shadowRoot.innerHTML=`<style>${CSS}
      :host{color-scheme:light} :host([dark]){color-scheme:dark}
      .main{padding:0;overflow:hidden}.editor-content{padding:24px;overflow:auto;min-height:0}.entry-toolbar{position:relative;z-index:1}.entry-toolbar h2{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.placeholder{display:flex;flex:1;flex-direction:column;align-items:center;justify-content:center;gap:12px;color:var(--secondary-text-color,#888)}.placeholder svg{width:64px;height:64px;opacity:.45} form{max-width:1400px} .field-row{flex-wrap:wrap}
      select.field-input, select.field-input option, select.field-input optgroup {
        color:var(--primary-text-color,#212121);
        background-color:var(--card-background-color,var(--primary-background-color,#fff));
      }
      button.sidebar-item{width:100%;border:0;text-align:left;font:inherit;color:var(--primary-text-color,#212121);background:transparent}
      button.sidebar-item.active{color:var(--text-primary-color,#fff);background:var(--primary-color,#03a9f4)}
      .sidebar-item small{margin-left:auto}.sidebar-empty{padding:16px;font-size:.85rem;line-height:1.5;color:var(--secondary-text-color,#888)} .form-actions{display:none}
      fieldset{border:0;padding:0;margin:0;min-width:0}
      .command-row{display:grid;grid-template-columns:minmax(110px,180px) minmax(220px,1fr) auto auto;align-items:center;gap:7px}.command-name{font-weight:500}.command-code{box-sizing:border-box;width:100%;height:36px;padding:7px 10px;border:1px solid var(--divider-color,#666);border-radius:5px;background:var(--card-background-color,#fff);color:var(--primary-text-color,#222);font-family:monospace}.command-row button{display:inline-flex;align-items:center;justify-content:center;gap:5px;height:36px;border:0;border-radius:5px;padding:7px 12px;color:#fff;white-space:nowrap}.command-row button ha-icon{--mdc-icon-size:15px}.command-row button[data-learn]{background:#ff9800}.command-row button[data-test]{background:var(--success-color,#2e7d32)}@media(max-width:700px){.command-row{grid-template-columns:1fr auto auto}.command-name{grid-column:1/-1}.editor-tabs{gap:4px}}
      [hidden]{display:none!important}.editor-tabs{display:flex;gap:6px;flex-wrap:wrap;margin:16px 0}.editor-tabs button{padding:10px;border:1px solid var(--divider-color,#777);background:var(--card-background-color,#fff);color:var(--primary-text-color,#222);border-radius:6px}.editor-tabs [aria-selected=true]{background:var(--primary-color,#03a9f4);color:var(--text-primary-color,#fff)}
      .choice-group{display:flex;align-items:center;gap:8px;margin-bottom:10px}.choice-title{width:200px;min-width:160px;font-size:.88rem;color:var(--secondary-text-color,#aaa)}.choice-box{display:flex;flex:1;flex-wrap:wrap;gap:7px;padding:8px;border:1px solid var(--divider-color,#666);border-radius:5px}.choice{position:relative;display:inline-flex;align-items:center;cursor:pointer}.choice input{position:absolute;inset:0;width:100%;height:100%;margin:0;opacity:0;cursor:pointer}.choice span{pointer-events:none;padding:5px 12px;border:1px solid var(--divider-color,#666);border-radius:16px;font-size:12px;line-height:1;color:var(--primary-text-color,#ddd)}.choice:has(input:checked) span{background:#ff9800;border-color:#ff9800;color:#fff}.choice:has(input:disabled) span{opacity:.85}.toggle-row{display:flex;align-items:center;gap:10px;margin:12px 0}.toggle-row>input{width:1px;height:1px;opacity:0;margin:0}.toggle-track{width:42px;height:24px;border-radius:14px;background:var(--disabled-color,#777);position:relative;cursor:pointer}.toggle-track:after{content:'';position:absolute;width:18px;height:18px;left:3px;top:3px;border-radius:50%;background:#fff;transition:left .15s}.toggle-row>input:checked+.toggle-track{background:#ff9800}.toggle-row>input:checked+.toggle-track:after{left:21px}.command-row{padding:10px 0;border-bottom:1px solid var(--divider-color,#777)}.command-row textarea{display:block;width:100%;box-sizing:border-box;min-height:60px;background:var(--card-background-color,#fff);color:var(--primary-text-color,#222)}.remote-key{margin:6px;padding:10px}.learning-overlay{position:fixed;inset:0;background:#0009;display:grid;place-items:center;z-index:10}.learning-overlay>div{background:var(--card-background-color,#fff);color:var(--primary-text-color,#222);padding:30px;max-width:400px}.form-actions{margin-top:20px}
      textarea{min-height:100px} .help{color:var(--secondary-text-color);line-height:1.6}
      @media(max-width:600px){.field-label,.choice-title{width:100%}.choice-group{display:block}.choice-box{margin-top:6px}.editor-content{padding:12px}.entry-toolbar{padding:8px}.entry-toolbar .btn{padding:6px 10px}.entry-toolbar h2{font-size:.9rem}}
      </style>
      <div class="topbar">${menuButton}<h1>Zigbee IR Ready</h1><button id="new" title="Add new IR device" aria-label="Add">➕ Add</button><button id="refresh" title="Refresh device list">⟳ Refresh</button></div>
      <div class="layout"><div class="sidebar">${sidebarHtml}
      </div><div class="main">${showingEditor?`<div class="entry-toolbar"><h2>${editing?esc(selected.name):'New Device'}</h2>${editing?'<button class="btn btn-danger" id="delete-device" type="button" title="Delete this device" aria-label="Delete Device">🗑 Delete</button>':''}<button class="btn btn-primary" id="save-device" type="submit" form="device-form" aria-label="${editing?'Save Changes':'Create Device'}">${editing?'💾 Save':'➕ Create'}</button></div><div class="editor-content">
      ${editing?'<p class="help">Changes apply to this existing entity. Device type is fixed; use New Device for a different type.</p>':''}
      <p class="help">The bundled IRremoteESP8266 engine provides ${this.catalogue.climate.length} HVAC protocols and ${this.catalogue.send.length} IRsend protocols. Encoding runs locally inside this HACS integration.</p>
      <form id="device-form"><fieldset>
      <div class="field-row"><label class="field-label" for="name">Device Name</label><input class="field-input" id="name" name="name" required maxlength="100"></div>
      <div class="field-row"><label class="field-label" for="device_type">Device Type</label><select class="field-input" id="device_type" name="device_type"><option value="climate">Climate</option><option value="media_player">Media Player</option><option value="remote">Remote</option><option value="light">Light</option></select></div>
      <div class="field-row"><label class="field-label" for="topic">MQTT Command Topic</label><input class="field-input" id="topic" name="topic" placeholder="zigbee2mqtt/Living Room IR/set/ir_code_to_send" required></div>
      <div class="field-row"><label class="field-label" for="transport">Blaster Transport</label><select class="field-input" id="transport" name="transport"><option value="zosung">Zosung JSON · protocol carrier frequency</option><option value="base64">Legacy Base64 · 38 kHz only</option></select></div>
      <p class="help">Zosung JSON requires a recent Zigbee2MQTT converter accepting full IR messages. Legacy Base64 works only for 38 kHz signals. Hardware limits still apply.</p>
      <div class="field-row"><label class="field-label" for="protocol">Brand / Protocol</label><select class="field-input" id="protocol" name="protocol" required></select></div>
      <p class="help" id="protocol_note" role="status"></p>
      <div id="commands" hidden>
      <div class="field-row" id="legacy-address" hidden><label class="field-label" for="address">Legacy Protocol Address</label><input class="field-input" id="address" name="address" type="number" min="0" max="255" value="0"></div>
      <div class="field-row"><label class="field-label" for="command_map">Named IRsend Commands</label><textarea class="field-input" id="command_map" name="command_map" placeholder='{"power": {"Bits": 32, "Data": "0x20DF10EF", "Repeat": 0}}'></textarea></div>
      <p class="help">Use IRsend objects with Bits, hexadecimal Data and optional Repeat. Protocol defaults to your selection and may be overridden per command. Media/Light require turn_on and turn_off. These are model command values, not learned Base64 codes.</p></div>
      <div id="climate_note">
      <div class="field-row"><label class="field-label" for="model">Protocol Model Number</label><input class="field-input" id="model" name="model" type="number" min="-1" max="32767" value="-1"></div>
      <div class="field-row"><label class="field-label" for="min_temp">Minimum Temperature</label><input class="field-input" id="min_temp" name="min_temp" type="number" min="1" max="49" value="16"></div>
      <div class="field-row"><label class="field-label" for="max_temp">Maximum Temperature</label><input class="field-input" id="max_temp" name="max_temp" type="number" min="2" max="50" value="30"></div>
      <div class="field-row"><label class="field-label" for="temp_step">Temperature Step</label><input class="field-input" id="temp_step" name="temp_step" type="number" min="0.5" max="1" step="0.5" value="1"></div>
      <div class="field-row"><label class="field-label" for="hvac_options">Extra IRhvac Options</label><textarea class="field-input" id="hvac_options" name="hvac_options" placeholder='{"SwingV": "Auto", "SwingH": "Off", "Turbo": false}'></textarea></div>
      <p class="help">Select the exact protocol variant and model used by your AC. Model -1 uses the upstream default. Configure the temperature range for your model; unsupported features may be ignored by its encoder.</p></div>
      <div class="form-actions" aria-hidden="true"></div></fieldset></form></div>`:`<div class="placeholder"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 5h10v2H7zm0 4h10v2H7zm0 4h7v2H7zm10 5.5L20 16l-3-2.5V17h-6v2h6v2.5z"/></svg><span>Select a device from the sidebar</span></div>`}</div></div><div class="statusbar status-info" role="status" aria-live="polite"></div>`;
    const nativeMenu=this.shadowRoot.querySelector('.menu-button');
    if(nativeMenu){nativeMenu.hass=this._hass;nativeMenu.narrow=this._narrow;}
    const fallbackMenu=this.shadowRoot.querySelector('#menu');
    if(fallbackMenu)fallbackMenu.onclick=()=>this.dispatchEvent(new CustomEvent('hass-toggle-menu',{bubbles:true,composed:true}));
    this.shadowRoot.querySelector('#refresh').onclick=()=>{if(!this.saving)this.refresh();};
    this.shadowRoot.querySelector('#new').onclick=()=>this.createDevice();
    for (const button of this.shadowRoot.querySelectorAll('[data-device-id]')) button.onclick=()=>this.selectDevice(button.dataset.deviceId);
    if(!showingEditor)return;
    if(editing)this.shadowRoot.querySelector('#delete-device').onclick=()=>this.deleteDevice(selected);
    const form=this.shadowRoot.querySelector('form');
    const deviceType=form.elements.namedItem('device_type');
    const protocol=form.elements.namedItem('protocol');
    const values=this.draft || (selected?{
      ...selected, protocol:selected.protocol.toUpperCase()==='ELECTRA'?'ELECTRA_AC':selected.protocol.toUpperCase(),
      transport:selected.transport || 'base64', model:selected.model ?? -1,
      min_temp:selected.min_temp ?? 16, max_temp:selected.max_temp ?? (selected.protocol.toUpperCase().startsWith('ELECTRA')?32:30),
      temp_step:selected.temp_step ?? 1, address:selected.address ?? 0,
      command_map:JSON.stringify(selected.commands || {},null,2), hvac_options:JSON.stringify(selected.hvac_options || {},null,2),
    }:{});
    for(const [name,value] of Object.entries(values)) {
      const field=form.elements.namedItem(name);
      if(field && name!=='protocol') field.value=value;
    }
    deviceType.disabled=editing;
    deviceType.onchange=()=>{
      const climate=deviceType.value==='climate';
      const names=climate?this.catalogue.climate:this.catalogue.send.map(p=>p.name);
      protocol.innerHTML=names.map(name=>`<option value="${esc(name)}">${esc(name.replaceAll('_',' '))}</option>`).join('');
      if (!names.length) protocol.innerHTML='<option value="">Loading protocol engine…</option>';
      protocol.onchange=()=>{this.shadowRoot.querySelector('#protocol_note').textContent=this.catalogue.notes?.[protocol.value] || '';};
      protocol.onchange();
      this.shadowRoot.querySelector('#commands').hidden=climate;
      this.shadowRoot.querySelector('#climate_note').hidden=!climate;
    };
    deviceType.onchange();
    if(values.protocol) {protocol.value=values.protocol;protocol.onchange();}
    const legacy=!!selected && Object.values(selected.commands || {}).some(value=>typeof value==='number');
    this.shadowRoot.querySelector('#legacy-address').hidden=!legacy;
    this.editorValues=null;this.validateEditor=null;
    const capture=()=>{this.draft={...Object.fromEntries(new FormData(form)),device_type:deviceType.value,...this.editorValues?.(),_command_drafts:Object.fromEntries([...form.querySelectorAll('[data-command]')].map(input=>[input.dataset.command,input.value]))};};
    form.oninput=capture;
    form.onchange=capture;
    form.onsubmit=async event=>{
      event.preventDefault(); if(this.saving)return;
      const button=this.shadowRoot.querySelector('#save-device'); button.disabled=true; this.saving=true;
      try {
        this.validateEditor?.();
        const data=Object.fromEntries(new FormData(form));
        const device={name:data.name,device_type:deviceType.value,topic:data.topic.trim(),protocol:data.protocol,transport:data.transport};
        if(device.device_type!=='climate') {
          device.commands=JSON.parse(data.command_map);
          if(legacy)device.address=Number(data.address);
        }
        else {
          device.model=Number(data.model); device.min_temp=Number(data.min_temp); device.max_temp=Number(data.max_temp); device.temp_step=Number(data.temp_step);
          device.hvac_options=JSON.parse(data.hvac_options.trim() || '{}');
          const editorData=this.editorValues?.() || {};
          const savedEditorFields=['hvac_modes','fan_modes','swing_modes','feature_switches','sleep_minutes','initial_hvac_mode','initial_target_temp','precision','temperature_unit','away_temp','mqtt_delay','temperature_sensor','humidity_sensor','power_sensor','availability_topic','keep_mode_on_power_on','ignore_off_temperature','hvac_options'];
          for(const key of savedEditorFields)if(Object.hasOwn(editorData,key))device[key]=editorData[key];
          // These controls are created by the tab editor. Copy them
          // explicitly into every climate save so browser FormData behavior,
          // tab changes, or an empty selection cannot silently omit them.
          for(const key of ['temperature_sensor','humidity_sensor','power_sensor','availability_topic']) {
            const value=editorData[key] ?? data[key] ?? '';
            device[key]=typeof value==='string'?value.trim():'';
          }
        }
        form.querySelector('fieldset').disabled=true;
        const saved=await this._hass.callWS(editing?{type:'tuya_ir_bridge/update',device_id:selected.id,device}:{type:'tuya_ir_bridge/create',device});
        this.devices=[...this.devices.filter(d=>d.id!==saved.id),saved];
        this.selectedId=saved.id; this.creating=false; this.draft=null;
        this.render();
        if (await this.refresh()) this.status(editing?'Changes saved. The existing entity has been updated.':'Device created. You can edit its settings here.');
        else this.status('Device saved, but the list could not refresh. Use Refresh; do not create the device again.');
      } catch(error) { this.status(errorText(error)); form.querySelector('fieldset').disabled=false; button.disabled=false; }
      finally {this.saving=false;}
    };
    mountEditor(this,form,selected,values,capture);
  }
}
if (!customElements.get('zigbee-ir-ready-panel')) customElements.define('zigbee-ir-ready-panel',ZigbeeIRPanel);
