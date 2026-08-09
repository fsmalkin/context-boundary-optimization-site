---
layout: default
title: Context-Boundary Optimization
description: Services computing, per task and at runtime, the information architecture an agent needs to act well.
---

<section class="hero" aria-labelledby="page-title">
  <p class="hero-meta"><span class="status-stamp">Working drafts</span><span>Research field guide · 2026</span></p>
  <h1 id="page-title">Context-Boundary Optimization</h1>
  <p class="hero-lede">Services computing, per task and at runtime, the information architecture an agent needs to act well.</p>
  <figure class="hero-sketch">
    <img src="{{ '/assets/images/cbo-workflow.webp' | relative_url }}" width="1200" height="600" alt="A task passes through a service, which computes a context contract containing the focused tools, obligations, and record requirements an agent needs.">
  </figure>
</section>

<nav class="index-nav" aria-label="Field guide sections">
  <a class="index-card" href="#papers">
    <span class="index-card-preview paper-preview" aria-hidden="true"><span><b>T</b> Technical</span><span><b>E</b> Economic</span></span>
    <span class="index-card-copy"><span>Read</span><h2>Papers</h2><p>The technical framework and its economic case.</p></span>
  </a>
  <a class="index-card" href="{{ '/library/' | relative_url }}">
    <img src="{{ '/assets/images/books.webp' | relative_url }}" width="600" height="600" alt="Hand-drawn books representing the reference implementation." loading="lazy">
    <span class="index-card-copy"><span>Library</span><h2>Build</h2><p>Dependency-free objects, a CLI, and a worked service.</p></span>
  </a>
  <a class="index-card explore" href="{{ '/demos/' | relative_url }}">
    <img src="{{ '/assets/images/toolbox.webp' | relative_url }}" width="600" height="600" alt="Hand-drawn toolbox representing the interactive traces and experiment artifacts." loading="lazy">
    <span class="index-card-copy"><span>Demos</span><h2>Explore</h2><p>Step through runs, scoring, and results.</p></span>
  </a>
</nav>

<section class="guide-section" aria-labelledby="boundary-heading">
  <div class="section-heading"><h2 id="boundary-heading">The missing boundary</h2></div>
  <div class="split-panel">
    <div>
      <p>When a person uses a software service, the interface surfaces relevant actions, confirms risky ones, and records what happened. An autonomous agent calling the same service through its API inherits only functions and types.</p>
      <p><strong>Context-boundary optimization</strong> has the service compute the task-specific information architecture instead. The governing object is a <strong>context contract</strong>; its mechanism is a <strong>fisheye view</strong> keyed to the current task.</p>
    </div>
    <figure class="figure-card">
      <img src="{{ '/figures/fig1-boundary.png' | relative_url }}" width="1120" height="748" alt="The service holds capabilities, obligations, and record requirements; the agent receives a focused context contract instead of a raw catalog." loading="lazy">
      <figcaption>The boundary carries the service knowledge the agent needs to act well.</figcaption>
    </figure>
  </div>
</section>

<section class="guide-section" id="papers" aria-labelledby="papers-heading">
  <p class="section-kicker">The argument in two papers</p>
  <div class="section-heading"><h2 id="papers-heading">Read the research</h2></div>
  <div class="paper-grid">
    <article class="paper-card">
      <span class="paper-number" aria-hidden="true">A</span>
      <h3>Technical framework</h3>
      <p>What is a context contract, and does one improve agent reliability?</p>
      <p class="paper-links"><a href="{{ '/papers/technical-paper.html' | relative_url }}">Read online →</a><a href="{{ '/papers/context-boundary-optimization.pdf' | relative_url }}">Open PDF</a></p>
    </article>
    <article class="paper-card">
      <span class="paper-number" aria-hidden="true">B</span>
      <h3>Economic argument</h3>
      <p>Who should compute the boundary, and why is the provider the low-cost producer?</p>
      <p class="paper-links"><a href="{{ '/papers/economic-paper.html' | relative_url }}">Read online →</a><a href="{{ '/papers/computing-the-context-boundary.pdf' | relative_url }}">Open PDF</a></p>
    </article>
  </div>
</section>

