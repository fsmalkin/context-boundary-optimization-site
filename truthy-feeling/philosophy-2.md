---
layout: truthy
title: "Degrees, Domains, and Ideal Evaluation"
description: "Philosophy II: selected formal examples on graded semantics, Sorites, uncertainty, and information preservation."
---
# Degrees, Domains, and Ideal Evaluation

*That Truthy Feeling · Philosophy II · Master's-level arguments, selected formal examples*

<div class="reading-note">By Fred Smalkin, Jr. · Working essay developed with substantial AI assistance. CST is a proposal; the cited studies do not establish a distinct correspondence schema.</div>

## Before you read (optional)

The post defines its notation. These readings offer preparation or alternative perspectives; they are not prerequisites for following the worked examples.

[Truth in First-Order Logic](https://forallx.openlogicproject.org/html/Ch31.html) — Preparation for recursive evaluation and quantifiers.

[These degrees go to eleven](https://www.njjsmith.com/philosophy/papers/Smith-etalDegreesEleven.pdf) — Developed graded semantics and its relation to scalar language.

[Tolerance and Degrees of Truth](https://arxiv.org/abs/2207.12786) — A substantive challenge to treating a continuum as uniquely required by Sorites.

## What this post examines

The philosophical proposal becomes more useful when we separate what is stipulated, what follows from it, and what remains an empirical or interpretive question. A graded semantics can assign a precise intermediate value. A procedure can correctly calculate that value. A physical mind can then be investigated as a possible implementation. None of these steps establishes the next merely by giving it a name.

This post works through value-preserving evaluation, a graded treatment of Sorites, and question-relative information sufficiency. These are explanatory companions to the full philosophical paper, not replacements for its broader discussion. The semantic resources have an established literature: Cintula and colleagues connect fuzzy logic with gradable predicates, while Smith distinguishes uncertainty from degrees of truth.[11,12] CST draws on those accounts rather than asking a partly filled glass to establish them from scratch.

## 1. Fix the question before evaluating it

Let a claim be expressed by a finite formula p. Its interpretation I fixes what its names and predicates mean, while its domain U supplies the objects being discussed. Write tau(p) for the value the interpreted formula receives. In the classical instance, that value is 0 or 1. In a graded instance, it can lie between them. Here “domain” means the objects of a supplied mathematical structure, not a separate ontological world. Ordinary evaluation also requires conditions such as time, scope and assumptions, whether expressed or fixed by interpretation.

This notation does not tell us which semantics is appropriate. A 250 mL glass containing 200 mL has fill fraction 0.8. We may stipulate that FULL measures that fraction, while FILLED-TO-CAPACITY remains binary. Ordinary “full” needs its own linguistic argument. The distinction between a scale and a standard for applying a word matters before calculation begins.[1]

Likewise, complete access to the Holmes stories does not fill every gap in the fiction. Specifying a story or narrative point helps identify what is asserted; it does not make the character historical or guarantee a verdict. The models below idealize the relevant atomic values as given. A finite sentence can nevertheless make a determinate claim about an infinite structure: interpretive underspecification and incomplete description are different limitations.

## 2. A small graded model

Take a finite nonempty domain, a finite relational vocabulary, and exact rational-valued tables for its predicates. Names identify objects, variables range over them, and equality remains crisp. There are no function symbols in this construction. Begin with:

    tau(not p) = 1 - tau(p)
    tau(p and q) = min(tau(p), tau(q))
    tau(p or q) = max(tau(p), tau(q)).

Universal quantification takes the minimum over the finite domain; existential quantification takes the maximum. These are specified compositional rules, not facts established by using decimal values. Other fuzzy frameworks make different choices.[2,3]

Suppose two glasses, A and B, have FULL values 0.8 and 0.4. Under these rules, “A and B are full” receives 0.4, “A or B is full” receives 0.8, and “B is not full” receives 0.6. “Every glass is full” receives 0.4, while “some glass is full” receives 0.8. The entries were supplied exactly; nothing here expresses uncertainty about them.

Smith's account relates the two kinds of partiality through expected semantic value:[12]

    Cr(p) = E_P[tau(p)].

P describes the agent's epistemic uncertainty, not a degree of membership. A known semantic value of 0.8 and an 80 percent probability of a binary truth both yield credence 0.8. In our simple example their distributions have variances zero and 0.16. The same mean therefore need not reveal the same representation. This is mathematical dispersion, not a definition of psychological confidence.

Restrict the predicate tables to 0 and 1 and the displayed operations recover the corresponding classical behavior. Intermediate values need not preserve every classical law: for p valued at 0.8, weak “p or not-p” receives 0.8 rather than 1. A theory cannot change truth values and silently retain every familiar connective and inference rule.

## 3. Why adequate evaluators agree

Define an evaluator operationally. It decodes expressions and tables correctly, looks up elementary values, recursively evaluates smaller expressions, and applies the specified operations. At a quantifier it examines every object. Give it enough memory and time to finish and require it to report the computed result without error.

Direct recursion supplies at least one such procedure. Let A* be the nonempty class of correct implementations. For every formula and assignment of objects to its free variables:

    Eval_a(p, U, I) = tau(p, U, I), for every a in A*.

The assignment is suppressed here only for brevity; closed sentences do not depend on it. Structural induction proves the result. Atomic lookups match the tables. If evaluation agrees on the parts, applying the same semantic operation gives agreement on the whole. At a quantifier this holds for each updated assignment, so the finite aggregation agrees too. Finite syntax, a finite domain and exact rational arithmetic ensure termination.

This is standard compositional evaluation correctness.[4] Interpretation and accurate atomic information remain assumptions. Different implementations can compute in different orders without changing the answer, but the proof does not settle the suitability of that semantics for natural language or its implementation in a brain.

The nonempty class matters: “all ideal agents agree” would be vacuous if no admissible procedure existed. A mathematical procedure nevertheless need not be available to an actual person with limited information. Infinite domains, arbitrary real inputs and nonterminating operations require additional arguments. The theorem supplies sufficient conditions for a guarantee, not prerequisites for every ordinary correct judgment. In a graded instance, the invariant is the appropriate degree rather than necessarily acceptance or rejection.

## 4. A coherent, limited response to Sorites

Take “nearly full,” a vague predicate rather than an exact at-capacity condition. Removing one drop seems not to change it, but enough removals leave the glass empty. A degree account must distinguish small change from exact preservation and specify both the conditional and the consequence relation.

Our earlier illustration used material implication defined as weak “not p or q,” giving max(1-a,b). It had a serious explanatory limitation: for intermediate a, even “if p, then p” was below fully true. That calculation was correct, but it could not attribute the loss of full truth specifically to small changes. The revision record preserves that criticism.

Here we instead use standard Łukasiewicz residual implication and strong conjunction:[11]

    I_L(a,b) = min(1, 1-a+b)
    T_L(a,b) = max(0, a+b-1).

Strong conjunction is not the minimum operation above. The residual is the negation of the strong conjunction of a with not-b; it is not the old weak-disjunction material conditional. The distinct definitions are part of the revised model.

Assign successive claims p_i values a_i=1-i/n, for i=0,...,n and n>1. This sequence is illustrative, not an experimentally established curve for ordinary “nearly full.” Every self-conditional now receives 1, while every adjacent decreasing conditional receives 1-1/n. With 100 steps, each receives 0.99. Combining k steps by strong conjunction gives:

    T_L applied to k step values = max(0, 1-k/n).

For all n steps the strong conjunction is zero. But the universal claim evaluated by the finite minimum of the step conditionals has value 1-1/n, not zero. These are different formulas: neither weak conjunction nor quantification may be silently replaced by strong conjunction to manufacture cumulative loss.

With consequence preserving designated value 1, the nearly true tolerance premise is not a fully true premise. We cannot propagate the initial fully true judgment through a sequence of fully true tolerance assertions, because those assertions are not supplied. This is a coherent degree-theoretic instance, not a new solution uniquely selecting a continuum. Epistemic and strict-tolerant alternatives remain substantive.[5]

The evaluation proof extends explicitly: add recursive clauses for I_L and T_L using their exact rational operations, then include those cases in the induction. Finiteness and termination are preserved. Endpoint restriction is classical, while weak excluded middle still differs at intermediate values. The proof establishes evaluation of this supplied semantics, not its psychological correctness.

## 5. What a summary must preserve

A separate result concerns information. Let S(w) represent state w and Q be a family of interpreted questions, with required answer tau_q(w). Suppose a decoder receives only the question and stored representation, without another source of state-specific evidence. Exact decoding is possible as a set-theoretic function precisely when:

    S(w1) = S(w2) implies tau_q(w1) = tau_q(w2), for every q in Q.

Necessity follows because identical inputs cannot distinguish different required answers. For sufficiency, assign each representation the common answer shared by all states mapped to it. The condition makes that assignment well-defined, not necessarily computable or efficient.

Two histories, (2,0) and (0,2), can be stored as their sum, 2. That representation answers “what is the negative sum?” in both cases. It cannot recover first-minus-second in both, because the required answers are 2 and -2. The limitation is relative to the question, not a reason to reject all compression.

For graded values the same principle holds. If merged states require 0.3 and 0.7, a common point estimate must err by at least 0.2 in one. A system might appropriately report uncertainty or seek evidence instead of guessing. If the questions distinguish every state, the representation must too; narrower question families can permit substantial compression.

## 6. Why this is not Gödel's completeness theorem

Logical completeness says that every semantic consequence of first-order assumptions is formally provable from them. It does not say that those assumptions settle every sentence about an intended structure. Completeness of a theory means settling each sentence or its negation; decidability concerns a procedure that always finishes with an answer.[6,8]

Gödelian incompleteness concerns consistent, effectively axiomatized theories sufficiently strong for elementary arithmetic. Such a theory cannot settle every sentence in its language. The undecided sentence is already expressible. True arithmetic is complete as a set of truths but not effectively axiomatizable.[6,9]

There is no inference from this to infinitely many primitive symbols or a language without syntax. Evaluation of a supplied finite structure, information retained in a summary, and the power of an effective theory are different subjects. Conflating them would make the account less precise, not more ambitious.

## 7. The philosophical role of the ideal

Peirce connected truth with the outcome toward which inquiry would ultimately settle.[7] Our result is narrower: under specified semantic and operational assumptions, evaluation preserves the value. It does not prove actual convergence, universal decidability or the appropriateness of one semantics for every claim.

The ideal nevertheless helps locate different problems. Missing facts, a misunderstood question, lost distinctions and an inadequate method can require observation, clarification, retrieval or new reasoning. CST proposes that represented information about the assessment helps guide that choice, including during disagreement. It inherits rather than discovers the connection between contextual rightness and cognitive control.[14]

For “reliable enough to deploy,” participants may disagree about the property, the reports, how testing generalizes, or acceptable costs. A lexical standard changes the interpreted proposition; an action policy need not change the value of an agreed claim. Clarification can recover intended content or negotiate a new question. People may substantively dispute which concept should govern, rather than merely misunderstand one another.[10]

The proposed diagnostic test asks whether independently elicited grounds improve selection of useful interventions. It must allow mixed and undiagnosed disputes and genuine value conflicts. Comparing selectors requires the same information and controls for elicitation itself. A useful method need not be a distinct neural schema. Neither its effectiveness nor its mechanism follows from the formal results.

## Known limitations and open questions

The adopted degree-theoretic resources provide an argued foundation, not proof that every ordinary judgment is graded. A human experiment can favor fuzzy predictions within a fragment while leaving an uncertain-threshold account equivalent, as Cremers and Kalvelyte show.[13] Discriminating those accounts requires changing the relevant assumptions, not collecting more equivalent ratings.

The residual/strong-conjunction instance repairs the old self-conditional defect without making its operations universal linguistic or cognitive laws. CST's proposed integration also has close predecessors; its value must lie in the explicit connections and tests it supplies. Philosophical correctness, an effective diagnostic practice and an identified brain mechanism remain different achievements. The account applies these distinctions to itself.

## Sources

[1] [Kennedy and McNally (2005), Scale Structure, Degree Modification, and the Semantics of Gradable Predicates](https://doi.org/10.1353/lan.2005.0071).

[2] [Zadeh (1965), Fuzzy Sets](https://doi.org/10.1016/S0019-9958(65)90241-X).

[3] [Badreddine et al., Logic Tensor Networks, author version 4](https://arxiv.org/abs/2012.13635v4).

[4] [Open Logic Project, forall x: Calgary, Truth in FOL](https://forallx.openlogicproject.org/html/Ch31.html).

[5] [Cobreros et al. (2022), Tolerance and Degrees of Truth](https://arxiv.org/abs/2207.12786).

[6] [Open Logic Project, Completeness and Decidability: Definitions](https://builds.openlogicproject.org/content/incompleteness/introduction/definitions.pdf).

[7] [Peirce (1878), How to Make Our Ideas Clear, section IV](https://www.peirce.org/writings/p119.html).

[8] [Open Logic Project, The completeness theorem](https://builds.openlogicproject.org/content/first-order-logic/completeness/completeness-thm.pdf).

[9] [Open Logic Project, The first incompleteness theorem](https://builds.openlogicproject.org/content/incompleteness/theories-computability/first-incompleteness.pdf).

[10] [Plunkett and Sundell (2013), Disagreement and the Semantics of Normative and Evaluative Terms](https://researchportalplus.anu.edu.au/en/publications/disagreement-and-the-semantics-of-normative-and-evaluative-terms/) — Author institutional abstract.

[11] [Cintula, Grimau, Noguera, and Smith (2022), These degrees go to eleven: fuzzy logics and gradable predicates](https://www.njjsmith.com/philosophy/papers/Smith-etalDegreesEleven.pdf).

[12] [Smith (2014), Vagueness, Uncertainty and Degrees of Belief](https://www.njjsmith.com/philosophy/papers/SmithVaguenessUncertaintyDegreesBelief.pdf).

[13] [Cremers and Kalvelyte (2024), An Empirical Comparison of Semantics for Quantified Vague Sentences](https://www.journals.vu.lt/problemos/article/view/38284/35927).

[14] [Mangan (2001), Sensation's Ghost: The Non-Sensory Fringe of Consciousness](https://www.researchgate.net/publication/247487522_Sensation%27s_ghost_The_non-sensory_fringe_of_consciousness).

## Explore with an AI tutor

[Open ChatGPT](https://chatgpt.com/) or [Open Claude](https://claude.ai/new), then copy the prompt below. These links open a service only: they do not attach this essay, prefill a request, or submit it. Supply only text you are entitled and comfortable to share. Treat the answer as a reading aid, not validation of CST.

> Ask me to paste one argument from this post. Define every symbol, work a finite numerical example, and separate assumptions from conclusions. Distinguish weak conjunction, strong conjunction and universal quantification. Do not silently repair a gap or treat evaluation correctness as proof of CST.

## Reading path

[Start with the shared introduction](introduction.html) · [Earlier: Philosophy I](philosophy-1.html) · [All five essays and companion-work status](./)
