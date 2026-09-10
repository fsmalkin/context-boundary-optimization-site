---
layout: truthy
title: "Testing a Model of Evaluation"
description: "Cognitive Science II: model comparison, information-preservation constraints, and tests of condition-sensitive inquiry."
---
# Testing a Model of Evaluation

*That Truthy Feeling · Cognitive Science II · Master's-level model comparison*

<div class="reading-note">By Fred Smalkin, Jr. · Working essay developed with substantial AI assistance. CST is a proposal; the cited studies do not establish a distinct correspondence schema.</div>

## Before you read (optional)

Basic probability and the college-level cognitive account are useful preparation. These outside readings provide measurement background and substantive comparators; the worked model is explained below.

[How to measure metacognition](https://doi.org/10.3389/fnhum.2014.00443) — Measurement rather than assumed access to experience.

[Self-evaluation of decision-making](https://pubmed.ncbi.nlm.nih.gov/28004960/) — A substantive second-order comparator.

[Double Crux](https://www.lesswrong.com/posts/exa5kmvopeRyfJgCy/double-crux-a-strategy-for-mutual-understanding) and [Taboo Your Words](https://www.lesswrong.com/posts/WBdvyyHLdxZSAMmoz/taboo-your-words) — Existing practical disagreement methods, not controlled efficacy evidence.

## What this post examines

Begin with an evaluator who understands a claim, has relevant information, and reaches an accurate assessment. A cognitive account should explain how that success is represented and used, including when the correct assessment is an intermediate degree. CST proposes a model of the assessment that helps direct judgment and inquiry. Starting with this successful case does not assume that every judgment is accurate or that CST has been empirically established.

A theory acquires empirical content when its specifications rule out observations, not when it supplies a new name for a familiar experience. This essay first develops measurement and information-preservation comparisons, then examines graded correspondence and useful inquiry during disagreement. The separate question of how social purposes and biological mechanisms can alter assessment comes near the end. The aim is to distinguish mechanisms without reproducing the complete experimental program.

## What would the schema have to contain?

Let p denote the claim, C-hat the evaluator's understanding of its interpretation and relevant conditions, E the available information, and v the assessment:

    S = g(p, C-hat, E, v).

C-hat can include referents, time, scope, assumptions and predicate meaning. It is represented information, not an oracle. “Reference domain” in earlier drafts was shorthand for the evaluation target, not a separate ontological world. Formal task domains retain their mathematical role.

S names the proposed schema; g still needs specification. A complete model must say what it preserves, how it changes and how a policy uses it to select assertion, clarification, retrieval or observation. Two people can give the same initial weather estimate while remembering different information about where a forecast applies. Those qualifications could direct different subsequent searches. But ordinary memory may preserve them without a distinct correspondence schema.

The architecture has direct predecessors. Nelson and Narens distinguish monitoring and control through a meta-level model,[11] while Mangan already connects felt rightness, contextual fit, retrieval and feedback.[12] Epistemic vigilance distinguishes understanding from acceptance and evaluates sources and content.[13] AST supplies a further model-informed-control analogy.[1] CST's proposed contribution is the explicit connection among represented semantic value, uncertainty, grounds and inquiry—not the invention of contextual rightness or metacognition.

## Begin with what an answer measures

Binary endorsement, a graded rating and a confidence report are different observations, not necessarily independent internal states. A common assessment can feed a thresholded answer and a noisy rating. For example:

    P(endorse) = 1 / (1 + exp(-v)).

This maps v to response probability. It is not automatically a semantic degree or activation level. The existing integration models concern binary tasks; graded report channels do not retrospectively change their semantics.

Confidence also needs a target. For a binary choice it can concern correctness; for a graded estimate it can concern error within a specified tolerance or uncertainty over values.[3] A person can be certain about an intermediate value. Smith's expected-semantic-value framework explains why a known degree and uncertainty over endpoints can share a mean report while remaining different distributions.[18] It does not establish the brain's implementation.

Behavior and reported feeling must be compared independently. Confidence-guided search already has substantial metacognitive models,[2] and Wang and Thompson report a manipulation that changed feelings-of-rightness ratings without changing reconsideration choices.[14] The relevant causal variable could be a shared cue or a different part of the assessment, not the report itself. A model must explain that dissociation as well as positive associations.

## A summary that answers yesterday's question

Consider evidence histories (2,0) and (0,2). Addition gives 2 in both. A person retaining only the total can negate it, but cannot recover first-minus-second correctly in both cases: the answers are 2 and -2.

This is an information restriction, not yet a storage theory. Revaluation research uses changed task demands to investigate what people retain.[4] Equal objective totals do not establish equal internal states; a person might retain components, order or context. The restriction concerns what can actually influence the later response.

A strict summary-only candidate says that later responses depend on the history only through the stored summary. If the complete distributions of retained states match, the same new rule must yield matching response distributions. This holds for binary or graded outputs. But failure to revise an answer can also reflect misunderstood rules or arithmetic error. The system might recognize missing information and seek help rather than repeat its old verdict. Content and policy must both be specified.

## Separating detail that is lost from detail that is unused

The implemented illustration separates retention r from use a conditional on retention. Detail can be lost, retained but unused, or retained and used. Let Y be binary endorsement, F a graded report, R accuracy on a later component probe and T the correct direction under the new rule:

    P(Y,F,R | T) = (1-r) K00 + r(1-a) K10 + ra K11.

Each K is the joint observation distribution for one state, conditional on T. The availability-only rival fixes a at 1. The more flexible candidate allows surviving information not to affect evaluation.

Both versions share illustrative measurement channels. When detail is used, decision accuracy is d. A restricted second-order reporter generates the rating using incomplete information about the decision, borrowing an idea from metacognition without implementing the entire Fleming–Daw model.[5] The probe has accuracy q when detail survives and is at chance otherwise. Under these fixed assumptions:

    Endorsement contrast = r a (2d - 1).
    Probability of correct probe = 0.5 + r(q - 0.5).

The contrast compares endorsement in cases requiring opposite answers. It depends on availability times use; an informative, calibrated probe adds a separate constraint on availability.

For r=0.8, a=0.4, d=0.85 and q=0.9, the contrast is 0.224 and probe accuracy 0.82. An availability-only rival preserving 0.82 probe accuracy predicts contrast 0.56. Reducing retention to match contrast 0.224 instead predicts probe accuracy 0.628. Under the specified channels, it cannot match both. These are analytical consequences of illustrative parameters, not estimated human effects.

## What that comparison cannot identify

If the probe is at chance even when detail survives, it cannot separate retention from use. Miscalibration can distort the conclusion. Correct later recall also does not prove earlier access: the probe may reactivate or reconstruct information. Stable access across responses is an assumption, not a consequence of their order.

A deeper limitation survives arbitrarily large samples. A generic selective-access account with the same three states reproduces the candidate's full response distribution. The numerical checks demonstrate this equivalence. They can distinguish some availability-only failures from available-but-unused information under fixed assumptions; they cannot choose between matched schema and selective-access interpretations.

A stronger test therefore requires an independently motivated restriction or intervention yielding different predictions. Giving CST a richer memory or more flexible reporter is not a fair comparison. The general evaluation–schema–inquiry loop is not implemented by placing separate demonstrations beside one another. The source paper retains full channels, recovery settings and limits. No new simulation or participant study is reported here.

## Tests aimed at graded correspondence

A glass holding exactly 200 mL out of 250 has known fill fraction 0.8. Under the stipulated proportional rule that is a precise intermediate value; the crisp brim-full condition is false. Obscuring the amount introduces uncertainty without changing the interpreted property.

A proposed task independently varies degree and evidence quality, checks understanding and elicits estimates plus an appropriate uncertainty measure. Transfer to new containers and combinations is more informative than repeating a taught number. Ordinary “full” should be investigated separately from taught semantics.

Concept combinations challenge simple operations on isolated memberships.[6] Moreover, Cremers and Kalvelyte found a tested fuzzy model whose predictions were also available to an uncertain-threshold account under specified assumptions.[17] The next design should vary those assumptions rather than repeatedly compare equivalent models. Intermediate averages can arise from mixtures of binary answers or genuine intermediate estimates; a useful model predicts more than the average.

A “nearly full” sequence can compare estimates, categorical reports, local comparisons and checking. The philosophical companion's Łukasiewicz illustration is a coherent formal instance, not an experimentally selected neural connective. Strong conjunction, weak conjunction and quantification have distinct meanings. Behavioral thresholds, noise and changed interpretation remain viable alternatives.

## Can a diagnosis improve the next question?

Two people disagreeing about whether a system is reliable may mean different properties, have different reports, infer different deployment risks or accept different trade-offs. A profile should admit mixtures and insufficient information. Different meanings may themselves express a substantive dispute over which concept should govern.[9]

Existing approaches already organize such inquiry. Communication repair targets the source of misunderstanding,[10] while Double Crux looks for considerations that would change a belief. It allows partial or multiple cruxes, not just one decisive proposition in every dispute.[19] Taboo Your Words is another predecessor for unpacking language. CST does not originate those practical moves.

The proposed information-level test asks whether independently elicited grounds and conditions improve choice of an intervention beyond verdicts and confidence. Compare targeted clarification, source exchange or assumption testing with equally resourced generic and strong existing methods. Validate intended differences, include mixed and unfamiliar cases, and fix the diagnostic rule before repair outcomes are known.

Elicitation can itself help. Selectors must receive the same information, with elicitation held constant or studied separately. Beating an information-poor baseline only establishes the value of more information. Use held-out people and content and assess outcomes independently of the diagnostic labels.

Score comprehension, diagnostic calibration, independent accuracy where assessable, costs and faithful identification of the remaining dispute. A well-understood value conflict can remain unresolved; a mistaken consensus is not success. A newly negotiated question must not be counted as both parties updating the original proposition.

A separate mechanistic test must ask whether a specified condition-bearing representation predicts inquiry and updating better than matched memory, grounding and metacognitive rivals. Qualifier reminders need comprehension and retrieval controls. No incremental prediction, no selective benefit of matched repair or an equally good simpler account limits the corresponding claim. The diagnostic note specifies proposals, not a completed extension of the mixture model.

## When evaluation serves other purposes

The preceding comparisons begin with useful assessment: estimating the relevant value, retaining grounds and choosing informative checks. An error in any of those operations is one way felt correctness can depart from accuracy. Social modulation raises a further question: what happens when an assessment also serves persuasion, affiliation or commitment? That question does not follow from the existence of semantic degrees.

Persuasion opportunities have affected privately elicited confidence,[7] but the mechanism remains contested. Zhang and Rand found similar self-persuasion under persuasion and summary tasks, supporting exposure to one side as an alternative to a uniquely persuasion-driven explanation.[15] Equal available evidence is not necessarily equal processing. A test of motives should match or independently manipulate exposure and effort.

Public commitment also differs from refusal to investigate. Jordan and Kteily found reputational benefits to considering opposing evidence before punishment.[16] An audience observing only an action may reward something different from one observing how the decision was reached. These findings do not collectively establish one moderator interaction; they identify conditions a new design should manipulate. Social influence can support inquiry as well as discourage it.

A bounded study could vary a commitment opportunity against accuracy or learning goals, control interpretation and evidence, and separately measure private estimates, public statements and information seeking. Counterbalanced order or separate groups can reduce manufactured consistency. A public-only effect supports a different conclusion from a change in private assessment or checking.

Moral conviction, perceived objectivity and confidence are not one variable. On the physicalist account, social learning operates through biological systems; an evolutionary explanation asks how their sensitivities developed. Evolutionary models identify conditions under which a strategy pays,[8] not the historical selection of a CST-specific representation. Asymmetric error costs can change an action threshold without changing a belief. Present incentives, cultural learning and evolutionary origins may interact but need distinct evidence. The proposed within-session study tests a proximal response, not evolutionary history.

## Known limitations and open questions

Graded semantics, an assessment model and a useful disagreement method are separate commitments. Their general ingredients have substantial prior work; the proposed contribution is in explicit integration and discriminating constraints. The full update and inquiry policy remain unspecified, and the worked response model remains exactly compatible with selective access.

The practical method is unvalidated, including elicitation and measurement effects. Contrary results on rightness, exposure and inquiry are therefore design constraints, not inconvenient findings to set aside. Formal value preservation does not select a semantics for every utterance or establish a cognitive mechanism. This applies equally to the assessment that CST itself is persuasive.

## Sources

[1] [Graziano and Webb (2015), The attention schema theory](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2015.00500/full).

[2] [Schulz et al. (2023), Metacognitive computations for information search](https://pubmed.ncbi.nlm.nih.gov/36757948/).

[3] [Fleming and Lau (2014), How to measure metacognition](https://doi.org/10.3389/fnhum.2014.00443).

[4] [Momennejad et al. (2017), The successor representation in human reinforcement learning](https://www.microsoft.com/en-us/research/publication/the-successor-representation-in-human-reinforcement-learning/).

[5] [Fleming and Daw (2017), Self-evaluation of decision-making](https://pubmed.ncbi.nlm.nih.gov/28004960/).

[6] [Hampton (1997), Conceptual combination](https://pubmed.ncbi.nlm.nih.gov/9421575/).

[7] [Schwardmann and van der Weele (2019), Deception and self-deception](https://epub.ub.uni-muenchen.de/78222/).

[8] [Johnson and Fowler (2011), The evolution of overconfidence](https://www.nature.com/articles/nature10384).

[9] [Plunkett and Sundell (2013), Disagreement and the Semantics of Normative and Evaluative Terms](https://researchportalplus.anu.edu.au/en/publications/disagreement-and-the-semantics-of-normative-and-evaluative-terms/) — Author abstract.

[10] [Dingemanse et al. (2015), Universal Principles in the Repair of Communication Problems](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0136100).

[11] [Nelson and Narens (1990), Metamemory](https://sites.socsci.uci.edu/~lnarens/1990/Nelson%26Narens_Book_Chapter_1990.pdf).

[12] [Mangan (2001), Sensation's Ghost](https://www.researchgate.net/publication/247487522_Sensation%27s_ghost_The_non-sensory_fringe_of_consciousness).

[13] [Sperber et al. (2010), Epistemic Vigilance](https://discovery.ucl.ac.uk/id/eprint/1331363/1/Wilson_Epistemic%20Vigilance%20revised%20final.pdf).

[14] [Wang and Thompson (2019), Fluency and Feeling of Rightness](https://pt.ffri.hr/index.php/pt/article/view/518).

[15] [Zhang and Rand (2025), Self-persuasion does not imply self-deception](https://pubmed.ncbi.nlm.nih.gov/40505337/).

[16] [Jordan and Kteily (2023), How reputation does (and does not) drive people to punish without looking](https://pubmed.ncbi.nlm.nih.gov/37406099/).

[17] [Cremers and Kalvelyte (2024), An Empirical Comparison of Semantics for Quantified Vague Sentences](https://www.journals.vu.lt/problemos/article/view/38284/35927).

[18] [Smith (2014), Vagueness, Uncertainty and Degrees of Belief](https://www.njjsmith.com/philosophy/papers/SmithVaguenessUncertaintyDegreesBelief.pdf).

[19] [Sabien (2017), Double Crux—A Strategy for Mutual Understanding](https://www.lesswrong.com/posts/exa5kmvopeRyfJgCy/double-crux-a-strategy-for-mutual-understanding).

## Explore with an AI tutor

[Open ChatGPT](https://chatgpt.com/) or [Open Claude](https://claude.ai/new), then copy the prompt below. These links open a service only: they do not attach this essay, prefill a request, or submit it. Supply only text you are entitled and comfortable to share. Treat the answer as a reading aid, not validation of CST.

> Ask me to paste a passage. Explain one model and the observation that could distinguish it from a matched rival. Check parameter meanings, measurement assumptions and observational equivalence. Separate numerical illustrations from human findings and prior work from the proposed addition. Do not run simulations or invent data.

## Reading path

[Start with the shared introduction](introduction.html) · [Read Cognitive Science I first](cognition-1.html) · [Optional formal background: Philosophy II](philosophy-2.html) · [All five essays and companion-work status](./)
