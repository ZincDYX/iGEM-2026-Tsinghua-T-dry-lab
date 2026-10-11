# Separate exploratory scalar formulas

The original M1–M4 and ER equations and approval requirements are unchanged.
LaTeX is a human-readable document, not executable code. Its meaning is not
guessed or automatically translated. A separately saved executable expression
is the authoritative calculation; the user must review its correspondence to
the LaTeX, source and changed assumptions.

In Workflow → select an original module → Formulas, select the base formula,
enter the new title, LaTeX, source and assumptions. Optionally enter a scalar
expression, each input's name/value/unit/source, and the result unit. Save an
immutable version, open its history entry, and choose **Prepare exploratory
workflow**. Review the explicit inputs, Accept, then Start. Saving or preparing
does not execute. Changing a saved version creates a new version; a recorded
run retains its original expression and input values after restart.

Supported expression language: `+`, `-`, `*`, `/`, `**` with literal integer
exponents from −16 to 16, and unary `sqrt`, `exp`, `ln`, `log10`, `abs`.
No Python evaluation, imports, attributes, indexing, comparisons, conditionals,
comprehensions, arbitrary functions, summation, derivatives or ODEs. Unsupported
expressions are rejected, not simplified or approximated. Each expression must
use exactly its declared variables. Units are checked before dispatch. Log and
exp arguments must be dimensionless. Addition/subtraction require compatible
dimensions; the declared output dimension must match the expression.

Unit grammar: `1`, `M`, `mM`, `uM`/`µM`/`μM`, `nM`, `mol`, `L`, `m`, `mm`,
`um`/`µm`/`μm`, `nm`, `s`, `min`, `h`, `kg`, `g`; multiplication, division,
integer powers (`^` or `**`) and parentheses. `M` is mol/L. Values are explicitly
converted to the SI length/time/amount/mass basis, evaluated without algebraic
rewriting, and converted to the selected result unit. Mole/particle or
monomer/assembly conversions, affine temperature units and chemical identity
changes are not inferred. Sources and applicability remain the user's
responsibility; providing a source string is not scientific approval.

Division by zero, invalid real-function domains and nonfinite results fail the
node. Expression size, depth and exponents are bounded to prevent unbounded
execution. The existing workflow engine supplies immutable inputs, durable
results, recovery, cancellation and authorized export; no second scheduler or
mutable global project access is introduced.

Results show the value, unit, expression and all original inputs in Results.
Export includes the recorded method and provenance. Every result remains
`unvalidated`, `evidence_ready=false`, `exploratory_scalar_calculation`.
It does not replace an original scientific stage or grant parameter approval.

Acceptance: AST/admission, ownership and document tests can run without science.
Numerical independent unit/function/domain oracles and durable engine execution
are in `tests/test_custom_formula.py` (`scientific_algorithm`); run them on the
authorized compute machine when workstation numerical work is prohibited.

## Private external model verification

Assistant Settings use a private workspace profile, not a project or repository
configuration. A reachable API is tested for actual JSON, streaming and tool
calls independently. A failed tool-call probe is not relabeled as supported.
The current planner uses typed JSON semantic decisions plus a deterministic
compiler, not model-selected executable shell commands. Model requests remain
bounded (4096 tokens, 512 KiB response, 4 s connection / 90 s read timeout);
truncated JSON is rejected explicitly. Real model acceptance is software
protocol/planning validation, not scientific or wet-lab validation.

Do not send a bearer key directly to a public HTTP endpoint. Use public HTTPS
or an explicitly configured loopback endpoint backed by a private encrypted
tunnel. Addresses, model identifiers and secrets used for laboratory acceptance
are excluded from source, release assets, reports and the source bundle.
