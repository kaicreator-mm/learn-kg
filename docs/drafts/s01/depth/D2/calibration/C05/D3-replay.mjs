import {readFileSync} from 'node:fs';
function evaluate(rule,x){
 if(!x||typeof x!=="object")return "HOLD";
 if(x.exit===true)return "STOP";
 if(x.exit!==false||x.permission!==true||x.versionMatch!==true)return "HOLD";
 if(rule==="D3-P12"){
 if(!Number.isFinite(x.remaining)||x.remaining<0||!Number.isFinite(x.cost)||x.cost<=0||x.cost>x.remaining||x.prerequisitesMet!==true||x.accessible!==true||x.goalMatch!==true)return "HOLD";
 return "NEXT_TASK_CANDIDATE";
 }
 if(rule==="D3-P13"){
 if(x.targetMatch!==true||x.rubricVerified!==true||x.changeControlled!==true||typeof x.family!=="string"||!x.family||typeof x.item!=="string"||!x.item||typeof x.previousItem!=="string"||!x.previousItem)return "HOLD";
 if(x.item===x.previousItem)return "REPEAT_ONLY";
 if(x.difficultyEquivalenceVerified!==true)return "VARIANT_CANDIDATE_UNCALIBRATED";
 return "CALIBRATED_VARIANT_CANDIDATE";
 }
 if(rule==="D3-P14"){
 if(typeof x.sourceDomain!=="string"||!x.sourceDomain||typeof x.targetDomain!=="string"||!x.targetDomain)return "HOLD";
 if(x.sourceDomain===x.targetDomain)return x.constructMatch===true?"SAME_CONSTRUCT_CANDIDATE":"HOLD";
 return x.sharedMechanism===true?"REUSE_MECHANISM_ONLY":"HOLD";
 }
 return "HOLD";
}
function runSession(s,events){
 let remaining=s.budget, stopped=false, seen=new Map(), candidates=[], trace=[];
 if(!Number.isFinite(remaining)||remaining<0||!Array.isArray(events))return {remaining:null,stopped:true,candidates:[],trace:["INVALID_SESSION"]};
 for(const e of events){
  if(stopped){trace.push("STOPPED");continue;}
  if(e.exit===true){stopped=true;trace.push("STOP");continue;}
  if(e.permission!==true||e.version!==s.version||e.domain!==s.domain||e.construct!==s.construct||typeof e.id!=="string"||!e.id||typeof e.digest!=="string"||!e.digest){trace.push("HOLD");continue;}
  const previous=seen.get(e.id);
  if(previous!==undefined){trace.push(previous===e.digest?"DUPLICATE_NO_UPDATE":"CONFLICT_HOLD");continue;}
  const p=evaluate("D3-P12",{exit:false,permission:true,versionMatch:true,remaining,cost:e.cost,goalMatch:true,accessible:e.accessible,prerequisitesMet:e.prerequisitesMet});
  if(p!=="NEXT_TASK_CANDIDATE"){trace.push("HOLD");continue;}
  seen.set(e.id,e.digest);remaining-=e.cost;
  if(e.interrupted===true||e.result==="MISSING"){trace.push("MISSING_OBSERVATION");continue;}
  if(e.interrupted!==false||e.actor!=="LEARNER"||e.assistance!=="NONE"||!["CORRECT","INCORRECT"].includes(e.result)){trace.push("NOT_INDEPENDENT");continue;}
  if(e.rubricVerified!==true){trace.push("RUBRIC_HOLD");continue;}
  candidates.push({eventId:e.id,result:e.result,construct:s.construct});trace.push("INDEPENDENT_CANDIDATE");
 }
 return {remaining,stopped,candidates,trace};
}
const {cases,sessions}=JSON.parse(readFileSync(new URL('./D3-fixtures.json',import.meta.url),'utf8'));
let failed=0;for(const f of cases){if(evaluate(f.rule,f.input)!==f.expected){failed++;console.error(f.id)}}
for(const f of sessions){if(JSON.stringify(runSession(f.session,f.events))!==JSON.stringify(f.expected)){failed++;console.error(f.id)}}
console.log(JSON.stringify({cases:cases.length,sessions:sessions.length,failed}));if(failed)process.exitCode=1;
