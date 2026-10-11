import type * as validators from "./public.validators.generated.js";
import * as inputValidators from './validators.inputs.generated.js';
import {validatorLoaders} from './validatorLoaders.generated';

// Infer the public types from generated type predicates: the schema registry
// is authoritative, so a second handwritten list cannot drift behind it.
type Validated<F> = F extends (value: unknown) => value is infer T ? T : never;
export type Protocol = {
  [K in keyof typeof validators]: Validated<(typeof validators)[K]>;
};
export function parsePublic<K extends keyof typeof inputValidators>(
  name: K,
  value: unknown,
): Protocol[K] {
  const validate = inputValidators[name];
  if (!validate(value))
    throw new Error(
      `Public protocol ${name}  is incompatible; no defaults or predictions were generated.`,
    );
  // Ajv runtime validated against the schema generated from this exact type.
  return value as Protocol[K];
}
export async function parsePublicAsync<K extends keyof Protocol>(name:K,value:unknown):Promise<Protocol[K]> {
  const family=await validatorLoaders[name]();
  const validate=(family as Partial<Record<keyof Protocol,(value:unknown)=>boolean>>)[name]!;
  if(!validate(value))throw Error(`Public protocol ${name} is incompatible; no defaults or predictions were generated.`);
  return value as Protocol[K];
}
export async function parseList<K extends keyof Protocol>(
  name: K,
  value: unknown,
): Promise<Protocol[K][]> {
  if (!Array.isArray(value))
    throw new Error("Incompatible public list protocol.");
  const family=await validatorLoaders[name]();
  const validate=(family as Partial<Record<keyof Protocol,(value:unknown)=>boolean>>)[name]!;
  if(value.some(item=>!validate(item)))throw Error(`Public list protocol ${name} is incompatible.`);
  return value as Protocol[K][];
}
export function object(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}
