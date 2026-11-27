import {readFileSync} from 'node:fs';
function calc(x){
 const finite=Number.isFinite, prob=v=>finite(v)&&v>=0&&v<=1;
 if(!x||typeof x!=="object")return "INVALID";
 if(x.mode==="habit"){
  const {a,b,c,day,fit}=x;if(![a,b,c,day].every(finite)||a<=0||b<=0||b>a||c<=0||day<0||typeof fit!=="boolean")return "INVALID";
  if(!fit)return "HOLD_FIT";
  return {value:a-b*Math.exp(-c*day),t95:Math.max(0,Math.log(20*b/a)/c),mastery:"NOT_INFERRED"};
 }
 if(x.mode==="retention"){
  if(!Array.isArray(x.rows)||!x.rows.length||!x.rows.every(r=>r&&typeof r.id==="string"&&r.id&&Number.isInteger(r.delayMinutes)&&r.delayMinutes>=0&&prob(r.score)&&typeof r.measure==="string"&&r.measure)||!Number.isInteger(x.delayMinutes)||x.delayMinutes<0||typeof x.measure!=="string"||!Array.isArray(x.expectedGroups)||new Set(x.expectedGroups).size!==x.expectedGroups.length||x.expectedGroups.length<2)return "INVALID";
  const r=x.rows.filter(r=>r.delayMinutes===x.delayMinutes&&r.measure===x.measure&&x.expectedGroups.includes(r.id));
  if(r.length!==x.expectedGroups.length||new Set(r.map(v=>v.id)).size!==r.length)return "HOLD_COMPARABILITY";
  const max=Math.max(...r.map(v=>v.score));return {highest:r.filter(v=>v.score===max).map(v=>v.id).sort(),scope:"DESCRIPTIVE_ONLY"};
 }
 if(x.mode==="contrast"){if(![x.effectA,x.effectB].every(finite)||typeof x.commonEstimand!=="boolean"||typeof x.validDirectDesign!=="boolean")return "INVALID";return x.commonEstimand&&x.validDirectDesign?{difference:x.effectA-x.effectB,inference:"UNCERTAINTY_REQUIRED"}:"HOLD_COMPARISON";}
 if(x.mode==="evidence"){
  if(!["audio","text","multimodal","oral_interaction"].includes(x.target)||!["audio","text","multimodal","oral_interaction"].includes(x.actual)||typeof x.answerProvided!=="boolean"||!["independent","replay","prompted","unknown"].includes(x.support)||typeof x.correct!=="boolean")return "INVALID";
  if(x.target!==x.actual||x.answerProvided)return "NOT_TARGET_EVIDENCE";
  if(x.support==="unknown")return "HOLD_SUPPORT";
  return {observed:x.correct?"CORRECT":"INCORRECT",condition:x.support,mastery:"NOT_INFERRED"};
 }
 if(x.mode==="mediation"){
  if(!Array.isArray(x.required)||!Array.isArray(x.conveyed)||![...x.required,...x.conveyed].every(v=>typeof v==="string"&&v.length>0)||new Set(x.required).size!==x.required.length||!x.required.length||typeof x.conflict!=="boolean")return "INVALID";
  if(x.conflict)return "HOLD_DISTORTION";
  const missing=x.required.filter(v=>!x.conveyed.includes(v));return {missing,fieldCoverage:missing.length===0?"COMPLETE":"INCOMPLETE",languageQuality:"NOT_INFERRED"};
 }
 return "INVALID";
}
function eq(a,b){if(typeof b==="number")return typeof a==="number"&&Math.abs(a-b)<1e-10;if(b&&typeof b==="object")return !!a&&typeof a==="object"&&Object.keys(a).length===Object.keys(b).length&&Object.entries(b).every(([k,v])=>eq(a[k],v));return a===b;}
const f=JSON.parse(readFileSync(new URL('./fixtures.json',import.meta.url),'utf8'));const r=f.cases.map(x=>({id:x.id,actual:calc(x.input),pass:eq(calc(x.input),x.expected)}));console.log(JSON.stringify({total:r.length,passed:r.filter(x=>x.pass).length,results:r}));if(r.some(x=>!x.pass))process.exitCode=1;
