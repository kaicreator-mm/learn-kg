import {readFileSync} from 'node:fs';
import {route,runLoop} from './unified-rules.mjs';
function summarizeLoop(x,expected){const actual={remaining:x.remaining,stopped:x.stopped,statuses:x.trace.map(t=>t.status),candidates:x.candidates.map(t=>t.eventId)};if("firstIngress"in expected)actual.firstIngress=x.trace[0]?.ingress;if("firstFeedback"in expected)actual.firstFeedback=x.trace[0]?.feedback;if("lastRetest"in expected)actual.lastRetest=x.candidates.at(-1)?.retest;return actual}
const {cases,loops}=JSON.parse(readFileSync(new URL('./unified-fixtures.json',import.meta.url),'utf8'));
let failed=0;for(const f of cases){if(route(f.rule,f.ctx,f.input)!==f.expected){failed++;console.error(f.id)}}for(const f of loops){if(JSON.stringify(summarizeLoop(runLoop(f.ctx,f.plan,f.events),f.expected))!==JSON.stringify(f.expected)){failed++;console.error(f.id)}}console.log(JSON.stringify({cases:cases.length,loops:loops.length,failed}));if(failed)process.exitCode=1;
