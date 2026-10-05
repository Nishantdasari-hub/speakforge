import { useCallback, useEffect, useRef, useState } from "react";
import Swal from "sweetalert2";
import { apiRequest } from "../api";

export default function AdminTests() {
  const [tests,setTests]=useState([]);
  const [title,setTitle]=useState("");
  const [description,setDescription]=useState("");
  const [editing,setEditing]=useState(null);
  const [error,setError]=useState("");
  const [busy,setBusy]=useState(false);
  const lock=useRef(false);
  const load=useCallback(async () => setTests(await apiRequest('/tests/')),[]);
  useEffect(() => { load().catch(err => setError(err.message)); },[load]);
  const reset=() => {setEditing(null);setTitle("");setDescription("");};
  const save=async event => {
    event.preventDefault();
    if(lock.current)return;
    lock.current=true;setBusy(true);setError("");
    try {
      await apiRequest(`/tests/${editing ?? ''}`,{method:editing ? 'PUT':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title,description})});
      reset();await load();
    } catch(err){setError(err.message);} finally{lock.current=false;setBusy(false);}
  };
  const remove=async id => {
    if(lock.current)return;
    const choice=await Swal.fire({title:'Delete Test?',icon:'warning',showCancelButton:true});
    if(!choice.isConfirmed)return;
    lock.current=true;setBusy(true);setError("");
    try{await apiRequest(`/tests/${id}`,{method:'DELETE'});if(editing===id)reset();await load();}
    catch(err){setError(err.message);}finally{lock.current=false;setBusy(false);}
  };
  return <section className="text-white space-y-6">
    <h1 className="text-3xl font-bold">Manage Tests</h1>
    {error&&<p role="alert" className="text-red-300">{error}</p>}
    <form onSubmit={save} className="bg-gray-900 rounded p-6 space-y-4 max-w-xl">
      <h2>{editing?'Edit Test':'Create New Test'}</h2>
      <input aria-label="Test title" required maxLength={255} value={title} onChange={e=>setTitle(e.target.value)} className="w-full bg-gray-800 rounded p-3" />
      <textarea aria-label="Test description" maxLength={500} value={description} onChange={e=>setDescription(e.target.value)} className="w-full bg-gray-800 rounded p-3" />
      <button disabled={busy} className="bg-blue-600 px-5 py-3 rounded">{editing?'Save Changes':'Create Test'}</button>
      {editing&&<button type="button" onClick={reset} disabled={busy} className="ml-4">Cancel</button>}
    </form>
    <h2 className="text-xl">Existing Tests</h2>
    {tests.map(test=><article key={test.id} className="bg-gray-900 rounded p-5 flex justify-between gap-4">
      <div><h3>{test.title}</h3><p className="text-gray-400">{test.description}</p></div>
      <div className="flex gap-4"><button disabled={busy} onClick={()=>{setEditing(test.id);setTitle(test.title);setDescription(test.description);}}>Edit</button><button disabled={busy} onClick={()=>remove(test.id)} className="text-red-300">Delete</button></div>
    </article>)}
  </section>;
}
