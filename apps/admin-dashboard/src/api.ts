const API=import.meta.env.VITE_API_URL||'http://localhost:8000/api/v1';
export function getToken(){return localStorage.getItem('token')||''}
export async function request(path:string,options:RequestInit={}){const r=await fetch(API+path,{...options,headers:{'Content-Type':'application/json',Authorization:`Bearer ${getToken()}`,...(options.headers||{})}});if(!r.ok)throw new Error((await r.json().catch(()=>({detail:'Error'}))).detail||'Error');return r.json()}
export async function login(email:string,password:string){const d=await request('/auth/login',{method:'POST',body:JSON.stringify({email,password})});localStorage.setItem('token',d.access_token);localStorage.setItem('role',d.role);return d}
