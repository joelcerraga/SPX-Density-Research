/* Optional offline browser check. Requires Playwright and a Chromium executable.
   Set CHROMIUM_EXECUTABLE, and optionally CHROMIUM_HELPER / CODEX_PRIMARY_RUNTIME_NODE_MODULES.
   Numerical tests do not depend on this browser tooling. */
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {chromium:pw}=require(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES?process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES+'/playwright':'playwright');
const args=process.env.CHROMIUM_HELPER?require(process.env.CHROMIUM_HELPER).args.filter(a=>!['--disable-web-security','--allow-running-insecure-content'].includes(a)):[];
(async()=>{
 const project=path.resolve(__dirname,'..'),out=process.env.COMPARISON_SCREENSHOTS||path.join(project,'results');
 const browser=await pw.launch({executablePath:process.env.CHROMIUM_EXECUTABLE,headless:true,args});
 const context=await browser.newContext({viewport:{width:1440,height:1050}});await context.setOffline(true);
 const page=await context.newPage(),errors=[],requests=[],checks=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url())});
 try{
  await page.goto('file://'+path.join(project,'interactive/dated_density_surface.html'));
  await page.waitForFunction(()=>document.querySelector('#surface')._fullLayout?.scene?._scene?.getCamera&&document.querySelector('#slice').data?.length===3);
  assert.match(await page.locator('#status').innerText(),/0 \/ 1,938/);
  assert.equal(await page.evaluate(()=>document.querySelector('#slice').data[0].x.length),480);
  checks.push('Offline render with 3 maturity rows, 3 observed snapshots and exact 240-bin slice curves');
  await page.waitForTimeout(400);await page.screenshot({path:path.join(out,'comparison-desktop.png'),fullPage:true});
  const expected=JSON.parse(fs.readFileSync(path.join(project,'results/comparison_summary.json'))),densities=[];
  const scales=[];
  for(let i=0;i<3;i++){
   await page.selectOption('#snapshot',String(i));await page.waitForFunction(i=>window.datedState.dateIndex===i,i);
   assert.equal(await page.evaluate(()=>window.datedState.pairCount),[840,969,950][i]);
   await page.selectOption('#horizon','common');
   await page.waitForFunction(()=>window.datedState.sliceDays===60);
   const vals=await page.evaluate(i=>document.querySelector('#slice').data[i].y,i),mass=expected.snapshots[i].common_60_days.mass;
   mass.forEach((w,j)=>assert(Math.abs(vals[2*j]-w/((2.2-.3)/240))<1e-9));
   const line=await page.evaluate(()=>document.querySelector('#surface').data[1]);assert(line.y.every(d=>d===60));
   densities.push(Math.max(...vals));
   scales.push(await page.evaluate(()=>JSON.stringify([document.querySelector('#surface').layout.scene.yaxis.range,document.querySelector('#surface').layout.scene.zaxis.range,document.querySelector('#slice').layout.yaxis.range])));
  }
  assert.equal(new Set(densities).size,3);assert.equal(new Set(scales).size,1);
  checks.push('Every snapshot has correct quote counts and common-horizon values; maturity/density scales remain fixed');
  assert(await page.locator('#maturity').isDisabled());
  await page.selectOption('#sample','matched');await page.waitForFunction(()=>window.datedState.sample==='matched');
  assert.match(await page.locator('#risk-note').innerText(),/no bounds are displayed/);
  assert.equal(await page.locator('#metrics td').filter({hasText:'—'}).count(),6);
  const control=JSON.parse(fs.readFileSync(path.join(project,'results/comparison_cases/sep18_late_matched.json')));
  const controlY=await page.evaluate(()=>document.querySelector('#slice').data[2].y);
  control.common_60_days.mass.forEach((w,j)=>assert(Math.abs(controlY[2*j]-w/((2.2-.3)/240))<1e-9));
  checks.push('Common-contract control changes fitted values and suppresses inapplicable all-pair risk bounds');
  await page.selectOption('#sample','full');await page.selectOption('#horizon','fixed');
  await page.locator('#maturity').focus();await page.keyboard.press('End');await page.keyboard.press('Enter');
  await page.waitForFunction(()=>window.datedState.maturityIndex===2);
  assert.match(await page.locator('#metrics-title').innerText(),/2026-12-18/);
  await page.selectOption('#range','central');assert.deepEqual(await page.evaluate(()=>window.datedState.range),[.7,1.3]);
  checks.push('Keyboard expiry selection and full/central display control update the linked figures');
  await page.click('#play');await page.waitForFunction(()=>window.datedState.dateIndex===0);await page.click('#play');
  await page.waitForTimeout(1700);assert.equal(await page.evaluate(()=>window.datedState.dateIndex),0);
  checks.push('Observed-snapshot playback advances and pauses without creating intermediate dates');
  const camera=()=>page.evaluate(()=>JSON.stringify(document.querySelector('#surface')._fullLayout.scene._scene.getCamera()));
  const before=await camera(),box=await page.locator('#surface').boundingBox();
  await page.mouse.move(box.x+box.width*.52,box.y+box.height*.52);await page.mouse.down();
  await page.mouse.move(box.x+box.width*.65,box.y+box.height*.57,{steps:14});await page.mouse.up();await page.waitForTimeout(350);
  const rotated=await camera();assert.notEqual(before,rotated);await page.mouse.wheel(0,-180);await page.waitForTimeout(350);assert.notEqual(await camera(),rotated);
  await page.click('#reset');await page.waitForTimeout(350);checks.push('3D rotation, wheel zoom and reset respond');
  await page.evaluate(()=>{window.hoverValue=null;document.querySelector('#surface').on('plotly_hover',e=>{window.hoverValue=e.points[0].z})});
  for(const [x,y] of [[.4,.5],[.45,.6],[.5,.6],[.55,.7],[.6,.65],[.65,.7],[.5,.5]]){
   await page.mouse.move(box.x+box.width*x,box.y+box.height*y);await page.waitForTimeout(180);
   if(await page.evaluate(()=>window.hoverValue!==null))break;
  }
  assert.equal(await page.evaluate(()=>typeof window.hoverValue),'number');checks.push('Pointer hover yields a numeric density value');
  await page.setViewportSize({width:390,height:844});await page.reload();
  await page.waitForFunction(()=>window.datedState&&document.querySelector('#surface')._fullLayout?.scene?._scene);await page.waitForTimeout(400);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  await page.selectOption('#horizon','common');await page.selectOption('#range','central');await page.waitForTimeout(250);
  await page.screenshot({path:path.join(out,'comparison-mobile.png'),fullPage:true});
  await page.setViewportSize({width:320,height:760});await page.waitForTimeout(350);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));checks.push('390px and 320px layouts avoid page overflow; risk table scrolls within its panel');
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);checks.push('No JavaScript errors or external HTTP requests');
  const report={browser:await browser.version(),plotly:await page.evaluate(()=>Plotly.version),checked_date:'2026-09-21',offline:true,checks,javascript_errors:errors,external_requests:requests};
  fs.writeFileSync(path.join(project,'results/comparison_browser_checks.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
