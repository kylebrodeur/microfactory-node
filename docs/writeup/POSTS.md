# Posts: Microfactory Node — Build Small

Canonical record of all drafted social posts and channel posts for the Build Small hackathon submission.

---

## Channel post / build-thread opener

A clever proof of concept that works — not a production system. Backyard AI judges a demo video, a writeup, a plausible "someone could use it" story, and a working Gradio app. Build the judged things well; keep everything else minimal. **A component nobody judges should never cost more than a component that is judged.** Simplify as you go.

For Microfactory Node: 3D Printer, the one judged moment is the Chief Engineer reading the room and recalling prior jobs before the nozzle moves — applying precedent when it fits and saying *"no close precedent"* when it doesn't. Everything else is scaffolding for that moment.

Built for @huggingface Build Small. 🔗 [Space link] #BuildSmall

---

## Variant A: the story lead

> My grandfather ran a shop. He built the thing and he inspected it, both at once, and he taught
> me at that bench. Alzheimer's took him, the shop was sold, and a lifetime of skill went with it.
>
> For the @huggingface Build Small hackathon I built the opposite of that: Microfactory Node: 3D
> Printer. A small Gemma model that runs entirely on my own machine and learns 3D printing job by
> job, conditions and all.
>
> Two agents do the work, named for the engineers I grew up watching. Chief Engineer O'Brien
> proposes the settings. La Forge inspects the plan and holds the print when the optimism is thin.
> Before the nozzle moves, the node recalls similar past jobs, weighs what today's heat and
> humidity change, and points at where it will fail. Every real outcome becomes a lesson it keeps.
> Knowledge that compounds instead of disappearing.
>
> 100% local. No cloud, no API key, $0 a month.
>
> 🔗 [Space link] #BuildSmall

---

## Variant B: the demo-moment lead

> "Humidity is 17 points higher than the job where this overhang sagged, so I'm raising cooling
> and dropping temp. Here is where it fails if you don't."
>
> That is Chief Engineer O'Brien: a small Gemma running on my laptop, reasoning over its own print
> history before the print starts. A second agent, La Forge, checks his plan and can hold the
> print. Built for @huggingface Build Small: Microfactory Node: 3D Printer, a maker's copilot whose
> knowledge compounds job by job and never leaves my machine.
>
> 🔗 [Space link] #BuildSmall

⚠ The quoted line must be a real (lightly trimmed) output from the final recording. Replace it
with an actual one before posting.

---

## Variant C: the maker-problem lead (base)

> Every failed 3D print is a knowledge failure. A veteran reads the part and the room and knows the
> overhang will sag. I am not that veteran, so I built one. Microfactory Node: 3D Printer: a small
> local model that learns from every job I run, keyed to the conditions in the room, and catches
> failures before they print. Local Gemma through Ollama, retrieval not fine-tuning, honest when it
> has no precedent. It is the first node of a bigger plan: connect the makers and the skill they hold.
>
> Built for @huggingface Build Small. 🔗 [Space link] #BuildSmall

### C1: tighter punch, same shape (CHOSEN)

> The one judged moment of Microfactory Node: 3D Printer is the Chief Engineer reading today's room against prior jobs before the nozzle moves. *"Humidity is higher than the job where this overhang sagged, so I'm raising retraction and adding support."* It either applies what fits or says *"no close precedent"* when nothing close exists. Local Gemma through Ollama, retrieval not fine-tuning, honest when it has no precedent. No API keys. No cloud bill.
>
> Built for @huggingface Build Small. 🔗 [Space link] #BuildSmall

### C2: bring the agents forward (CHOSEN)

> I built Microfactory Node: 3D Printer around one judged moment: the Chief Engineer reads the room, retrieves similar past jobs, and calls the shot before the nozzle moves. *"Humidity is higher than the job where this overhang sagged — raising retraction, adding support."* When nothing close exists it says *"no close precedent"* and reasons from material properties instead. La Forge checks the plan and can hold the print.
>
> Retrieval, not fine-tuning. Honest when there is no precedent. No cloud, no API key.
>
> Built for @huggingface Build Small. 🔗 [Space link] #BuildSmall

### C3: shorter, for X / Threads / Bluesky

> I built a 3D printing copilot that learns from every job I run.
>
> Small local Gemma. Retrieval from past prints, adjusted for room conditions, flags failures
> before they happen. Honest when it has no precedent.
>
> No cloud. No API key. No bill.
>
> Microfactory Node: 3D Printer, for @huggingface Build Small.
>
> 🔗 [Space link] #BuildSmall

### C4: the bigger plan front-loaded

> The goal is simple: stop losing maker knowledge every time a skilled printer steps away from the
> bench.
>
> Microfactory Node: 3D Printer is the first node. A small local Gemma model remembers my prints,
> reads the room, and warns me where the next job will fail before the nozzle moves. Chief Engineer
> O'Brien proposes. La Forge inspects and holds the print when the plan is thin. Every outcome
> becomes a lesson.
>
> Local. Retrieval based. Honest about what it does not know.
>
> Built for @huggingface Build Small. 🔗 [Space link] #BuildSmall

---

**Ship list:** C1 and C2 are the chosen variants. The channel post above can run as a standalone build-thread opener or after the demo clip.

**Checklist for whichever variant ships:**
- [ ] Real Space URL in (`https://node.microfactory.space`)
- [ ] Asset attached (Beat-3 clip > still > nothing)
- [ ] Posted where judges can open it without login (X / Bluesky / LinkedIn)
- [ ] **URL of the post added to the Space README** (explicit requirement)
- [ ] Quoted model output (Variant B) is genuine
