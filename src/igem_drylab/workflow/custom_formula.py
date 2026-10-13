"""Restricted scalar, unit-checked exploratory calculations, not formal M1–M4.

LaTeX is presentation only. Explicit expressions are interpreted as an AST,
never evaluated as Python. The existing engine owns approval, freezing and jobs.
"""
import ast
import math
from fractions import Fraction
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from .models import Contract, WorkflowError


# SI basis: length, time, amount, mass. M means mol/litre, not mol/m³.
ZERO = (Fraction(0),) * 4
UNITS = {
    'm': (1., (1, 0, 0, 0)), 'nm': (1e-9, (1, 0, 0, 0)),
    'um': (1e-6, (1, 0, 0, 0)), 'mm': (1e-3, (1, 0, 0, 0)),
    's': (1., (0, 1, 0, 0)), 'min': (60., (0, 1, 0, 0)),
    'h': (3600., (0, 1, 0, 0)), 'mol': (1., (0, 0, 1, 0)),
    'kg': (1., (0, 0, 0, 1)), 'g': (1e-3, (0, 0, 0, 1)),
    'L': (1e-3, (3, 0, 0, 0)),
    'M': (1e3, (-3, 0, 1, 0)), 'mM': (1., (-3, 0, 1, 0)),
    'uM': (1e-3, (-3, 0, 1, 0)), 'nM': (1e-6, (-3, 0, 1, 0)),
}
FUNCTIONS = {'sqrt': math.sqrt, 'exp': math.exp, 'ln': math.log,
             'log10': math.log10, 'abs': abs}


def tree(text):
    try:
        result = ast.parse(text, mode='eval').body
    except (SyntaxError, RecursionError):
        raise ValueError('formula_invalid_expression') from None
    nodes = list(ast.walk(result))
    if len(nodes) > 160:
        raise ValueError('formula_expression_too_large')
    def depth(node):
        return 1 + max((depth(child) for child in ast.iter_child_nodes(node)), default=0)
    if depth(result) > 24:
        raise ValueError('formula_expression_too_deep')
    return result


def exponent(node):
    sign = 1
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        node, sign = node.operand, -1
    if not isinstance(node, ast.Constant) or type(node.value) is not int or abs(node.value) > 16:
        raise ValueError('formula_power_requires_integer_minus16_to16')
    return sign * node.value


def expression_latex(expression):
    """Presentation of the admitted execution AST; preserve every operation."""
    def render(node):
        if isinstance(node, ast.Name):
            return r'\mathrm{' + node.id.replace('_', r'\_') + '}'
        if isinstance(node, ast.Constant): return str(node.value)
        if isinstance(node, ast.UnaryOp):
            return ('-' if isinstance(node.op, ast.USub) else '+') + r'\left(' + render(node.operand) + r'\right)'
        if isinstance(node, ast.BinOp):
            left,right=render(node.left),render(node.right)
            if isinstance(node.op,ast.Div): return r'\frac{' + left + '}{' + right + '}'
            if isinstance(node.op,ast.Pow): return r'\left(' + left + r'\right)^{' + right + '}'
            operator={ast.Add:'+',ast.Sub:'-',ast.Mult:r'\cdot'}[type(node.op)]
            return r'\left(' + left + operator + right + r'\right)'
        argument=render(node.args[0])
        if node.func.id=='sqrt': return r'\sqrt{' + argument + '}'
        if node.func.id=='abs': return r'\left|' + argument + r'\right|'
        return {'exp':r'\exp','ln':r'\ln','log10':r'\log_{10}'}[node.func.id]+r'\left('+argument+r'\right)'
    return render(tree(expression))


def expression_view(expression):
    """Read-only positions from the execution AST, not inferred from LaTeX."""
    def render(node):
        if isinstance(node, ast.Name): return {'kind':'variable','name':node.id}
        if isinstance(node, ast.Constant): return {'kind':'constant','value':node.value}
        if isinstance(node, ast.UnaryOp):
            return {'kind':'unary','operator':'-' if isinstance(node.op,ast.USub) else '+','argument':render(node.operand)}
        if isinstance(node, ast.BinOp):
            return {'kind':'binary','operator':{ast.Add:'add',ast.Sub:'subtract',ast.Mult:'multiply',ast.Div:'divide',ast.Pow:'power'}[type(node.op)],'left':render(node.left),'right':render(node.right)}
        return {'kind':'function','name':node.func.id,'argument':render(node.args[0])}
    return render(tree(expression))


