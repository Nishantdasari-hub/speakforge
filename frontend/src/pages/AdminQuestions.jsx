import { useCallback, useEffect, useRef, useState } from "react";
import Swal from "sweetalert2";
import { apiRequest } from "../api";

export default function AdminQuestions(){
  const [tests,setTests]=useState([]);
  const [selected,setSelected]=useState('');
  const [questions,setQuestions]=useState([]);
  const [text,setText]=useState('');
  const [type,setType]=useState('audio');
  const [limit,setLimit]=useState(30);
  const [order,setOrder]=useState(1);
  const [editing,setEditing]=useState(null);
  const [error,setError]=useState('');
  const [busy,setBusy]=useState(false);
  const lock=useRef(false);
  const reset=()=>{setText('');setEditing(null);setType('audio');setLimit(30);setOrder(1);};
  useEffect(()=>{apiRequest('/tests/').then(setTests).catch(err=>setError(err.message));},[]);
  const load=useCallback(async()=>{
    if(selected)setQuestions(await apiRequest(`/tests/${selected}/questions`));
  },[selected]);
  useEffect(()=>{
    const controller=new AbortController();setQuestions([]);reset();
    if(selected)apiRequest(`/tests/${selected}/questions`,{signal:controller.signal}).then(setQuestions).catch(err=>{if(err.name!=='AbortError')setError(err.message);});
    return()=>controller.abort();
  },[selected]);
  const save=async event=>{
    event.preventDefault();if(lock.current)return;
    lock.current=true;setBusy(true);setError('');
    try{
      await apiRequest(`/tests/${selected}/questions${editing?`/${editing}`:''}`,{method:editing?'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question_text:text,question_type:type,time_limit:Number(limit),order_number:Number(order)})});
      reset();await load();
    }catch(err){setError(err.message);}finally{lock.current=false;setBusy(false);}
  };
  const remove=async id=>{
    if(lock.current)return;
    const choice=await Swal.fire({title:'Delete Question?',icon:'warning',showCancelButton:true});
    if(!choice.isConfirmed)return;
    lock.current=true;setBusy(true);setError('');
    try{await apiRequest(`/tests/${selected}/questions/${id}`,{method:'DELETE'});if(editing===id)reset();await load();}
    catch(err){setError(err.message);}finally{lock.current=false;setBusy(false);}
  };
  return <section className="text-white space-y-6">
    <h1 className="text-3xl font-bold">Manage Questions</h1>
    {error&&<p role="alert" className="text-red-300">{error}</p>}
    <label className="block">Select Test<select aria-label="Select Test" value={selected} disabled={busy} onChange={e=>{setSelected(e.target.value);setError('');}} className="block bg-gray-800 p-3 rounded w-full mt-2"><option value="">Choose Test</option>{tests.map(t=><option key={t.id} value={t.id}>{t.title}</option>)}</select></label>
    {selected&&<form onSubmit={save} className="bg-gray-900 p-6 rounded space-y-4">
      <h2>{editing?'Edit Question':'Create Question'}</h2>
      <textarea aria-label="Question text" required maxLength={2000} value={text} onChange={e=>setText(e.target.value)} className="bg-gray-800 p-3 w-full rounded" />
      <div className="flex flex-wrap gap-4">
        <label>Type<select aria-label="Question type" value={type} onChange={e=>setType(e.target.value)} className="bg-gray-800 p-3 block"><option value="audio">Audio</option><option value="text">Text</option></select></label>
        <label>Seconds<input aria-label="Time limit" type="number" min={5} max={300} required value={limit} onChange={e=>setLimit(e.target.value)} className="bg-gray-800 p-3 block" /></label>
        <label>Order<input aria-label="Question order" type="number" min={1} max={1000} required value={order} onChange={e=>setOrder(e.target.value)} className="bg-gray-800 p-3 block" /></label>
      </div>
      <button disabled={busy} className="bg-blue-600 px-5 py-3 rounded">{editing?'Save Question':'Create Question'}</button>
      {editing&&<button type="button" disabled={busy} onClick={reset} className="ml-4">Cancel</button>}
    </form>}
    {questions.map(q=><article key={q.id} className="bg-gray-900 rounded p-5 flex justify-between gap-4"><div><h3>{q.question_text}</h3><p>{q.question_type} · {q.time_limit}s · Order {q.order_number}</p></div><div className="flex gap-4"><button disabled={busy} onClick={()=>{setEditing(q.id);setText(q.question_text);setType(q.question_type);setLimit(q.time_limit);setOrder(q.order_number);}}>Edit</button><button disabled={busy} onClick={()=>remove(q.id)} className="text-red-300">Delete</button></div></article>)}
    {selected&&!questions.length&&<p>No questions yet.</p>}
  </section>;
}
