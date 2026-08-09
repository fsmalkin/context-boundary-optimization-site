# CBO sales landing research and cold baseline

Date: 2026-08-09
Stage: full-loop-mock-first R&D, uncertified
Live baseline: https://fsmalkin.github.io/context-boundary-optimization-site/

## Cold baseline

An independent cold reader could decide that CBO was relevant and summarized it
as a service-generated, task-specific brief containing the capabilities and
operating rules an agent needs. The reader still could not assess adoption
readiness.

The strongest baseline findings were:

1. The API distinction was understandable, but MCP was absent. The reader could
   not place CBO relative to MCP.
2. The page did not sharply separate CBO from tool selection, prompt assembly,
   retrieval, or policy middleware.
3. "Optimization" had no plain-English objective or tradeoff above the fold.
4. Compatibility and integration effort were hard to judge. Project maturity
   also lacked a quick signal.
5. The reader chose Evidence first because the page foregrounded working-draft
   status, confirming that proof should support the story without masquerading
   as a visitor job.

Baseline observation: mobile-first 390 x 844, 2026-08-09T04:56:17.480Z.

## Current official-source patterns

### LangChain

[LangChain](https://www.langchain.com/langchain) leads with an outcome, defines
the category in one sentence, offers a build CTA and a docs CTA, then supports
the promise with a few differentiated benefits. Its open-source status,
integrations, and runtime give visitors fast credibility signals without
turning the hero into a feature inventory.

CBO implication: lead with the user-visible integration problem and a direct
category sentence. Separate "understand" from "build" as the first two paths.

### Model Context Protocol

The official [MCP introduction](https://modelcontextprotocol.io/docs/getting-started/intro)
defines the standard in one sentence, uses a familiar connection analogy,
gives concrete examples, explains benefits by audience, and ends in distinct
build paths. The [architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)
also draws a clean boundary among the host, its dedicated server clients, and
each server's context surface.

CBO implication: say what MCP standardizes before saying what CBO adds. The
recommended story is additive: the API executes service operations; MCP is the
standard agent-facing connection; CBO lets the service compute the focused
context and obligations carried through that connection.

### Vercel AI SDK

[Vercel AI SDK](https://vercel.com/ai-sdk) names the layer it owns, places a
working code example beside the primary claim, lists specific SDK capabilities,
and provides an immediate docs/install route. The page makes the first use feel
small even though the surrounding platform is broad.

CBO implication: name the owned layer as the service context boundary and show
one concrete task before introducing the full framework.

### LlamaIndex

The official [LlamaIndex framework introduction](https://developers.llamaindex.ai/python/framework/)
starts from the missing-context problem, defines context augmentation, explains
who the framework serves, and offers a 30-second quickstart while preserving
deeper documentation for advanced readers.

CBO implication: begin at beginner altitude, then expose a clear depth gradient
through navigation. A prospective adopter should be able to understand the
idea before encountering the seven boundary dimensions or research method.

## CBO narrative and information architecture

The landing page should answer five questions in order:

1. What the interface supplies: an operation schema covers the callable surface;
   the task still needs service context and obligations.
2. What CBO is: a provider-owned context layer that computes one focused,
   versioned context contract for the task.
3. Where MCP fits: MCP supplies the standard connection; CBO supplies the
   service-owned context policy and task-scoped content.
4. Why it matters: every connected agent can reuse the service's own boundary
   instead of reconstructing it independently.
5. What to do next: understand the model, open the billing example, or inspect
   the working research and traces.

Primary navigation should use visitor intent: Why CBO, How it works, Build,
Research. A separate credibility band should carry the papers and trace demos.
It should also link the reference implementation and project status. License
links complete the trust layer. This keeps proof
available without presenting "Evidence" as a peer visitor job.

## Variant hypotheses

1. Problem first: the API/MCP/CBO layer comparison produces the fastest category
   comprehension.
2. Mechanism first: "context as a service for your service" creates the most
   memorable product position when paired with a three-step task flow.
3. Adoption first: one billing task and one small next step make the project
   feel most usable without implying production maturity.

Every direction preserves the warm plain-paper surface, printed type, existing
hand-sketched raster illustrations, and working-draft status. Current research
and library destinations remain available. Demo and GitHub links remain too.
The drafts present CBO as an addition to APIs and MCP. They make no
production-readiness or completed-validation claim.

## Blind mock reads

Each direction received a fresh, independent mobile read at 390 x 844. The
reader received only an API or service-owner persona, a comprehension goal, and
the exact mock URL. These results are uncertified R&D evidence.

| Direction | Task outcome and comprehension | Primary action | Remaining friction | Recommendation |
| --- | --- | --- | --- | --- |
| 1 - Problem first | PASS. The reader identified an open-source framework and Python reference library, then accurately separated API execution, the MCP connection, and CBO's task-specific context role. | Open the billing example. | MCP detail begins below the first screen; compatibility, adoption effort, and maturity need deeper pages. | Recommended because it opens with the requested API/MCP/CBO distinction and routes directly to the billing example. |
| 2 - Mechanism first | PASS. The reader understood API operations, MCP as the recommended connection, and CBO as the service-owned contract and receipt layer. | Open the billing example. | The page leaves the contract schema, installation, maintenance maturity, and the boundary with adjacent MCP mechanisms to deeper material. | Lead with this direction to foreground `Context as a service for your service`; the reader selected that exact phrase from the initial screen. |
| 3 - Adoption first | PASS. The reader understood the API execution surface, MCP reference path, and CBO framework, then recognized a narrow first-use pattern. | Open the billing example. | The acronym, MCP requirement boundary, compatibility, and adoption cost require deeper material. | Use it to foreground the adoption sequence. Direction 1 gives the concept definition more precision. |

The initial reads exposed one common category gap. Every final mock now states
`Framework + Python reference library` above the fold and promotes the billing
example as the primary action. Direction 2 now names all three layers directly.
Direction 3 now places its core claim before the illustration on mobile. The
final reads passed those corrected seams.

The forty-operation to four-action scenario is an illustrative mental model.
The linked billing service is the working reference example for inspecting the
contract, gate, and receipt structure. Its existing service scenario is the
implemented scope; invoice 4471 and the catalog size remain illustration-only.
