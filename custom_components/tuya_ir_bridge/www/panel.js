export const CSS = `
:host {
  display: flex;
  flex-direction: column;
  height: 100%;
  font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
  background: var(--primary-background-color, #fafafa);
  color: var(--primary-text-color, #212121);
  box-sizing: border-box;
}

/* ---- top bar ---- */
.topbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  height: 56px;
  background: var(--app-header-background-color, var(--primary-color, #03a9f4));
  color: var(--app-header-text-color, #fff);
  box-shadow: 0 2px 4px rgba(0,0,0,.2);
  flex-shrink: 0;
}
.topbar h1 { margin: 0; font-size: 1.1rem; font-weight: 500; flex: 1; }
.menu-button {
  color: inherit;
  flex: 0 0 auto;
  margin-left: -8px;
}
.menu-fallback {
  width: 40px;
  height: 40px;
  padding: 8px;
  font-size: 1.4rem;
  line-height: 1;
}
.topbar button {
  background: rgba(255,255,255,.15);
  border: none; border-radius: 4px;
  color: inherit; cursor: pointer;
  padding: 6px 12px; font-size: .85rem;
}
.topbar button:hover { background: rgba(255,255,255,.28); }

/* ---- layout ---- */
.layout {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

/* ---- sidebar ---- */
.sidebar {
  width: 240px;
  min-width: 200px;
  background: var(--sidebar-background-color, var(--card-background-color, #fff));
  border-right: 1px solid var(--divider-color, #e0e0e0);
  overflow-y: auto;
  flex-shrink: 0;
}
.sidebar-section { padding: 0; }
.sidebar-section + .sidebar-section {
  border-top: 2px solid var(--divider-color, #e0e0e0);
  margin-top: 4px;
}
.sidebar-section-title {
  padding: 10px 16px 6px;
  font-size: .7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .1em;
  color: var(--primary-color, #03a9f4);
  background: color-mix(in srgb, var(--primary-color, #03a9f4) 8%, var(--sidebar-background-color, var(--card-background-color, #fff)));
  border-left: 3px solid var(--primary-color, #03a9f4);
}
.sidebar-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 16px 9px 22px;
  cursor: pointer;
  border-radius: 0;
  transition: background .15s;
  font-size: .9rem;
  border-left: 3px solid transparent;
}
.sidebar-item:hover { background: var(--secondary-background-color, #f5f5f5); }
.sidebar-item.active {
  background: var(--primary-color, #03a9f4);
  color: #fff;
  font-weight: 600;
  border-left-color: rgba(255,255,255,.5);
}
.sidebar-item.active:hover { background: var(--primary-color, #03a9f4); }
.sidebar-dup-btn {
  margin-left: auto;
  flex-shrink: 0;
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
  border-radius: 4px;
  opacity: 0;
  transition: opacity .15s;
  color: inherit;
  line-height: 1;
}
.sidebar-item:hover .sidebar-dup-btn { opacity: .6; }
.sidebar-item:hover .sidebar-dup-btn:hover { opacity: 1; background: rgba(0,0,0,.08); }
.sidebar-item.active .sidebar-dup-btn:hover { background: rgba(255,255,255,.2); }
.sidebar-badge {
  font-size: .7rem;
  background: var(--accent-color, #ff9800);
  color: #fff;
  border-radius: 10px;
  padding: 1px 6px;
  margin-left: auto;
}

/* ---- main content ---- */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* ---- entry toolbar ---- */
.entry-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-bottom: 1px solid var(--divider-color, #e0e0e0);
  background: var(--card-background-color, #fff);
  flex-shrink: 0;
}
.entry-toolbar h2 { margin: 0; font-size: 1rem; flex: 1; }
.btn {
  border: none; border-radius: 4px; cursor: pointer;
  padding: 6px 14px; font-size: .84rem; transition: opacity .15s;
}
.btn:hover { opacity: .85; }
.btn-primary { background: var(--primary-color, #03a9f4); color: #fff; }
.btn-secondary {
  background: var(--secondary-background-color, #f0f0f0);
  color: var(--primary-text-color, #212121);
  border: 1px solid var(--divider-color, #ddd);
}
.btn-danger { background: var(--error-color, #db4437); color: #fff; }

/* ---- tabs ---- */
.tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid var(--divider-color, #e0e0e0);
  background: var(--card-background-color, #fff);
  padding: 0 16px;
  overflow-x: auto;
  flex-shrink: 0;
  scrollbar-width: none;
}
.tabs::-webkit-scrollbar { display: none; }
.tab {
  padding: 10px 16px;
  cursor: pointer;
  font-size: .88rem;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  white-space: nowrap;
  transition: color .15s;
  color: var(--secondary-text-color, #727272);
}
.tab:hover { color: var(--primary-text-color, #212121); }
.tab.active {
  color: var(--primary-color, #03a9f4);
  border-bottom-color: var(--primary-color, #03a9f4);
  font-weight: 500;
}

/* ---- fields area ---- */
.fields-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}
.required-legend {
  font-size: .78rem;
  color: var(--secondary-text-color, #888);
  margin-bottom: 12px;
}
.required-star { color: var(--error-color, #db4437); font-weight: bold; margin-left: 2px; }
.field-input.field-error,
.custom-select.field-error .custom-select-trigger,
.multi-select-wrap.field-error {
  border-color: var(--error-color, #db4437) !important;
  background: color-mix(in srgb, var(--error-color, #db4437) 8%, var(--input-fill-color, #fafafa));
}
.field-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.field-label {
  width: 200px;
  min-width: 160px;
  font-size: .88rem;
  color: var(--secondary-text-color, #555);
  flex-shrink: 0;
}
.field-input {
  flex: 1;
  padding: 7px 10px;
  border: 1px solid var(--input-ink-color, #ccc);
  border-radius: 4px;
  background: var(--input-fill-color, #fafafa);
  color: var(--primary-text-color, #212121);
  font-size: .9rem;
  font-family: inherit;
  min-width: 0;
}
.field-input:focus {
  outline: none;
  border-color: var(--primary-color, #03a9f4);
}
.field-input.ir-field {
  font-family: monospace;
  font-size: .88rem;
  text-transform: uppercase;
}
/* ---- custom themed dropdown (replaces native select) ---- */
.custom-select {
  position: relative;
  flex: 1;
  min-width: 0;
}
.custom-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 10px;
  border: 1px solid var(--input-ink-color, #555);
  border-radius: 4px;
  background: var(--input-fill-color, var(--secondary-background-color, #2d2d2d));
  color: var(--primary-text-color, #e0e0e0);
  font-size: .9rem;
  cursor: pointer;
  user-select: none;
}
.custom-select-trigger:hover {
  border-color: var(--primary-color, #03a9f4);
}
.custom-select-arrow { font-size: .75rem; margin-left: 8px; flex-shrink: 0; }
.custom-select-dropdown {
  position: absolute;
  top: calc(100% + 2px);
  left: 0; right: 0;
  z-index: 200;
  background: var(--card-background-color, #2d2d2d);
  border: 1px solid var(--divider-color, #444);
  border-radius: 4px;
  box-shadow: 0 4px 16px rgba(0,0,0,.4);
  overflow: hidden;
}
.custom-select-option {
  padding: 9px 12px;
  cursor: pointer;
  font-size: .9rem;
  color: var(--primary-text-color, #e0e0e0);
}
.custom-select-option:hover {
  background: var(--secondary-background-color, #3a3a3a);
}
.custom-select-option.selected {
  background: var(--primary-color, #03a9f4);
  color: #fff;
}
.field-number {
  width: 100px;
  flex: none;
}
.field-unit {
  font-size: .8rem;
  color: var(--secondary-text-color, #888);
  width: 24px;
}
.btn-icon {
  border: none; border-radius: 4px; cursor: pointer;
  padding: 6px 8px; font-size: .78rem;
  white-space: nowrap;
  flex-shrink: 0;
}
.btn-learn {
  background: var(--warning-color, #ff9800);
  color: #fff;
}
.btn-test {
  background: var(--success-color, #4caf50);
  color: #fff;
}
.btn-icon:disabled { opacity: .5; cursor: default; }

/* ---- custom commands section ---- */
.custom-commands-wrap { display: flex; flex-direction: column; gap: 8px; padding: 4px 0 8px; }
.custom-cmds-list { display: flex; flex-direction: column; gap: 6px; }
.custom-cmd-row { display: flex; align-items: center; gap: 6px; }
.custom-cmd-name { width: 100px; flex-shrink: 0; }
.custom-cmd-data { flex: 1; min-width: 80px; }
.btn-del-cmd { background: var(--error-color, #f44336); color: #fff; }
.custom-cmds-empty { margin: 0 0 4px; font-size: .85rem; color: var(--secondary-text-color, #666); }
.btn-add-custom-cmd { align-self: flex-start; }

/* ---- multi-select pills ---- */
.multi-select-wrap {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  align-content: flex-start;
  gap: 6px;
  padding: 8px;
  border: 1px solid var(--input-ink-color, #555);
  border-radius: 4px;
  background: var(--input-fill-color, var(--secondary-background-color, #2a2a2a));
}
.multi-select-item {
  padding: 4px 12px;
  border-radius: 16px;
  cursor: pointer;
  font-size: .82rem;
  border: 1px solid var(--divider-color, #555);
  color: var(--secondary-text-color, #aaa);
  user-select: none;
  transition: background .12s, color .12s;
}
.multi-select-item:hover { border-color: var(--primary-color, #03a9f4); color: var(--primary-text-color, #eee); }
.multi-select-item.selected {
  background: var(--primary-color, #03a9f4);
  color: #fff;
  border-color: var(--primary-color, #03a9f4);
}

/* ---- toggle switch ---- */
.toggle-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}
.toggle-switch {
  position: relative;
  width: 42px;
  height: 24px;
  flex-shrink: 0;
}
.toggle-switch input { opacity: 0; width: 0; height: 0; position: absolute; }
.toggle-slider {
  position: absolute; inset: 0;
  background: var(--divider-color, #555);
  border-radius: 24px;
  cursor: pointer;
  transition: background .2s;
}
.toggle-slider:before {
  content: "";
  position: absolute;
  width: 18px; height: 18px;
  bottom: 3px; left: 3px;
  background: #fff;
  border-radius: 50%;
  transition: transform .2s;
}
.toggle-switch input:checked + .toggle-slider { background: var(--primary-color, #03a9f4); }
.toggle-switch input:checked + .toggle-slider:before { transform: translateX(18px); }
.toggle-state { font-size: .85rem; color: var(--secondary-text-color, #aaa); min-width: 28px; }

/* ---- section headers & dividers inside field list ---- */
.section-header {
  font-size: .74rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: .07em;
  color: var(--secondary-text-color, #888);
  padding: 14px 0 6px;
  border-bottom: 1px solid var(--divider-color, #e0e0e0);
  margin-bottom: 4px;
}
.field-divider {
  border: none;
  border-top: 2px solid var(--divider-color, #e0e0e0);
  margin: 20px 0 8px;
}

/* ---- entity picker ---- */
.entity-picker {
  position: relative;
  flex: 1;
  min-width: 0;
}
.entity-picker .custom-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 10px;
  border: 1px solid var(--input-ink-color, #555);
  border-radius: 4px;
  background: var(--input-fill-color, var(--secondary-background-color, #2d2d2d));
  color: var(--primary-text-color, #e0e0e0);
  font-size: .9rem;
  cursor: pointer;
  user-select: none;
}
.entity-picker .custom-select-trigger:hover { border-color: var(--primary-color, #03a9f4); }
.entity-dropdown {
  position: absolute;
  top: calc(100% + 2px);
  left: 0; right: 0;
  z-index: 300;
  background: var(--card-background-color, #2d2d2d);
  border: 1px solid var(--divider-color, #444);
  border-radius: 4px;
  box-shadow: 0 4px 20px rgba(0,0,0,.45);
  flex-direction: column;
  max-height: 260px;
}
.entity-dropdown:not([hidden]) { display: flex; }
.entity-search-wrap {
  padding: 6px 8px;
  border-bottom: 1px solid var(--divider-color, #444);
  flex-shrink: 0;
}
.entity-search {
  width: 100%;
  box-sizing: border-box;
  padding: 5px 8px;
  border: 1px solid var(--input-ink-color, #555);
  border-radius: 4px;
  background: var(--input-fill-color, #1a1a1a);
  color: var(--primary-text-color, #e0e0e0);
  font-size: .85rem;
  font-family: inherit;
}
.entity-search:focus { outline: none; border-color: var(--primary-color, #03a9f4); }
.entity-list { overflow-y: auto; flex: 1; }
.entity-option {
  padding: 7px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.entity-option:hover { background: var(--secondary-background-color, #3a3a3a); }
.entity-option.selected {
  background: var(--primary-color, #03a9f4);
  color: #fff;
}
.entity-opt-name { font-size: .88rem; }
.entity-opt-id {
  font-size: .74rem;
  color: var(--secondary-text-color, #aaa);
  font-family: monospace;
}
.entity-option.selected .entity-opt-id { color: rgba(255,255,255,.75); }
.entity-option.none-opt { font-style: italic; color: var(--secondary-text-color, #888); }

/* ---- placeholder / empty ---- */
.placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--secondary-text-color, #888);
  gap: 12px;
  font-size: 1rem;
}
.placeholder svg { width: 64px; height: 64px; opacity: .3; }

/* ---- status bar ---- */
.statusbar {
  height: 32px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  font-size: .82rem;
  flex-shrink: 0;
  border-top: 1px solid var(--divider-color, #e0e0e0);
  background: var(--card-background-color, #fff);
}
.status-ok { color: var(--success-color, #4caf50); }
.status-err { color: var(--error-color, #db4437); }
.status-info { color: var(--secondary-text-color, #555); }

/* ---- modal overlay ---- */
.modal-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.45);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal {
  background: var(--card-background-color, #fff);
  border-radius: 8px;
  padding: 24px;
  width: min(520px, 92vw);
  box-shadow: 0 8px 32px rgba(0,0,0,.25);
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 80vh;
}
.modal h3 { margin: 0; font-size: 1rem; }
.modal textarea {
  flex: 1;
  min-height: 200px;
  resize: vertical;
  padding: 8px;
  font-family: monospace;
  font-size: .85rem;
  border: 1px solid var(--divider-color, #ccc);
  border-radius: 4px;
  background: var(--input-fill-color, #fafafa);
  color: var(--primary-text-color, #212121);
}
.modal-actions { display: flex; gap: 8px; justify-content: flex-end; }

/* ---- IR database source tabs ---- */
.db-src-tabs { display: flex; gap: 6px; margin: 10px 0 12px; }
.db-src-tab {
  flex: 1; padding: 7px 10px;
  border: 1px solid var(--divider-color, #ddd); border-radius: 6px;
  cursor: pointer; background: var(--secondary-background-color, #f5f5f5);
  font-size: .85rem; color: var(--primary-text-color, #212121); transition: all .15s;
}
.db-src-tab.active {
  background: var(--primary-color, #03a9f4); color: #fff;
  border-color: var(--primary-color, #03a9f4);
}

/* ---- Flipper IRDB browser ---- */
.flipper-breadcrumb {
  font-size: .78rem; color: var(--secondary-text-color, #666);
  margin-bottom: 6px; min-height: 1.2em; line-height: 1.6;
}
.flipper-bc-link {
  cursor: pointer; color: var(--primary-color, #03a9f4);
  text-decoration: underline;
}
.flipper-list {
  border: 1px solid var(--divider-color, #ddd); border-radius: 6px;
  max-height: 260px; overflow-y: auto;
}
.flipper-item {
  padding: 8px 12px; cursor: pointer; font-size: .88rem;
  display: flex; align-items: center; gap: 8px;
  border-bottom: 1px solid var(--divider-color, #eee); transition: background .1s;
}
.flipper-item:last-child { border-bottom: none; }
.flipper-item:hover { background: var(--secondary-background-color, #f5f5f5); }
.flipper-item.selected {
  background: color-mix(in srgb, var(--primary-color, #03a9f4) 12%, transparent);
}
.flipper-loading {
  padding: 20px; text-align: center;
  color: var(--secondary-text-color, #666); font-size: .88rem;
}
.flipper-status {
  margin-top: 6px; font-size: .82rem;
  color: var(--secondary-text-color, #666); min-height: 1.4em;
}

/* ---- learning overlay ---- */
.learn-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,.55);
  display: flex; align-items: center; justify-content: center;
  z-index: 2000;
}
.learn-card {
  background: var(--card-background-color, #fff);
  border-radius: 12px;
  padding: 32px;
  width: min(380px, 90vw);
  text-align: center;
  box-shadow: 0 8px 40px rgba(0,0,0,.3);
}
.learn-card h3 { margin: 0 0 8px; font-size: 1.1rem; }
.learn-card p { margin: 0 0 20px; color: var(--secondary-text-color, #666); font-size: .9rem; }
.learn-spinner {
  width: 48px; height: 48px;
  border: 4px solid var(--divider-color, #eee);
  border-top-color: var(--primary-color, #03a9f4);
  border-radius: 50%;
  animation: spin .8s linear infinite;
  margin: 0 auto 20px;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ---- Media Player source-mode tabs ---- */
.src-mode-tabs {
  display: flex;
  margin: 4px 0 10px;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid var(--divider-color, #e0e0e0);
  width: fit-content;
}
.src-mode-tab {
  padding: 7px 18px;
  border: none;
  background: var(--card-background-color, #fff);
  color: var(--secondary-text-color, #666);
  cursor: pointer;
  font-family: inherit;
  font-size: 0.85em;
  transition: background 0.15s;
}
.src-mode-tab:not(:last-child) {
  border-right: 1px solid var(--divider-color, #e0e0e0);
}
.src-mode-tab.active {
  background: var(--primary-color, #03a9f4);
  color: #fff;
  font-weight: 600;
}
.src-mode-tab:hover:not(.active) {
  background: var(--secondary-background-color, #f5f5f5);
}
.src-cycle-hint {
  font-size: 0.78em;
  color: var(--secondary-text-color, #888);
  padding: 0 0 8px;
  width: 100%;
  font-style: italic;
}
`;

