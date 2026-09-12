import {useEffect,useState} from 'react';
import {MessageCircle,RefreshCw,Send} from 'lucide-react';
import {request} from './api';

type Status={cloud_api_ready:boolean;verify_token_ready:boolean;access_token_ready:boolean;phone_number_id_ready:boolean;signature_validation_ready:boolean;api_version:string};
type EventRow={id:string;external_id:string;event_type:string;from_number?:string|null;to_number?:string|null;status?:string|null;message_type?:string|null;body?:string|null;created_at:string};

export default function WhatsAppPanel(){
  const[status,setStatus]=useState<Status|null>(null);
  const[events,setEvents]=useState<EventRow[]>([]);
  const[to,setTo]=useState('');
  const[mode,setMode]=useState<'template'|'text'>('template');
  const[text,setText]=useState('Prueba de WhatsApp desde LAYA Market');
  const[busy,setBusy]=useState(false);
  const[msg,setMsg]=useState('');
  const[err,setErr]=useState('');

  async function load(){
    try{
      setErr('');
      const[s,e]=await Promise.all([request('/whatsapp/status'),request('/whatsapp/events?limit=50')]);
      setStatus(s);setEvents(e);
    }catch(e:any){setErr(e.message||'No se pudo cargar WhatsApp')}
  }
  useEffect(()=>{load()},[]);

  async function send(){
    if(!to.trim())return setErr('Ingresa el número destinatario autorizado en Meta.');
    try{
      setBusy(true);setErr('');setMsg('');
      const body=mode==='text'?{to,mode,text}:{to,mode,template_name:'hello_world',language_code:'en_US'};
      const r=await request('/whatsapp/send-test',{method:'POST',body:JSON.stringify(body)});
      setMsg(r.sent?'Mensaje enviado a Meta correctamente.':'Meta no confirmó el envío.');
      setTimeout(load,1200);
    }catch(e:any){setErr(e.message||'No se pudo enviar el mensaje')}finally{setBusy(false)}
  }

  const flag=(label:string,ok:boolean|undefined)=><div className="card metric-card"><div className="muted">{label}</div><div className="metric" style={{fontSize:22}}>{ok?'✓ Listo':'✕ Falta'}</div></div>;

  return <div>
    <div className="toolbar"><div><div className="eyebrow">META CLOUD API</div><h2 style={{margin:'4px 0'}}>WhatsApp</h2><p className="muted">Verificación, envío de prueba y eventos recibidos por el webhook.</p></div><button className="btn ghost" onClick={load}><RefreshCw size={16}/> Actualizar</button></div>
    {err&&<div className="error-card">{err}</div>}{msg&&<div className="card" style={{marginBottom:16}}>{msg}</div>}
    <div className="grid">
      {flag('Cloud API',status?.cloud_api_ready)}
      {flag('Verify token',status?.verify_token_ready)}
      {flag('Access token',status?.access_token_ready)}
      {flag('Phone Number ID',status?.phone_number_id_ready)}
      {flag('Firma App Secret',status?.signature_validation_ready)}
    </div>
    <div className="card" style={{marginTop:18}}>
      <div style={{display:'flex',alignItems:'center',gap:10}}><MessageCircle size={20}/><b>Prueba de salida</b></div>
      <p className="muted">Usa un destinatario que hayas autorizado como número de prueba en Meta.</p>
      <div className="form">
        <label className="field">Destinatario con código de país<input value={to} onChange={e=>setTo(e.target.value)} placeholder="549261..."/></label>
        <label className="field">Modo<select value={mode} onChange={e=>setMode(e.target.value as 'template'|'text')}><option value="template">Plantilla hello_world</option><option value="text">Texto libre</option></select></label>
        {mode==='text'&&<label className="field">Mensaje<input value={text} onChange={e=>setText(e.target.value)}/></label>}
      </div>
      <button className="btn gold" disabled={busy} onClick={send}><Send size={16}/> {busy?'Enviando...':'Enviar prueba'}</button>
    </div>
    <div className="table-wrap" style={{marginTop:18}}><table><thead><tr><th>Evento</th><th>Estado/tipo</th><th>Origen</th><th>Destino</th><th>Contenido</th><th>Fecha</th></tr></thead><tbody>{events.length===0?<tr><td colSpan={6} className="muted">Todavía no hay eventos almacenados.</td></tr>:events.map(x=><tr key={x.id}><td><b>{x.event_type}</b><div className="muted small">{x.external_id.slice(0,22)}</div></td><td><span className="badge">{x.status||x.message_type||'—'}</span></td><td>{x.from_number||'—'}</td><td>{x.to_number||'—'}</td><td>{x.body||'—'}</td><td>{new Date(x.created_at).toLocaleString()}</td></tr>)}</tbody></table></div>
  </div>
}
