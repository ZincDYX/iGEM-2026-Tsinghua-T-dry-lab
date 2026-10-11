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
// An annotation-only Pydantic Any schema permits every JSON value, not just
// objects. json-schema-to-typescript otherwise infers an index-signature
// interface from its title. Boolean true has identical validation semantics.
function typescriptSchema(schema) {
  if (!schema || typeof schema !== 'object') return schema;
  const annotations = new Set(['title','description','default','examples']);
  if (Object.keys(schema).every(key => annotations.has(key))) return true;
  const maps = new Set(['properties','patternProperties','$defs','definitions','dependentSchemas']);
  const arrays = new Set(['allOf','anyOf','oneOf','prefixItems']);
  const children = new Set(['items','additionalProperties','contains','not','if','then','else','propertyNames','unevaluatedProperties']);
  return Object.fromEntries(Object.entries(schema).map(([key,value]) => [key,
    maps.has(key) ? Object.fromEntries(Object.entries(value).map(([name,item]) => [name,typescriptSchema(item)])) :
      arrays.has(key) ? value.map(typescriptSchema) : children.has(key) ? typescriptSchema(value) : value]));
}
for (const [name,schema] of Object.entries(schemas)) {
  const output = await compile(typescriptSchema(schema),name,{bannerComment:"/* Generated from public Pydantic contracts. Do not edit. */",additionalProperties:false});
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
  if(!value||typeof value!=="object")return value;
  // Descriptions/defaults remain in the exported schemas and TypeScript docs.
  // They do not participate in validation (useDefaults is false), so do not
  // embed those repeated annotations in the executable browser validators.
  const annotations=new Set(["title","description","default","examples"]);
  const maps=new Set(["properties","patternProperties","$defs","definitions","dependentSchemas"]);
  const arrays=new Set(["allOf","anyOf","oneOf","prefixItems"]);
  const children=new Set(["items","additionalProperties","contains","not","if","then","else","propertyNames","unevaluatedProperties"]);
  return Object.fromEntries(Object.entries(value).filter(([key])=>!annotations.has(key)).map(([key,item])=>{
    if(key==="$ref"&&typeof item==="string"&&item.startsWith("#/$defs/"))return[key,`urn:fusionlab:shared${item}`];
    if(maps.has(key))return[key,Object.fromEntries(Object.entries(item).map(([name,schema])=>[name,externalReferences(schema)]))];
    if(arrays.has(key))return[key,item.map(externalReferences)];
    if(children.has(key))return[key,externalReferences(item)];
    // Literal enum/const objects and property names are not schema annotations.
    return[key,item];
  }));
}
ajv.addSchema({$id:"urn:fusionlab:shared",$defs:externalReferences(definitions)},"shared");
for(const[name,schema]of Object.entries(schemas)){const{$defs,...root}=schema;ajv.addSchema(externalReferences(root),name);}
const validation=standaloneCode(ajv,Object.fromEntries(Object.keys(schemas).map(name=>[name,name])));
await build({stdin:{contents:validation,resolveDir:fileURLToPath(new URL("..",import.meta.url)),loader:"js"},bundle:true,format:"esm",platform:"browser",write:true,
  outfile:fileURLToPath(new URL("../src/contracts/public.validators.generated.js",import.meta.url))});
await writeFile(new URL("../src/contracts/public.validators.generated.d.ts",import.meta.url),Object.keys(schemas).map(name=>`export function ${name}(value:unknown):value is import("./${name}.generated").${name};`).join("\n")+"\n");
