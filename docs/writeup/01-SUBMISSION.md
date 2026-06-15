# Microfactory Node: 3D Printer

*A small local model that learns a craft, job by job, so the craft can't be lost.*

My grandfather had a shop. He trained as an electrical engineer, taught EE labs for twelve
years, then spent a career as a communications engineer for the City of Beaumont. At home he
was a tinkerer. The shop was a home RadioShack with a machine shop bolted onto it, and I spent
a good part of my childhood in there. He gave me tasks. He would set me to work, then look over
what I'd done and tell me where it would fail and why. He was the one who built the thing and
the one who inspected it. Both voices, in the same patient person.

I grew up on shows full of people like that. Engineers who could talk to the machine, who could
fix almost anything with the right tool and a clear head. I wanted that. The knowledge, the
hands, the calm. My grandfather was the closest version I ever got to stand next to, and I
learned a lot at that bench.

Then Alzheimer's took him. The shop was sold, the tools scattered, and a lifetime of skill that
lived in his hands went with him. Decades of know-how, gone in an afternoon.

He's gone. The spirit isn't.

There are a lot of people like him out there: makers, machinists, mechanics, hobbyists who hold
real craft and no good way to pass it on. I want to connect them and their skill. This project
is the first node of that. It uses AI to empower a solo maker, and it does the opposite of
replacing the human: it puts human knowledge on the bench, in front, where you can watch it
work. The larger plan is the Microfactory, a network of small machines and the people who run
them with a real economy growing around the work. This submission is one node of it, built end
to end so the idea reads as a working thing and not a sketch. The rest is on the roadmap, not in
this demo.

## What the node does

The node is a small local model, Gemma, running on my own machine through Ollama. It learns 3D
printing the way a shop hand learns it: one job at a time, conditions and all. Before a print
runs it looks at the part, the material, and the room, recalls the closest jobs it has already
seen, and weighs what they teach about this one. Then it proposes settings and points at where
this print will fail, before the nozzle moves. Most tools watch a print fail while it happens.
This one gets ahead of the nozzle.

Two named agents do the work, and they map straight onto my grandfather. **Chief Engineer
O'Brien** proposes. He is the hands-on one: he reads the room, recalls precedent, commits to a
plan, terse and physical. **La Forge** inspects. He is the skeptic who reads O'Brien's plan
before anything prints and says where the optimism is thin. When La Forge disputes a plan, the
print is held until I clear it. O'Brien is the optimist. La Forge is not. My grandfather was
both at once. The model is never allowed to grade its own work.

The knowledge compounds. Every real outcome becomes one durable lesson, keyed to material,
geometry, and the room, appended to a ledger the node reads from forever after. Job N+1 starts
smarter than job N. That is the whole point: craft that accumulates instead of evaporating.

## How it works

One loop, end to end. A job comes in: geometry, material, and the room's temperature and
humidity. The node retrieves precedent, prior jobs with the same material and geometry, ranked
by how close their conditions were to today's. No vector database, no embeddings: a mechanism
plain enough to inspect and trust. O'Brien evaluates what transfers, out loud, on screen. "This
same overhang sagged at lower humidity than today's, so conditions are worse: raising cooling,
dropping temp." When nothing close exists he says "no close precedent" and reasons from material
properties instead. Knowing what he doesn't know is a feature.

Then the guardrails. A deterministic check, the Spine, clamps anything outside hard material
bounds before it could ever reach a printer. La Forge gives the plan a second opinion. I print,
and I report the outcome: the human stays at the helm. The node reflects, distills the result
into one lesson, and files it. On top of the loop sits a small learned policy: per material,
geometry, and condition bucket, it accumulates setting offsets from what actually happened, so
what it learned on one humid PETG job carries to the next humid PETG job and not only an
identical one. Retrieval recalls. The policy generalizes. Both feed every recommendation.

