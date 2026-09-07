/* Device manager; CSS reused under MIT from Tasmota IR Ready. */
import {CSS} from './panel.js';
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
class ZigbeeIRPanel extends HTMLElement {
  constructor() { super(); this.attachShadow({mode:'open'}); this.devices=[]; }
  set hass(value) { this._hass=value; if (!this.started) { this.started=true; this.render(); this.refresh(); } }
  async refresh() {
    try { this.devices=await this._hass.callWS({type:'tuya_ir_bridge/list'}); this.render(); }
    catch(error) { this.status(error.message || String(error)); }
  }
  status(message) { this.shadowRoot.querySelector('.statusbar').textContent=message; }
  render() {
    this.shadowRoot.innerHTML=`<style>${CSS}
      .main {padding:24px;overflow:auto} form{max-width:760px} .field-row{flex-wrap:wrap}
      textarea{min-height:100px} .help{color:var(--secondary-text-color);line-height:1.6}
      @media(max-width:600px){.field-label{width:100%}.main{padding:12px}}
      </style>
      <div class="topbar"><button id="menu" aria-label="Open sidebar">☰</button><h1>Zigbee IR Ready</h1><button id="refresh">⟳ Refresh</button></div>
      <div class="layout"><div class="sidebar">${['climate','media_player','remote','light'].map(type=>`
        <div class="sidebar-section-title">${esc(type.replace('_',' '))}</div>${this.devices.filter(d=>d.device_type===type).map(d=>`<div class="sidebar-item">${esc(d.name)}</div>`).join('')}`).join('')}
      </div><div class="main"><h2>Create Device</h2>
      <p class="help">Connect a virtual device to your Zigbee2MQTT IR blaster. This preview supports Electra AC, NEC and Samsung32.</p>
      <form>
      <div class="field-row"><label class="field-label" for="name">Device Name</label><input class="field-input" id="name" name="name" required maxlength="100"></div>
      <div class="field-row"><label class="field-label" for="device_type">Device Type</label><select class="field-input" id="device_type" name="device_type"><option value="climate">Climate</option><option value="media_player">Media Player</option><option value="remote">Remote</option><option value="light">Light</option></select></div>
      <div class="field-row"><label class="field-label" for="topic">MQTT Command Topic</label><input class="field-input" id="topic" name="topic" placeholder="zigbee2mqtt/Living Room IR/set/ir_code_to_send" required></div>
      <div class="field-row"><label class="field-label" for="protocol">Brand / Protocol</label><select class="field-input" id="protocol" name="protocol"><option value="electra">Electra AC (experimental)</option></select></div>
      <div id="commands" hidden><div class="field-row"><label class="field-label" for="address">Protocol Address</label><input class="field-input" type="number" id="address" name="address" min="0" max="255" value="0"></div>
      <div class="field-row"><label class="field-label" for="command_map">Named Command IDs</label><textarea class="field-input" id="command_map" name="command_map" placeholder='{"turn_on": 1, "turn_off": 2}'></textarea></div>
      <p class="help">Enter documented numeric command IDs for your model. Protocol selection alone cannot determine which number means power or volume. No learned Base64 codes are stored.</p></div>
      <p class="help" id="climate_note">Electra: 16–32°C, mode and fan control. Hardware validation is pending. Other AC families require separate encoder ports.</p>
      <button type="submit">Create Device</button></form></div></div><div class="statusbar status-info" role="status" aria-live="polite"></div>`;
    this.shadowRoot.querySelector('#menu').onclick=()=>this.dispatchEvent(new CustomEvent('hass-toggle-menu',{bubbles:true,composed:true}));
    this.shadowRoot.querySelector('#refresh').onclick=()=>this.refresh();
    const form=this.shadowRoot.querySelector('form');
    form.device_type.onchange=()=>{
      const climate=form.device_type.value==='climate';
      form.protocol.innerHTML=climate?'<option value="electra">Electra AC (experimental)</option>':'<option value="nec">NEC</option><option value="samsung">Samsung32</option>';
      this.shadowRoot.querySelector('#commands').hidden=climate;
      this.shadowRoot.querySelector('#climate_note').hidden=!climate;
    };
    form.onsubmit=async event=>{
      event.preventDefault(); const button=form.querySelector('[type=submit]'); button.disabled=true;
      try {
        const data=Object.fromEntries(new FormData(form));
        const device={name:data.name,device_type:data.device_type,topic:data.topic.trim(),protocol:data.protocol};
        if(device.device_type!=='climate'){device.address=Number(data.address);device.commands=JSON.parse(data.command_map);}
        await this._hass.callWS({type:'tuya_ir_bridge/create',device});
        await this.refresh(); this.status('Device created. Its native entity is available in Home Assistant.');
      } catch(error) { this.status(error.message || String(error)); button.disabled=false; }
    };
  }
}
customElements.define('zigbee-ir-ready-panel',ZigbeeIRPanel);
