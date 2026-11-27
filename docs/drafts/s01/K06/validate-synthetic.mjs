// S01 investigation only; Node >=22; node validate-synthetic.mjs
import {readFileSync} from 'node:fs';
function classify(a){
 if(!a||typeof a!=="object")return "INVALID";
 if(a.mode==="observation"){if(!["correct","incorrect","unknown"].includes(a.result)||!["learner","other","unknown"].includes(a.actor)||!["none","access_only","content_hint","answer","unknown"].includes(a.help))return "INVALID";if(a.result==="unknown"||a.actor==="unknown"||a.help==="unknown")return "UNKNOWN";if(a.actor==="other")return "NOT_LEARNER_EVIDENCE";if(["content_hint","answer"].includes(a.help))return "ASSISTED_OBSERVATION";return a.result==="correct"?"INDEPENDENT_CORRECT_OBSERVATION":"INDEPENDENT_ERROR_OBSERVATION";}
 if(a.mode==="route"){if(!["independent_correct","assisted_correct","error","unknown"].includes(a.observation)||!Number.isInteger(a.budget)||a.budget<0||typeof a.authorized!=="boolean"||!["distinguished","unresolved"].includes(a.cause))return "INVALID";if(!a.authorized)return "HOLD_AUTH";if(a.budget===0)return "STOP_BUDGET";if(a.observation==="unknown")return "REQUEST_EVIDENCE";if(a.observation==="assisted_correct")return "PROPOSE_LESS_HELP_PROBE";if(a.observation==="independent_correct")return "RECORD_OBSERVATION_NOT_MASTERY";return a.cause==="distinguished"?"PROPOSE_TARGETED_RETEACH":"PROPOSE_DISCRIMINATING_PROBE";}
 if(a.mode==="fidelity"){if(!Number.isInteger(a.planned)||!Number.isInteger(a.delivered)||a.planned<=0||a.delivered<0||a.delivered>a.planned||!["preserved","changed","unknown"].includes(a.core))return "INVALID";return {dose:a.delivered+"/"+a.planned,core:a.core,outcome:"NOT_INFERRED"};}
 return "INVALID";
}
const evidence=JSON.parse(readFileSync(new URL('./logic-evidence.json',import.meta.url),'utf8'));
let passed=0;
for (const row of evidence.records) { const actual=classify(row.input); if(JSON.stringify(actual)!==JSON.stringify(row.expected)) throw Error(row.id+': mismatch'); passed++; }
console.log(JSON.stringify({passed,total:evidence.records.length}));