This is retrieval plus reflection plus a small learned policy, not fine-tuning, and that is
deliberate. Fine-tuning would bury the knowledge in the weights where you can't watch it move.
Retrieval keeps the memory visible: a lesson gets written after one job and pulled back up to
shape the next, in plain sight. For a system meant to preserve and show accumulated craft,
visible memory beats invisible memory.

## Why small, local, and constrained is the honest fit

A model this size earns trust through constraints, not through scale. The surface is narrow,
three or four setting levers. The Spine does safety in plain Python. La Forge grades the plan,
a separate deterministic world grades the print, and the model grades neither. Take the
guardrails away and a model this small will confidently hand you a ruined spool. Leave them in
and it behaves like a careful shop hand. Constraints are what make a small model trustworthy in
front of a machine.

It runs offline, on my own hardware, for $0 a month. That is not a deployment footnote: it is
the point. The knowledge a maker builds over a lifetime should not rent space in someone's
cloud, and it should not vanish when the shop closes. The public Space runs the live model on
ZeroGPU so you can see the real reasoning. If the GPU is cold or out of quota the node falls
back to the deterministic advisor and the banner says so plainly. The reasoning panel never
fakes output.

## What's real, and what's honest about its limits

Everything above runs in the demo: condition-keyed retrieval, visible precedent evaluation, the
Spine veto, O'Brien and La Forge, human-reported outcomes, the growing ledger, the learning
loop, local Gemma. One boundary is simulated. Print outcomes come from a deterministic,
physics-lite stand-in for the printer so the closed loop can run on camera. It is labeled in the
app and it is one swap from the real machine.

I ran that simulator against real FDM failure prints to check it honestly. Pulling and parsing
those corpora is the heavy work a laptop and a small Space cannot do, so it runs on **Modal**: the
ingestion produced 1,304 material reference facts and 178 cleaned calibration prints, for about
five cents of compute. After cleaning the
data it scored 32.6% agreement on 178 prints: correct on every clean success, blind to the
moderate failures. The gap is structural, not a knob I could quietly turn, and forcing a prettier
number would have broken the part that already works. So I left the constants alone, wrote down
why, and named the fix. There is a maintenance lesson in it too: one unparsed field, fan speed
defaulting to zero, had silently flipped the read on a third of the set before the cleanup. The
same rule that keeps the model from grading itself kept me from grading the simulator on bad
data.

Named as frontier, and honest about its state: fine-tuning on the accumulated ledger so the craft
lives in the weights as well as the memory (a LoRA is training on Modal now, and the live node
stays retrieval-based until a held-out eval earns the swap), streaming validated start-gcode
straight to the
Ender, real sensors in place of sliders, and the same compounding loop running across every
machine in the shop. That last one is where the Microfactory economy begins.

## Close

The shop is gone. The tools scattered, and the skill that lived in his hands went with him. I
built this node so that loss isn't the default ending for a maker's knowledge. He's gone. The
spirit isn't, and now it has somewhere to live and something to do.

---

*Live: [node.microfactory.space](https://node.microfactory.space) (fallback:
[the HF Space](https://huggingface.co/spaces/build-small-hackathon/microfactory-lab)).*

*Track: Backyard AI (`build-small-hackathon`, `backyard-ai`). Badges: Off the Grid
(`off-the-grid`, local Ollama/Gemma), Llama Champion (`llama-champion`, Ollama runs on
llama.cpp), Sharing is Caring (`sharing-is-caring`: the
[ledger trace](https://huggingface.co/datasets/kylebrodeur/chief-engineer-ledger) and the live
field-log are published as open datasets), Field Notes (`field-notes`), Off-Brand (`off-brand`,
the Astrometrics console skin), Tiny Titan (`tiny-titan`, Gemma E-class at ~4B effective via
MatFormer), and Well-Tuned (`well-tuned`): the node is tuned end to end, the persona/prompt
steering, the deterministic Spine, and the Brain/Inspector split, with a LoRA on the ledger
training as the weights-level version. Storytelling is a judging principle, not a badge.*
