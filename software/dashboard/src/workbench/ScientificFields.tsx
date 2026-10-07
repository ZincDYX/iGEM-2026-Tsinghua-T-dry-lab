import type { ProjectView } from "../contracts/generated";
type AssetIdentity = ProjectView["files"][number];
import { useState } from "react";

// One small editor for less-common fields and initial setup. The backend's
// existing Pydantic schema supplies choices/types; it never supplies form values.
export type FieldSchema = {
  $ref?: string;
  $defs?: Record<string, FieldSchema>;
  type?: string;
  format?: string;
  title?: string;
  const?: unknown;
  enum?: unknown[];
  anyOf?: FieldSchema[];
  properties?: Record<string, FieldSchema>;
  required?: string[];
  items?: FieldSchema;
  additionalProperties?: boolean | FieldSchema;
  minimum?: number;
  maximum?: number;
  minLength?: number;
  description?: string;
  readOnly?: boolean;
};
export function ScientificFields({
  schema,
  definitions,
  value,
  onChange,
  path,
  files,
}: {
  schema: FieldSchema;
  definitions: Record<string, FieldSchema>;
  value: unknown;
  onChange: (v: unknown) => void;
  path: string;
  files: AssetIdentity[];
}) {
  if (schema.readOnly)
    return (
      <p>
        {path}:{" "}
        <output aria-label={path}>
          {value === undefined || value === null
            ? "Not recorded"
            : JSON.stringify(value)}
        </output>
      </p>
    );
  if (schema.$ref)
    return (
      <ScientificFields
        {...{ definitions, value, onChange, path, files }}
        schema={definitions[schema.$ref.split("/").at(-1)!]}
      />
    );
  const choice = schema.anyOf?.filter((s) => s.type !== "null");
  if (choice)
    return (
      <UnionField
        {...{ schema, definitions, value, onChange, path, files }}
        choices={choice}
      />
    );
  if (schema.properties) {
    const row = (value ?? {}) as Record<string, unknown>;
    const entries = Object.entries(schema.properties);
    const fields = (rows: typeof entries) =>
      rows.map(([key, child]) => (
        <div key={key}>
          {schema.required?.includes(key) && <small>Required: {key}</small>}
          <ScientificFields
            {...{ definitions, files }}
            schema={child}
            path={path + "." + key}
            value={row[key]}
            onChange={(v) => {
              const next = { ...row };
              if (v === undefined) delete next[key];
              else next[key] = v;
              onChange(next);
            }}
          />
        </div>
      ));
    return (
      <fieldset>
        <legend>{path}</legend>
        {fields(entries.filter(([key]) => schema.required?.includes(key)))}
        <details>
          <summary>Additional {path} fields</summary>
          {fields(entries.filter(([key]) => !schema.required?.includes(key)))}
        </details>
      </fieldset>
    );
  }
  if (schema.type === "array") {
    const rows = (value ?? []) as unknown[];
    return (
      <details>
        <summary>
          {path} ({rows.length})
        </summary>
        {rows.map((v, i) => (
          <div key={i}>
            <ScientificFields
              {...{ definitions, files }}
              schema={schema.items!}
              path={path + "." + i}
              value={v}
              onChange={(next) =>
                onChange(rows.map((r, j) => (i === j ? next : r)))
              }
            />
            <button onClick={() => onChange(rows.filter((_, j) => j !== i))}>
              Remove {path} {i + 1}
            </button>
            <button
              disabled={i === 0}
              onClick={() => {
                const next = [...rows];
                [next[i - 1], next[i]] = [next[i], next[i - 1]];
                onChange(next);
              }}
            >
              Move {path} {i + 1} up
            </button>
          </div>
        ))}
        <button
          onClick={() =>
            onChange([
              ...rows,
              schema.items?.type === "object" || schema.items?.$ref
                ? {}
                : schema.items?.type === "array"
                  ? []
                  : "",
            ])
          }
        >
          Add {path} item
        </button>
      </details>
    );
  }
  if (schema.type === "object") {
    const rows = (value ?? {}) as Record<string, unknown>,
      child =
        typeof schema.additionalProperties === "object"
          ? schema.additionalProperties
          : {};
    return (
      <details>
        <summary>
          {path} ({Object.keys(rows).length} entries)
        </summary>
        {Object.entries(rows).map(([key, v]) => (
          <div key={key}>
            <ScientificFields
              {...{ definitions, files }}
              schema={child}
              path={path + "." + key}
              value={v}
              onChange={(next) => onChange({ ...rows, [key]: next })}
            />
            <button
              onClick={() => {
                const next = { ...rows };
                delete next[key];
                onChange(next);
              }}
            >
              Remove {path}.{key}
            </button>
          </div>
        ))}
        <DictionaryKey
          path={path}
          existingKeys={Object.keys(rows)}
          onAdd={(key) => {
            onChange({ ...rows, [key]: "" });
          }}
        />
      </details>
    );
  }
  if (!schema.type && schema.const === undefined && !schema.enum)
    return (
      <ArbitraryField {...{ definitions, value, onChange, path, files }} />
    );
  const attributes = { "data-input-path": path, "aria-label": path };
  if (schema.const !== undefined || schema.enum || schema.type === "boolean") {
    const options =
      schema.enum ??
      (schema.const !== undefined ? [schema.const] : [true, false]);
    return (
      <label>
        {path}
        <select
          {...attributes}
          value={value === undefined || value === null ? "" : String(value)}
          onChange={(e) =>
            onChange(
              e.target.value === ""
                ? undefined
                : options.find((v) => String(v) === e.target.value),
            )
          }
        >
          <option value="">Not declared</option>
          {options.map((v) => (
            <option key={String(v)} value={String(v)}>
              {String(v)}
            </option>
          ))}
        </select>
      </label>
    );
  }
  if (schema.format === "path")
    return (
      <label>
        {path}
        <select
          {...attributes}
          value={String(value ?? "")}
          onChange={(e) => onChange(e.target.value || undefined)}
        >
          <option value="">Choose registered file</option>
          {files.map((f) => (
            <option key={f.id} value={f.path}>
              {f.name}
            </option>
          ))}
        </select>
      </label>
    );
  return (
    <label>
      {path}
      <input
        {...attributes}
        type={
          schema.type === "number" || schema.type === "integer"
            ? "number"
            : "text"
        }
        step={schema.type === "integer" ? 1 : "any"}
        min={schema.minimum}
        max={schema.maximum}
        value={value === undefined || value === null ? "" : String(value)}
        onChange={(e) =>
          onChange(
            e.target.value === ""
              ? ""
              : schema.type === "number" || schema.type === "integer"
                ? e.target.valueAsNumber
                : e.target.value,
          )
        }
      />
    </label>
  );
}

