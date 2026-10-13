import type { ReactNode } from "react";
import { object } from "../contracts/validation";
import { EditableValue } from "./EditableValue";

/** Positions come from the admitted execution AST. No LaTeX/DOM guessing. */
export function BoundFormula({
  tree,
  variables,
  frozen,
  onSave,
  missing = "Add data",
  actions,
}: {
  tree: Record<string, unknown>;
  variables: Record<
    string,
    { value: number; unit: string; readOnly?: boolean }
  >;
  frozen: boolean;
  onSave: (name: string, value: number, unit: string) => Promise<void>;
  missing?: string;
  actions?: (name: string) => ReactNode;
}) {
  function render(node: Record<string, unknown>, path: string): ReactNode {
    if (node.kind === "variable") {
      const name = String(node.name),
        input = variables[name];
      return input ? (
        <span className="formula-input" data-variable={name}>
          <span className="formula-symbol">{name}</span>
          <EditableValue
            name={name}
            value={input.value}
            unit={input.unit}
            frozen={frozen || input.readOnly}
            onSave={(value, unit) => onSave(name, value, unit)}
          />
          {actions?.(name)}
        </span>
      ) : (
        <span>
          {name}
          {missing ? " — " + missing : ""}
        </span>
      );
    }
    if (node.kind === "constant") return <span>{String(node.value)}</span>;
    if (node.kind === "binary" && object(node.left) && object(node.right)) {
      const left = render(node.left, path + "l"),
        right = render(node.right, path + "r");
      if (node.operator === "divide")
        return (
          <span className="formula-fraction">
            <span>{left}</span>
            <span>{right}</span>
          </span>
        );
      if (node.operator === "power")
        return (
          <span>
            ({left})<sup>{right}</sup>
          </span>
        );
      return (
        <span>
          ({left}
          <span className="formula-operator">
            {{add:'+',subtract:'−',multiply:'×'}[String(node.operator) as 'add'|'subtract'|'multiply']??'Unknown operation'}
          </span>
          {right})
        </span>
      );
    }
    if (node.kind === "unary" && object(node.argument))
      return (
        <span>
          {String(node.operator)}({render(node.argument, path + "u")})
        </span>
      );
    if (node.kind === "function" && object(node.argument))
      return (
        <span>
          {String(node.name)}({render(node.argument, path + "a")})
        </span>
      );
    return (
      <span>
        Expression display unavailable; its stored method is unchanged.
      </span>
    );
  }
  return (
    <div className="bound-formula" aria-label="Formula input values">
      {render(tree, "root")}
    </div>
  );
}
