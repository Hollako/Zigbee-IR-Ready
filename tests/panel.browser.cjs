// Optional real-browser regression test. Set PLAYWRIGHT_MODULE and BROWSER_EXECUTABLE.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:process.env.BROWSER_EXECUTABLE});
  try {
    const page=await browser.newPage({viewport:{width:1200,height:1000}});
    const errors=[]; page.on('pageerror',error=>errors.push(error.message));
    await page.route('http://panel.test/**',async route=>{
      const name=new URL(route.request().url()).pathname.slice(1);
      if(name.endsWith('.js')) return route.fulfill({contentType:'text/javascript',body:fs.readFileSync(path.join(root,'custom_components/tuya_ir_bridge/www',name),'utf8')});
      return route.fulfill({contentType:'text/html',body:`<html><style>body{margin:0;--primary-text-color:#e1e1e1;--secondary-text-color:#aaa;--card-background-color:#1c1c1c;--primary-background-color:#111;--secondary-background-color:#282828;--primary-color:#03a9f4;--input-fill-color:#222;--input-ink-color:#555}</style><zigbee-ir-ready-panel></zigbee-ir-ready-panel><script type="module">
      import '/manager.js';
      window.devices=[{id:'ac',name:'Bedroom AC',device_type:'climate',protocol:'ELECTRA_AC',topic:'zigbee2mqtt/Bedroom/set/ir_code_to_send',transport:'zosung',model:-1,min_temp:16,max_temp:32,temp_step:1,hvac_options:{SwingV:'Auto'}},{id:'tv',name:'Legacy TV',device_type:'remote',protocol:'nec',address:18,topic:'zigbee2mqtt/TV/set/ir_code_to_send',commands:{power:32}}];
      window.requests=[];
      window.hass={themes:{darkMode:true},callWS:async message=>{
        window.requests.push(message);
        if(message.type.endsWith('/list'))return structuredClone(window.devices);
        if(message.type.endsWith('/catalogue'))return {climate:['DAIKIN','ELECTRA_AC','GREE'],send:[{name:'NEC'},{name:'SONY'}]};
        if(message.type.endsWith('/update')){const saved={...message.device,id:message.device_id};window.devices=window.devices.map(d=>d.id===saved.id?saved:d);return saved;}
        throw Error('Unexpected request');
      }};
      document.querySelector('zigbee-ir-ready-panel').hass=window.hass;
      </script></html>`});
    });
    await page.goto('http://panel.test/');
    await page.getByRole('button',{name:'Edit Bedroom AC'}).click();
    assert.equal(await page.locator('#name').inputValue(),'Bedroom AC');
    assert.equal(await page.locator('#protocol').inputValue(),'ELECTRA_AC');
    assert.equal(await page.locator('#device_type').isDisabled(),true);
    const colors=await page.locator('#protocol option').first().evaluate(option=>({color:getComputedStyle(option).color,background:getComputedStyle(option).backgroundColor,scheme:getComputedStyle(option).colorScheme}));
    assert.equal(colors.color,'rgb(225, 225, 225)');
    assert.equal(colors.background,'rgb(28, 28, 28)');
    assert.equal(colors.scheme,'dark');
    await page.locator('#protocol').evaluate(select=>select.size=3);
    fs.mkdirSync(path.join(root,'.build'),{recursive:true});
    await page.screenshot({path:path.join(root,'.build/panel-dark-edit.png'),fullPage:true});
    await page.locator('#protocol').evaluate(select=>select.size=1);
    await page.locator('#name').fill('Bedroom AC Updated');
    await page.locator('#max_temp').fill('30');
    await page.getByRole('button',{name:'Save Changes',exact:true}).click();
    await page.getByRole('status').filter({hasText:'Changes saved'}).waitFor();
    let updates=await page.evaluate(()=>requests.filter(r=>r.type.endsWith('/update')));
    assert.equal(updates.length,1); assert.equal(updates[0].device_id,'ac');
    assert.equal(updates[0].device.max_temp,30);
    assert.equal(await page.evaluate(()=>devices.length),2);
    await page.getByRole('button',{name:'Edit Legacy TV'}).click();
    assert.equal(await page.locator('#address').inputValue(),'18');
    assert.equal(await page.locator('#transport').inputValue(),'base64');
    await page.getByRole('button',{name:'Save Changes',exact:true}).click();
    await page.getByRole('status').filter({hasText:'Changes saved'}).waitFor();
    updates=await page.evaluate(()=>requests.filter(r=>r.type.endsWith('/update')));
    assert.equal(updates[1].device.address,18);
    await page.evaluate(()=>{hass.themes.darkMode=false;document.body.style.setProperty('--primary-text-color','#212121');document.body.style.setProperty('--card-background-color','#fff');document.querySelector('zigbee-ir-ready-panel').hass=hass;});
    assert.equal(await page.locator('#protocol').evaluate(el=>getComputedStyle(el).colorScheme),'light');
    assert.deepEqual(errors,[]);
    console.log('Browser: dark/light colors, edit loading, stable update ID, and legacy address retention passed');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
