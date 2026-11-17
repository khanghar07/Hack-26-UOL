import React,{useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {onAuthStateChanged,signInWithEmailAndPassword,signOut} from 'firebase/auth';
import {auth} from './auth';
import './style.css';
import {readApiResponse} from './response.mjs';
async function api(path, body){
 const token=await auth.currentUser.getIdToken();
 const r=await fetch((import.meta.env.VITE_API_URL||'')+'/api/'+path,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+token,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined});
 return readApiResponse(r);
}
function Brand(){return <b className="brand"><i>N</i> NovaWorks CRM</b>}
function Login(){const [show,S]=useState(false),[error,E]=useState(''),[busy,B]=useState(false);
 return <main className="login"><form onSubmit={async e=>{e.preventDefault();const f=new FormData(e.target);B(true);E('');try{await signInWithEmailAndPassword(auth,f.get('email').trim(),f.get('password'))}catch{E('Sign-in failed. Check your email, password and connection.')}finally{B(false)}}}><Brand/><h1>Sign in</h1><label>Email<input type="email" name="email" autoComplete="username" required/></label><label>Password<input type={show?'text':'password'} name="password" autoComplete="current-password" required/></label><button type="button" onClick={()=>S(!show)}>{show?'Hide':'Show'} password</button><p role="alert">{error}</p><button className="primary" disabled={busy}>{busy?'Signing in…':'Sign in'}</button></form></main>}
const date=x=>new Date(x+'T12:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'});
function Tasks({tasks}){return <div className="tasks">{tasks.map(t=><article key={t.id}><h3>{t.title}</h3><p>{t.description}</p><small>{t.assigneeName||t.assigneeId} · {date(t.deadline)} · {t.estimatedHours} h</small></article>)}</div>}
function Import(){const [value,V]=useState(''),[day,D]=useState('2026-10-07'),[busy,B]=useState(false),[error,E]=useState(''),[result,R]=useState(null);
return <><h1>Create from Transcript</h1><form onSubmit={async e=>{e.preventDefault();B(true);E('');R(null);try{R(await api('transcript',{meetingDate:day,transcript:value}))}catch(e){E(e.message)}finally{B(false)}}}><label>Meeting date<input type="date" disabled={busy} required value={day} onChange={e=>{D(e.target.value);R(null)}}/></label><label>Meeting transcript<textarea rows="16" disabled={busy} required value={value} onChange={e=>{V(e.target.value);R(null)}}/></label><button className="primary" disabled={busy||!value.trim()}>{busy?'Creating projects…':'Create from Transcript'}</button><p role="alert">{error}</p>{result&&<p role="status">{result.replayed?'Already saved':'Saved'} · {result.projectCount} projects · {result.taskCount} tasks. <a href="#projects">View projects</a></p>}</form></>}
function View({page,me}){const [data,A]=useState(null),[error,E]=useState(''),[retry,T]=useState(0);
const detail=page.startsWith('project/'),agent=me.role==='AGENT';
const path=detail?'projects/'+encodeURIComponent(page.slice(8)):page==='team'?'team':page==='tasks'&&agent?'tasks/mine':page==='projects'&&!agent?'projects':null;
useEffect(()=>{let active=true;if(path){A(null);E('');api(path).then(x=>active&&A(x)).catch(e=>active&&E(e.message))}return()=>{active=false}},[path,retry]);
if(page==='import'&&me.role==='ADMIN')return <Import/>;
if(!path)return <h1>Page unavailable</h1>;
if(error)return <><p role="alert">{error}</p><button onClick={()=>T(retry+1)}>Retry</button></>;
if(!data)return <p role="status">Loading…</p>;
if(detail)return <><a href={agent?'#tasks':'#projects'}>← {agent?'My Tasks':'Projects'}</a><h1>{data.name}</h1><p>{data.description}</p><small>{data.clientName} · {data.managerName} · Due {date(data.deadline)}</small><h2>Tasks ({data.taskCount})</h2><Tasks tasks={data.tasks}/></>;
if(page==='team')return <><h1>Team Directory</h1>{['ADMIN','MANAGER','AGENT'].map(role=><section key={role}><h2>{{ADMIN:'Administrator',MANAGER:'Managers',AGENT:'Developers'}[role]}</h2><div className="grid">{data.members.filter(m=>m.role===role).map(m=><article key={m.id}><h3>{m.name}</h3><p>{m.specialization}</p><small>{m.skills.join(' · ')}</small></article>)}</div></section>)}</>;
if(page==='tasks')return <><h1>My Tasks</h1>{!data.tasks.length&&<article>No tasks assigned yet.</article>}{[...new Set(data.tasks.map(t=>t.projectId))].map(id=><section key={id}><h2><a href={'#project/'+id}>{data.tasks.find(t=>t.projectId===id).projectName}</a></h2><Tasks tasks={data.tasks.filter(t=>t.projectId===id).map(t=>({...t,assigneeName:me.name}))}/></section>)}</>;
return <><header><h1>{me.role==='ADMIN'?'Projects':'My Projects'}</h1>{me.role==='ADMIN'&&<a className="primary" href="#import">Create from Transcript</a>}</header>{!data.projects.length&&<article>No projects yet.</article>}<div className="grid">{data.projects.map(p=><a className="card" key={p.id} href={'#project/'+p.id}><small>{p.clientName}</small><h2>{p.name}</h2><p>{p.description}</p><footer>{p.managerName} · {date(p.deadline)} · {p.taskCount} tasks</footer></a>)}</div></>}
function App(){const [user,U]=useState(undefined),[me,M]=useState(null),[error,E]=useState(''),[hash,H]=useState(location.hash),[attempt,T]=useState(0);
useEffect(()=>onAuthStateChanged(auth,u=>{U(u);M(null);E('')}),[]);useEffect(()=>{let active=true;if(user)api('me').then(m=>active&&M(m)).catch(e=>active&&E(e.message));return()=>{active=false}},[user,attempt]);useEffect(()=>{const f=()=>H(location.hash);addEventListener('hashchange',f);return()=>removeEventListener('hashchange',f)},[]);
if(user===null)return <Login/>;if(!me)return <main><p>{error||'Opening workspace…'}</p>{error&&<><button onClick={()=>{E('');T(attempt+1)}}>Retry</button><button onClick={()=>signOut(auth)}>Log out</button></>}</main>;
const agent=me.role==='AGENT',home=agent?'tasks':'projects',page=hash.slice(1)||home;
return <div className="shell"><aside><Brand/><nav><a href={'#'+home}>{agent?'My Tasks':me.role==='MANAGER'?'My Projects':'Projects'}</a><a href="#team">Team Directory</a></nav><div className="identity">{me.name}<small>{me.role}</small><button onClick={async()=>{await signOut(auth);location.hash=''}}>Log out</button></div></aside><main><View key={page} page={page} me={me}/></main></div>}
createRoot(document.getElementById('root')).render(<App/>);
