import {readFile,writeFile} from "node:fs/promises";
import {compile} from "json-schema-to-typescript";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import standaloneCode from "ajv/dist/standalone/index.js";
import {build} from "esbuild";
import {fileURLToPath} from "node:url";
import {existsSync} from "node:fs";
import {join} from "node:path";
import {spawnSync} from "node:child_process";

// Regenerate the Python source schema before consuming it. Otherwise this
// command can silently produce validators for an obsolete checked-in schema.
const repository = fileURLToPath(new URL("../../..", import.meta.url));
const localPython = join(repository, ".venv", process.platform === "win32" ? "Scripts/python.exe" : "bin/python");
const python = process.env.FUSIONLAB_SCHEMA_PYTHON ?? (existsSync(localPython) ? localPython : "python");
const exported = spawnSync(python, ["-B", "scripts/generate_workbench_schema.py", "--output", "software/dashboard/src/contracts/public.schemas.json"], {
  cwd: repository,
  env: {...process.env, PYTHONPATH: join(repository, "src")},
  stdio: "inherit",
});
if (exported.error || exported.status !== 0) throw new Error("Public schema export failed; configure FUSIONLAB_SCHEMA_PYTHON with the project environment.");

const source = new URL("../src/contracts/public.schemas.json",import.meta.url);
const schemas = JSON.parse(await readFile(source,"utf8"));
const exports = [];
for (const [name,schema] of Object.entries(schemas)) {
  const output = await compile(schema,name,{bannerComment:"/* Generated from public Pydantic contracts. Do not edit. */",additionalProperties:false});
  await writeFile(new URL(`../src/contracts/${name}.generated.ts`,import.meta.url),output);
  exports.push(`export type { ${name} } from "./${name}.generated";`);
}
await writeFile(new URL("../src/contracts/generated.ts",import.meta.url),exports.join("\n")+"\n");

// Compile at build time, never new Function/eval in the WebView. Bundle only
// generated validators and small helpers, retaining the existing strict CSP.
const ajv = new Ajv2020({strict:false,allErrors:false,inlineRefs:false,coerceTypes:false,useDefaults:false,removeAdditional:false,code:{source:true,esm:true}});
addFormats(ajv);ajv.addFormat("path",/^asset:[0-9a-f-]{36}$/);
// The same Python definition appears in several response envelopes. Share
// identical definitions instead of compiling a fresh scientific config each
// time. Fail on a name collision rather than choosing a different contract.
const definitions={};
for(const schema of Object.values(schemas))for(const[name,definition]of Object.entries(schema.$defs??{})){
  if(name in definitions&&JSON.stringify(definitions[name])!==JSON.stringify(definition))throw new Error(`Conflicting schema definition: ${name}`);
  definitions[name]=definition;
}
function externalReferences(value){
  if(Array.isArray(value))return value.map(externalReferences);
  if(value&&typeof value==="object")return Object.fromEntries(Object.entries(value).map(([key,item])=>[key,key==="$ref"&&typeof item==="string"&&item.startsWith("#/$defs/")?`urn:fusionlab:shared${item}`:externalReferences(item)]));
  return value;
}
ajv.addSchema({$id:"urn:fusionlab:shared",$defs:externalReferences(definitions)},"shared");
for(const[name,schema]of Object.entries(schemas)){const{$defs,...root}=schema;ajv.addSchema(externalReferences(root),name);}
const validation=standaloneCode(ajv,Object.fromEntries(Object.keys(schemas).map(name=>[name,name])));
await build({stdin:{contents:validation,resolveDir:fileURLToPath(new URL("..",import.meta.url)),loader:"js"},bundle:true,format:"esm",platform:"browser",write:true,
  outfile:fileURLToPath(new URL("../src/contracts/public.validators.generated.js",import.meta.url))});
await writeFile(new URL("../src/contracts/public.validators.generated.d.ts",import.meta.url),Object.keys(schemas).map(name=>`export function ${name}(value:unknown):value is import("./${name}.generated").${name};`).join("\n")+"\n");
