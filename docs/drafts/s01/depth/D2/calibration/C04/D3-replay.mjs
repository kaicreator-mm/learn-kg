import {readFileSync} from 'node:fs';
function evaluate(rule,x){
 if(!x||typeof x!=="object")return "HOLD";
 if(x.exit===true)return "STOP";
 if(x.exit!==false||x.permission!==true||x.versionMatch!==true)return "HOLD";
 if(rule==="D3-P08"){
   if(!Number.isFinite(x.budget)||x.budget<0||!Number.isFinite(x.cost)||x.cost<0||x.cost>x.budget||x.accessible!==true||x.prerequisitesMet!==true||x.materialScopeMatch!==true)return "HOLD";
   const match={RETENTION:["RETRIEVAL","SPACED_RETRIEVAL"],STRATEGY_DISCRIMINATION:["INTERLEAVED_PRACTICE","CASE_COMPARISON"],CONCEPT_EXPLANATION:["SELF_EXPLANATION","CASE_COMPARISON"],PROCEDURAL_PRACTICE:["GUIDED_PRACTICE","INDEPENDENT_PRACTICE"]};
   return Object.hasOwn(match,x.target)&&match[x.target].includes(x.mode)?"MODE_CANDIDATE":"HOLD";
 }
 if(rule==="D3-P09"){
   if(x.interrupted===true||x.response==="MISSING")return "MISSING_OBSERVATION";
   if(x.interrupted!==false||x.rubricVerified!==true||x.actor!=="LEARNER"||x.assistance!=="NONE")return "HOLD";
   if(x.response==="CORRECT")return "NO_ERROR_OBSERVED";
   if(x.response!=="INCORRECT")return "HOLD";
   return x.independentContrastVerified===true&&x.patternRepeated===true?"TESTABLE_ERROR_HYPOTHESIS":"REQUEST_DISCRIMINATING_TASK";
 }
 if(rule==="D3-P10"){
   if(x.choice!=="ACCEPT"||x.targetMatch!==true)return "HOLD";
   if(x.rubricDisputed===true)return "REVIEW_RUBRIC_BEFORE_FEEDBACK";
   if(x.rubricDisputed!==false)return "HOLD";
   if(x.observation==="MISSING_OBSERVATION")return "OFFER_RESUME_OR_ALTERNATIVE";
   if(x.observation==="TESTABLE_ERROR_HYPOTHESIS"&&x.support==="PROCESS_HINT")return "OFFER_PROCESS_HINT";
   if(x.observation==="REQUEST_DISCRIMINATING_TASK"&&x.support==="CLARIFY")return "OFFER_CLARIFYING_TASK";
   if(x.observation==="NO_ERROR_OBSERVED"&&x.support==="RESULT")return "OFFER_TASK_RESULT_FEEDBACK";
   return "HOLD";
 }
 if(rule==="D3-P11"){
   if(x.choice!=="ACCEPT"||x.budgetAvailable!==true||x.nonCoercive!==true||x.goalOwnedByLearner!==true)return "HOLD";
   if(x.kind==="ENCOURAGEMENT")return "OFFER_ENCOURAGEMENT";
   if(x.kind==="PROGRESS_REFLECTION"&&x.progressEvidenceVerified===true)return "OFFER_PROGRESS_REFLECTION";
   if(x.kind==="SMALL_GOAL"&&x.goalFeasible===true)return "OFFER_SMALL_GOAL";
   return "HOLD";
 }
 return "HOLD";
}
const cases=JSON.parse(readFileSync(new URL('./D3-fixtures.json',import.meta.url),'utf8'));
let failed=0;for(const f of cases){const actual=evaluate(f.rule,f.input);if(actual!==f.expected){failed++;console.error(f.id,actual,f.expected)}}
console.log(JSON.stringify({cases:cases.length,failed}));if(failed)process.exitCode=1;
