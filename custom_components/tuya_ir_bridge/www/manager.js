/* Device manager; CSS reused under MIT from Tasmota IR Ready. */
import {CSS} from './panel.js';
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const errorText = error => {
  const detail = error?.error || error;
  if (detail?.code === 'unknown_error') return 'Home Assistant could not complete the request. Check Settings → System → Logs for tuya_ir_bridge, and ensure the integration is updated and Home Assistant has restarted.';
  if (detail?.code === 'unauthorized') return 'Sign in with a Home Assistant administrator account to manage IR devices.';
  return detail?.message || String(detail || 'Request failed. Please try again.');
};
class ZigbeeIRPanel extends HTMLElement {
  constructor() { super(); this.attachShadow({mode:'open'}); this.devices=[]; this.catalogue={climate:[],send:[]}; this.selectedId=null; this.draft=null; }
  set hass(value) {
    this._hass=value;
    this.toggleAttribute('dark',value.themes?.darkMode===true);
    if (!this.started) { this.started=true; this.render(); this.refresh(); }
  }
  selectDevice(id) {
    if (this.saving) return;
    this.selectedId=id; this.draft=null; this.render();
  }
  async refresh() {
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
  render() {
    const selected=this.devices.find(device=>device.id===this.selectedId);
    const editing=!!selected;
    this.shadowRoot.innerHTML=`<style>${CSS}
      :host{color-scheme:light} :host([dark]){color-scheme:dark}
      .main {padding:24px;overflow:auto} form{max-width:760px} .field-row{flex-wrap:wrap}
      select.field-input, select.field-input option, select.field-input optgroup {
        color:var(--primary-text-color,#212121);
        background-color:var(--card-background-color,var(--primary-background-color,#fff));
      }
      button.sidebar-item{width:100%;border:0;text-align:left;font:inherit;color:var(--primary-text-color,#212121);background:transparent}
      button.sidebar-item.active{color:var(--text-primary-color,#fff);background:var(--primary-color,#03a9f4)}
      .sidebar-item small{margin-left:auto} .form-actions{display:flex;gap:12px}
      fieldset{border:0;padding:0;margin:0;min-width:0}
      textarea{min-height:100px} .help{color:var(--secondary-text-color);line-height:1.6}
      @media(max-width:600px){.field-label{width:100%}.main{padding:12px}}
      </style>
      <div class="topbar"><button id="menu" aria-label="Open sidebar">☰</button><h1>Zigbee IR Ready</h1><button id="new">＋ New Device</button><button id="refresh">⟳ Refresh</button></div>
      <div class="layout"><div class="sidebar">${['climate','media_player','remote','light'].map(type=>`
        <div class="sidebar-section-title">${esc(type.replace('_',' '))}</div>${this.devices.filter(d=>d.device_type===type).map(d=>`<button type="button" class="sidebar-item${d.id===this.selectedId?' active':''}" data-device-id="${esc(d.id)}" aria-label="Edit ${esc(d.name)}"><span>${esc(d.name)}</span><small>Edit</small></button>`).join('')}`).join('')}
      </div><div class="main"><h2>${editing?'Edit Device':'Create Device'}</h2>
      ${editing?'<p class="help">Changes apply to this existing entity. Device type is fixed; use New Device for a different type.</p>':''}
      <p class="help">The bundled IRremoteESP8266 engine provides ${this.catalogue.climate.length} HVAC protocols and ${this.catalogue.send.length} IRsend protocols. Encoding runs locally inside this HACS integration.</p>
      <form><fieldset>
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
      <div class="form-actions"><button type="submit">${editing?'Save Changes':'Create Device'}</button>${editing?'<button id="cancel" type="button">Cancel Changes</button>':''}</div></fieldset></form></div></div><div class="statusbar status-info" role="status" aria-live="polite"></div>`;
    this.shadowRoot.querySelector('#menu').onclick=()=>this.dispatchEvent(new CustomEvent('hass-toggle-menu',{bubbles:true,composed:true}));
    this.shadowRoot.querySelector('#refresh').onclick=()=>{if(!this.saving)this.refresh();};
    this.shadowRoot.querySelector('#new').onclick=()=>this.selectDevice(null);
    for (const button of this.shadowRoot.querySelectorAll('[data-device-id]')) button.onclick=()=>this.selectDevice(button.dataset.deviceId);
    if(editing) this.shadowRoot.querySelector('#cancel').onclick=()=>this.selectDevice(this.selectedId);
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
    const capture=()=>{this.draft={...Object.fromEntries(new FormData(form)),device_type:deviceType.value};};
    form.oninput=capture;
    form.onchange=capture;
    form.onsubmit=async event=>{
      event.preventDefault(); if(this.saving)return;
      const button=form.querySelector('[type=submit]'); button.disabled=true; this.saving=true;
      try {
        const data=Object.fromEntries(new FormData(form));
        const device={name:data.name,device_type:deviceType.value,topic:data.topic.trim(),protocol:data.protocol,transport:data.transport};
        if(device.device_type!=='climate') {
          device.commands=JSON.parse(data.command_map);
          if(legacy)device.address=Number(data.address);
        }
        else {
          device.model=Number(data.model); device.min_temp=Number(data.min_temp); device.max_temp=Number(data.max_temp); device.temp_step=Number(data.temp_step);
          device.hvac_options=JSON.parse(data.hvac_options.trim() || '{}');
        }
        form.querySelector('fieldset').disabled=true;
        const saved=await this._hass.callWS(editing?{type:'tuya_ir_bridge/update',device_id:selected.id,device}:{type:'tuya_ir_bridge/create',device});
        this.devices=[...this.devices.filter(d=>d.id!==saved.id),saved];
        this.selectedId=saved.id; this.draft=null;
        this.render();
        if (await this.refresh()) this.status(editing?'Changes saved. The existing entity has been updated.':'Device created. You can edit its settings here.');
        else this.status('Device saved, but the list could not refresh. Use Refresh; do not create the device again.');
      } catch(error) { this.status(errorText(error)); form.querySelector('fieldset').disabled=false; button.disabled=false; }
      finally {this.saving=false;}
    };
  }
}
if (!customElements.get('zigbee-ir-ready-panel')) customElements.define('zigbee-ir-ready-panel',ZigbeeIRPanel);
