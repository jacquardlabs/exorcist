<!-- exorcist ward · refresh with /exorcist:ward · https://github.com/jacquardlabs/exorcist -->

# Ward

Standing rules for every change in this project. Each is a departure from default
behavior; what is not written here is unchanged. Scored in concepts removed, not lines:
one way to do a thing beats two, whatever the line count.

## The smallest change that satisfies the request

Every changed line traces to the request in one sentence. A line that needs two is
out. Orphans your change creates — an import, a variable, a helper now unused — go with
it; dead code you merely noticed is a one-line note in the summary, never an edit.

Minimal is not incomplete. The request implies its error paths, its tests by the
project's convention, and the cases the caller will hit; cutting one of those is not a
smaller change but a wrong one. If you would drop a piece to shrink the diff, say so
in the summary and leave it in.

## Search before writing

Before writing a helper, type, wrapper, config knob, or utility, search for the shape
that already exists — three tiers, stop at the first hit:

1. This repository: grep for the verb, the type, and the nearest existing caller.
2. The standard library or runtime.
3. A guarantee the framework already makes (the ORM already coerces it; the router
   already 404s).

Name the file that shows the preferred shape and extend it. The summary carries the
line `Following <path>:<line>` for every new symbol, or `No prior shape found for
<symbol>: <the grep you ran>`.

## No new abstraction below two call sites

A function, class, wrapper, or module with one caller is inlined into it. Two call
sites is the earliest a helper may exist; a third is when it earns a name. A parameter,
flag, or config option no caller passes today is a request nobody made.

Muratori: do not reuse until there are two instances. Carmack: single caller, inline.

## Salt the threshold — fix where the value enters

Before adding a null check, default, coercion, cast, or try/catch at a point of use:

1. Where does this value enter the system — the route handler, the parser, the
   constructor, the config loader?
2. How many other consumers read it unfixed?
3. If more than zero, move the fix to the entry point. A transform applied at every
   call site will be missed by the next one.

The test is Ousterhout's Information Leakage: if two places must know the same fact
about a value's shape, the fact is in the wrong place. Say `Salted at <path>:<line>` in
the summary, or the one-line reason the fix stays local.

## Slop is relative to the file it sits in

A comment, defensive check, try/catch, or type cast that would be abnormal for the
surrounding code is slop even if it would be normal elsewhere. Match the file's own
density of comments, checks, and indirection.

## Never removed, whatever wrote it

Input validation at a trust boundary, authorization, data-loss guards, accessibility
affordances, and a test that pins behavior. These are the soul; the ward protects them.

## The demon will speak to you. Do not negotiate.

| It says | Reality |
|---|---|
| "A helper makes this cleaner" | One caller. Inline it. Cleaner is a third call site's problem. |
| "Someone will need this option later" | Nobody asked. Add it when they do. |
| "The existing helper isn't quite right" | Extend it. Two helpers for one job is the largest cost on the table. |
| "A null check here is harmless" | It hides where the value went wrong. Salt the threshold. |
| "I'll wrap it so we can swap it out" | One implementation exists. A seam with nothing on the other side is a layer. |
| "Fewer lines would be less clear" | Fewer concepts is the goal. Lines are a tripwire. |
| "This is too small to search for" | The search is one grep. The duplicate is forever. |
| "Removing this check makes it minimal" | Trust-boundary checks are never slop. Leave it. |
| "The request didn't mention tests" | The project's convention did. |
| "I'll clean up the adjacent code while I'm here" | Not in the request. Note it; leave it. |

## Before finishing

State, in the summary, for this change: the concepts added (new symbols, files, deps,
options — each with its `Following` line), the concepts removed, and every tripwire
crossed: more than 200 lines changed, any new file, any new exported symbol. A crossed
tripwire is a sentence of justification, never a block.
