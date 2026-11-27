const C02=(()=>{
function evaluate(rule,x){
 if(rule==="D3-P01"){if(x.observed_channel!=="HANDWRITING"||!Array.isArray(x.ordered_trace)||!x.ordered_trace.length||x.independent!==true)return "UNKNOWN";return "ELIGIBLE_FOR_SCORING";}
 if(rule==="D3-P02"){if(x.observed_channel==="SIMULATION")return "SIMULATION_ONLY";return x.observed_channel==="REAL"&&x.external_receipt===true?"EXTERNAL_RESULT_PRESENT":"UNKNOWN";}
 if(rule==="D3-P03"){return x.context_known===true&&typeof x.stated_intent==="string"&&x.stated_intent.trim()!==""?"STATED_INTENT_ONLY":"UNKNOWN";}
 throw Error("unknown rule");
}
return {evaluate};
})();
const C03=(()=>{
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
return {evaluate};
})();
const C04=(()=>{
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
return {evaluate};
})();
const C05=(()=>{
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
return {evaluate,runSession};
})();
function route(rule,ctx,x){
 if(!ctx||typeof ctx!=="object"||Array.isArray(ctx))return "HOLD";
 if(ctx.exit===true)return "STOP";
 if(ctx.exit!==false||ctx.permission!==true||ctx.versionMatch!==true||typeof ctx.domain!=="string"||!ctx.domain.trim()||typeof ctx.construct!=="string"||!ctx.construct.trim()||!x||typeof x!=="object"||Array.isArray(x))return "HOLD";
 if(x.exit===true)return "STOP";
 if(("permission" in x&&x.permission!==true)||("versionMatch" in x&&x.versionMatch!==true))return "HOLD";
 const input={...x,exit:false,permission:true,versionMatch:true};
 if(!/^D3-P(0[1-9]|1[0-5])$/.test(rule))return "HOLD";
 const n=Number(rule.slice(-2));
 if(n===4&&input.rubricVerified!==true)return "HOLD";
 if(n===13&&(typeof input.previousFamily!=="string"||input.previousFamily!==input.family))return "HOLD";
 if(n===14&&input.targetDomain!==ctx.domain)return "HOLD";
 if(n===15)return "USE_FINITE_SESSION";
 return (n<=3?C02:n<=7?C03:n<=11?C04:C05).evaluate(rule,input);
}
function runLoop(ctx,plan,events){
 const result={remaining:plan?.budget??null,stopped:false,trace:[],candidates:[]};
 if(route("D3-P12",ctx,{remaining:plan?.budget,cost:1,prerequisitesMet:true,accessible:true,goalMatch:true})!=="NEXT_TASK_CANDIDATE"||!Array.isArray(events)||typeof plan.version!=="string"||!plan.version.trim()){result.stopped=true;result.trace.push("INVALID_OR_STOPPED_SESSION");return result}
 const seen=new Map();
 for(const e of events){
  if(result.stopped){result.trace.push({status:"STOPPED"});continue}
  if(!e||typeof e!=="object"){result.trace.push({status:"HOLD"});continue}
  if(e.exit===true){result.stopped=true;result.trace.push({status:"STOP"});continue}
  if(e.exit!==false||e.permission!==true||e.version!==plan.version||e.domain!==ctx.domain||e.construct!==ctx.construct||typeof e.id!=="string"||!e.id.trim()||typeof e.digest!=="string"||!e.digest.trim()){result.trace.push({status:"HOLD"});continue}
  const prior=seen.get(e.id);if(prior!==undefined){result.trace.push({status:prior===e.digest?"DUPLICATE_NO_UPDATE":"CONFLICT_HOLD"});continue}
  const base={budget:result.remaining,cost:e.cost,accessible:e.accessible,prerequisitesMet:e.prerequisitesMet,materialScopeMatch:e.materialScopeMatch,target:plan.target,mode:e.mode};
  const mode=route("D3-P08",ctx,base),next=route("D3-P12",ctx,{...base,remaining:result.remaining,goalMatch:true});
  if(mode!=="MODE_CANDIDATE"||next!=="NEXT_TASK_CANDIDATE"){result.trace.push({status:"HOLD",mode,next});continue}
  const variant=route("D3-P13",ctx,{targetMatch:e.targetMatch,rubricVerified:e.rubricVerified,changeControlled:e.changeControlled,family:e.family,previousFamily:e.previousFamily,item:e.item,previousItem:e.previousItem,difficultyEquivalenceVerified:e.difficultyEquivalenceVerified});
  if(!["VARIANT_CANDIDATE_UNCALIBRATED","CALIBRATED_VARIANT_CANDIDATE","REPEAT_ONLY"].includes(variant)){result.trace.push({status:"HOLD",variant});continue}
  seen.set(e.id,e.digest);result.remaining-=e.cost;
  const observation=route("D3-P04",ctx,{observed:e.observed,interrupted:e.interrupted,result:e.result,actor:e.actor,assistance:e.assistance,rubricVerified:e.rubricVerified});
  const diagnosis=route("D3-P09",ctx,{interrupted:e.interrupted,response:e.result,actor:e.actor,assistance:e.assistance,rubricVerified:e.rubricVerified,independentContrastVerified:e.independentContrastVerified,patternRepeated:e.patternRepeated});
  const feedback=route("D3-P10",ctx,{choice:e.feedbackChoice,targetMatch:e.targetMatch,rubricDisputed:e.rubricDisputed,observation:diagnosis,support:e.feedbackSupport});
  const incentive=route("D3-P11",ctx,{choice:e.incentiveChoice,budgetAvailable:result.remaining>0,nonCoercive:e.nonCoercive,goalOwnedByLearner:e.goalOwnedByLearner,kind:e.incentiveKind,progressEvidenceVerified:e.progressEvidenceVerified,goalFeasible:e.goalFeasible});
  const retest=route("D3-P05",ctx,{targetMatch:e.targetMatch,independent:observation==="INDEPENDENT_OBSERVATION",feedbackDuring:e.feedbackDuring,rubricMatch:e.rubricVerified,repeatedItem:variant==="REPEAT_ONLY",elapsedVerified:e.elapsedVerified,newContext:e.newContext,transferDesignVerified:e.transferDesignVerified,delayCriterionMet:e.delayCriterionMet});
  const ingress=route("D3-P07",ctx,{targetMatch:e.targetMatch,eventId:e.id,payloadDigest:e.digest,priorDigest:null,evidenceRoute:observation});
  if(ingress==="UPDATE_CANDIDATE_ONLY")result.candidates.push({eventId:e.id,result:e.result,domain:ctx.domain,construct:ctx.construct,retest});
  result.trace.push({status:"OBSERVED",mode,variant,observation,diagnosis,feedback,incentive,retest,ingress});
 }
 return result;
}
export {route,runLoop};
