import './remote_card.js';
class ZigbeeRemotePanel extends HTMLElement {
  constructor(){super();this.attachShadow({mode:'open'});this.selected=null;}
  set hass(hass){this._hass=hass;this.toggleAttribute('dark',hass.themes?.darkMode===true);const remotes=Object.entries(hass.states||{}).filter(([id,state])=>id.startsWith('remote.')&&state.attributes.zigbee_ir_device_id);const signature=JSON.stringify(remotes.map(([id,state])=>[id,state.attributes.friendly_name]));if(this.signature!==signature){this.signature=signature;this.render(remotes);}const card=this.shadowRoot.querySelector('zigbee-ir-ready-remote-card');if(card)card.hass=hass;}
  render(remotes){
    this.shadowRoot.innerHTML='<style>:host{color-scheme:light;display:block;box-sizing:border-box;min-height:100vh;font-family:var(--paper-font-body1_-_font-family,Arial);padding:20px;background:var(--primary-background-color);color:var(--primary-text-color)}:host([dark]){color-scheme:dark}header{display:flex;gap:16px;align-items:center}select{background:var(--card-background-color);color:var(--primary-text-color);padding:12px}main{max-width:480px;margin:20px auto}</style><header><button aria-label="Open sidebar">☰</button><h2>IR Remotes</h2><select aria-label="Remote device"></select></header><main></main>';
    this.shadowRoot.querySelector('button').onclick=()=>this.dispatchEvent(new CustomEvent('hass-toggle-menu',{bubbles:true,composed:true}));
    const select=this.shadowRoot.querySelector('select');for(const [id,state] of remotes){const option=document.createElement('option');option.value=id;option.textContent=state.attributes.friendly_name||id;select.append(option);}
    if(remotes.some(([id])=>id===this.selected))select.value=this.selected;
    const show=()=>{this.selected=select.value;const main=this.shadowRoot.querySelector('main');main.replaceChildren();if(!this.selected){main.textContent='Create a Remote or Media Player in Zigbee IR Ready to see its controls here.';return;}const card=document.createElement('zigbee-ir-ready-remote-card');card.setConfig({entity:this.selected});card.hass=this._hass;main.append(card);};select.onchange=show;show();
  }
}
if(!customElements.get('zigbee-ir-remotes-panel'))customElements.define('zigbee-ir-remotes-panel',ZigbeeRemotePanel);
