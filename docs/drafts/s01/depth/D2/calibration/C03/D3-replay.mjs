import {readFileSync} from 'node:fs';
function evaluate(rule,x){
 if(!x||typeof x!=="object")return "HOLD";
 if(rule==="D3-P04"){
 if(x.permission!==true||x.versionMatch!==true||x.observed!==true||x.interrupted!==false||!["CORRECT","INCORRECT"].includes(x.result))return "HOLD";
 if(x.assistance==="NONE"&&x.actor==="LEARNER")return "INDEPENDENT_OBSERVATION";
 if(x.assistance==="HINT"||x.assistance==="ANSWER"||x.actor==="EXTERNAL")return "ASSISTED_OR_EXTERNAL_ONLY";
 return "HOLD";
 }
 if(rule==="D3-P05"){
 if(x.targetMatch!==true||x.independent!==true||x.versionMatch!==true||x.feedbackDuring!==false||x.rubricMatch!==true)return "HOLD";
 if(x.repeatedItem===true)return "REPEAT_ONLY";
 if(x.repeatedItem!==false||x.elapsedVerified!==true)return "HOLD";
 if(x.newContext===true&&x.transferDesignVerified===true)return "TRANSFER_CANDIDATE";
 if(x.newContext===false&&x.delayCriterionMet===true)return "RETENTION_CANDIDATE";
 return "HOLD";
 }
 if(rule==="D3-P06"){
 if(x.exit===true)return "STOP";
 if(x.exit!==false||x.permission!==true||x.choice!=="ACCEPT"||x.budgetAvailable!==true)return "HOLD";
 if(x.support==="HINT"||x.support==="REFLECTION"||x.support==="ENCOURAGEMENT")return "OFFER_SELECTED_SUPPORT";
 return "HOLD";
 }
 if(rule==="D3-P07"){
 if(x.permission!==true||x.versionMatch!==true||x.targetMatch!==true||typeof x.eventId!=="string"||!x.eventId.trim()||typeof x.payloadDigest!=="string"||!x.payloadDigest.trim())return "HOLD";
 if(x.priorDigest===x.payloadDigest)return "DUPLICATE_NO_UPDATE";
 if(x.priorDigest!==null)return "CONFLICT_HOLD";
 if(x.evidenceRoute!=="INDEPENDENT_OBSERVATION")return "HOLD";
 return "UPDATE_CANDIDATE_ONLY";
 }
 return "HOLD";
}
const cases=JSON.parse(readFileSync(new URL('./D3-fixtures.json',import.meta.url),'utf8'));
let failed=0;for(const f of cases){const actual=evaluate(f.rule,f.input);if(actual!==f.expected){failed++;console.error(f.id,actual,f.expected)}}
console.log(JSON.stringify({cases:cases.length,failed}));if(failed)process.exitCode=1;
