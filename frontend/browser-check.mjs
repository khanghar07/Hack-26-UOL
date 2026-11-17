import {chromium} from '@playwright/test';
import {readFileSync, mkdirSync} from 'node:fs';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
let capture;
try{
 const page=await browser.newPage({viewport:{width:1280,height:800}});
 if(process.env.DEMO_FRAMES){mkdirSync(process.env.DEMO_FRAMES,{recursive:true});let n=0,working=false;capture=setInterval(async()=>{if(working)return;working=true;try{await page.screenshot({path:process.env.DEMO_FRAMES+'/'+String(n++).padStart(5,'0')+'.png'})}catch{}finally{working=false}},400)}
 await page.goto('http://127.0.0.1:8014');
 async function login(email,password){await page.getByLabel('Email',{exact:true}).fill(email);await page.getByLabel('Password',{exact:true}).fill(password);await page.getByRole('button',{name:'Sign in',exact:true}).click();}
 const pause=()=>process.env.DEMO_FRAMES?page.waitForTimeout(1400):Promise.resolve();
 const env=readFileSync('../.env','utf8');const val=k=>env.match(new RegExp('^'+k+'=(.*)$','m'))[1];
 await pause();await login(val('ADMIN_EMAIL'),val('ADMIN_PASSWORD'));
 await page.getByRole('heading',{name:'Projects',exact:true}).waitFor();
 await pause();await page.getByText('Team Directory',{exact:true}).click();await page.getByText('Maryam Asif',{exact:true}).waitFor();
 await pause();await page.getByRole('link',{name:'Projects',exact:true}).click();
 await page.getByText('Create from Transcript',{exact:true}).click();
 await page.getByLabel('Meeting transcript').fill(readFileSync('../sample_transcript.txt','utf8'));
 await pause();await page.getByRole('button',{name:'Create from Transcript'}).click();
 await page.getByRole('link',{name:'View projects'}).waitFor({timeout:200000});
 await pause();await page.getByRole('link',{name:'View projects'}).click();
 await pause();await page.getByText('UrbanCart Website',{exact:true}).click();await page.getByText('Tasks (4)',{exact:true}).waitFor();
 await pause();await page.reload();await page.getByText('Tasks (4)',{exact:true}).waitFor();
 await pause();await page.getByRole('button',{name:'Log out'}).click();
 await login('ayesha@novaworks.example','Demo123!');await page.getByRole('heading',{name:'My Projects'}).waitFor();
 if(await page.locator('.card').count()!==1)throw Error('Manager project count');
 await pause();await page.getByRole('button',{name:'Log out'}).click();await page.setViewportSize({width:390,height:844});
 await login('hamza@novaworks.example','Demo123!');await page.getByText('Booking and account APIs',{exact:true}).waitFor();
 if(await page.locator('.tasks article').count()!==2)throw Error('Developer task count');
 await pause();await page.getByRole('link',{name:'QuickServe Mobile App'}).click();await page.getByText('Tasks (1)',{exact:true}).waitFor();
 if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('Mobile overflow');
 await pause();console.log('PASS browser: sign-in, directory, transcript endpoint, refresh, logout, manager and mobile agent views.');
}finally{clearInterval(capture);await browser.close();}
