import {readFileSync} from 'node:fs';
function calc(x){
 const finite=Number.isFinite, probability=v=>finite(v)&&v>=0&&v<=1, count=v=>Number.isSafeInteger(v)&&v>=0;
 if(!x||typeof x!=="object")return "INVALID";
 if(x.mode==="cat"){
  if(!Array.isArray(x.items)||!x.items.every(i=>i&&typeof i.id==="string"&&i.id&&finite(i.info)&&i.info>=0&&["yes","no","unknown"].includes(i.eligible))||new Set(x.items.map(i=>i.id)).size!==x.items.length)return "INVALID";
  const candidates=x.items.filter(i=>i.eligible==="yes").sort((a,b)=>b.info-a.info||(a.id<b.id?-1:a.id>b.id?1:0));
  return candidates.length?{id:candidates[0].id,optimality:"ELIGIBLE_ONLY"}:"HOLD_NO_ELIGIBLE";
 }
 if(x.mode==="stop"){
  if(!finite(x.se)||x.se<0||!finite(x.target)||x.target<=0||!count(x.used)||!count(x.max)||x.max===0||x.used>x.max||!count(x.available)||typeof x.contentComplete!=="boolean")return "INVALID";
  const precision=x.se<=x.target, criteria=precision&&x.contentComplete;
  return {reason:criteria?"TARGET_CRITERIA":x.used===x.max?"ITEM_LIMIT":x.available===0?"EXHAUSTED":"CONTINUE",precision,contentComplete:x.contentComplete};
 }
 if(x.mode==="kappa"){
  const t=x.table;if(!Array.isArray(t)||t.length<2||!t.every(r=>Array.isArray(r)&&r.length===t.length&&r.every(count)))return "INVALID";
  const N=t.flat().reduce((a,b)=>a+b,0);if(!Number.isSafeInteger(N)||N===0)return "INVALID";
  const po=t.reduce((s,r,i)=>s+r[i],0)/N;
  const pe=t.reduce((s,r,i)=>s+(r.reduce((a,b)=>a+b,0)/N)*(t.reduce((a,b)=>a+b[i],0)/N),0);
  return {po,pe,kappa:pe===1?"UNDEFINED":(po-pe)/(1-pe)};
 }
 if(x.mode==="screen"){
  if(typeof x.reference!=="boolean"||![x.tp,x.fn,x.fp,x.tn].every(count))return "INVALID";
  if(!x.reference)return "REFERENCE_REQUIRED";
  const ratio=(a,b)=>a+b===0?"UNDEFINED":a/(a+b);
  return {sensitivity:ratio(x.tp,x.fn),specificity:ratio(x.tn,x.fp),ppv:ratio(x.tp,x.fp),npv:ratio(x.tn,x.fn)};
 }
 if(x.mode==="ppv"){
  if(![x.se,x.sp,x.base].every(probability))return "INVALID";
  const a=x.se*x.base,b=(1-x.sp)*(1-x.base);
  return a+b===0?"UNDEFINED":a/(a+b);
 }
 if(x.mode==="collocation"){
  const {N,fx,fy,fxy}=x;
  if(![N,fx,fy,fxy].every(count)||N===0||fx>N||fy>N||fxy>Math.min(fx,fy)||fxy<fx+fy-N)return "INVALID";
  const pmi=fx===0||fy===0?"UNDEFINED":fxy===0?"NEGATIVE_INFINITY":Math.log2((fxy/N)/((fx/N)*(fy/N)));
  return {pmi,dice:fx+fy===0?"UNDEFINED":2*fxy/(fx+fy)};
 }
 return "INVALID";
}
function eq(a,b){if(typeof b==="number")return typeof a==="number"&&Math.abs(a-b)<1e-10;if(b&&typeof b==="object")return !!a&&typeof a==="object"&&Object.keys(a).length===Object.keys(b).length&&Object.entries(b).every(([k,v])=>eq(a[k],v));return a===b;}
const f=JSON.parse(readFileSync(new URL('./fixtures.json',import.meta.url),'utf8'));const r=f.cases.map(x=>({id:x.id,actual:calc(x.input),pass:eq(calc(x.input),x.expected)}));console.log(JSON.stringify({total:r.length,passed:r.filter(x=>x.pass).length,results:r}));if(r.some(x=>!x.pass))process.exitCode=1;