<section class="guide-section" aria-labelledby="concrete-heading">
  <div class="section-heading"><h2 id="concrete-heading">The idea, concretely</h2></div>
  <div class="split-panel">
    <figure class="figure-card">
      <img src="{{ '/figures/fig2-fisheye.png' | relative_url }}" width="1536" height="1024" alt="A full uniform tool catalog becomes a task-scoped fisheye view with relevant tools and obligations expanded near the focus." loading="lazy">
      <figcaption>Detail follows the task; distant capabilities recede.</figcaption>
    </figure>
    <div>
      <p>A service exposes forty API functions. An agent asked to <em>refund the duplicate charge on invoice 4471</em> may need four of them, one approval rule, and one record format. Today it receives all forty and a prompt hoping it infers the rest.</p>
      <div class="concept-callout"><p><strong>A context contract makes that inference unnecessary.</strong> The service computes a focused view, states the obligations, specifies the expected record, and enforces the rules deterministically.</p></div>
    </div>
  </div>
</section>

<section class="guide-section" id="build" aria-labelledby="build-heading">
  <p class="section-kicker">Reference implementation</p>
  <div class="section-heading"><h2 id="build-heading">Build a contract</h2></div>
  <div class="split-panel">
    <div>
      <p><code>context_contract</code> gives each construct in the papers a small Python object with no dependencies. Use the advisor, the CLI, or the worked billing-service example.</p>
      <a class="library-cta" href="{{ '/library/' | relative_url }}">Browse the library →</a>
    </div>
    <div class="code-card" aria-label="Python context contract example">
      <div class="code-card-header"><span>Python</span><span>Focused view + gate</span></div>
      <pre><code>from context_contract import ContextContract, focused_view, Gate

contract = ContextContract.load("contract.json")
view = focused_view(catalog, task, contract, k=4)
verdict = Gate(contract).check(action)</code></pre>
    </div>
  </div>
</section>

<section class="guide-section" id="explore" aria-labelledby="explore-heading">
  <p class="section-kicker">Experiment artifacts</p>
  <div class="section-heading"><h2 id="explore-heading">Explore the runs</h2></div>
  <div class="demo-list">
    <a class="demo-link" href="{{ '/demos/trace-browser.html' | relative_url }}"><strong>Trace browser →</strong><span>Follow what an agent did, turn by turn.</span></a>
    <a class="demo-link" href="{{ '/demos/adjudication.html' | relative_url }}"><strong>Adjudication →</strong><span>See how a run was scored and where scorers disagreed.</span></a>
    <a class="demo-link" href="{{ '/demos/plain-english-results.html' | relative_url }}"><strong>Plain-English results →</strong><span>Read the findings without the statistics.</span></a>
  </div>
</section>

<section class="guide-section" aria-labelledby="figures-heading">
  <div class="section-heading"><h2 id="figures-heading">Field notes</h2></div>
  <div class="figure-grid">
    <figure class="figure-card"><img src="{{ '/figures/fig3-runtime-flow.png' | relative_url }}" width="1536" height="1024" alt="The agent and service co-author context at runtime; the gate can reject, proceed, approve, or clarify and adapt." loading="lazy"><figcaption>Runtime flow</figcaption></figure>
    <figure class="figure-card"><img src="{{ '/figures/fig4-amortization.png' | relative_url }}" width="1536" height="1024" alt="Provider-side boundary computation is amortized across agents instead of reconstructed by every consumer." loading="lazy"><figcaption>Provider-side amortization</figcaption></figure>
    <figure class="figure-card"><img src="{{ '/figures/fig5-enforcement.png' | relative_url }}" width="1536" height="1024" alt="An advisory policy can be bypassed; a provider-enforced gate executes policy before a tool call." loading="lazy"><figcaption>Execution-bound enforcement</figcaption></figure>
    <figure class="figure-card"><img src="{{ '/figures/fig6-spectrum.png' | relative_url }}" width="1536" height="1024" alt="Context contracts occupy the middle ground between raw APIs and subagents on flexibility, runtime cost, and scaling." loading="lazy"><figcaption>Cost-capability spectrum</figcaption></figure>
  </div>
</section>

<section class="guide-section status-note" aria-labelledby="status-heading">
  <h2 id="status-heading">Current status</h2>
  <p>The library implements the framework through a complete, runnable worked example. The empirical claims are still being strengthened, so both papers remain working drafts.</p>
</section>
