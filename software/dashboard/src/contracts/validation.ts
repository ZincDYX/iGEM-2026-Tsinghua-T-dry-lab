import * as validators from "./public.validators.generated.js";

// Infer the public types from generated type predicates: the schema registry
// is authoritative, so a second handwritten list cannot drift behind it.
type Validated<F> = F extends (value: unknown) => value is infer T ? T : never;
export type Protocol = {
  [K in keyof typeof validators]: Validated<(typeof validators)[K]>;
};
export function parsePublic<K extends keyof Protocol>(
  name: K,
  value: unknown,
): Protocol[K] {
  const validate = validators[name];
  if (!validate(value))
    throw new Error(
      `Public protocol ${name}  is incompatible; no defaults or predictions were generated.`,
    );
  // Ajv runtime validated against the schema generated from this exact type.
  return value as Protocol[K];
}
export function parseList<K extends keyof Protocol>(
  name: K,
  value: unknown,
): Protocol[K][] {
  if (!Array.isArray(value))
    throw new Error("Incompatible public list protocol.");
  return value.map((item) => parsePublic(name, item));
}
export function object(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
