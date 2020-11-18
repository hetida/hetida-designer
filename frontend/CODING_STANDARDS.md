# hetida designer Frontend - Coding Standards

TODO: Add more examples - we'll add those on-the-fly when we find and repair
instances of bad code.

Our most important code style rule is: **Write code for humans.** Make your code
as readable, maintainable and debuggable as possible. Rather than sticking to the
letter of rigid coding standards ask yourself: "What is the solution that provides
most benefit to our users with the lowest total cost of ownership?"

The following document provides some hints of what we consider maintainable code.

- [General Coding Practices](#general)
- [Specific Code Rules](#specific)
- [Low level coding style](#low-level)
- [UI Components, HTML, CSS](#ui)
- [Global State and Services](#state)

We know that our codebase does not yet always consistently follow these code rules
for historical reasons. Help us to improve by contributing
[your first pull request](../CONTRIBUTING.md)!

## <a name="general"></a> General Coding Practices

Some high-level heuristics:

- **Simplicity matters!** Apply [Ockham's Razor](https://en.wikipedia.org/wiki/Occam%27s_razor)
  and the [KISS principle](https://en.wikipedia.org/wiki/KISS_principle) wherever
  possible. Always ask yourself "What is the problem I'm trying to solve?". Often
  simple if "boring" concepts solve the problem better than complex, over-engineered
  solutions. Follow the principle of least surprise and avoid premature optimization.
  Most of the time the performance impact of ad-hoc optimizations is imperceptible
  but the readability and complexity disadvantage of prematurely optimized code
  is real. Prefer readable and well organized code over highly sophisticated
  "smart code" that is especially terse, uses obscure language features or shaves
  off a few processor cycles unless there is a well-defined and measurable business
  advantage to it that warrants the additional complexity. Finding simple solutions
  to complex problems is difficult and often means going through some experimentation
  and refactoring cycles. Unnecessary complexity represents technical debt that someone
  else will have to pay in the future.

- **Consistency matters!** If you see that someone has introduced some kind of
  principle, example or coding style before you then you have two choices: either
  follow the existing principle or refactor everything to be consistent with the
  principle you think is better. We usually prefer the former as it causes less
  disruption and potential for regression. Introducing additional inconsistency
  is not an option. It means that whoever learns the code has to learn multiple
  solutions to the same problem. No alleged local improvement is good enough to
  overcome the maintainability and complexity disadvantage of inconsistency.
  Contributions that make the code more consistent, simpler and thereby more
  readable are welcome. They may be a great way to familiarize yourself with the
  code base. Just make sure you contact us beforehand so that we agree on a
  common understanding on what is considered "more consistent".

- **Names matter!** Consciously spend time on naming files, functions, variables,
  components, types, etc. such that others associate the right concepts on first
  read. Specific names are better than generic names. Avoid synonyms for a single
  concept. We prefer self-explanatory code over inline comments.

- **APIs matter!** Consistently structure your code into directories, files, classes,
  functions, blocks, etc. as all of these represent some kind of conceptual
  encapsulation (module, interface, API, ...) that help others to understand
  what's going on generally without having to concern themselves with implementation
  details. It is good practice to introduce well-named intermediate functions
  or variables as a self-documenting internal API that explains what you are doing.
  Use established coding patterns and algorithms that can be recognized
  by other experienced programmers. Think well about APIs - even internal ones -
  as bad encapsulation tends to strongly impact maintainability. The better you
  understand the problem domain the easier it will be to write well-encapsulated
  code.

- **State representation matters!** Think hard how you model state. State should be
  as local as possible - prefer component state over global ngrx state if possible,
  especially when representing transient UI state. Only put into global state what
  you'd also persist to a shared database table. State should represent well-known
  real-world entities. These tend to be extensible and easy to reason about. Prefer
  derived functional views of state and declarative programming patterns over
  redundancy and imperative programming patterns. Never cache intermediate
  results unless you can prove that the resulting performance optimization is
  required to solve some real business problem. Make sure you normalize your state
  by introducing references (in memory or via instance ids) rather than duplicating
  state. Both, functional derivation and state normalization, help you to maintain
  a "single point of truth" for each piece of information. This protects us from
  hard-to-debug and hard-to-reason-about race conditions. Knowledge of the
  [flux](https://facebook.github.io/flux/docs/in-depth-overview) aka
  [CQRS](https://docs.microsoft.com/en-us/azure/architecture/patterns/cqrs#solution) pattern
  and [normalization formalisms](https://en.wikipedia.org/wiki/Database_normalization)
  will be helpful.

- **Decoupling matters!** Avoid premature abstraction - only consolidate code along
  the [DRY principle](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) if you
  express a well-founded business or programming concept rather than an accidental
  similarity. Never centralize concepts that may be re-used some time in the future
  unless actual re-use is already present in the code base. Prefer redundancy
  ("copy & own ") if unsure. Introduce concepts after they emerge in your code
  rather than upfront based on theory. Prefer composition over inheritance. Beware
  of prematurely introduced "decoupling layers" as they often do the contrary to
  what they promise. They may cause unnecessary indirection and abstraction that
  is hard to reason about. The agile method puts clean, conceptual code center
  stage but never introduces concepts before they are needed. If you have to
  introduce coupling then make it as easy as possible to discover. People should
  never be frightened to change code because it is unclear what might break.

We know that our codebase does not yet follow these guidelines everywhere. You are
very welcome to help us make it simpler, more consistent, better structured, more
declarative, more readable and thereby easier to extend and maintain!

## <a name="specific"></a> Specific Code Rules

### <a name="low-level"></a> Low-level coding style (whitespace, newlines, parentheses, braces, etc.)

We use prettier, tsc and tslint in combination with husky to enforce low-level
coding style. We mostly use the default configuration of these tools following the
principle of least surprise. We use tslint rather than eslint as Angular still does
not have full eslint support. We'll switch to eslint as soon as it is officially
supported by the Angular team.

We believe that low-level coding style rules have little impact on maintainability
as long as they are implemented consistently. We therefore do not document low level
rules separately - please configure your IDE and shell to enforce low-level rules
consistently and automatically. Be sure that you don't change whitespace or line
endings unless required by automatic formatting. Large non-functional whitespace
changes make it unnecessarily difficult to identify the original author of a given line
of code.

When it comes to low-level naming patterns (lower case vs. upper case, camel case
vs. underscores, etc.) or other low-level aspect of coding style that is not automatically
kept consistent by our tooling then please follow the established practice of surrounding
code. If you see any inconsistencies then use the pattern that is most common in the
code base, thereby helping us to make our code more consistent over time.

### <a name="ui"></a> UI Components, HTML and CSS

Following our general coding practices, we try to keep components, HTML markup and
CSS styles as simple, readable and well-encapsulated as possible. The following
guidelines are ordered by priority - with the most important rule first:

#### 1. Build well-encapsulated Angular components.

Structure the UI into **well encapsulated Angular components**. Choose real-world
concepts to name your components and choose component properties that fit
component or domain concepts. Do not leak implementation details through
APIs above or below your component's abstraction level. Try to avoid the
need to expose APIs via methods of the component instance. Avoid injection
via component or view injectors. Both, instance APIs and component/view injection,
tend to break encapsulation.

Public component methods and variables which are used **in the template only** have
to be prefixed by an underscore (`_`). They must not be referred to from outside the
component.

Forward events and data via **one-way component properties** whenever possible as
these provide a clean component API that is highly readable and maintainable.
Avoid two-way binding. Whenever possible follow the flux pattern by separating
events (callbacks), local/global state updates and data inputs.

**Avoid custom directives** - especially when these rely on implementation details
of the host component. Directives tend to couple to their host environment
via badly documented APIs thereby breaking encapsulation.

**Prefer keeping component state local** whenever possible and pass it to child
components via one-way binding to avoid redundant state. Only resort to ngrx if
sharing well-defined global domain concepts across several components. If you
see that you are creating properties just to pass through state across several
component layers and therefore create properties that actually don't fit the
components' concept then ngrx may be the right tool to inject state into the
middle of a component hierarchy.

**Keep your global state and component state normalized** and access it via methods
from the template that calculate any derivations and denormalizations on the fly.

Try to **avoid imperative state updates** as they tend to go against the
grain of Angular's change detection algorithm. Use functional/declarative patterns
instead. A single user interaction should trigger a single state update via
callbacks which will then be resolved to an updated DOM in a single change
detection loop. A DOM update should never trigger further events or secondary
state updates. Such code easily produces race conditions and is hard to debug
and reason about.

Whenever your template, component stylesheet or component code becomes too long
or too complex, **consider creating sub-components**. Use opportunities
to improve encapsulation and readability by keeping [layout, application logic and presentational
concerns](https://www.madebymike.com.au/writing/css-architecture-for-modern-web-applications/)
apart. But don't go overboard - keep component structure as simple as possible,
do not prematurely cater for re-usability, do not introduce unnecessary abstraction
or superfluous decoupling layers just to stick to some architectural principle
by the letter! Simplicity and maintainability always beat architectural "cleanliness".

#### 2. Prefer Angular Material over custom components/styles.

We use [Angular Material](https://material.angular.io/) rather than rolling
our own low-level component library. Whenever possible use Angular Material
to simplify your markup and stylesheet. Prefer using Material's standard design
over custom styling if possible.

#### 3. Keep your CSS styles as local as possible.

**Always keep component specific styling within the component stylesheet.**

Within your component template choose wisely between a **utility-first** and a
more **semantic BEM** approach. If your styling can be expressed with a few generic
utility classes (usually up to 3 per element) without negatively impacting
readability of your template, then prefer the utility-first approach. Introduce
local semantic classes following [BEM notation](http://getbem.com/introduction/)
if it improves readability of your code or removes local duplication. Use
well-chosen block, element and modifier names to document the structure of
your markup. Be especially aware of premature abstraction when using BEM.
Never introduce artificial class names that do not represent real world concepts
from the problem domain - [if in doubt stick to the utility-first
approach](https://adamwathan.me/css-utility-classes-and-separation-of-concerns/).

Never introduce additional utility classes or global BEM just to solve a local
problem. If in doubt prefer local redundancy over global coupling.

#### 4. If you have to override global styles, prefer keeping your overrides local.

Try to avoid the need for global overrides of the Angular Material framework
as much as possible. Try to customize Angular Material components by applying
styles to the root element within your component-specific stylesheets first.
If you absolutely have to override internal styles of Material components or
you need access to global SCSS theming variables then do so by introducing an
SCSS-partial that is co-located with your component:

```shell script
.../
 your-component/
   your-component.component.ts
   your-component.component.html
   your-component.component.scss
   _your-component.component.theme.scss # <-- co-located theming/overrides
```

Within the theming file, expose a single SCSS mixin, like this

```scss
@mixin your-component-theme($primary, $secondary) {
 // Wrap your component-specific overrides into a unique block name class.
 .your-component {
   // Use BEM nomenclature to make your overrides more readable if
   // possible.
   &__some-element {
     // The $primary and $secondary SCSS variables provide access
     // to the theme-specific primary and secondary color palette.
     .mat-button-toggle {
       background-color: map-get($secondary, 700);
       ...
     }
   }
 }
}
```

Include your mixin within the global Angular Material theming partial.

```scss
// In /src/style/material/_theme.scss:
...
@include your-component-theme($primary, $secondary);
...
```

Use this approach even if your styles do not need access to theming variables.
Just create a mixin without parameters in that case. This will lead to duplicate
styles per theme in the browser. Unless you introduce thousands of styling
rules (which you won't) the resulting performance impact is negligible, though.
Beware of premature optimization.

While this technique is technically equivalent to a global override, it uses
directory structure and class scope to maintain encapsulation in practice. It
also sets up a "pit of success" in the sense that SCSS compilation will stop
working with a useful error message if you remove or rename the component and
forget to also remove/rename the mixin from the global theming file. Thereby
we avoid dead code and central coupling when a component is removed or needs
to be changed.

#### 5. As a last resort: use global styles

If none of the above solves your problem then - as a last resort - you may
introduce global overrides for Angular Material (or other low-level design
frameworks) or global BEM blocks.

Globally shared variants of Material components can be introduced with modifiers
that include the name of the Material component followed by two dashes and then
a readable modification name, e.g. `mat-button--small`.

If you really think that you have introduced a duplication of styles that can
be maintained more easily by introducing a global concept then you may use a
global block name class instead.

Never introduce central coupling to some abstract or generic CSS class unless
such coupling is easy to discover. Try to avoid generic global class names
that cannot be easily searched for across the whole codebase.

Global overrides and BEM blocks may only be introduced if they actually generate
re-use across several components. Never introduce global styling just because you
believe that it might be useful to others in the future. That re-use will never
happen.

### <a name="state"></a> Global State (ngrx) and Services

Global state and services introduce global coupling and should be avoided by default.
Think of them in the same way as you think of global variables (i.e. `windows.something`).

Where global state cannot be avoided it should be kept in ngrx rather than hidden
in variables inside services. Most of the time ngrx should only be used to keep
cached copies of the server state as an optimization to avoid server roundtrips
during change detection.

Transient local UI state is almost never legitimately kept in ngrx or services. Ask
yourself whether it would make sense to persist a given piece of information into
a database across application invocations. If not then probably your state should
be kept within a component rather than placed into global state. Only put UI state
into ngrx if passing it through intermediate component properties breaks component
encapsulation.

Global state should not represent the structure of the server's denormalized REST
API but rather represent a normalized version of the server's externally visible
data model. Normalize entities following the same best practices that you would
apply to a relational database to maintain data integrity. Keep a single point of
truth for each piece of information by using references via ids rather than duplicating
instances of dependent entities.

Each entity is represented in the store's state by a single top-level key named
after the entity. Reducers, actions, selectors and types belonging to an entity
are kept in a single folder also named after the entity. You may use `@ngrx/entity`
to maintain the entity state. If you need to keep additional meta-information about
an entity (e.g. loading state) then other sub-keys may be introduced into the entity's
state key (e.g. "loadingState" vs. "data"). Entity instances are kept in a hash which
is indexed by entity instance ID. The order of entities is given by an array of all
ids.

Actions should contain the entity name and should have CRUD- or REST-inspired
prefixes (e.g. "get", "add", "remove", "patch", "put", etc.).

An action must never produce an inconsistent application state even if several
asynchronous actions need to be executed in sequence. Always commit dependent
objects to the store before you commit an object that depends on it. Make sure
that on deleting an object all objects having dependencies on this object will
also be deleted.

We try to avoid having to recur to `@ngrx/effects` as effects tend to be difficult
to maintain. We rather build services that use promises or pipes to orchestrate
asynchronous actions. See https://medium.com/@m3po22/stop-using-ngrx-effects-for-that-a6ccfe186399
for some inspiration.

All access to state must be hidden behind selectors. Selectors are the right place
to denormalize and transform global state on the fly. Only build selectors to hide
the internal structure of state. Selectors are the right place to resolve dependencies
among entity instances, i.e. to replace ids by references to the dependent instance.
Transformations which are used in a single component go into that component not into
a global selector.

To avoid race conditions always us a single selector (i.e. a single observable)
per component. Generic CRUD selectors should be co-located with the central ngrx
files corresponding to the selected entity. Component specific combinations of
selectors should be placed directly into the component file or at least co-located
with the component file.

Global services - if at all necessary - should be stateless. Avoid observables other
than the ones generated by ngrx as these tend to introduce hard-to-debug race
conditions and usually break the flux/CQRS pattern. If you have to use observables
then keep your pipes stateless and side-effect free.
