import { readFileSync } from 'node:fs';
function evaluate(rule,x){
 if(rule==="D3-P01"){if(x.observed_channel!=="HANDWRITING"||!Array.isArray(x.ordered_trace)||!x.ordered_trace.length||x.independent!==true)return "UNKNOWN";return "ELIGIBLE_FOR_SCORING";}
 if(rule==="D3-P02"){if(x.observed_channel==="SIMULATION")return "SIMULATION_ONLY";return x.observed_channel==="REAL"&&x.external_receipt===true?"EXTERNAL_RESULT_PRESENT":"UNKNOWN";}
 if(rule==="D3-P03"){return x.context_known===true&&typeof x.stated_intent==="string"&&x.stated_intent.trim()!==""?"STATED_INTENT_ONLY":"UNKNOWN";}
 throw Error("unknown rule");
}
const fixtures=JSON.parse(readFileSync(new URL('./D3-fixtures.json',import.meta.url),'utf8'));
let fails=0; for(const f of fixtures){const actual=evaluate(f.rule,f.input);if(actual!==f.expected){fails++;console.error(f.id,actual,f.expected)}}
console.log(JSON.stringify({cases:fixtures.length,failed:fails}));if(fails)process.exitCode=1;
