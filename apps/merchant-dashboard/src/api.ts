const API=import.meta.env.VITE_API_URL||'http://localhost:8000/api/v1';
export function getToken(){return localStorage.getItem('token')||''}
export async function request(path:string,options:RequestInit={}){const token=getToken();const headers:any={'Content-Type':'application/json',...(options.headers||{})};if(token)headers.Authorization=`Bearer ${token}`;const r=await fetch(API+path,{...options,headers});if(!r.ok)throw new Error((await r.json().catch(()=>({detail:'Error'}))).detail||'Error');return r.json()}