function UnionField(
  props: Parameters<typeof ScientificFields>[0] & { choices: FieldSchema[] },
) {
  const { schema, choices, value, onChange, path } = props;
  const [mode, setMode] = useState(
    choices.findIndex((s) => s.type === typeof value),
  );
  const selected = choices[mode >= 0 ? mode : 0],
    nullable = schema.anyOf!.some((s) => s.type === "null");
  return (
    <div>
      {nullable && (
        <label>
          <input
            type="checkbox"
            checked={value !== null && value !== undefined}
            onChange={(e) =>
              onChange(
                e.target.checked
                  ? selected.type === "object" || selected.$ref
                    ? {}
                    : selected.type === "array"
                      ? []
                      : ""
                  : null,
              )
            }
          />
          Declare {path}
        </label>
      )}
      {choices.length > 1 && (
        <label>
          {path} value type
          <select
            value={mode >= 0 ? mode : 0}
            onChange={(e) => {
              setMode(Number(e.target.value));
              onChange("");
            }}
          >
            {choices.map((s, i) => (
              <option key={i} value={i}>
                {s.type}
              </option>
            ))}
          </select>
        </label>
      )}
      {(!nullable || (value !== null && value !== undefined)) && (
        <ScientificFields {...props} schema={selected} />
      )}
    </div>
  );
}
function ArbitraryField(
  props: Omit<Parameters<typeof ScientificFields>[0], "schema">,
) {
  const { value, onChange, path } = props;
  const initialType =
    value === null
      ? "null"
      : Array.isArray(value)
        ? "array"
        : typeof value === "object"
          ? "object"
          : typeof value === "number"
            ? "number"
            : typeof value === "boolean"
              ? "boolean"
              : "string";
  const [type, setType] = useState(initialType);
  return (
    <div>
      <label>
        {path} explicit value type
        <select
          value={type}
          onChange={(e) => {
            setType(e.target.value as typeof initialType);
            onChange(
              (
                {
                  object: {},
                  array: [],
                  number: "",
                  boolean: "",
                  null: null,
                  string: "",
                } as Record<string, unknown>
              )[e.target.value],
            );
          }}
        >
          {["string", "number", "boolean", "object", "array", "null"].map(
            (t) => (
              <option key={t}>{t}</option>
            ),
          )}
        </select>
      </label>
      {type !== "null" && (
        <ScientificFields
          {...props}
          schema={{ type, additionalProperties: {}, items: {} }}
        />
      )}
    </div>
  );
}
function DictionaryKey({
  path,
  onAdd,
  existingKeys,
}: {
  path: string;
  onAdd: (key: string) => void;
  existingKeys: string[];
}) {
  const [key, setKey] = useState("");
  return (
    <div>
      <label>
        {path} new key
        <input value={key} onChange={(e) => setKey(e.target.value)} />
      </label>
      <button
        disabled={!key.trim() || existingKeys.includes(key.trim())}
        onClick={() => {
          onAdd(key.trim());
          setKey("");
        }}
      >
        Add {path} entry
      </button>
    </div>
  );
}
