import {readFileSync} from 'node:fs';
function calc(x){
 const n=v=>Number.isSafeInteger(v)&&v>=0, finite=Number.isFinite;
 if(!x||typeof x!=="object")return "INVALID";
 if(x.mode==="standardize"){
  if(!Array.isArray(x.strata)||!x.strata.length||!x.strata.every(s=>s&&typeof s.id==="string"&&s.id.length>0&&n(s.n1)&&n(s.y1)&&n(s.n0)&&n(s.y0)&&s.y1<=s.n1&&s.y0<=s.n0&&finite(s.w)&&s.w>=0)||new Set(x.strata.map(s=>s.id)).size!==x.strata.length||Math.abs(x.strata.reduce((a,s)=>a+s.w,0)-1)>1e-10)return "INVALID";
  if(x.strata.some(s=>s.w>0&&(s.n1===0||s.n0===0)))return "HOLD_SUPPORT";
  const sum=k=>x.strata.reduce((a,s)=>a+s[k],0);
  if(!sum("n1")||!sum("n0"))return "HOLD_SUPPORT";
  return {crude:sum("y1")/sum("n1")-sum("y0")/sum("n0"),standardized:x.strata.reduce((a,s)=>a+(s.w===0?0:s.w*(s.y1/s.n1-s.y0/s.n0)),0)};
 }
 if(x.mode==="iv"){
  if(!Array.isArray(x.studies)||!x.studies.length||!x.studies.every(s=>s&&typeof s.id==="string"&&s.id.length>0&&finite(s.effect)&&finite(s.se)&&s.se>0)||new Set(x.studies.map(s=>s.id)).size!==x.studies.length)return "INVALID";
  if(x.sameScale!==true||x.independent!==true||x.commonEffect!==true)return "HOLD_ASSUMPTION";
  const w=x.studies.map(s=>1/s.se**2),total=w.reduce((a,b)=>a+b,0);
  const effect=x.studies.reduce((a,s,i)=>a+s.effect*w[i],0)/total,se=1/Math.sqrt(total);
  return finite(effect)&&finite(se)&&se>0?{effect,se}:"INVALID";
 }
 if(x.mode==="identify"){
  if(!["yes","no","unknown"].includes(x.exchangeability)||!["yes","no","unknown"].includes(x.positivity)||!["yes","no","unknown"].includes(x.consistency))return "INVALID";
  return [x.exchangeability,x.positivity,x.consistency].every(v=>v==="yes")?"ASSUMPTIONS_ASSERTED_NOT_ESTABLISHED":"HOLD_IDENTIFICATION";
 }
 return "INVALID";
}
function eq(a,b){if(typeof b==="number")return typeof a==="number"&&Math.abs(a-b)<1e-10;if(b&&typeof b==="object")return !!a&&typeof a==="object"&&Object.keys(a).length===Object.keys(b).length&&Object.entries(b).every(([k,v])=>eq(a[k],v));return a===b;}
const e=JSON.parse(readFileSync(new URL('./logic-evidence.json',import.meta.url),'utf8'));for(const r of e.records){if(!eq(calc(r.input),r.expected))throw Error(r.id);}console.log(JSON.stringify({passed:e.records.length,total:e.records.length}));