def dimensions(node, names, *, unit=False):
    if (isinstance(node, ast.Constant) and type(node.value) in {int, float}
            and (not isinstance(node.value, int) or node.value.bit_length() <= 1023)
            and math.isfinite(node.value)):
        if unit and node.value != 1:
            raise ValueError('formula_unit_constant_must_be_one')
        return ZERO
    if isinstance(node, ast.Name) and node.id in names:
        return names[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)) and not unit:
        return dimensions(node.operand, names)
    if isinstance(node, ast.BinOp):
        left = dimensions(node.left, names, unit=unit)
        if isinstance(node.op, ast.Pow):
            return tuple(value * exponent(node.right) for value in left)
        right = dimensions(node.right, names, unit=unit)
        if isinstance(node.op, (ast.Mult, ast.Div)):
            sign = -1 if isinstance(node.op, ast.Div) else 1
            return tuple(a + sign * b for a, b in zip(left, right))
        if isinstance(node.op, (ast.Add, ast.Sub)) and not unit:
            if left != right:
                raise ValueError('formula_addition_unit_mismatch')
            return left
    if (not unit and isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in FUNCTIONS and len(node.args) == 1 and not node.keywords):
        value = dimensions(node.args[0], names)
        if node.func.id == 'sqrt':
            return tuple(Fraction(x) / 2 for x in value)
        if node.func.id == 'abs':
            return value
        if value != ZERO:
            raise ValueError('formula_log_exp_requires_dimensionless_argument')
        return ZERO
    raise ValueError('formula_unsupported_syntax_or_symbol')


def calculate(node, names):
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.Name):
        return names[node.id]
    if isinstance(node, ast.UnaryOp):
        value = calculate(node.operand, names)
        return -value if isinstance(node.op, ast.USub) else value
    if isinstance(node, ast.Call):
        return FUNCTIONS[node.func.id](calculate(node.args[0], names))
    left = calculate(node.left, names)
    if isinstance(node.op, ast.Pow):
        return left ** exponent(node.right)
    right = calculate(node.right, names)
    if isinstance(node.op, ast.Add): return left + right
    if isinstance(node.op, ast.Sub): return left - right
    if isinstance(node.op, ast.Mult): return left * right
    return left / right


def unit_definition(text):
    expression = tree(text.replace('µ', 'u').replace('μ', 'u').replace('^', '**'))
    dimension = dimensions(expression, {name: value[1] for name, value in UNITS.items()}, unit=True)
    scale = calculate(expression, {name: value[0] for name, value in UNITS.items()})
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError('formula_invalid_unit_scale')
    return scale, dimension


class FormulaVariable(Contract):
    value: float
    unit: str = Field(min_length=1, max_length=100)
    source: str = Field(min_length=1, max_length=2000)


class FormulaSpec(Contract):
    expression: str = Field(min_length=1, max_length=2000)
    variables: dict[str, FormulaVariable] = Field(min_length=1, max_length=64)
    output_unit: str = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def admission(self):
        if any(not name.isidentifier() or name in FUNCTIONS for name in self.variables):
            raise ValueError('formula_invalid_variable_name')
        units = {name: unit_definition(value.unit)[1] for name, value in self.variables.items()}
        expression = tree(self.expression)
        used = {node.id for node in ast.walk(expression) if isinstance(node, ast.Name)} - FUNCTIONS.keys()
        if used != self.variables.keys():
            raise ValueError('formula_variables_must_match_expression_exactly')
        if dimensions(expression, units) != unit_definition(self.output_unit)[1]:
            raise ValueError('formula_output_unit_mismatch')
        return self


class FormulaExecution(Contract):
    method_id: str
    method_version: int = Field(ge=1)
    title: str
    base_method_id: str
    base_version: str
    latex: str
    reason: str
    source_reference: str
    spec: FormulaSpec


class FormulaResult(Contract):
    schema_version: Literal['custom-formula-v1'] = 'custom-formula-v1'
    method: FormulaExecution
    value: float
    unit: str
    validation_status: Literal['unvalidated'] = 'unvalidated'
    evidence_ready: Literal[False] = False
    claim_scope: Literal['exploratory_scalar_calculation'] = 'exploratory_scalar_calculation'
    interpretation: str = 'User formula, explicit SI conversions; not an original M1–M4 result or approved evidence.'


def run_formula(payload: FormulaExecution, context):
    # Admission is repeated by the typed engine; evaluation reads only the
    # frozen payload, not mutable draft tables or the global project.
    values = {name: variable.value * unit_definition(variable.unit)[0]
              for name, variable in payload.spec.variables.items()}
    try:
        result = calculate(tree(payload.spec.expression), values) / unit_definition(payload.spec.output_unit)[0]
        if not math.isfinite(result): raise ValueError('nonfinite')
    except (ValueError, OverflowError, ZeroDivisionError):
        raise WorkflowError('formula_domain_or_nonfinite_result') from None
    return FormulaResult(method=payload,value=result,unit=payload.spec.output_unit).model_dump(mode='json')


def custom_formula_tool():
    from .tools import ToolDefinition
    return ToolDefinition('workflow.custom_formula', 'Custom scalar formula',
        'Execute a frozen, unit-checked scalar expression after workflow approval. Scientifically unvalidated; does not replace M1–M4.',
        '1', FormulaExecution, run_formula, 'exploratory_calculation',
        output_schema=FormulaResult.model_json_schema(),implementation_files=(Path(__file__),))
