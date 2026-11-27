// S01 draft, Node >=22; run: node validate-synthetic.mjs
import { readFileSync } from 'node:fs';
function check(a){
 if(!a||typeof a!=="object")return "INVALID";
 if(a.mode==="route"){if(!Array.isArray(a.paths)||a.paths.length===0||!Array.isArray(a.recommended)||!a.recommended.every(x=>typeof x==="string")||!a.paths.every(p=>Array.isArray(p)&&p.length>0&&new Set(p.map(e=>e.id)).size===p.length&&p.every(e=>typeof e.id==="string"&&e.id.length>0&&["SAT","UNSAT","UNKNOWN"].includes(e.state)&&["qualified","draft"].includes(e.status))))return "INVALID";
 const p=a.paths.map(p=>p.some(e=>e.status==="qualified"&&e.state==="UNSAT")?"BLOCKED":p.some(e=>e.status!=="qualified"||e.state==="UNKNOWN")?"HOLD":"READY");
 return p.includes("READY")?"CANDIDATE_PATH_AVAILABLE":p.includes("HOLD")?"HOLD_UNKNOWN":"NO_PATH_CONFIRMED";}
 if(a.mode==="alignment"){if(!Array.isArray(a.required)||!Array.isArray(a.assessed)||!Array.isArray(a.taught)||![...a.required,...a.assessed,...a.taught].every(x=>typeof x==="string"&&x.length>0)||!a.required.length||new Set(a.required).size!==a.required.length)return "INVALID";return {teachingGap:a.required.filter(x=>!a.taught.includes(x)),assessmentGap:a.required.filter(x=>!a.assessed.includes(x)),mastery:"NOT_INFERRED"};}
 if(a.mode==="gate"){if(!["valid","invalid","unknown"].includes(a.evidence)||!["pass","fail","unknown"].includes(a.criterion)||!["pass","fail","unknown","not_required"].includes(a.integration)||typeof a.authorized!=="boolean")return "INVALID";if(!a.authorized)return "HOLD_AUTH";if(a.evidence!=="valid"||a.criterion==="unknown"||a.integration==="unknown")return "HOLD_EVIDENCE";if(a.criterion==="fail"||a.integration==="fail")return "REMEDIATE_CANDIDATE";return "ADVANCE_CANDIDATE_NOT_MASTERY";}
 return "INVALID";
}
const evidence=JSON.parse(readFileSync(new URL('./logic-evidence.json',import.meta.url),'utf8'));
let passed=0;
for(const r of evidence.records){if(JSON.stringify(check(r.input))!==JSON.stringify(r.expected))throw Error(r.id);passed++;}
console.log(JSON.stringify({passed,total:evidence.records.length}));
