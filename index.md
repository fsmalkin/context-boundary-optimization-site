---
layout: default
title: Context-Boundary Optimization
description: Context-Boundary Optimization lets a software service prepare the focused context and rules an AI agent needs for each task.
---

<section class="hero" aria-labelledby="page-title">
  <p class="hero-meta"><span class="status-stamp">Working drafts</span><span>Product guide · 2026</span></p>
  <h1 id="page-title">Give AI agents the right context for each task</h1>
  <p class="hero-lede"><strong>Context-Boundary Optimization</strong> lets a software service prepare a focused operating brief before an agent acts. The brief carries the relevant capabilities and service rules for that job.</p>
  <figure class="hero-sketch">
    <img src="{{ '/assets/images/cbo-workflow.webp' | relative_url }}" width="1200" height="600" alt="A task goes to a service, which prepares a focused context contract for an AI agent.">
  </figure>
</section>

<section class="guide-section" aria-labelledby="product-gap-heading">
  <p class="section-kicker">For product teams</p>
  <div class="section-heading"><h2 id="product-gap-heading">APIs expose actions. Agents still need product context.</h2></div>
  <div class="split-panel">
    <div>
      <p>Product teams decide what people can do and which rules apply through the interface. An agent often reaches the same service through an API that provides a catalog of functions with less guidance about the current job.</p>
      <p>CBO assigns that missing step to the service. For each task, the service computes a focused package called a <strong>context contract</strong>. It tells the agent which capabilities matter and keeps the service's operating rules attached to execution.</p>
      <div class="concept-callout"><p>The design places the boundary at the service so multiple agent integrations can reuse one product-defined source of context.</p></div>
    </div>
    <figure class="figure-card">
      <img src="{{ '/figures/fig1-boundary.png' | relative_url }}" width="1120" height="748" alt="The service turns its capabilities and operating requirements into a focused context contract for the agent." loading="lazy">
      <figcaption>The service prepares the task boundary before the agent acts.</figcaption>
    </figure>
  </div>
</section>

<section class="guide-section" aria-labelledby="example-heading">
  <div class="section-heading"><h2 id="example-heading">A refund task should begin with a focused brief</h2></div>
  <div class="split-panel">
    <figure class="figure-card">
      <img src="{{ '/figures/fig2-fisheye.png' | relative_url }}" width="1536" height="1024" alt="A large API catalog becomes a focused view centered on the current task." loading="lazy">
      <figcaption>Relevant detail expands around the current task.</figcaption>
    </figure>
    <div>
      <p>A billing API may expose forty functions. An agent resolving a duplicate charge on invoice 4471 may need four functions plus the approval and recordkeeping requirements. The service can assemble that context from the task before the agent takes action.</p>
      <p>The context contract defines the product boundary for the task. It narrows the working view and supplies service rules that a deterministic gate can check.</p>
    </div>
  </div>
</section>

<section class="guide-section" aria-labelledby="deep-dive-heading">
  <div class="section-heading"><h2 id="deep-dive-heading">Open the deep dive that matches your job</h2></div>
  <nav class="index-nav" aria-label="Context-Boundary Optimization deep dives">
    <a class="index-card" href="{{ '/papers/' | relative_url }}">
      <span class="index-card-preview paper-preview" aria-hidden="true"><span><b>T</b> Technical</span><span><b>E</b> Economic</span></span>
      <span class="index-card-copy"><span>Papers</span><h2>Research</h2><p>Read the framework, experiments, and economic argument.</p></span>
    </a>
    <a class="index-card" href="{{ '/library/' | relative_url }}">
      <img src="{{ '/assets/images/books.webp' | relative_url }}" width="600" height="600" alt="Hand-drawn books representing the reference implementation." loading="lazy">
      <span class="index-card-copy"><span>Library</span><h2>Implementation</h2><p>Inspect the Python objects, CLI, and worked billing service.</p></span>
    </a>
    <a class="index-card explore" href="{{ '/demos/' | relative_url }}">
      <img src="{{ '/assets/images/toolbox.webp' | relative_url }}" width="600" height="600" alt="Hand-drawn toolbox representing the experiment evidence." loading="lazy">
      <span class="index-card-copy"><span>Demos</span><h2>Evidence</h2><p>Walk through traces, scoring, and plain-English results.</p></span>
    </a>
  </nav>
</section>

<section class="guide-section status-note" aria-labelledby="status-heading">
  <h2 id="status-heading">Research status</h2>
  <p>The framework and reference implementation are available. Both papers remain working drafts while the empirical claims are strengthened.</p>
</section>
