var __getOwnPropNames = Object.getOwnPropertyNames;
var __commonJS = (cb, mod) => function __require() {
  try {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  } catch (e) {
    throw mod = 0, e;
  }
};

// node_modules/.pnpm/ajv@8.18.0/node_modules/ajv/dist/runtime/ucs2length.js
var require_ucs2length = __commonJS({
  "node_modules/.pnpm/ajv@8.18.0/node_modules/ajv/dist/runtime/ucs2length.js"(exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    function ucs2length(str) {
      const len = str.length;
      let length = 0;
      let pos = 0;
      let value;
      while (pos < len) {
        length++;
        value = str.charCodeAt(pos++);
        if (value >= 55296 && value <= 56319 && pos < len) {
          value = str.charCodeAt(pos);
          if ((value & 64512) === 56320)
            pos++;
        }
      }
      return length;
    }
    exports.default = ucs2length;
    ucs2length.code = 'require("ajv/dist/runtime/ucs2length").default';
  }
});

// <stdin>
var ProposalView = validate266;
var schema113 = { "additionalProperties": false, "properties": { "observation": { "anyOf": [{ "$ref": "urn:fusionlab:shared#/$defs/ScientificObservation" }, { "type": "null" }] }, "scientific_actions": { "items": { "discriminator": { "mapping": { "evaluate_result": "#/$defs/EvaluateResultAction", "finish": "#/$defs/FinishAction", "inspect_job": "#/$defs/InspectJobAction", "inspect_project": "#/$defs/InspectProjectAction", "prepare_node": "#/$defs/PrepareNodeAction", "propose_experiment": "#/$defs/ProposeExperimentAction", "retrieve_evidence": "#/$defs/RetrieveEvidenceAction", "submit_job": "#/$defs/SubmitJobAction", "wait": "#/$defs/WaitAction" }, "propertyName": "kind" }, "oneOf": [{ "$ref": "urn:fusionlab:shared#/$defs/InspectProjectAction" }, { "$ref": "urn:fusionlab:shared#/$defs/RetrieveEvidenceAction" }, { "$ref": "urn:fusionlab:shared#/$defs/PrepareNodeAction" }, { "$ref": "urn:fusionlab:shared#/$defs/SubmitJobAction" }, { "$ref": "urn:fusionlab:shared#/$defs/InspectJobAction" }, { "$ref": "urn:fusionlab:shared#/$defs/EvaluateResultAction" }, { "$ref": "urn:fusionlab:shared#/$defs/ProposeExperimentAction" }, { "$ref": "urn:fusionlab:shared#/$defs/WaitAction" }, { "$ref": "urn:fusionlab:shared#/$defs/FinishAction" }] }, "type": "array" }, "reviewed_tool_labels": { "items": { "type": "string" }, "type": "array" }, "id": { "type": "string" }, "task_id": { "type": "string" }, "project_id": { "type": "string" }, "source": { "type": "string" }, "status": { "enum": ["proposed", "accepted", "rejected", "blocked", "stale"], "type": "string" }, "objective": { "type": "string" }, "rationale": { "type": "string" }, "change_types": { "items": { "type": "string" }, "type": "array" }, "evidence": { "items": { "type": "string" }, "type": "array" }, "requested_stages": { "items": { "type": "string" }, "type": "array" }, "execution_stages": { "items": { "type": "string" }, "type": "array" }, "reused_artifacts": { "items": { "type": "string" }, "type": "array" }, "missing_inputs": { "items": { "type": "string" }, "type": "array" }, "limitations": { "items": { "type": "string" }, "type": "array" }, "workflow": { "anyOf": [{ "$ref": "urn:fusionlab:shared#/$defs/Workflow" }, { "type": "null" }] }, "confirmation": { "anyOf": [{ "$ref": "urn:fusionlab:shared#/$defs/PlanBinding" }, { "type": "null" }] }, "created_at": { "type": "string" }, "review_identity": { "anyOf": [{ "additionalProperties": true, "type": "object" }, { "type": "null" }] }, "previous_review_identity": { "anyOf": [{ "additionalProperties": true, "type": "object" }, { "type": "null" }] } }, "required": ["observation", "scientific_actions", "reviewed_tool_labels", "id", "task_id", "project_id", "source", "status", "objective", "rationale", "change_types", "evidence", "requested_stages", "execution_stages", "reused_artifacts", "missing_inputs", "limitations", "workflow", "confirmation", "created_at", "review_identity", "previous_review_identity"], "type": "object" };
var func1 = Object.prototype.hasOwnProperty;
var schema114 = { "additionalProperties": false, "properties": { "project_id": { "title": "Project Id", "type": "string" }, "project_revision": { "title": "Project Revision", "type": "integer" }, "observation_identity": { "title": "Observation Identity", "type": "string" }, "scientific_input_identity": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Scientific Input Identity" }, "prepared_through": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Prepared Through" }, "scenarios": { "additionalProperties": { "type": "string" }, "title": "Scenarios", "type": "object" }, "available_input_refs": { "items": { "type": "string" }, "title": "Available Input Refs", "type": "array" }, "gaps": { "items": { "$ref": "#/$defs/ScientificGap" }, "title": "Gaps", "type": "array" }, "omitted_gap_count": { "title": "Omitted Gap Count", "type": "integer" }, "parameter_summaries": { "items": { "$ref": "#/$defs/ReviewedParameterSummary" }, "title": "Parameter Summaries", "type": "array" }, "omitted_parameter_count": { "title": "Omitted Parameter Count", "type": "integer" }, "capabilities": { "items": { "$ref": "#/$defs/DomainCapability" }, "title": "Capabilities", "type": "array" }, "recorded_results": { "items": { "$ref": "#/$defs/RecordedStageResult" }, "title": "Recorded Results", "type": "array" }, "recorded_jobs": { "items": { "$ref": "#/$defs/RecordedJob" }, "title": "Recorded Jobs", "type": "array" }, "accepted_proposal_refs": { "items": { "type": "string" }, "title": "Accepted Proposal Refs", "type": "array" }, "budget": { "additionalProperties": { "anyOf": [{ "type": "integer" }, { "type": "number" }, { "type": "null" }] }, "title": "Budget", "type": "object" }, "limitations": { "items": { "type": "string" }, "title": "Limitations", "type": "array" } }, "required": ["project_id", "project_revision", "observation_identity", "scientific_input_identity", "prepared_through", "scenarios", "available_input_refs", "gaps", "omitted_gap_count", "parameter_summaries", "omitted_parameter_count", "capabilities", "recorded_results", "recorded_jobs", "accepted_proposal_refs", "budget", "limitations"], "title": "ScientificObservation", "type": "object" };
function validate268(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate268.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.stage === void 0 && (missing0 = "stage") || data.code === void 0 && (missing0 = "code") || data.construct_id === void 0 && (missing0 = "construct_id") || data.condition_id === void 0 && (missing0 = "condition_id") || data.reasons === void 0 && (missing0 = "reasons")) {
        validate268.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "stage" || key0 === "code" || key0 === "construct_id" || key0 === "condition_id" || key0 === "reasons")) {
            validate268.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.stage !== void 0) {
            const _errs2 = errors;
            if (typeof data.stage !== "string") {
              validate268.errors = [{ instancePath: instancePath + "/stage", schemaPath: "#/properties/stage/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.code !== void 0) {
              const _errs4 = errors;
              if (typeof data.code !== "string") {
                validate268.errors = [{ instancePath: instancePath + "/code", schemaPath: "#/properties/code/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.construct_id !== void 0) {
                let data2 = data.construct_id;
                const _errs6 = errors;
                const _errs7 = errors;
                let valid1 = false;
                const _errs8 = errors;
                if (typeof data2 !== "string") {
                  const err0 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                }
                var _valid0 = _errs8 === errors;
                valid1 = valid1 || _valid0;
                const _errs10 = errors;
                if (data2 !== null) {
                  const err1 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                }
                var _valid0 = _errs10 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err2 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err2];
                  } else {
                    vErrors.push(err2);
                  }
                  errors++;
                  validate268.errors = vErrors;
                  return false;
                } else {
                  errors = _errs7;
                  if (vErrors !== null) {
                    if (_errs7) {
                      vErrors.length = _errs7;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.condition_id !== void 0) {
                  let data3 = data.condition_id;
                  const _errs12 = errors;
                  const _errs13 = errors;
                  let valid2 = false;
                  const _errs14 = errors;
                  if (typeof data3 !== "string") {
                    const err3 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                  }
                  var _valid1 = _errs14 === errors;
                  valid2 = valid2 || _valid1;
                  const _errs16 = errors;
                  if (data3 !== null) {
                    const err4 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err4];
                    } else {
                      vErrors.push(err4);
                    }
                    errors++;
                  }
                  var _valid1 = _errs16 === errors;
                  valid2 = valid2 || _valid1;
                  if (!valid2) {
                    const err5 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err5];
                    } else {
                      vErrors.push(err5);
                    }
                    errors++;
                    validate268.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs13;
                    if (vErrors !== null) {
                      if (_errs13) {
                        vErrors.length = _errs13;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs12 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.reasons !== void 0) {
                    let data4 = data.reasons;
                    const _errs18 = errors;
                    if (errors === _errs18) {
                      if (Array.isArray(data4)) {
                        var valid3 = true;
                        const len0 = data4.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          const _errs20 = errors;
                          if (typeof data4[i0] !== "string") {
                            validate268.errors = [{ instancePath: instancePath + "/reasons/" + i0, schemaPath: "#/properties/reasons/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid3 = _errs20 === errors;
                          if (!valid3) {
                            break;
                          }
                        }
                      } else {
                        validate268.errors = [{ instancePath: instancePath + "/reasons", schemaPath: "#/properties/reasons/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs18 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate268.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate268.errors = vErrors;
  return errors === 0;
}
validate268.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema116 = { "additionalProperties": false, "properties": { "parameter_id": { "title": "Parameter Id", "type": "string" }, "parameter_type": { "title": "Parameter Type", "type": "string" }, "construct_id": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Construct Id" }, "condition_id": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Condition Id" }, "review_status": { "title": "Review Status", "type": "string" }, "source_type": { "title": "Source Type", "type": "string" }, "unit": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Unit" }, "entity_basis": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Entity Basis" }, "model_version": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Model Version" }, "value": { "anyOf": [{ "type": "number" }, { "type": "string" }], "title": "Value" }, "parameter_version": { "title": "Parameter Version", "type": "integer" }, "conditions": { "additionalProperties": { "anyOf": [{ "type": "string" }, { "type": "number" }] }, "title": "Conditions", "type": "object" } }, "required": ["parameter_id", "parameter_type", "construct_id", "condition_id", "review_status", "source_type", "unit", "entity_basis", "model_version", "value", "parameter_version", "conditions"], "title": "ReviewedParameterSummary", "type": "object" };
function validate270(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate270.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.parameter_id === void 0 && (missing0 = "parameter_id") || data.parameter_type === void 0 && (missing0 = "parameter_type") || data.construct_id === void 0 && (missing0 = "construct_id") || data.condition_id === void 0 && (missing0 = "condition_id") || data.review_status === void 0 && (missing0 = "review_status") || data.source_type === void 0 && (missing0 = "source_type") || data.unit === void 0 && (missing0 = "unit") || data.entity_basis === void 0 && (missing0 = "entity_basis") || data.model_version === void 0 && (missing0 = "model_version") || data.value === void 0 && (missing0 = "value") || data.parameter_version === void 0 && (missing0 = "parameter_version") || data.conditions === void 0 && (missing0 = "conditions")) {
        validate270.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema116.properties, key0)) {
            validate270.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.parameter_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.parameter_id !== "string") {
              validate270.errors = [{ instancePath: instancePath + "/parameter_id", schemaPath: "#/properties/parameter_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.parameter_type !== void 0) {
              const _errs4 = errors;
              if (typeof data.parameter_type !== "string") {
                validate270.errors = [{ instancePath: instancePath + "/parameter_type", schemaPath: "#/properties/parameter_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.construct_id !== void 0) {
                let data2 = data.construct_id;
                const _errs6 = errors;
                const _errs7 = errors;
                let valid1 = false;
                const _errs8 = errors;
                if (typeof data2 !== "string") {
                  const err0 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                }
                var _valid0 = _errs8 === errors;
                valid1 = valid1 || _valid0;
                const _errs10 = errors;
                if (data2 !== null) {
                  const err1 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                }
                var _valid0 = _errs10 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err2 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err2];
                  } else {
                    vErrors.push(err2);
                  }
                  errors++;
                  validate270.errors = vErrors;
                  return false;
                } else {
                  errors = _errs7;
                  if (vErrors !== null) {
                    if (_errs7) {
                      vErrors.length = _errs7;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.condition_id !== void 0) {
                  let data3 = data.condition_id;
                  const _errs12 = errors;
                  const _errs13 = errors;
                  let valid2 = false;
                  const _errs14 = errors;
                  if (typeof data3 !== "string") {
                    const err3 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                  }
                  var _valid1 = _errs14 === errors;
                  valid2 = valid2 || _valid1;
                  const _errs16 = errors;
                  if (data3 !== null) {
                    const err4 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err4];
                    } else {
                      vErrors.push(err4);
                    }
                    errors++;
                  }
                  var _valid1 = _errs16 === errors;
                  valid2 = valid2 || _valid1;
                  if (!valid2) {
                    const err5 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err5];
                    } else {
                      vErrors.push(err5);
                    }
                    errors++;
                    validate270.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs13;
                    if (vErrors !== null) {
                      if (_errs13) {
                        vErrors.length = _errs13;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs12 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.review_status !== void 0) {
                    const _errs18 = errors;
                    if (typeof data.review_status !== "string") {
                      validate270.errors = [{ instancePath: instancePath + "/review_status", schemaPath: "#/properties/review_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs18 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.source_type !== void 0) {
                      const _errs20 = errors;
                      if (typeof data.source_type !== "string") {
                        validate270.errors = [{ instancePath: instancePath + "/source_type", schemaPath: "#/properties/source_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.unit !== void 0) {
                        let data6 = data.unit;
                        const _errs22 = errors;
                        const _errs23 = errors;
                        let valid3 = false;
                        const _errs24 = errors;
                        if (typeof data6 !== "string") {
                          const err6 = { instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err6];
                          } else {
                            vErrors.push(err6);
                          }
                          errors++;
                        }
                        var _valid2 = _errs24 === errors;
                        valid3 = valid3 || _valid2;
                        const _errs26 = errors;
                        if (data6 !== null) {
                          const err7 = { instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err7];
                          } else {
                            vErrors.push(err7);
                          }
                          errors++;
                        }
                        var _valid2 = _errs26 === errors;
                        valid3 = valid3 || _valid2;
                        if (!valid3) {
                          const err8 = { instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err8];
                          } else {
                            vErrors.push(err8);
                          }
                          errors++;
                          validate270.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs23;
                          if (vErrors !== null) {
                            if (_errs23) {
                              vErrors.length = _errs23;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs22 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.entity_basis !== void 0) {
                          let data7 = data.entity_basis;
                          const _errs28 = errors;
                          const _errs29 = errors;
                          let valid4 = false;
                          const _errs30 = errors;
                          if (typeof data7 !== "string") {
                            const err9 = { instancePath: instancePath + "/entity_basis", schemaPath: "#/properties/entity_basis/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err9];
                            } else {
                              vErrors.push(err9);
                            }
                            errors++;
                          }
                          var _valid3 = _errs30 === errors;
                          valid4 = valid4 || _valid3;
                          const _errs32 = errors;
                          if (data7 !== null) {
                            const err10 = { instancePath: instancePath + "/entity_basis", schemaPath: "#/properties/entity_basis/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err10];
                            } else {
                              vErrors.push(err10);
                            }
                            errors++;
                          }
                          var _valid3 = _errs32 === errors;
                          valid4 = valid4 || _valid3;
                          if (!valid4) {
                            const err11 = { instancePath: instancePath + "/entity_basis", schemaPath: "#/properties/entity_basis/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err11];
                            } else {
                              vErrors.push(err11);
                            }
                            errors++;
                            validate270.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs29;
                            if (vErrors !== null) {
                              if (_errs29) {
                                vErrors.length = _errs29;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs28 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.model_version !== void 0) {
                            let data8 = data.model_version;
                            const _errs34 = errors;
                            const _errs35 = errors;
                            let valid5 = false;
                            const _errs36 = errors;
                            if (typeof data8 !== "string") {
                              const err12 = { instancePath: instancePath + "/model_version", schemaPath: "#/properties/model_version/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err12];
                              } else {
                                vErrors.push(err12);
                              }
                              errors++;
                            }
                            var _valid4 = _errs36 === errors;
                            valid5 = valid5 || _valid4;
                            const _errs38 = errors;
                            if (data8 !== null) {
                              const err13 = { instancePath: instancePath + "/model_version", schemaPath: "#/properties/model_version/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err13];
                              } else {
                                vErrors.push(err13);
                              }
                              errors++;
                            }
                            var _valid4 = _errs38 === errors;
                            valid5 = valid5 || _valid4;
                            if (!valid5) {
                              const err14 = { instancePath: instancePath + "/model_version", schemaPath: "#/properties/model_version/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err14];
                              } else {
                                vErrors.push(err14);
                              }
                              errors++;
                              validate270.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs35;
                              if (vErrors !== null) {
                                if (_errs35) {
                                  vErrors.length = _errs35;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs34 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.value !== void 0) {
                              let data9 = data.value;
                              const _errs40 = errors;
                              const _errs41 = errors;
                              let valid6 = false;
                              const _errs42 = errors;
                              if (!(typeof data9 == "number")) {
                                const err15 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/anyOf/0/type", keyword: "type", params: { type: "number" }, message: "must be number" };
                                if (vErrors === null) {
                                  vErrors = [err15];
                                } else {
                                  vErrors.push(err15);
                                }
                                errors++;
                              }
                              var _valid5 = _errs42 === errors;
                              valid6 = valid6 || _valid5;
                              const _errs44 = errors;
                              if (typeof data9 !== "string") {
                                const err16 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/anyOf/1/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err16];
                                } else {
                                  vErrors.push(err16);
                                }
                                errors++;
                              }
                              var _valid5 = _errs44 === errors;
                              valid6 = valid6 || _valid5;
                              if (!valid6) {
                                const err17 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                if (vErrors === null) {
                                  vErrors = [err17];
                                } else {
                                  vErrors.push(err17);
                                }
                                errors++;
                                validate270.errors = vErrors;
                                return false;
                              } else {
                                errors = _errs41;
                                if (vErrors !== null) {
                                  if (_errs41) {
                                    vErrors.length = _errs41;
                                  } else {
                                    vErrors = null;
                                  }
                                }
                              }
                              var valid0 = _errs40 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.parameter_version !== void 0) {
                                let data10 = data.parameter_version;
                                const _errs46 = errors;
                                if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)))) {
                                  validate270.errors = [{ instancePath: instancePath + "/parameter_version", schemaPath: "#/properties/parameter_version/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                var valid0 = _errs46 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.conditions !== void 0) {
                                  let data11 = data.conditions;
                                  const _errs48 = errors;
                                  if (errors === _errs48) {
                                    if (data11 && typeof data11 == "object" && !Array.isArray(data11)) {
                                      for (const key1 in data11) {
                                        let data12 = data11[key1];
                                        const _errs51 = errors;
                                        const _errs52 = errors;
                                        let valid8 = false;
                                        const _errs53 = errors;
                                        if (typeof data12 !== "string") {
                                          const err18 = { instancePath: instancePath + "/conditions/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/conditions/additionalProperties/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err18];
                                          } else {
                                            vErrors.push(err18);
                                          }
                                          errors++;
                                        }
                                        var _valid6 = _errs53 === errors;
                                        valid8 = valid8 || _valid6;
                                        const _errs55 = errors;
                                        if (!(typeof data12 == "number")) {
                                          const err19 = { instancePath: instancePath + "/conditions/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/conditions/additionalProperties/anyOf/1/type", keyword: "type", params: { type: "number" }, message: "must be number" };
                                          if (vErrors === null) {
                                            vErrors = [err19];
                                          } else {
                                            vErrors.push(err19);
                                          }
                                          errors++;
                                        }
                                        var _valid6 = _errs55 === errors;
                                        valid8 = valid8 || _valid6;
                                        if (!valid8) {
                                          const err20 = { instancePath: instancePath + "/conditions/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/conditions/additionalProperties/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                          if (vErrors === null) {
                                            vErrors = [err20];
                                          } else {
                                            vErrors.push(err20);
                                          }
                                          errors++;
                                          validate270.errors = vErrors;
                                          return false;
                                        } else {
                                          errors = _errs52;
                                          if (vErrors !== null) {
                                            if (_errs52) {
                                              vErrors.length = _errs52;
                                            } else {
                                              vErrors = null;
                                            }
                                          }
                                        }
                                        var valid7 = _errs51 === errors;
                                        if (!valid7) {
                                          break;
                                        }
                                      }
                                    } else {
                                      validate270.errors = [{ instancePath: instancePath + "/conditions", schemaPath: "#/properties/conditions/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                      return false;
                                    }
                                  }
                                  var valid0 = _errs48 === errors;
                                } else {
                                  var valid0 = true;
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate270.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate270.errors = vErrors;
  return errors === 0;
}
validate270.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema117 = { "additionalProperties": false, "properties": { "tool_id": { "title": "Tool Id", "type": "string" }, "version": { "title": "Version", "type": "string" }, "resource": { "title": "Resource", "type": "string" }, "route_state": { "enum": ["local_method", "configured_not_verified", "unconfigured"], "title": "Route State", "type": "string" }, "execution_allowed_by_policy": { "title": "Execution Allowed By Policy", "type": "boolean" } }, "required": ["tool_id", "version", "resource", "route_state", "execution_allowed_by_policy"], "title": "DomainCapability", "type": "object" };
function validate272(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate272.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.tool_id === void 0 && (missing0 = "tool_id") || data.version === void 0 && (missing0 = "version") || data.resource === void 0 && (missing0 = "resource") || data.route_state === void 0 && (missing0 = "route_state") || data.execution_allowed_by_policy === void 0 && (missing0 = "execution_allowed_by_policy")) {
        validate272.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "tool_id" || key0 === "version" || key0 === "resource" || key0 === "route_state" || key0 === "execution_allowed_by_policy")) {
            validate272.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.tool_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.tool_id !== "string") {
              validate272.errors = [{ instancePath: instancePath + "/tool_id", schemaPath: "#/properties/tool_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.version !== void 0) {
              const _errs4 = errors;
              if (typeof data.version !== "string") {
                validate272.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.resource !== void 0) {
                const _errs6 = errors;
                if (typeof data.resource !== "string") {
                  validate272.errors = [{ instancePath: instancePath + "/resource", schemaPath: "#/properties/resource/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.route_state !== void 0) {
                  let data3 = data.route_state;
                  const _errs8 = errors;
                  if (typeof data3 !== "string") {
                    validate272.errors = [{ instancePath: instancePath + "/route_state", schemaPath: "#/properties/route_state/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data3 === "local_method" || data3 === "configured_not_verified" || data3 === "unconfigured")) {
                    validate272.errors = [{ instancePath: instancePath + "/route_state", schemaPath: "#/properties/route_state/enum", keyword: "enum", params: { allowedValues: schema117.properties.route_state.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.execution_allowed_by_policy !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.execution_allowed_by_policy !== "boolean") {
                      validate272.errors = [{ instancePath: instancePath + "/execution_allowed_by_policy", schemaPath: "#/properties/execution_allowed_by_policy/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate272.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate272.errors = vErrors;
  return errors === 0;
}
validate272.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema118 = { "additionalProperties": false, "properties": { "run_id": { "title": "Run Id", "type": "string" }, "node_id": { "title": "Node Id", "type": "string" }, "stage": { "title": "Stage", "type": "string" }, "node_status": { "title": "Node Status", "type": "string" }, "attempt": { "title": "Attempt", "type": "integer" }, "result_ref": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Result Ref" }, "current_project_revision": { "title": "Current Project Revision", "type": "boolean" }, "scientific_status_counts": { "additionalProperties": { "type": "integer" }, "title": "Scientific Status Counts", "type": "object" }, "numerically_solved_count": { "anyOf": [{ "type": "integer" }, { "type": "null" }], "title": "Numerically Solved Count" }, "evidence_ready_count": { "anyOf": [{ "type": "integer" }, { "type": "null" }], "title": "Evidence Ready Count" }, "claim_scopes": { "items": { "type": "string" }, "title": "Claim Scopes", "type": "array" } }, "required": ["run_id", "node_id", "stage", "node_status", "attempt", "result_ref", "current_project_revision", "scientific_status_counts", "numerically_solved_count", "evidence_ready_count", "claim_scopes"], "title": "RecordedStageResult", "type": "object" };
function validate274(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate274.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.run_id === void 0 && (missing0 = "run_id") || data.node_id === void 0 && (missing0 = "node_id") || data.stage === void 0 && (missing0 = "stage") || data.node_status === void 0 && (missing0 = "node_status") || data.attempt === void 0 && (missing0 = "attempt") || data.result_ref === void 0 && (missing0 = "result_ref") || data.current_project_revision === void 0 && (missing0 = "current_project_revision") || data.scientific_status_counts === void 0 && (missing0 = "scientific_status_counts") || data.numerically_solved_count === void 0 && (missing0 = "numerically_solved_count") || data.evidence_ready_count === void 0 && (missing0 = "evidence_ready_count") || data.claim_scopes === void 0 && (missing0 = "claim_scopes")) {
        validate274.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema118.properties, key0)) {
            validate274.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.run_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.run_id !== "string") {
              validate274.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.node_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.node_id !== "string") {
                validate274.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.stage !== void 0) {
                const _errs6 = errors;
                if (typeof data.stage !== "string") {
                  validate274.errors = [{ instancePath: instancePath + "/stage", schemaPath: "#/properties/stage/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.node_status !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.node_status !== "string") {
                    validate274.errors = [{ instancePath: instancePath + "/node_status", schemaPath: "#/properties/node_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.attempt !== void 0) {
                    let data4 = data.attempt;
                    const _errs10 = errors;
                    if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)))) {
                      validate274.errors = [{ instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.result_ref !== void 0) {
                      let data5 = data.result_ref;
                      const _errs12 = errors;
                      const _errs13 = errors;
                      let valid1 = false;
                      const _errs14 = errors;
                      if (typeof data5 !== "string") {
                        const err0 = { instancePath: instancePath + "/result_ref", schemaPath: "#/properties/result_ref/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      }
                      var _valid0 = _errs14 === errors;
                      valid1 = valid1 || _valid0;
                      const _errs16 = errors;
                      if (data5 !== null) {
                        const err1 = { instancePath: instancePath + "/result_ref", schemaPath: "#/properties/result_ref/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      }
                      var _valid0 = _errs16 === errors;
                      valid1 = valid1 || _valid0;
                      if (!valid1) {
                        const err2 = { instancePath: instancePath + "/result_ref", schemaPath: "#/properties/result_ref/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err2];
                        } else {
                          vErrors.push(err2);
                        }
                        errors++;
                        validate274.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs13;
                        if (vErrors !== null) {
                          if (_errs13) {
                            vErrors.length = _errs13;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.current_project_revision !== void 0) {
                        const _errs18 = errors;
                        if (typeof data.current_project_revision !== "boolean") {
                          validate274.errors = [{ instancePath: instancePath + "/current_project_revision", schemaPath: "#/properties/current_project_revision/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                          return false;
                        }
                        var valid0 = _errs18 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.scientific_status_counts !== void 0) {
                          let data7 = data.scientific_status_counts;
                          const _errs20 = errors;
                          if (errors === _errs20) {
                            if (data7 && typeof data7 == "object" && !Array.isArray(data7)) {
                              for (const key1 in data7) {
                                let data8 = data7[key1];
                                const _errs23 = errors;
                                if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)))) {
                                  validate274.errors = [{ instancePath: instancePath + "/scientific_status_counts/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/scientific_status_counts/additionalProperties/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                var valid2 = _errs23 === errors;
                                if (!valid2) {
                                  break;
                                }
                              }
                            } else {
                              validate274.errors = [{ instancePath: instancePath + "/scientific_status_counts", schemaPath: "#/properties/scientific_status_counts/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                              return false;
                            }
                          }
                          var valid0 = _errs20 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.numerically_solved_count !== void 0) {
                            let data9 = data.numerically_solved_count;
                            const _errs25 = errors;
                            const _errs26 = errors;
                            let valid3 = false;
                            const _errs27 = errors;
                            if (!(typeof data9 == "number" && (!(data9 % 1) && !isNaN(data9)))) {
                              const err3 = { instancePath: instancePath + "/numerically_solved_count", schemaPath: "#/properties/numerically_solved_count/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                              if (vErrors === null) {
                                vErrors = [err3];
                              } else {
                                vErrors.push(err3);
                              }
                              errors++;
                            }
                            var _valid1 = _errs27 === errors;
                            valid3 = valid3 || _valid1;
                            const _errs29 = errors;
                            if (data9 !== null) {
                              const err4 = { instancePath: instancePath + "/numerically_solved_count", schemaPath: "#/properties/numerically_solved_count/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err4];
                              } else {
                                vErrors.push(err4);
                              }
                              errors++;
                            }
                            var _valid1 = _errs29 === errors;
                            valid3 = valid3 || _valid1;
                            if (!valid3) {
                              const err5 = { instancePath: instancePath + "/numerically_solved_count", schemaPath: "#/properties/numerically_solved_count/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err5];
                              } else {
                                vErrors.push(err5);
                              }
                              errors++;
                              validate274.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs26;
                              if (vErrors !== null) {
                                if (_errs26) {
                                  vErrors.length = _errs26;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs25 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.evidence_ready_count !== void 0) {
                              let data10 = data.evidence_ready_count;
                              const _errs31 = errors;
                              const _errs32 = errors;
                              let valid4 = false;
                              const _errs33 = errors;
                              if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)))) {
                                const err6 = { instancePath: instancePath + "/evidence_ready_count", schemaPath: "#/properties/evidence_ready_count/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                if (vErrors === null) {
                                  vErrors = [err6];
                                } else {
                                  vErrors.push(err6);
                                }
                                errors++;
                              }
                              var _valid2 = _errs33 === errors;
                              valid4 = valid4 || _valid2;
                              const _errs35 = errors;
                              if (data10 !== null) {
                                const err7 = { instancePath: instancePath + "/evidence_ready_count", schemaPath: "#/properties/evidence_ready_count/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                if (vErrors === null) {
                                  vErrors = [err7];
                                } else {
                                  vErrors.push(err7);
                                }
                                errors++;
                              }
                              var _valid2 = _errs35 === errors;
                              valid4 = valid4 || _valid2;
                              if (!valid4) {
                                const err8 = { instancePath: instancePath + "/evidence_ready_count", schemaPath: "#/properties/evidence_ready_count/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                if (vErrors === null) {
                                  vErrors = [err8];
                                } else {
                                  vErrors.push(err8);
                                }
                                errors++;
                                validate274.errors = vErrors;
                                return false;
                              } else {
                                errors = _errs32;
                                if (vErrors !== null) {
                                  if (_errs32) {
                                    vErrors.length = _errs32;
                                  } else {
                                    vErrors = null;
                                  }
                                }
                              }
                              var valid0 = _errs31 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.claim_scopes !== void 0) {
                                let data11 = data.claim_scopes;
                                const _errs37 = errors;
                                if (errors === _errs37) {
                                  if (Array.isArray(data11)) {
                                    var valid5 = true;
                                    const len0 = data11.length;
                                    for (let i0 = 0; i0 < len0; i0++) {
                                      const _errs39 = errors;
                                      if (typeof data11[i0] !== "string") {
                                        validate274.errors = [{ instancePath: instancePath + "/claim_scopes/" + i0, schemaPath: "#/properties/claim_scopes/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      var valid5 = _errs39 === errors;
                                      if (!valid5) {
                                        break;
                                      }
                                    }
                                  } else {
                                    validate274.errors = [{ instancePath: instancePath + "/claim_scopes", schemaPath: "#/properties/claim_scopes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                    return false;
                                  }
                                }
                                var valid0 = _errs37 === errors;
                              } else {
                                var valid0 = true;
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate274.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate274.errors = vErrors;
  return errors === 0;
}
validate274.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema119 = { "additionalProperties": false, "properties": { "run_id": { "title": "Run Id", "type": "string" }, "node_id": { "title": "Node Id", "type": "string" }, "tool_id": { "title": "Tool Id", "type": "string" }, "node_status": { "title": "Node Status", "type": "string" }, "attempt": { "title": "Attempt", "type": "integer" }, "tool_status": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Tool Status" }, "parse_status": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Parse Status" }, "remote_status": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Remote Status" }, "remote_poll_count": { "anyOf": [{ "type": "integer" }, { "type": "null" }], "default": null, "title": "Remote Poll Count" }, "remote_cancellation_confirmed": { "const": false, "default": false, "title": "Remote Cancellation Confirmed", "type": "boolean" } }, "required": ["run_id", "node_id", "tool_id", "node_status", "attempt", "tool_status", "parse_status", "remote_status", "remote_poll_count", "remote_cancellation_confirmed"], "title": "RecordedJob", "type": "object" };
function validate276(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate276.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.run_id === void 0 && (missing0 = "run_id") || data.node_id === void 0 && (missing0 = "node_id") || data.tool_id === void 0 && (missing0 = "tool_id") || data.node_status === void 0 && (missing0 = "node_status") || data.attempt === void 0 && (missing0 = "attempt") || data.tool_status === void 0 && (missing0 = "tool_status") || data.parse_status === void 0 && (missing0 = "parse_status") || data.remote_status === void 0 && (missing0 = "remote_status") || data.remote_poll_count === void 0 && (missing0 = "remote_poll_count") || data.remote_cancellation_confirmed === void 0 && (missing0 = "remote_cancellation_confirmed")) {
        validate276.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema119.properties, key0)) {
            validate276.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.run_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.run_id !== "string") {
              validate276.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.node_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.node_id !== "string") {
                validate276.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.tool_id !== void 0) {
                const _errs6 = errors;
                if (typeof data.tool_id !== "string") {
                  validate276.errors = [{ instancePath: instancePath + "/tool_id", schemaPath: "#/properties/tool_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.node_status !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.node_status !== "string") {
                    validate276.errors = [{ instancePath: instancePath + "/node_status", schemaPath: "#/properties/node_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.attempt !== void 0) {
                    let data4 = data.attempt;
                    const _errs10 = errors;
                    if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)))) {
                      validate276.errors = [{ instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.tool_status !== void 0) {
                      let data5 = data.tool_status;
                      const _errs12 = errors;
                      const _errs13 = errors;
                      let valid1 = false;
                      const _errs14 = errors;
                      if (typeof data5 !== "string") {
                        const err0 = { instancePath: instancePath + "/tool_status", schemaPath: "#/properties/tool_status/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      }
                      var _valid0 = _errs14 === errors;
                      valid1 = valid1 || _valid0;
                      const _errs16 = errors;
                      if (data5 !== null) {
                        const err1 = { instancePath: instancePath + "/tool_status", schemaPath: "#/properties/tool_status/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      }
                      var _valid0 = _errs16 === errors;
                      valid1 = valid1 || _valid0;
                      if (!valid1) {
                        const err2 = { instancePath: instancePath + "/tool_status", schemaPath: "#/properties/tool_status/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err2];
                        } else {
                          vErrors.push(err2);
                        }
                        errors++;
                        validate276.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs13;
                        if (vErrors !== null) {
                          if (_errs13) {
                            vErrors.length = _errs13;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.parse_status !== void 0) {
                        let data6 = data.parse_status;
                        const _errs18 = errors;
                        const _errs19 = errors;
                        let valid2 = false;
                        const _errs20 = errors;
                        if (typeof data6 !== "string") {
                          const err3 = { instancePath: instancePath + "/parse_status", schemaPath: "#/properties/parse_status/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err3];
                          } else {
                            vErrors.push(err3);
                          }
                          errors++;
                        }
                        var _valid1 = _errs20 === errors;
                        valid2 = valid2 || _valid1;
                        const _errs22 = errors;
                        if (data6 !== null) {
                          const err4 = { instancePath: instancePath + "/parse_status", schemaPath: "#/properties/parse_status/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err4];
                          } else {
                            vErrors.push(err4);
                          }
                          errors++;
                        }
                        var _valid1 = _errs22 === errors;
                        valid2 = valid2 || _valid1;
                        if (!valid2) {
                          const err5 = { instancePath: instancePath + "/parse_status", schemaPath: "#/properties/parse_status/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err5];
                          } else {
                            vErrors.push(err5);
                          }
                          errors++;
                          validate276.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs19;
                          if (vErrors !== null) {
                            if (_errs19) {
                              vErrors.length = _errs19;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs18 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.remote_status !== void 0) {
                          let data7 = data.remote_status;
                          const _errs24 = errors;
                          const _errs25 = errors;
                          let valid3 = false;
                          const _errs26 = errors;
                          if (typeof data7 !== "string") {
                            const err6 = { instancePath: instancePath + "/remote_status", schemaPath: "#/properties/remote_status/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err6];
                            } else {
                              vErrors.push(err6);
                            }
                            errors++;
                          }
                          var _valid2 = _errs26 === errors;
                          valid3 = valid3 || _valid2;
                          const _errs28 = errors;
                          if (data7 !== null) {
                            const err7 = { instancePath: instancePath + "/remote_status", schemaPath: "#/properties/remote_status/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err7];
                            } else {
                              vErrors.push(err7);
                            }
                            errors++;
                          }
                          var _valid2 = _errs28 === errors;
                          valid3 = valid3 || _valid2;
                          if (!valid3) {
                            const err8 = { instancePath: instancePath + "/remote_status", schemaPath: "#/properties/remote_status/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err8];
                            } else {
                              vErrors.push(err8);
                            }
                            errors++;
                            validate276.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs25;
                            if (vErrors !== null) {
                              if (_errs25) {
                                vErrors.length = _errs25;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs24 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.remote_poll_count !== void 0) {
                            let data8 = data.remote_poll_count;
                            const _errs30 = errors;
                            const _errs31 = errors;
                            let valid4 = false;
                            const _errs32 = errors;
                            if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)))) {
                              const err9 = { instancePath: instancePath + "/remote_poll_count", schemaPath: "#/properties/remote_poll_count/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                              if (vErrors === null) {
                                vErrors = [err9];
                              } else {
                                vErrors.push(err9);
                              }
                              errors++;
                            }
                            var _valid3 = _errs32 === errors;
                            valid4 = valid4 || _valid3;
                            const _errs34 = errors;
                            if (data8 !== null) {
                              const err10 = { instancePath: instancePath + "/remote_poll_count", schemaPath: "#/properties/remote_poll_count/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err10];
                              } else {
                                vErrors.push(err10);
                              }
                              errors++;
                            }
                            var _valid3 = _errs34 === errors;
                            valid4 = valid4 || _valid3;
                            if (!valid4) {
                              const err11 = { instancePath: instancePath + "/remote_poll_count", schemaPath: "#/properties/remote_poll_count/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err11];
                              } else {
                                vErrors.push(err11);
                              }
                              errors++;
                              validate276.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs31;
                              if (vErrors !== null) {
                                if (_errs31) {
                                  vErrors.length = _errs31;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs30 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.remote_cancellation_confirmed !== void 0) {
                              let data9 = data.remote_cancellation_confirmed;
                              const _errs36 = errors;
                              if (typeof data9 !== "boolean") {
                                validate276.errors = [{ instancePath: instancePath + "/remote_cancellation_confirmed", schemaPath: "#/properties/remote_cancellation_confirmed/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                return false;
                              }
                              if (false !== data9) {
                                validate276.errors = [{ instancePath: instancePath + "/remote_cancellation_confirmed", schemaPath: "#/properties/remote_cancellation_confirmed/const", keyword: "const", params: { allowedValue: false }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid0 = _errs36 === errors;
                            } else {
                              var valid0 = true;
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate276.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate276.errors = vErrors;
  return errors === 0;
}
validate276.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate267(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate267.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.project_revision === void 0 && (missing0 = "project_revision") || data.observation_identity === void 0 && (missing0 = "observation_identity") || data.scientific_input_identity === void 0 && (missing0 = "scientific_input_identity") || data.prepared_through === void 0 && (missing0 = "prepared_through") || data.scenarios === void 0 && (missing0 = "scenarios") || data.available_input_refs === void 0 && (missing0 = "available_input_refs") || data.gaps === void 0 && (missing0 = "gaps") || data.omitted_gap_count === void 0 && (missing0 = "omitted_gap_count") || data.parameter_summaries === void 0 && (missing0 = "parameter_summaries") || data.omitted_parameter_count === void 0 && (missing0 = "omitted_parameter_count") || data.capabilities === void 0 && (missing0 = "capabilities") || data.recorded_results === void 0 && (missing0 = "recorded_results") || data.recorded_jobs === void 0 && (missing0 = "recorded_jobs") || data.accepted_proposal_refs === void 0 && (missing0 = "accepted_proposal_refs") || data.budget === void 0 && (missing0 = "budget") || data.limitations === void 0 && (missing0 = "limitations")) {
        validate267.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema114.properties, key0)) {
            validate267.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate267.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.project_revision !== void 0) {
              let data1 = data.project_revision;
              const _errs4 = errors;
              if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)))) {
                validate267.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.observation_identity !== void 0) {
                const _errs6 = errors;
                if (typeof data.observation_identity !== "string") {
                  validate267.errors = [{ instancePath: instancePath + "/observation_identity", schemaPath: "#/properties/observation_identity/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scientific_input_identity !== void 0) {
                  let data3 = data.scientific_input_identity;
                  const _errs8 = errors;
                  const _errs9 = errors;
                  let valid1 = false;
                  const _errs10 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/scientific_input_identity", schemaPath: "#/properties/scientific_input_identity/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                  }
                  var _valid0 = _errs10 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs12 = errors;
                  if (data3 !== null) {
                    const err1 = { instancePath: instancePath + "/scientific_input_identity", schemaPath: "#/properties/scientific_input_identity/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                  }
                  var _valid0 = _errs12 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err2 = { instancePath: instancePath + "/scientific_input_identity", schemaPath: "#/properties/scientific_input_identity/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate267.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs9;
                    if (vErrors !== null) {
                      if (_errs9) {
                        vErrors.length = _errs9;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.prepared_through !== void 0) {
                    let data4 = data.prepared_through;
                    const _errs14 = errors;
                    const _errs15 = errors;
                    let valid2 = false;
                    const _errs16 = errors;
                    if (typeof data4 !== "string") {
                      const err3 = { instancePath: instancePath + "/prepared_through", schemaPath: "#/properties/prepared_through/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                      if (vErrors === null) {
                        vErrors = [err3];
                      } else {
                        vErrors.push(err3);
                      }
                      errors++;
                    }
                    var _valid1 = _errs16 === errors;
                    valid2 = valid2 || _valid1;
                    const _errs18 = errors;
                    if (data4 !== null) {
                      const err4 = { instancePath: instancePath + "/prepared_through", schemaPath: "#/properties/prepared_through/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err4];
                      } else {
                        vErrors.push(err4);
                      }
                      errors++;
                    }
                    var _valid1 = _errs18 === errors;
                    valid2 = valid2 || _valid1;
                    if (!valid2) {
                      const err5 = { instancePath: instancePath + "/prepared_through", schemaPath: "#/properties/prepared_through/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err5];
                      } else {
                        vErrors.push(err5);
                      }
                      errors++;
                      validate267.errors = vErrors;
                      return false;
                    } else {
                      errors = _errs15;
                      if (vErrors !== null) {
                        if (_errs15) {
                          vErrors.length = _errs15;
                        } else {
                          vErrors = null;
                        }
                      }
                    }
                    var valid0 = _errs14 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.scenarios !== void 0) {
                      let data5 = data.scenarios;
                      const _errs20 = errors;
                      if (errors === _errs20) {
                        if (data5 && typeof data5 == "object" && !Array.isArray(data5)) {
                          for (const key1 in data5) {
                            const _errs23 = errors;
                            if (typeof data5[key1] !== "string") {
                              validate267.errors = [{ instancePath: instancePath + "/scenarios/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/scenarios/additionalProperties/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid3 = _errs23 === errors;
                            if (!valid3) {
                              break;
                            }
                          }
                        } else {
                          validate267.errors = [{ instancePath: instancePath + "/scenarios", schemaPath: "#/properties/scenarios/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                          return false;
                        }
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.available_input_refs !== void 0) {
                        let data7 = data.available_input_refs;
                        const _errs25 = errors;
                        if (errors === _errs25) {
                          if (Array.isArray(data7)) {
                            var valid4 = true;
                            const len0 = data7.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              const _errs27 = errors;
                              if (typeof data7[i0] !== "string") {
                                validate267.errors = [{ instancePath: instancePath + "/available_input_refs/" + i0, schemaPath: "#/properties/available_input_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid4 = _errs27 === errors;
                              if (!valid4) {
                                break;
                              }
                            }
                          } else {
                            validate267.errors = [{ instancePath: instancePath + "/available_input_refs", schemaPath: "#/properties/available_input_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs25 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.gaps !== void 0) {
                          let data9 = data.gaps;
                          const _errs29 = errors;
                          if (errors === _errs29) {
                            if (Array.isArray(data9)) {
                              var valid5 = true;
                              const len1 = data9.length;
                              for (let i1 = 0; i1 < len1; i1++) {
                                const _errs31 = errors;
                                if (!validate268(data9[i1], { instancePath: instancePath + "/gaps/" + i1, parentData: data9, parentDataProperty: i1, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate268.errors : vErrors.concat(validate268.errors);
                                  errors = vErrors.length;
                                }
                                var valid5 = _errs31 === errors;
                                if (!valid5) {
                                  break;
                                }
                              }
                            } else {
                              validate267.errors = [{ instancePath: instancePath + "/gaps", schemaPath: "#/properties/gaps/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs29 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.omitted_gap_count !== void 0) {
                            let data11 = data.omitted_gap_count;
                            const _errs32 = errors;
                            if (!(typeof data11 == "number" && (!(data11 % 1) && !isNaN(data11)))) {
                              validate267.errors = [{ instancePath: instancePath + "/omitted_gap_count", schemaPath: "#/properties/omitted_gap_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            var valid0 = _errs32 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.parameter_summaries !== void 0) {
                              let data12 = data.parameter_summaries;
                              const _errs34 = errors;
                              if (errors === _errs34) {
                                if (Array.isArray(data12)) {
                                  var valid6 = true;
                                  const len2 = data12.length;
                                  for (let i2 = 0; i2 < len2; i2++) {
                                    const _errs36 = errors;
                                    if (!validate270(data12[i2], { instancePath: instancePath + "/parameter_summaries/" + i2, parentData: data12, parentDataProperty: i2, rootData, dynamicAnchors })) {
                                      vErrors = vErrors === null ? validate270.errors : vErrors.concat(validate270.errors);
                                      errors = vErrors.length;
                                    }
                                    var valid6 = _errs36 === errors;
                                    if (!valid6) {
                                      break;
                                    }
                                  }
                                } else {
                                  validate267.errors = [{ instancePath: instancePath + "/parameter_summaries", schemaPath: "#/properties/parameter_summaries/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs34 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.omitted_parameter_count !== void 0) {
                                let data14 = data.omitted_parameter_count;
                                const _errs37 = errors;
                                if (!(typeof data14 == "number" && (!(data14 % 1) && !isNaN(data14)))) {
                                  validate267.errors = [{ instancePath: instancePath + "/omitted_parameter_count", schemaPath: "#/properties/omitted_parameter_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                var valid0 = _errs37 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.capabilities !== void 0) {
                                  let data15 = data.capabilities;
                                  const _errs39 = errors;
                                  if (errors === _errs39) {
                                    if (Array.isArray(data15)) {
                                      var valid7 = true;
                                      const len3 = data15.length;
                                      for (let i3 = 0; i3 < len3; i3++) {
                                        const _errs41 = errors;
                                        if (!validate272(data15[i3], { instancePath: instancePath + "/capabilities/" + i3, parentData: data15, parentDataProperty: i3, rootData, dynamicAnchors })) {
                                          vErrors = vErrors === null ? validate272.errors : vErrors.concat(validate272.errors);
                                          errors = vErrors.length;
                                        }
                                        var valid7 = _errs41 === errors;
                                        if (!valid7) {
                                          break;
                                        }
                                      }
                                    } else {
                                      validate267.errors = [{ instancePath: instancePath + "/capabilities", schemaPath: "#/properties/capabilities/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                      return false;
                                    }
                                  }
                                  var valid0 = _errs39 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.recorded_results !== void 0) {
                                    let data17 = data.recorded_results;
                                    const _errs42 = errors;
                                    if (errors === _errs42) {
                                      if (Array.isArray(data17)) {
                                        var valid8 = true;
                                        const len4 = data17.length;
                                        for (let i4 = 0; i4 < len4; i4++) {
                                          const _errs44 = errors;
                                          if (!validate274(data17[i4], { instancePath: instancePath + "/recorded_results/" + i4, parentData: data17, parentDataProperty: i4, rootData, dynamicAnchors })) {
                                            vErrors = vErrors === null ? validate274.errors : vErrors.concat(validate274.errors);
                                            errors = vErrors.length;
                                          }
                                          var valid8 = _errs44 === errors;
                                          if (!valid8) {
                                            break;
                                          }
                                        }
                                      } else {
                                        validate267.errors = [{ instancePath: instancePath + "/recorded_results", schemaPath: "#/properties/recorded_results/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                        return false;
                                      }
                                    }
                                    var valid0 = _errs42 === errors;
                                  } else {
                                    var valid0 = true;
                                  }
                                  if (valid0) {
                                    if (data.recorded_jobs !== void 0) {
                                      let data19 = data.recorded_jobs;
                                      const _errs45 = errors;
                                      if (errors === _errs45) {
                                        if (Array.isArray(data19)) {
                                          var valid9 = true;
                                          const len5 = data19.length;
                                          for (let i5 = 0; i5 < len5; i5++) {
                                            const _errs47 = errors;
                                            if (!validate276(data19[i5], { instancePath: instancePath + "/recorded_jobs/" + i5, parentData: data19, parentDataProperty: i5, rootData, dynamicAnchors })) {
                                              vErrors = vErrors === null ? validate276.errors : vErrors.concat(validate276.errors);
                                              errors = vErrors.length;
                                            }
                                            var valid9 = _errs47 === errors;
                                            if (!valid9) {
                                              break;
                                            }
                                          }
                                        } else {
                                          validate267.errors = [{ instancePath: instancePath + "/recorded_jobs", schemaPath: "#/properties/recorded_jobs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                          return false;
                                        }
                                      }
                                      var valid0 = _errs45 === errors;
                                    } else {
                                      var valid0 = true;
                                    }
                                    if (valid0) {
                                      if (data.accepted_proposal_refs !== void 0) {
                                        let data21 = data.accepted_proposal_refs;
                                        const _errs48 = errors;
                                        if (errors === _errs48) {
                                          if (Array.isArray(data21)) {
                                            var valid10 = true;
                                            const len6 = data21.length;
                                            for (let i6 = 0; i6 < len6; i6++) {
                                              const _errs50 = errors;
                                              if (typeof data21[i6] !== "string") {
                                                validate267.errors = [{ instancePath: instancePath + "/accepted_proposal_refs/" + i6, schemaPath: "#/properties/accepted_proposal_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                return false;
                                              }
                                              var valid10 = _errs50 === errors;
                                              if (!valid10) {
                                                break;
                                              }
                                            }
                                          } else {
                                            validate267.errors = [{ instancePath: instancePath + "/accepted_proposal_refs", schemaPath: "#/properties/accepted_proposal_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                            return false;
                                          }
                                        }
                                        var valid0 = _errs48 === errors;
                                      } else {
                                        var valid0 = true;
                                      }
                                      if (valid0) {
                                        if (data.budget !== void 0) {
                                          let data23 = data.budget;
                                          const _errs52 = errors;
                                          if (errors === _errs52) {
                                            if (data23 && typeof data23 == "object" && !Array.isArray(data23)) {
                                              for (const key2 in data23) {
                                                let data24 = data23[key2];
                                                const _errs55 = errors;
                                                const _errs56 = errors;
                                                let valid12 = false;
                                                const _errs57 = errors;
                                                if (!(typeof data24 == "number" && (!(data24 % 1) && !isNaN(data24)))) {
                                                  const err6 = { instancePath: instancePath + "/budget/" + key2.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/budget/additionalProperties/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                                  if (vErrors === null) {
                                                    vErrors = [err6];
                                                  } else {
                                                    vErrors.push(err6);
                                                  }
                                                  errors++;
                                                }
                                                var _valid2 = _errs57 === errors;
                                                valid12 = valid12 || _valid2;
                                                const _errs59 = errors;
                                                if (!(typeof data24 == "number")) {
                                                  const err7 = { instancePath: instancePath + "/budget/" + key2.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/budget/additionalProperties/anyOf/1/type", keyword: "type", params: { type: "number" }, message: "must be number" };
                                                  if (vErrors === null) {
                                                    vErrors = [err7];
                                                  } else {
                                                    vErrors.push(err7);
                                                  }
                                                  errors++;
                                                }
                                                var _valid2 = _errs59 === errors;
                                                valid12 = valid12 || _valid2;
                                                const _errs61 = errors;
                                                if (data24 !== null) {
                                                  const err8 = { instancePath: instancePath + "/budget/" + key2.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/budget/additionalProperties/anyOf/2/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                                  if (vErrors === null) {
                                                    vErrors = [err8];
                                                  } else {
                                                    vErrors.push(err8);
                                                  }
                                                  errors++;
                                                }
                                                var _valid2 = _errs61 === errors;
                                                valid12 = valid12 || _valid2;
                                                if (!valid12) {
                                                  const err9 = { instancePath: instancePath + "/budget/" + key2.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/budget/additionalProperties/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                                  if (vErrors === null) {
                                                    vErrors = [err9];
                                                  } else {
                                                    vErrors.push(err9);
                                                  }
                                                  errors++;
                                                  validate267.errors = vErrors;
                                                  return false;
                                                } else {
                                                  errors = _errs56;
                                                  if (vErrors !== null) {
                                                    if (_errs56) {
                                                      vErrors.length = _errs56;
                                                    } else {
                                                      vErrors = null;
                                                    }
                                                  }
                                                }
                                                var valid11 = _errs55 === errors;
                                                if (!valid11) {
                                                  break;
                                                }
                                              }
                                            } else {
                                              validate267.errors = [{ instancePath: instancePath + "/budget", schemaPath: "#/properties/budget/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                              return false;
                                            }
                                          }
                                          var valid0 = _errs52 === errors;
                                        } else {
                                          var valid0 = true;
                                        }
                                        if (valid0) {
                                          if (data.limitations !== void 0) {
                                            let data25 = data.limitations;
                                            const _errs63 = errors;
                                            if (errors === _errs63) {
                                              if (Array.isArray(data25)) {
                                                var valid13 = true;
                                                const len7 = data25.length;
                                                for (let i7 = 0; i7 < len7; i7++) {
                                                  const _errs65 = errors;
                                                  if (typeof data25[i7] !== "string") {
                                                    validate267.errors = [{ instancePath: instancePath + "/limitations/" + i7, schemaPath: "#/properties/limitations/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                    return false;
                                                  }
                                                  var valid13 = _errs65 === errors;
                                                  if (!valid13) {
                                                    break;
                                                  }
                                                }
                                              } else {
                                                validate267.errors = [{ instancePath: instancePath + "/limitations", schemaPath: "#/properties/limitations/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                                return false;
                                              }
                                            }
                                            var valid0 = _errs63 === errors;
                                          } else {
                                            var valid0 = true;
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate267.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate267.errors = vErrors;
  return errors === 0;
}
validate267.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var func2 = require_ucs2length().default;
function validate279(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate279.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.reason === void 0 && (missing0 = "reason") || data.evidence_refs === void 0 && (missing0 = "evidence_refs") || data.kind === void 0 && (missing0 = "kind")) {
        validate279.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "reason" || key0 === "evidence_refs" || key0 === "kind")) {
            validate279.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.reason !== void 0) {
            let data0 = data.reason;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (typeof data0 === "string") {
                if (func2(data0) < 1) {
                  validate279.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                  return false;
                }
              } else {
                validate279.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.evidence_refs !== void 0) {
              let data1 = data.evidence_refs;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (typeof data1[i0] !== "string") {
                      validate279.errors = [{ instancePath: instancePath + "/evidence_refs/" + i0, schemaPath: "#/properties/evidence_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate279.errors = [{ instancePath: instancePath + "/evidence_refs", schemaPath: "#/properties/evidence_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.kind !== void 0) {
                let data3 = data.kind;
                const _errs8 = errors;
                if (typeof data3 !== "string") {
                  validate279.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("inspect_project" !== data3) {
                  validate279.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "inspect_project" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs8 === errors;
              } else {
                var valid0 = true;
              }
            }
          }
        }
      }
    } else {
      validate279.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate279.errors = vErrors;
  return errors === 0;
}
validate279.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema121 = { "additionalProperties": false, "properties": { "reason": { "minLength": 1, "title": "Reason", "type": "string" }, "evidence_refs": { "items": { "type": "string" }, "title": "Evidence Refs", "type": "array" }, "kind": { "const": "retrieve_evidence", "title": "Kind", "type": "string" }, "query": { "minLength": 1, "title": "Query", "type": "string" }, "source_scope": { "enum": ["project_registry", "registered_artifacts"], "title": "Source Scope", "type": "string" } }, "required": ["reason", "evidence_refs", "kind", "query", "source_scope"], "title": "RetrieveEvidenceAction", "type": "object" };
function validate281(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate281.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.reason === void 0 && (missing0 = "reason") || data.evidence_refs === void 0 && (missing0 = "evidence_refs") || data.kind === void 0 && (missing0 = "kind") || data.query === void 0 && (missing0 = "query") || data.source_scope === void 0 && (missing0 = "source_scope")) {
        validate281.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "reason" || key0 === "evidence_refs" || key0 === "kind" || key0 === "query" || key0 === "source_scope")) {
            validate281.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.reason !== void 0) {
            let data0 = data.reason;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (typeof data0 === "string") {
                if (func2(data0) < 1) {
                  validate281.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                  return false;
                }
              } else {
                validate281.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.evidence_refs !== void 0) {
              let data1 = data.evidence_refs;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (typeof data1[i0] !== "string") {
                      validate281.errors = [{ instancePath: instancePath + "/evidence_refs/" + i0, schemaPath: "#/properties/evidence_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate281.errors = [{ instancePath: instancePath + "/evidence_refs", schemaPath: "#/properties/evidence_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.kind !== void 0) {
                let data3 = data.kind;
                const _errs8 = errors;
                if (typeof data3 !== "string") {
                  validate281.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("retrieve_evidence" !== data3) {
                  validate281.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "retrieve_evidence" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs8 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.query !== void 0) {
                  let data4 = data.query;
                  const _errs10 = errors;
                  if (errors === _errs10) {
                    if (typeof data4 === "string") {
                      if (func2(data4) < 1) {
                        validate281.errors = [{ instancePath: instancePath + "/query", schemaPath: "#/properties/query/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      }
                    } else {
                      validate281.errors = [{ instancePath: instancePath + "/query", schemaPath: "#/properties/query/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs10 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.source_scope !== void 0) {
                    let data5 = data.source_scope;
                    const _errs12 = errors;
                    if (typeof data5 !== "string") {
                      validate281.errors = [{ instancePath: instancePath + "/source_scope", schemaPath: "#/properties/source_scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data5 === "project_registry" || data5 === "registered_artifacts")) {
                      validate281.errors = [{ instancePath: instancePath + "/source_scope", schemaPath: "#/properties/source_scope/enum", keyword: "enum", params: { allowedValues: schema121.properties.source_scope.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs12 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate281.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate281.errors = vErrors;
  return errors === 0;
}
validate281.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate283(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate283.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.reason === void 0 && (missing0 = "reason") || data.evidence_refs === void 0 && (missing0 = "evidence_refs") || data.kind === void 0 && (missing0 = "kind") || data.tool_id === void 0 && (missing0 = "tool_id") || data.input_refs === void 0 && (missing0 = "input_refs")) {
        validate283.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "reason" || key0 === "evidence_refs" || key0 === "kind" || key0 === "tool_id" || key0 === "input_refs")) {
            validate283.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.reason !== void 0) {
            let data0 = data.reason;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (typeof data0 === "string") {
                if (func2(data0) < 1) {
                  validate283.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                  return false;
                }
              } else {
                validate283.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.evidence_refs !== void 0) {
              let data1 = data.evidence_refs;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (typeof data1[i0] !== "string") {
                      validate283.errors = [{ instancePath: instancePath + "/evidence_refs/" + i0, schemaPath: "#/properties/evidence_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate283.errors = [{ instancePath: instancePath + "/evidence_refs", schemaPath: "#/properties/evidence_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.kind !== void 0) {
                let data3 = data.kind;
                const _errs8 = errors;
                if (typeof data3 !== "string") {
                  validate283.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("prepare_node" !== data3) {
                  validate283.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "prepare_node" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs8 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.tool_id !== void 0) {
                  const _errs10 = errors;
                  if (typeof data.tool_id !== "string") {
                    validate283.errors = [{ instancePath: instancePath + "/tool_id", schemaPath: "#/properties/tool_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs10 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.input_refs !== void 0) {
                    let data5 = data.input_refs;
                    const _errs12 = errors;
                    if (errors === _errs12) {
                      if (Array.isArray(data5)) {
                        var valid2 = true;
                        const len1 = data5.length;
                        for (let i1 = 0; i1 < len1; i1++) {
                          const _errs14 = errors;
                          if (typeof data5[i1] !== "string") {
                            validate283.errors = [{ instancePath: instancePath + "/input_refs/" + i1, schemaPath: "#/properties/input_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid2 = _errs14 === errors;
                          if (!valid2) {
                            break;
                          }
                        }
                      } else {
                        validate283.errors = [{ instancePath: instancePath + "/input_refs", schemaPath: "#/properties/input_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs12 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate283.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate283.errors = vErrors;
  return errors === 0;
}
validate283.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate285(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate285.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.reason === void 0 && (missing0 = "reason") || data.evidence_refs === void 0 && (missing0 = "evidence_refs") || data.kind === void 0 && (missing0 = "kind") || data.reviewed_proposal_id === void 0 && (missing0 = "reviewed_proposal_id")) {
        validate285.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "reason" || key0 === "evidence_refs" || key0 === "kind" || key0 === "reviewed_proposal_id")) {
            validate285.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.reason !== void 0) {
            let data0 = data.reason;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (typeof data0 === "string") {
                if (func2(data0) < 1) {
                  validate285.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                  return false;
                }
              } else {
                validate285.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.evidence_refs !== void 0) {
              let data1 = data.evidence_refs;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (typeof data1[i0] !== "string") {
                      validate285.errors = [{ instancePath: instancePath + "/evidence_refs/" + i0, schemaPath: "#/properties/evidence_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate285.errors = [{ instancePath: instancePath + "/evidence_refs", schemaPath: "#/properties/evidence_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.kind !== void 0) {
                let data3 = data.kind;
                const _errs8 = errors;
                if (typeof data3 !== "string") {
                  validate285.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("submit_job" !== data3) {
                  validate285.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "submit_job" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs8 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.reviewed_proposal_id !== void 0) {
                  const _errs10 = errors;
                  if (typeof data.reviewed_proposal_id !== "string") {
                    validate285.errors = [{ instancePath: instancePath + "/reviewed_proposal_id", schemaPath: "#/properties/reviewed_proposal_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs10 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        }
      }
    } else {
      validate285.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate285.errors = vErrors;
  return errors === 0;
}
validate285.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate287(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate287.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.reason === void 0 && (missing0 = "reason") || data.evidence_refs === void 0 && (missing0 = "evidence_refs") || data.kind === void 0 && (missing0 = "kind") || data.run_id === void 0 && (missing0 = "run_id")) {
        validate287.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "reason" || key0 === "evidence_refs" || key0 === "kind" || key0 === "run_id")) {
            validate287.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.reason !== void 0) {
            let data0 = data.reason;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (typeof data0 === "string") {
                if (func2(data0) < 1) {
                  validate287.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                  return false;
                }
              } else {
                validate287.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.evidence_refs !== void 0) {
              let data1 = data.evidence_refs;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (typeof data1[i0] !== "string") {
                      validate287.errors = [{ instancePath: instancePath + "/evidence_refs/" + i0, schemaPath: "#/properties/evidence_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate287.errors = [{ instancePath: instancePath + "/evidence_refs", schemaPath: "#/properties/evidence_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.kind !== void 0) {
                let data3 = data.kind;
                const _errs8 = errors;
                if (typeof data3 !== "string") {
                  validate287.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("inspect_job" !== data3) {
                  validate287.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "inspect_job" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs8 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  const _errs10 = errors;
                  if (typeof data.run_id !== "string") {
                    validate287.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs10 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        }
      }
    } else {
      validate287.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate287.errors = vErrors;
  return errors === 0;
}
validate287.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema125 = { "additionalProperties": false, "properties": { "reason": { "minLength": 1, "title": "Reason", "type": "string" }, "evidence_refs": { "items": { "type": "string" }, "title": "Evidence Refs", "type": "array" }, "kind": { "const": "evaluate_result", "title": "Kind", "type": "string" }, "result_ref": { "title": "Result Ref", "type": "string" }, "metric": { "enum": ["recorded_stage_status", "recorded_mass_balance", "recorded_applicability"], "title": "Metric", "type": "string" } }, "required": ["reason", "evidence_refs", "kind", "result_ref", "metric"], "title": "EvaluateResultAction", "type": "object" };
function validate289(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate289.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.reason === void 0 && (missing0 = "reason") || data.evidence_refs === void 0 && (missing0 = "evidence_refs") || data.kind === void 0 && (missing0 = "kind") || data.result_ref === void 0 && (missing0 = "result_ref") || data.metric === void 0 && (missing0 = "metric")) {
        validate289.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "reason" || key0 === "evidence_refs" || key0 === "kind" || key0 === "result_ref" || key0 === "metric")) {
            validate289.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.reason !== void 0) {
            let data0 = data.reason;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (typeof data0 === "string") {
                if (func2(data0) < 1) {
                  validate289.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                  return false;
                }
              } else {
                validate289.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.evidence_refs !== void 0) {
              let data1 = data.evidence_refs;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (typeof data1[i0] !== "string") {
                      validate289.errors = [{ instancePath: instancePath + "/evidence_refs/" + i0, schemaPath: "#/properties/evidence_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate289.errors = [{ instancePath: instancePath + "/evidence_refs", schemaPath: "#/properties/evidence_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.kind !== void 0) {
                let data3 = data.kind;
                const _errs8 = errors;
                if (typeof data3 !== "string") {
                  validate289.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("evaluate_result" !== data3) {
                  validate289.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "evaluate_result" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs8 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.result_ref !== void 0) {
                  const _errs10 = errors;
                  if (typeof data.result_ref !== "string") {
                    validate289.errors = [{ instancePath: instancePath + "/result_ref", schemaPath: "#/properties/result_ref/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs10 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.metric !== void 0) {
                    let data5 = data.metric;
                    const _errs12 = errors;
                    if (typeof data5 !== "string") {
                      validate289.errors = [{ instancePath: instancePath + "/metric", schemaPath: "#/properties/metric/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data5 === "recorded_stage_status" || data5 === "recorded_mass_balance" || data5 === "recorded_applicability")) {
                      validate289.errors = [{ instancePath: instancePath + "/metric", schemaPath: "#/properties/metric/enum", keyword: "enum", params: { allowedValues: schema125.properties.metric.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs12 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate289.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate289.errors = vErrors;
  return errors === 0;
}
validate289.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate291(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate291.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.reason === void 0 && (missing0 = "reason") || data.evidence_refs === void 0 && (missing0 = "evidence_refs") || data.kind === void 0 && (missing0 = "kind") || data.hypothesis === void 0 && (missing0 = "hypothesis") || data.controls === void 0 && (missing0 = "controls") || data.observable === void 0 && (missing0 = "observable") || data.refutation_criterion === void 0 && (missing0 = "refutation_criterion") || data.requires_human_review === void 0 && (missing0 = "requires_human_review")) {
        validate291.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "reason" || key0 === "evidence_refs" || key0 === "kind" || key0 === "hypothesis" || key0 === "controls" || key0 === "observable" || key0 === "refutation_criterion" || key0 === "requires_human_review")) {
            validate291.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.reason !== void 0) {
            let data0 = data.reason;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (typeof data0 === "string") {
                if (func2(data0) < 1) {
                  validate291.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                  return false;
                }
              } else {
                validate291.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.evidence_refs !== void 0) {
              let data1 = data.evidence_refs;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (typeof data1[i0] !== "string") {
                      validate291.errors = [{ instancePath: instancePath + "/evidence_refs/" + i0, schemaPath: "#/properties/evidence_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate291.errors = [{ instancePath: instancePath + "/evidence_refs", schemaPath: "#/properties/evidence_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.kind !== void 0) {
                let data3 = data.kind;
                const _errs8 = errors;
                if (typeof data3 !== "string") {
                  validate291.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("propose_experiment" !== data3) {
                  validate291.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "propose_experiment" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs8 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.hypothesis !== void 0) {
                  let data4 = data.hypothesis;
                  const _errs10 = errors;
                  if (errors === _errs10) {
                    if (typeof data4 === "string") {
                      if (func2(data4) < 1) {
                        validate291.errors = [{ instancePath: instancePath + "/hypothesis", schemaPath: "#/properties/hypothesis/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      }
                    } else {
                      validate291.errors = [{ instancePath: instancePath + "/hypothesis", schemaPath: "#/properties/hypothesis/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs10 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.controls !== void 0) {
                    let data5 = data.controls;
                    const _errs12 = errors;
                    if (errors === _errs12) {
                      if (Array.isArray(data5)) {
                        if (data5.length < 1) {
                          validate291.errors = [{ instancePath: instancePath + "/controls", schemaPath: "#/properties/controls/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                          return false;
                        } else {
                          var valid2 = true;
                          const len1 = data5.length;
                          for (let i1 = 0; i1 < len1; i1++) {
                            const _errs14 = errors;
                            if (typeof data5[i1] !== "string") {
                              validate291.errors = [{ instancePath: instancePath + "/controls/" + i1, schemaPath: "#/properties/controls/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid2 = _errs14 === errors;
                            if (!valid2) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate291.errors = [{ instancePath: instancePath + "/controls", schemaPath: "#/properties/controls/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs12 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.observable !== void 0) {
                      let data7 = data.observable;
                      const _errs16 = errors;
                      if (errors === _errs16) {
                        if (typeof data7 === "string") {
                          if (func2(data7) < 1) {
                            validate291.errors = [{ instancePath: instancePath + "/observable", schemaPath: "#/properties/observable/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          }
                        } else {
                          validate291.errors = [{ instancePath: instancePath + "/observable", schemaPath: "#/properties/observable/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs16 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.refutation_criterion !== void 0) {
                        let data8 = data.refutation_criterion;
                        const _errs18 = errors;
                        if (errors === _errs18) {
                          if (typeof data8 === "string") {
                            if (func2(data8) < 1) {
                              validate291.errors = [{ instancePath: instancePath + "/refutation_criterion", schemaPath: "#/properties/refutation_criterion/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            }
                          } else {
                            validate291.errors = [{ instancePath: instancePath + "/refutation_criterion", schemaPath: "#/properties/refutation_criterion/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs18 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.requires_human_review !== void 0) {
                          let data9 = data.requires_human_review;
                          const _errs20 = errors;
                          if (typeof data9 !== "boolean") {
                            validate291.errors = [{ instancePath: instancePath + "/requires_human_review", schemaPath: "#/properties/requires_human_review/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                            return false;
                          }
                          if (true !== data9) {
                            validate291.errors = [{ instancePath: instancePath + "/requires_human_review", schemaPath: "#/properties/requires_human_review/const", keyword: "const", params: { allowedValue: true }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid0 = _errs20 === errors;
                        } else {
                          var valid0 = true;
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate291.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate291.errors = vErrors;
  return errors === 0;
}
validate291.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate293(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate293.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.reason === void 0 && (missing0 = "reason") || data.evidence_refs === void 0 && (missing0 = "evidence_refs") || data.kind === void 0 && (missing0 = "kind") || data.pending_refs === void 0 && (missing0 = "pending_refs")) {
        validate293.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "reason" || key0 === "evidence_refs" || key0 === "kind" || key0 === "pending_refs")) {
            validate293.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.reason !== void 0) {
            let data0 = data.reason;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (typeof data0 === "string") {
                if (func2(data0) < 1) {
                  validate293.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                  return false;
                }
              } else {
                validate293.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.evidence_refs !== void 0) {
              let data1 = data.evidence_refs;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (typeof data1[i0] !== "string") {
                      validate293.errors = [{ instancePath: instancePath + "/evidence_refs/" + i0, schemaPath: "#/properties/evidence_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate293.errors = [{ instancePath: instancePath + "/evidence_refs", schemaPath: "#/properties/evidence_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.kind !== void 0) {
                let data3 = data.kind;
                const _errs8 = errors;
                if (typeof data3 !== "string") {
                  validate293.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("wait" !== data3) {
                  validate293.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "wait" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs8 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.pending_refs !== void 0) {
                  let data4 = data.pending_refs;
                  const _errs10 = errors;
                  if (errors === _errs10) {
                    if (Array.isArray(data4)) {
                      if (data4.length < 1) {
                        validate293.errors = [{ instancePath: instancePath + "/pending_refs", schemaPath: "#/properties/pending_refs/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                        return false;
                      } else {
                        var valid2 = true;
                        const len1 = data4.length;
                        for (let i1 = 0; i1 < len1; i1++) {
                          const _errs12 = errors;
                          if (typeof data4[i1] !== "string") {
                            validate293.errors = [{ instancePath: instancePath + "/pending_refs/" + i1, schemaPath: "#/properties/pending_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid2 = _errs12 === errors;
                          if (!valid2) {
                            break;
                          }
                        }
                      }
                    } else {
                      validate293.errors = [{ instancePath: instancePath + "/pending_refs", schemaPath: "#/properties/pending_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs10 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        }
      }
    } else {
      validate293.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate293.errors = vErrors;
  return errors === 0;
}
validate293.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema128 = { "additionalProperties": false, "properties": { "reason": { "minLength": 1, "title": "Reason", "type": "string" }, "evidence_refs": { "items": { "type": "string" }, "title": "Evidence Refs", "type": "array" }, "kind": { "const": "finish", "title": "Kind", "type": "string" }, "outcome": { "enum": ["available_work_completed", "human_input_required", "no_compute_requested"], "title": "Outcome", "type": "string" } }, "required": ["reason", "evidence_refs", "kind", "outcome"], "title": "FinishAction", "type": "object" };
function validate295(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate295.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.reason === void 0 && (missing0 = "reason") || data.evidence_refs === void 0 && (missing0 = "evidence_refs") || data.kind === void 0 && (missing0 = "kind") || data.outcome === void 0 && (missing0 = "outcome")) {
        validate295.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "reason" || key0 === "evidence_refs" || key0 === "kind" || key0 === "outcome")) {
            validate295.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.reason !== void 0) {
            let data0 = data.reason;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (typeof data0 === "string") {
                if (func2(data0) < 1) {
                  validate295.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                  return false;
                }
              } else {
                validate295.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.evidence_refs !== void 0) {
              let data1 = data.evidence_refs;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (typeof data1[i0] !== "string") {
                      validate295.errors = [{ instancePath: instancePath + "/evidence_refs/" + i0, schemaPath: "#/properties/evidence_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate295.errors = [{ instancePath: instancePath + "/evidence_refs", schemaPath: "#/properties/evidence_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.kind !== void 0) {
                let data3 = data.kind;
                const _errs8 = errors;
                if (typeof data3 !== "string") {
                  validate295.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("finish" !== data3) {
                  validate295.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "finish" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs8 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.outcome !== void 0) {
                  let data4 = data.outcome;
                  const _errs10 = errors;
                  if (typeof data4 !== "string") {
                    validate295.errors = [{ instancePath: instancePath + "/outcome", schemaPath: "#/properties/outcome/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data4 === "available_work_completed" || data4 === "human_input_required" || data4 === "no_compute_requested")) {
                    validate295.errors = [{ instancePath: instancePath + "/outcome", schemaPath: "#/properties/outcome/enum", keyword: "enum", params: { allowedValues: schema128.properties.outcome.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs10 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        }
      }
    } else {
      validate295.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate295.errors = vErrors;
  return errors === 0;
}
validate295.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var pattern10 = new RegExp("^[A-Za-z0-9_.-]+$", "u");
function validate233(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate233.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.kind === void 0 && (missing0 = "kind") || data.value === void 0 && (missing0 = "value")) {
        validate233.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "kind" || key0 === "value")) {
            validate233.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.kind !== void 0) {
            let data0 = data.kind;
            if (typeof data0 !== "string") {
              validate233.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            if ("literal" !== data0) {
              validate233.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "literal" }, message: "must be equal to constant" }];
              return false;
            }
          }
        }
      }
    } else {
      validate233.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate233.errors = vErrors;
  return errors === 0;
}
validate233.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate235(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate235.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.kind === void 0 && (missing0 = "kind") || data.path === void 0 && (missing0 = "path")) {
        validate235.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "kind" || key0 === "path")) {
            validate235.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.kind !== void 0) {
            let data0 = data.kind;
            const _errs2 = errors;
            if (typeof data0 !== "string") {
              validate235.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            if ("project" !== data0) {
              validate235.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "project" }, message: "must be equal to constant" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.path !== void 0) {
              let data1 = data.path;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    let data2 = data1[i0];
                    const _errs6 = errors;
                    const _errs7 = errors;
                    let valid2 = false;
                    const _errs8 = errors;
                    if (typeof data2 !== "string") {
                      const err0 = { instancePath: instancePath + "/path/" + i0, schemaPath: "#/properties/path/items/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    }
                    var _valid0 = _errs8 === errors;
                    valid2 = valid2 || _valid0;
                    const _errs10 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                      const err1 = { instancePath: instancePath + "/path/" + i0, schemaPath: "#/properties/path/items/anyOf/1/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                      if (vErrors === null) {
                        vErrors = [err1];
                      } else {
                        vErrors.push(err1);
                      }
                      errors++;
                    }
                    var _valid0 = _errs10 === errors;
                    valid2 = valid2 || _valid0;
                    if (!valid2) {
                      const err2 = { instancePath: instancePath + "/path/" + i0, schemaPath: "#/properties/path/items/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err2];
                      } else {
                        vErrors.push(err2);
                      }
                      errors++;
                      validate235.errors = vErrors;
                      return false;
                    } else {
                      errors = _errs7;
                      if (vErrors !== null) {
                        if (_errs7) {
                          vErrors.length = _errs7;
                        } else {
                          vErrors = null;
                        }
                      }
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate235.errors = [{ instancePath: instancePath + "/path", schemaPath: "#/properties/path/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
          }
        }
      }
    } else {
      validate235.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate235.errors = vErrors;
  return errors === 0;
}
validate235.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate237(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate237.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.kind === void 0 && (missing0 = "kind") || data.node_id === void 0 && (missing0 = "node_id") || data.path === void 0 && (missing0 = "path")) {
        validate237.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "kind" || key0 === "node_id" || key0 === "path")) {
            validate237.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.kind !== void 0) {
            let data0 = data.kind;
            const _errs2 = errors;
            if (typeof data0 !== "string") {
              validate237.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            if ("node" !== data0) {
              validate237.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "node" }, message: "must be equal to constant" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.node_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.node_id !== "string") {
                validate237.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.path !== void 0) {
                let data2 = data.path;
                const _errs6 = errors;
                if (errors === _errs6) {
                  if (Array.isArray(data2)) {
                    var valid1 = true;
                    const len0 = data2.length;
                    for (let i0 = 0; i0 < len0; i0++) {
                      let data3 = data2[i0];
                      const _errs8 = errors;
                      const _errs9 = errors;
                      let valid2 = false;
                      const _errs10 = errors;
                      if (typeof data3 !== "string") {
                        const err0 = { instancePath: instancePath + "/path/" + i0, schemaPath: "#/properties/path/items/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      }
                      var _valid0 = _errs10 === errors;
                      valid2 = valid2 || _valid0;
                      const _errs12 = errors;
                      if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)))) {
                        const err1 = { instancePath: instancePath + "/path/" + i0, schemaPath: "#/properties/path/items/anyOf/1/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      }
                      var _valid0 = _errs12 === errors;
                      valid2 = valid2 || _valid0;
                      if (!valid2) {
                        const err2 = { instancePath: instancePath + "/path/" + i0, schemaPath: "#/properties/path/items/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err2];
                        } else {
                          vErrors.push(err2);
                        }
                        errors++;
                        validate237.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs9;
                        if (vErrors !== null) {
                          if (_errs9) {
                            vErrors.length = _errs9;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid1 = _errs8 === errors;
                      if (!valid1) {
                        break;
                      }
                    }
                  } else {
                    validate237.errors = [{ instancePath: instancePath + "/path", schemaPath: "#/properties/path/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
            }
          }
        }
      }
    } else {
      validate237.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate237.errors = vErrors;
  return errors === 0;
}
validate237.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema100 = { "additionalProperties": false, "properties": { "kind": { "const": "sequence", "default": "sequence", "title": "Kind", "type": "string" }, "source": { "enum": ["project", "scientific_fasta"], "title": "Source", "type": "string" }, "file_id": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "File Id" }, "record_id": { "title": "Record Id", "type": "string" }, "sequence_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sequence Sha256", "type": "string" }, "construct_version": { "minimum": 1, "title": "Construct Version", "type": "integer" } }, "required": ["kind", "source", "file_id", "record_id", "sequence_sha256", "construct_version"], "title": "SequenceRef", "type": "object" };
var pattern4 = new RegExp("^[0-9a-f]{64}$", "u");
function validate239(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate239.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.kind === void 0 && (missing0 = "kind") || data.source === void 0 && (missing0 = "source") || data.file_id === void 0 && (missing0 = "file_id") || data.record_id === void 0 && (missing0 = "record_id") || data.sequence_sha256 === void 0 && (missing0 = "sequence_sha256") || data.construct_version === void 0 && (missing0 = "construct_version")) {
        validate239.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "kind" || key0 === "source" || key0 === "file_id" || key0 === "record_id" || key0 === "sequence_sha256" || key0 === "construct_version")) {
            validate239.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.kind !== void 0) {
            let data0 = data.kind;
            const _errs2 = errors;
            if (typeof data0 !== "string") {
              validate239.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            if ("sequence" !== data0) {
              validate239.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "sequence" }, message: "must be equal to constant" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.source !== void 0) {
              let data1 = data.source;
              const _errs4 = errors;
              if (typeof data1 !== "string") {
                validate239.errors = [{ instancePath: instancePath + "/source", schemaPath: "#/properties/source/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              if (!(data1 === "project" || data1 === "scientific_fasta")) {
                validate239.errors = [{ instancePath: instancePath + "/source", schemaPath: "#/properties/source/enum", keyword: "enum", params: { allowedValues: schema100.properties.source.enum }, message: "must be equal to one of the allowed values" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.file_id !== void 0) {
                let data2 = data.file_id;
                const _errs6 = errors;
                const _errs7 = errors;
                let valid1 = false;
                const _errs8 = errors;
                if (typeof data2 !== "string") {
                  const err0 = { instancePath: instancePath + "/file_id", schemaPath: "#/properties/file_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                }
                var _valid0 = _errs8 === errors;
                valid1 = valid1 || _valid0;
                const _errs10 = errors;
                if (data2 !== null) {
                  const err1 = { instancePath: instancePath + "/file_id", schemaPath: "#/properties/file_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                }
                var _valid0 = _errs10 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err2 = { instancePath: instancePath + "/file_id", schemaPath: "#/properties/file_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err2];
                  } else {
                    vErrors.push(err2);
                  }
                  errors++;
                  validate239.errors = vErrors;
                  return false;
                } else {
                  errors = _errs7;
                  if (vErrors !== null) {
                    if (_errs7) {
                      vErrors.length = _errs7;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.record_id !== void 0) {
                  const _errs12 = errors;
                  if (typeof data.record_id !== "string") {
                    validate239.errors = [{ instancePath: instancePath + "/record_id", schemaPath: "#/properties/record_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs12 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.sequence_sha256 !== void 0) {
                    let data4 = data.sequence_sha256;
                    const _errs14 = errors;
                    if (errors === _errs14) {
                      if (typeof data4 === "string") {
                        if (!pattern4.test(data4)) {
                          validate239.errors = [{ instancePath: instancePath + "/sequence_sha256", schemaPath: "#/properties/sequence_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate239.errors = [{ instancePath: instancePath + "/sequence_sha256", schemaPath: "#/properties/sequence_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs14 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.construct_version !== void 0) {
                      let data5 = data.construct_version;
                      const _errs16 = errors;
                      if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)))) {
                        validate239.errors = [{ instancePath: instancePath + "/construct_version", schemaPath: "#/properties/construct_version/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      if (errors === _errs16) {
                        if (typeof data5 == "number") {
                          if (data5 < 1 || isNaN(data5)) {
                            validate239.errors = [{ instancePath: instancePath + "/construct_version", schemaPath: "#/properties/construct_version/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                      var valid0 = _errs16 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate239.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate239.errors = vErrors;
  return errors === 0;
}
validate239.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate241(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate241.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.items === void 0 && (missing0 = "items") || data.item_argument === void 0 && (missing0 = "item_argument")) {
        validate241.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "items" || key0 === "item_argument")) {
            validate241.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.items !== void 0) {
            let data0 = data.items;
            const _errs2 = errors;
            const _errs3 = errors;
            let valid1 = false;
            let passing0 = null;
            const _errs4 = errors;
            if (!validate233(data0, { instancePath: instancePath + "/items", parentData: data, parentDataProperty: "items", rootData, dynamicAnchors })) {
              vErrors = vErrors === null ? validate233.errors : vErrors.concat(validate233.errors);
              errors = vErrors.length;
            }
            var _valid0 = _errs4 === errors;
            if (_valid0) {
              valid1 = true;
              passing0 = 0;
              var props0 = true;
            }
            const _errs5 = errors;
            if (!validate235(data0, { instancePath: instancePath + "/items", parentData: data, parentDataProperty: "items", rootData, dynamicAnchors })) {
              vErrors = vErrors === null ? validate235.errors : vErrors.concat(validate235.errors);
              errors = vErrors.length;
            }
            var _valid0 = _errs5 === errors;
            if (_valid0 && valid1) {
              valid1 = false;
              passing0 = [passing0, 1];
            } else {
              if (_valid0) {
                valid1 = true;
                passing0 = 1;
                if (props0 !== true) {
                  props0 = true;
                }
              }
              const _errs6 = errors;
              if (!validate237(data0, { instancePath: instancePath + "/items", parentData: data, parentDataProperty: "items", rootData, dynamicAnchors })) {
                vErrors = vErrors === null ? validate237.errors : vErrors.concat(validate237.errors);
                errors = vErrors.length;
              }
              var _valid0 = _errs6 === errors;
              if (_valid0 && valid1) {
                valid1 = false;
                passing0 = [passing0, 2];
              } else {
                if (_valid0) {
                  valid1 = true;
                  passing0 = 2;
                  if (props0 !== true) {
                    props0 = true;
                  }
                }
                const _errs7 = errors;
                if (!validate239(data0, { instancePath: instancePath + "/items", parentData: data, parentDataProperty: "items", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate239.errors : vErrors.concat(validate239.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs7 === errors;
                if (_valid0 && valid1) {
                  valid1 = false;
                  passing0 = [passing0, 3];
                } else {
                  if (_valid0) {
                    valid1 = true;
                    passing0 = 3;
                    if (props0 !== true) {
                      props0 = true;
                    }
                  }
                }
              }
            }
            if (!valid1) {
              const err0 = { instancePath: instancePath + "/items", schemaPath: "#/properties/items/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
              if (vErrors === null) {
                vErrors = [err0];
              } else {
                vErrors.push(err0);
              }
              errors++;
              validate241.errors = vErrors;
              return false;
            } else {
              errors = _errs3;
              if (vErrors !== null) {
                if (_errs3) {
                  vErrors.length = _errs3;
                } else {
                  vErrors = null;
                }
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.item_argument !== void 0) {
              const _errs8 = errors;
              if (typeof data.item_argument !== "string") {
                validate241.errors = [{ instancePath: instancePath + "/item_argument", schemaPath: "#/properties/item_argument/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs8 === errors;
            } else {
              var valid0 = true;
            }
          }
        }
      }
    } else {
      validate241.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate241.errors = vErrors;
  return errors === 0;
}
validate241.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate298(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate298.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.label === void 0 && (missing0 = "label") || data.tool_id === void 0 && (missing0 = "tool_id") || data.inputs === void 0 && (missing0 = "inputs") || data.depends_on === void 0 && (missing0 = "depends_on") || data.map === void 0 && (missing0 = "map")) {
        validate298.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "label" || key0 === "tool_id" || key0 === "inputs" || key0 === "depends_on" || key0 === "map")) {
            validate298.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            let data0 = data.id;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (typeof data0 === "string") {
                if (func2(data0) < 1) {
                  validate298.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                  return false;
                } else {
                  if (!pattern10.test(data0)) {
                    validate298.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9_.-]+$" }, message: 'must match pattern "^[A-Za-z0-9_.-]+$"' }];
                    return false;
                  }
                }
              } else {
                validate298.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.label !== void 0) {
              const _errs4 = errors;
              if (typeof data.label !== "string") {
                validate298.errors = [{ instancePath: instancePath + "/label", schemaPath: "#/properties/label/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.tool_id !== void 0) {
                const _errs6 = errors;
                if (typeof data.tool_id !== "string") {
                  validate298.errors = [{ instancePath: instancePath + "/tool_id", schemaPath: "#/properties/tool_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.inputs !== void 0) {
                  let data3 = data.inputs;
                  const _errs8 = errors;
                  if (errors === _errs8) {
                    if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                      for (const key1 in data3) {
                        let data4 = data3[key1];
                        const _errs11 = errors;
                        const _errs12 = errors;
                        let valid2 = false;
                        let passing0 = null;
                        const _errs13 = errors;
                        if (!validate233(data4, { instancePath: instancePath + "/inputs/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), parentData: data3, parentDataProperty: key1, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate233.errors : vErrors.concat(validate233.errors);
                          errors = vErrors.length;
                        }
                        var _valid0 = _errs13 === errors;
                        if (_valid0) {
                          valid2 = true;
                          passing0 = 0;
                          var props0 = true;
                        }
                        const _errs14 = errors;
                        if (!validate235(data4, { instancePath: instancePath + "/inputs/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), parentData: data3, parentDataProperty: key1, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate235.errors : vErrors.concat(validate235.errors);
                          errors = vErrors.length;
                        }
                        var _valid0 = _errs14 === errors;
                        if (_valid0 && valid2) {
                          valid2 = false;
                          passing0 = [passing0, 1];
                        } else {
                          if (_valid0) {
                            valid2 = true;
                            passing0 = 1;
                            if (props0 !== true) {
                              props0 = true;
                            }
                          }
                          const _errs15 = errors;
                          if (!validate237(data4, { instancePath: instancePath + "/inputs/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), parentData: data3, parentDataProperty: key1, rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate237.errors : vErrors.concat(validate237.errors);
                            errors = vErrors.length;
                          }
                          var _valid0 = _errs15 === errors;
                          if (_valid0 && valid2) {
                            valid2 = false;
                            passing0 = [passing0, 2];
                          } else {
                            if (_valid0) {
                              valid2 = true;
                              passing0 = 2;
                              if (props0 !== true) {
                                props0 = true;
                              }
                            }
                            const _errs16 = errors;
                            if (!validate239(data4, { instancePath: instancePath + "/inputs/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), parentData: data3, parentDataProperty: key1, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate239.errors : vErrors.concat(validate239.errors);
                              errors = vErrors.length;
                            }
                            var _valid0 = _errs16 === errors;
                            if (_valid0 && valid2) {
                              valid2 = false;
                              passing0 = [passing0, 3];
                            } else {
                              if (_valid0) {
                                valid2 = true;
                                passing0 = 3;
                                if (props0 !== true) {
                                  props0 = true;
                                }
                              }
                            }
                          }
                        }
                        if (!valid2) {
                          const err0 = { instancePath: instancePath + "/inputs/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/inputs/additionalProperties/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                          validate298.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs12;
                          if (vErrors !== null) {
                            if (_errs12) {
                              vErrors.length = _errs12;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid1 = _errs11 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    } else {
                      validate298.errors = [{ instancePath: instancePath + "/inputs", schemaPath: "#/properties/inputs/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.depends_on !== void 0) {
                    let data5 = data.depends_on;
                    const _errs17 = errors;
                    if (errors === _errs17) {
                      if (Array.isArray(data5)) {
                        var valid3 = true;
                        const len0 = data5.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          const _errs19 = errors;
                          if (typeof data5[i0] !== "string") {
                            validate298.errors = [{ instancePath: instancePath + "/depends_on/" + i0, schemaPath: "#/properties/depends_on/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid3 = _errs19 === errors;
                          if (!valid3) {
                            break;
                          }
                        }
                      } else {
                        validate298.errors = [{ instancePath: instancePath + "/depends_on", schemaPath: "#/properties/depends_on/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs17 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.map !== void 0) {
                      let data7 = data.map;
                      const _errs21 = errors;
                      const _errs22 = errors;
                      let valid4 = false;
                      const _errs23 = errors;
                      if (!validate241(data7, { instancePath: instancePath + "/map", parentData: data, parentDataProperty: "map", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate241.errors : vErrors.concat(validate241.errors);
                        errors = vErrors.length;
                      }
                      var _valid1 = _errs23 === errors;
                      valid4 = valid4 || _valid1;
                      const _errs24 = errors;
                      if (data7 !== null) {
                        const err1 = { instancePath: instancePath + "/map", schemaPath: "#/properties/map/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      }
                      var _valid1 = _errs24 === errors;
                      valid4 = valid4 || _valid1;
                      if (!valid4) {
                        const err2 = { instancePath: instancePath + "/map", schemaPath: "#/properties/map/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err2];
                        } else {
                          vErrors.push(err2);
                        }
                        errors++;
                        validate298.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs22;
                        if (vErrors !== null) {
                          if (_errs22) {
                            vErrors.length = _errs22;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs21 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate298.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate298.errors = vErrors;
  return errors === 0;
}
validate298.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate305(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate305.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.target_node_id === void 0 && (missing0 = "target_node_id") || data.max_completed_stages === void 0 && (missing0 = "max_completed_stages") || data.checkpoints_before === void 0 && (missing0 = "checkpoints_before") || data.checkpoints_after === void 0 && (missing0 = "checkpoints_after") || data.allowed_tools === void 0 && (missing0 = "allowed_tools") || data.max_tool_calls === void 0 && (missing0 = "max_tool_calls") || data.stop_after_seconds === void 0 && (missing0 = "stop_after_seconds") || data.memory_limit_mb === void 0 && (missing0 = "memory_limit_mb")) {
        validate305.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "target_node_id" || key0 === "max_completed_stages" || key0 === "checkpoints_before" || key0 === "checkpoints_after" || key0 === "allowed_tools" || key0 === "max_tool_calls" || key0 === "stop_after_seconds" || key0 === "memory_limit_mb")) {
            validate305.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.target_node_id !== void 0) {
            let data0 = data.target_node_id;
            const _errs2 = errors;
            const _errs3 = errors;
            let valid1 = false;
            const _errs4 = errors;
            if (typeof data0 !== "string") {
              const err0 = { instancePath: instancePath + "/target_node_id", schemaPath: "#/properties/target_node_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
              if (vErrors === null) {
                vErrors = [err0];
              } else {
                vErrors.push(err0);
              }
              errors++;
            }
            var _valid0 = _errs4 === errors;
            valid1 = valid1 || _valid0;
            const _errs6 = errors;
            if (data0 !== null) {
              const err1 = { instancePath: instancePath + "/target_node_id", schemaPath: "#/properties/target_node_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
              if (vErrors === null) {
                vErrors = [err1];
              } else {
                vErrors.push(err1);
              }
              errors++;
            }
            var _valid0 = _errs6 === errors;
            valid1 = valid1 || _valid0;
            if (!valid1) {
              const err2 = { instancePath: instancePath + "/target_node_id", schemaPath: "#/properties/target_node_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
              if (vErrors === null) {
                vErrors = [err2];
              } else {
                vErrors.push(err2);
              }
              errors++;
              validate305.errors = vErrors;
              return false;
            } else {
              errors = _errs3;
              if (vErrors !== null) {
                if (_errs3) {
                  vErrors.length = _errs3;
                } else {
                  vErrors = null;
                }
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.max_completed_stages !== void 0) {
              let data1 = data.max_completed_stages;
              const _errs8 = errors;
              const _errs9 = errors;
              let valid2 = false;
              const _errs10 = errors;
              if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)))) {
                const err3 = { instancePath: instancePath + "/max_completed_stages", schemaPath: "#/properties/max_completed_stages/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                if (vErrors === null) {
                  vErrors = [err3];
                } else {
                  vErrors.push(err3);
                }
                errors++;
              }
              if (errors === _errs10) {
                if (typeof data1 == "number") {
                  if (data1 < 1 || isNaN(data1)) {
                    const err4 = { instancePath: instancePath + "/max_completed_stages", schemaPath: "#/properties/max_completed_stages/anyOf/0/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" };
                    if (vErrors === null) {
                      vErrors = [err4];
                    } else {
                      vErrors.push(err4);
                    }
                    errors++;
                  }
                }
              }
              var _valid1 = _errs10 === errors;
              valid2 = valid2 || _valid1;
              const _errs12 = errors;
              if (data1 !== null) {
                const err5 = { instancePath: instancePath + "/max_completed_stages", schemaPath: "#/properties/max_completed_stages/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                if (vErrors === null) {
                  vErrors = [err5];
                } else {
                  vErrors.push(err5);
                }
                errors++;
              }
              var _valid1 = _errs12 === errors;
              valid2 = valid2 || _valid1;
              if (!valid2) {
                const err6 = { instancePath: instancePath + "/max_completed_stages", schemaPath: "#/properties/max_completed_stages/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                if (vErrors === null) {
                  vErrors = [err6];
                } else {
                  vErrors.push(err6);
                }
                errors++;
                validate305.errors = vErrors;
                return false;
              } else {
                errors = _errs9;
                if (vErrors !== null) {
                  if (_errs9) {
                    vErrors.length = _errs9;
                  } else {
                    vErrors = null;
                  }
                }
              }
              var valid0 = _errs8 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.checkpoints_before !== void 0) {
                let data2 = data.checkpoints_before;
                const _errs14 = errors;
                if (errors === _errs14) {
                  if (Array.isArray(data2)) {
                    var valid3 = true;
                    const len0 = data2.length;
                    for (let i0 = 0; i0 < len0; i0++) {
                      const _errs16 = errors;
                      if (typeof data2[i0] !== "string") {
                        validate305.errors = [{ instancePath: instancePath + "/checkpoints_before/" + i0, schemaPath: "#/properties/checkpoints_before/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid3 = _errs16 === errors;
                      if (!valid3) {
                        break;
                      }
                    }
                  } else {
                    validate305.errors = [{ instancePath: instancePath + "/checkpoints_before", schemaPath: "#/properties/checkpoints_before/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs14 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.checkpoints_after !== void 0) {
                  let data4 = data.checkpoints_after;
                  const _errs18 = errors;
                  if (errors === _errs18) {
                    if (Array.isArray(data4)) {
                      var valid4 = true;
                      const len1 = data4.length;
                      for (let i1 = 0; i1 < len1; i1++) {
                        const _errs20 = errors;
                        if (typeof data4[i1] !== "string") {
                          validate305.errors = [{ instancePath: instancePath + "/checkpoints_after/" + i1, schemaPath: "#/properties/checkpoints_after/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid4 = _errs20 === errors;
                        if (!valid4) {
                          break;
                        }
                      }
                    } else {
                      validate305.errors = [{ instancePath: instancePath + "/checkpoints_after", schemaPath: "#/properties/checkpoints_after/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs18 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.allowed_tools !== void 0) {
                    let data6 = data.allowed_tools;
                    const _errs22 = errors;
                    if (errors === _errs22) {
                      if (Array.isArray(data6)) {
                        var valid5 = true;
                        const len2 = data6.length;
                        for (let i2 = 0; i2 < len2; i2++) {
                          const _errs24 = errors;
                          if (typeof data6[i2] !== "string") {
                            validate305.errors = [{ instancePath: instancePath + "/allowed_tools/" + i2, schemaPath: "#/properties/allowed_tools/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid5 = _errs24 === errors;
                          if (!valid5) {
                            break;
                          }
                        }
                      } else {
                        validate305.errors = [{ instancePath: instancePath + "/allowed_tools", schemaPath: "#/properties/allowed_tools/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs22 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.max_tool_calls !== void 0) {
                      let data8 = data.max_tool_calls;
                      const _errs26 = errors;
                      if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)))) {
                        validate305.errors = [{ instancePath: instancePath + "/max_tool_calls", schemaPath: "#/properties/max_tool_calls/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      if (errors === _errs26) {
                        if (typeof data8 == "number") {
                          if (data8 < 1 || isNaN(data8)) {
                            validate305.errors = [{ instancePath: instancePath + "/max_tool_calls", schemaPath: "#/properties/max_tool_calls/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                      var valid0 = _errs26 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.stop_after_seconds !== void 0) {
                        let data9 = data.stop_after_seconds;
                        const _errs28 = errors;
                        const _errs29 = errors;
                        let valid6 = false;
                        const _errs30 = errors;
                        if (errors === _errs30) {
                          if (typeof data9 == "number") {
                            if (data9 <= 0 || isNaN(data9)) {
                              const err7 = { instancePath: instancePath + "/stop_after_seconds", schemaPath: "#/properties/stop_after_seconds/anyOf/0/exclusiveMinimum", keyword: "exclusiveMinimum", params: { comparison: ">", limit: 0 }, message: "must be > 0" };
                              if (vErrors === null) {
                                vErrors = [err7];
                              } else {
                                vErrors.push(err7);
                              }
                              errors++;
                            }
                          } else {
                            const err8 = { instancePath: instancePath + "/stop_after_seconds", schemaPath: "#/properties/stop_after_seconds/anyOf/0/type", keyword: "type", params: { type: "number" }, message: "must be number" };
                            if (vErrors === null) {
                              vErrors = [err8];
                            } else {
                              vErrors.push(err8);
                            }
                            errors++;
                          }
                        }
                        var _valid2 = _errs30 === errors;
                        valid6 = valid6 || _valid2;
                        const _errs32 = errors;
                        if (data9 !== null) {
                          const err9 = { instancePath: instancePath + "/stop_after_seconds", schemaPath: "#/properties/stop_after_seconds/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err9];
                          } else {
                            vErrors.push(err9);
                          }
                          errors++;
                        }
                        var _valid2 = _errs32 === errors;
                        valid6 = valid6 || _valid2;
                        if (!valid6) {
                          const err10 = { instancePath: instancePath + "/stop_after_seconds", schemaPath: "#/properties/stop_after_seconds/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err10];
                          } else {
                            vErrors.push(err10);
                          }
                          errors++;
                          validate305.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs29;
                          if (vErrors !== null) {
                            if (_errs29) {
                              vErrors.length = _errs29;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs28 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.memory_limit_mb !== void 0) {
                          let data10 = data.memory_limit_mb;
                          const _errs34 = errors;
                          const _errs35 = errors;
                          let valid7 = false;
                          const _errs36 = errors;
                          if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)))) {
                            const err11 = { instancePath: instancePath + "/memory_limit_mb", schemaPath: "#/properties/memory_limit_mb/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                            if (vErrors === null) {
                              vErrors = [err11];
                            } else {
                              vErrors.push(err11);
                            }
                            errors++;
                          }
                          if (errors === _errs36) {
                            if (typeof data10 == "number") {
                              if (data10 < 1 || isNaN(data10)) {
                                const err12 = { instancePath: instancePath + "/memory_limit_mb", schemaPath: "#/properties/memory_limit_mb/anyOf/0/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" };
                                if (vErrors === null) {
                                  vErrors = [err12];
                                } else {
                                  vErrors.push(err12);
                                }
                                errors++;
                              }
                            }
                          }
                          var _valid3 = _errs36 === errors;
                          valid7 = valid7 || _valid3;
                          const _errs38 = errors;
                          if (data10 !== null) {
                            const err13 = { instancePath: instancePath + "/memory_limit_mb", schemaPath: "#/properties/memory_limit_mb/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err13];
                            } else {
                              vErrors.push(err13);
                            }
                            errors++;
                          }
                          var _valid3 = _errs38 === errors;
                          valid7 = valid7 || _valid3;
                          if (!valid7) {
                            const err14 = { instancePath: instancePath + "/memory_limit_mb", schemaPath: "#/properties/memory_limit_mb/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err14];
                            } else {
                              vErrors.push(err14);
                            }
                            errors++;
                            validate305.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs35;
                            if (vErrors !== null) {
                              if (_errs35) {
                                vErrors.length = _errs35;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs34 === errors;
                        } else {
                          var valid0 = true;
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate305.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate305.errors = vErrors;
  return errors === 0;
}
validate305.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate297(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate297.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.name === void 0 && (missing0 = "name") || data.description === void 0 && (missing0 = "description") || data.version === void 0 && (missing0 = "version") || data.nodes === void 0 && (missing0 = "nodes") || data.execution_policy === void 0 && (missing0 = "execution_policy")) {
        validate297.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "name" || key0 === "description" || key0 === "version" || key0 === "nodes" || key0 === "execution_policy")) {
            validate297.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate297.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.name !== void 0) {
              const _errs4 = errors;
              if (typeof data.name !== "string") {
                validate297.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.description !== void 0) {
                const _errs6 = errors;
                if (typeof data.description !== "string") {
                  validate297.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.version !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.version !== "string") {
                    validate297.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.nodes !== void 0) {
                    let data4 = data.nodes;
                    const _errs10 = errors;
                    if (errors === _errs10) {
                      if (Array.isArray(data4)) {
                        if (data4.length < 1) {
                          validate297.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                          return false;
                        } else {
                          var valid1 = true;
                          const len0 = data4.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs12 = errors;
                            if (!validate298(data4[i0], { instancePath: instancePath + "/nodes/" + i0, parentData: data4, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate298.errors : vErrors.concat(validate298.errors);
                              errors = vErrors.length;
                            }
                            var valid1 = _errs12 === errors;
                            if (!valid1) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate297.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.execution_policy !== void 0) {
                      const _errs13 = errors;
                      if (!validate305(data.execution_policy, { instancePath: instancePath + "/execution_policy", parentData: data, parentDataProperty: "execution_policy", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate305.errors : vErrors.concat(validate305.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs13 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate297.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate297.errors = vErrors;
  return errors === 0;
}
validate297.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate308(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate308.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.project_revision === void 0 && (missing0 = "project_revision") || data.project_input_sha256 === void 0 && (missing0 = "project_input_sha256") || data.workflow_sha256 === void 0 && (missing0 = "workflow_sha256")) {
        validate308.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "project_id" || key0 === "project_revision" || key0 === "project_input_sha256" || key0 === "workflow_sha256")) {
            validate308.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate308.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.project_revision !== void 0) {
              let data1 = data.project_revision;
              const _errs4 = errors;
              if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)))) {
                validate308.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                return false;
              }
              if (errors === _errs4) {
                if (typeof data1 == "number") {
                  if (data1 < 1 || isNaN(data1)) {
                    validate308.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                    return false;
                  }
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.project_input_sha256 !== void 0) {
                let data2 = data.project_input_sha256;
                const _errs6 = errors;
                if (errors === _errs6) {
                  if (typeof data2 === "string") {
                    if (!pattern4.test(data2)) {
                      validate308.errors = [{ instancePath: instancePath + "/project_input_sha256", schemaPath: "#/properties/project_input_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                      return false;
                    }
                  } else {
                    validate308.errors = [{ instancePath: instancePath + "/project_input_sha256", schemaPath: "#/properties/project_input_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.workflow_sha256 !== void 0) {
                  let data3 = data.workflow_sha256;
                  const _errs8 = errors;
                  if (errors === _errs8) {
                    if (typeof data3 === "string") {
                      if (!pattern4.test(data3)) {
                        validate308.errors = [{ instancePath: instancePath + "/workflow_sha256", schemaPath: "#/properties/workflow_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate308.errors = [{ instancePath: instancePath + "/workflow_sha256", schemaPath: "#/properties/workflow_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        }
      }
    } else {
      validate308.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate308.errors = vErrors;
  return errors === 0;
}
validate308.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate266(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate266.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.observation === void 0 && (missing0 = "observation") || data.scientific_actions === void 0 && (missing0 = "scientific_actions") || data.reviewed_tool_labels === void 0 && (missing0 = "reviewed_tool_labels") || data.id === void 0 && (missing0 = "id") || data.task_id === void 0 && (missing0 = "task_id") || data.project_id === void 0 && (missing0 = "project_id") || data.source === void 0 && (missing0 = "source") || data.status === void 0 && (missing0 = "status") || data.objective === void 0 && (missing0 = "objective") || data.rationale === void 0 && (missing0 = "rationale") || data.change_types === void 0 && (missing0 = "change_types") || data.evidence === void 0 && (missing0 = "evidence") || data.requested_stages === void 0 && (missing0 = "requested_stages") || data.execution_stages === void 0 && (missing0 = "execution_stages") || data.reused_artifacts === void 0 && (missing0 = "reused_artifacts") || data.missing_inputs === void 0 && (missing0 = "missing_inputs") || data.limitations === void 0 && (missing0 = "limitations") || data.workflow === void 0 && (missing0 = "workflow") || data.confirmation === void 0 && (missing0 = "confirmation") || data.created_at === void 0 && (missing0 = "created_at") || data.review_identity === void 0 && (missing0 = "review_identity") || data.previous_review_identity === void 0 && (missing0 = "previous_review_identity")) {
        validate266.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema113.properties, key0)) {
            validate266.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.observation !== void 0) {
            let data0 = data.observation;
            const _errs2 = errors;
            const _errs3 = errors;
            let valid1 = false;
            const _errs4 = errors;
            if (!validate267(data0, { instancePath: instancePath + "/observation", parentData: data, parentDataProperty: "observation", rootData, dynamicAnchors })) {
              vErrors = vErrors === null ? validate267.errors : vErrors.concat(validate267.errors);
              errors = vErrors.length;
            }
            var _valid0 = _errs4 === errors;
            valid1 = valid1 || _valid0;
            const _errs5 = errors;
            if (data0 !== null) {
              const err0 = { instancePath: instancePath + "/observation", schemaPath: "#/properties/observation/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
              if (vErrors === null) {
                vErrors = [err0];
              } else {
                vErrors.push(err0);
              }
              errors++;
            }
            var _valid0 = _errs5 === errors;
            valid1 = valid1 || _valid0;
            if (!valid1) {
              const err1 = { instancePath: instancePath + "/observation", schemaPath: "#/properties/observation/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
              if (vErrors === null) {
                vErrors = [err1];
              } else {
                vErrors.push(err1);
              }
              errors++;
              validate266.errors = vErrors;
              return false;
            } else {
              errors = _errs3;
              if (vErrors !== null) {
                if (_errs3) {
                  vErrors.length = _errs3;
                } else {
                  vErrors = null;
                }
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.scientific_actions !== void 0) {
              let data1 = data.scientific_actions;
              const _errs7 = errors;
              if (errors === _errs7) {
                if (Array.isArray(data1)) {
                  var valid2 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    let data2 = data1[i0];
                    const _errs9 = errors;
                    const _errs10 = errors;
                    let valid3 = false;
                    let passing0 = null;
                    const _errs11 = errors;
                    if (!validate279(data2, { instancePath: instancePath + "/scientific_actions/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate279.errors : vErrors.concat(validate279.errors);
                      errors = vErrors.length;
                    }
                    var _valid1 = _errs11 === errors;
                    if (_valid1) {
                      valid3 = true;
                      passing0 = 0;
                      var props1 = true;
                    }
                    const _errs12 = errors;
                    if (!validate281(data2, { instancePath: instancePath + "/scientific_actions/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate281.errors : vErrors.concat(validate281.errors);
                      errors = vErrors.length;
                    }
                    var _valid1 = _errs12 === errors;
                    if (_valid1 && valid3) {
                      valid3 = false;
                      passing0 = [passing0, 1];
                    } else {
                      if (_valid1) {
                        valid3 = true;
                        passing0 = 1;
                        if (props1 !== true) {
                          props1 = true;
                        }
                      }
                      const _errs13 = errors;
                      if (!validate283(data2, { instancePath: instancePath + "/scientific_actions/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate283.errors : vErrors.concat(validate283.errors);
                        errors = vErrors.length;
                      }
                      var _valid1 = _errs13 === errors;
                      if (_valid1 && valid3) {
                        valid3 = false;
                        passing0 = [passing0, 2];
                      } else {
                        if (_valid1) {
                          valid3 = true;
                          passing0 = 2;
                          if (props1 !== true) {
                            props1 = true;
                          }
                        }
                        const _errs14 = errors;
                        if (!validate285(data2, { instancePath: instancePath + "/scientific_actions/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate285.errors : vErrors.concat(validate285.errors);
                          errors = vErrors.length;
                        }
                        var _valid1 = _errs14 === errors;
                        if (_valid1 && valid3) {
                          valid3 = false;
                          passing0 = [passing0, 3];
                        } else {
                          if (_valid1) {
                            valid3 = true;
                            passing0 = 3;
                            if (props1 !== true) {
                              props1 = true;
                            }
                          }
                          const _errs15 = errors;
                          if (!validate287(data2, { instancePath: instancePath + "/scientific_actions/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate287.errors : vErrors.concat(validate287.errors);
                            errors = vErrors.length;
                          }
                          var _valid1 = _errs15 === errors;
                          if (_valid1 && valid3) {
                            valid3 = false;
                            passing0 = [passing0, 4];
                          } else {
                            if (_valid1) {
                              valid3 = true;
                              passing0 = 4;
                              if (props1 !== true) {
                                props1 = true;
                              }
                            }
                            const _errs16 = errors;
                            if (!validate289(data2, { instancePath: instancePath + "/scientific_actions/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate289.errors : vErrors.concat(validate289.errors);
                              errors = vErrors.length;
                            }
                            var _valid1 = _errs16 === errors;
                            if (_valid1 && valid3) {
                              valid3 = false;
                              passing0 = [passing0, 5];
                            } else {
                              if (_valid1) {
                                valid3 = true;
                                passing0 = 5;
                                if (props1 !== true) {
                                  props1 = true;
                                }
                              }
                              const _errs17 = errors;
                              if (!validate291(data2, { instancePath: instancePath + "/scientific_actions/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate291.errors : vErrors.concat(validate291.errors);
                                errors = vErrors.length;
                              }
                              var _valid1 = _errs17 === errors;
                              if (_valid1 && valid3) {
                                valid3 = false;
                                passing0 = [passing0, 6];
                              } else {
                                if (_valid1) {
                                  valid3 = true;
                                  passing0 = 6;
                                  if (props1 !== true) {
                                    props1 = true;
                                  }
                                }
                                const _errs18 = errors;
                                if (!validate293(data2, { instancePath: instancePath + "/scientific_actions/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate293.errors : vErrors.concat(validate293.errors);
                                  errors = vErrors.length;
                                }
                                var _valid1 = _errs18 === errors;
                                if (_valid1 && valid3) {
                                  valid3 = false;
                                  passing0 = [passing0, 7];
                                } else {
                                  if (_valid1) {
                                    valid3 = true;
                                    passing0 = 7;
                                    if (props1 !== true) {
                                      props1 = true;
                                    }
                                  }
                                  const _errs19 = errors;
                                  if (!validate295(data2, { instancePath: instancePath + "/scientific_actions/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                    vErrors = vErrors === null ? validate295.errors : vErrors.concat(validate295.errors);
                                    errors = vErrors.length;
                                  }
                                  var _valid1 = _errs19 === errors;
                                  if (_valid1 && valid3) {
                                    valid3 = false;
                                    passing0 = [passing0, 8];
                                  } else {
                                    if (_valid1) {
                                      valid3 = true;
                                      passing0 = 8;
                                      if (props1 !== true) {
                                        props1 = true;
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                    if (!valid3) {
                      const err2 = { instancePath: instancePath + "/scientific_actions/" + i0, schemaPath: "#/properties/scientific_actions/items/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                      if (vErrors === null) {
                        vErrors = [err2];
                      } else {
                        vErrors.push(err2);
                      }
                      errors++;
                      validate266.errors = vErrors;
                      return false;
                    } else {
                      errors = _errs10;
                      if (vErrors !== null) {
                        if (_errs10) {
                          vErrors.length = _errs10;
                        } else {
                          vErrors = null;
                        }
                      }
                    }
                    var valid2 = _errs9 === errors;
                    if (!valid2) {
                      break;
                    }
                  }
                } else {
                  validate266.errors = [{ instancePath: instancePath + "/scientific_actions", schemaPath: "#/properties/scientific_actions/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs7 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.reviewed_tool_labels !== void 0) {
                let data3 = data.reviewed_tool_labels;
                const _errs20 = errors;
                if (errors === _errs20) {
                  if (Array.isArray(data3)) {
                    var valid4 = true;
                    const len1 = data3.length;
                    for (let i1 = 0; i1 < len1; i1++) {
                      const _errs22 = errors;
                      if (typeof data3[i1] !== "string") {
                        validate266.errors = [{ instancePath: instancePath + "/reviewed_tool_labels/" + i1, schemaPath: "#/properties/reviewed_tool_labels/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid4 = _errs22 === errors;
                      if (!valid4) {
                        break;
                      }
                    }
                  } else {
                    validate266.errors = [{ instancePath: instancePath + "/reviewed_tool_labels", schemaPath: "#/properties/reviewed_tool_labels/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs20 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.id !== void 0) {
                  const _errs24 = errors;
                  if (typeof data.id !== "string") {
                    validate266.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs24 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.task_id !== void 0) {
                    const _errs26 = errors;
                    if (typeof data.task_id !== "string") {
                      validate266.errors = [{ instancePath: instancePath + "/task_id", schemaPath: "#/properties/task_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs26 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.project_id !== void 0) {
                      const _errs28 = errors;
                      if (typeof data.project_id !== "string") {
                        validate266.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs28 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.source !== void 0) {
                        const _errs30 = errors;
                        if (typeof data.source !== "string") {
                          validate266.errors = [{ instancePath: instancePath + "/source", schemaPath: "#/properties/source/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs30 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.status !== void 0) {
                          let data9 = data.status;
                          const _errs32 = errors;
                          if (typeof data9 !== "string") {
                            validate266.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if (!(data9 === "proposed" || data9 === "accepted" || data9 === "rejected" || data9 === "blocked" || data9 === "stale")) {
                            validate266.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema113.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                            return false;
                          }
                          var valid0 = _errs32 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.objective !== void 0) {
                            const _errs34 = errors;
                            if (typeof data.objective !== "string") {
                              validate266.errors = [{ instancePath: instancePath + "/objective", schemaPath: "#/properties/objective/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid0 = _errs34 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.rationale !== void 0) {
                              const _errs36 = errors;
                              if (typeof data.rationale !== "string") {
                                validate266.errors = [{ instancePath: instancePath + "/rationale", schemaPath: "#/properties/rationale/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid0 = _errs36 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.change_types !== void 0) {
                                let data12 = data.change_types;
                                const _errs38 = errors;
                                if (errors === _errs38) {
                                  if (Array.isArray(data12)) {
                                    var valid5 = true;
                                    const len2 = data12.length;
                                    for (let i2 = 0; i2 < len2; i2++) {
                                      const _errs40 = errors;
                                      if (typeof data12[i2] !== "string") {
                                        validate266.errors = [{ instancePath: instancePath + "/change_types/" + i2, schemaPath: "#/properties/change_types/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      var valid5 = _errs40 === errors;
                                      if (!valid5) {
                                        break;
                                      }
                                    }
                                  } else {
                                    validate266.errors = [{ instancePath: instancePath + "/change_types", schemaPath: "#/properties/change_types/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                    return false;
                                  }
                                }
                                var valid0 = _errs38 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.evidence !== void 0) {
                                  let data14 = data.evidence;
                                  const _errs42 = errors;
                                  if (errors === _errs42) {
                                    if (Array.isArray(data14)) {
                                      var valid6 = true;
                                      const len3 = data14.length;
                                      for (let i3 = 0; i3 < len3; i3++) {
                                        const _errs44 = errors;
                                        if (typeof data14[i3] !== "string") {
                                          validate266.errors = [{ instancePath: instancePath + "/evidence/" + i3, schemaPath: "#/properties/evidence/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                        var valid6 = _errs44 === errors;
                                        if (!valid6) {
                                          break;
                                        }
                                      }
                                    } else {
                                      validate266.errors = [{ instancePath: instancePath + "/evidence", schemaPath: "#/properties/evidence/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                      return false;
                                    }
                                  }
                                  var valid0 = _errs42 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.requested_stages !== void 0) {
                                    let data16 = data.requested_stages;
                                    const _errs46 = errors;
                                    if (errors === _errs46) {
                                      if (Array.isArray(data16)) {
                                        var valid7 = true;
                                        const len4 = data16.length;
                                        for (let i4 = 0; i4 < len4; i4++) {
                                          const _errs48 = errors;
                                          if (typeof data16[i4] !== "string") {
                                            validate266.errors = [{ instancePath: instancePath + "/requested_stages/" + i4, schemaPath: "#/properties/requested_stages/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                          var valid7 = _errs48 === errors;
                                          if (!valid7) {
                                            break;
                                          }
                                        }
                                      } else {
                                        validate266.errors = [{ instancePath: instancePath + "/requested_stages", schemaPath: "#/properties/requested_stages/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                        return false;
                                      }
                                    }
                                    var valid0 = _errs46 === errors;
                                  } else {
                                    var valid0 = true;
                                  }
                                  if (valid0) {
                                    if (data.execution_stages !== void 0) {
                                      let data18 = data.execution_stages;
                                      const _errs50 = errors;
                                      if (errors === _errs50) {
                                        if (Array.isArray(data18)) {
                                          var valid8 = true;
                                          const len5 = data18.length;
                                          for (let i5 = 0; i5 < len5; i5++) {
                                            const _errs52 = errors;
                                            if (typeof data18[i5] !== "string") {
                                              validate266.errors = [{ instancePath: instancePath + "/execution_stages/" + i5, schemaPath: "#/properties/execution_stages/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                            var valid8 = _errs52 === errors;
                                            if (!valid8) {
                                              break;
                                            }
                                          }
                                        } else {
                                          validate266.errors = [{ instancePath: instancePath + "/execution_stages", schemaPath: "#/properties/execution_stages/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                          return false;
                                        }
                                      }
                                      var valid0 = _errs50 === errors;
                                    } else {
                                      var valid0 = true;
                                    }
                                    if (valid0) {
                                      if (data.reused_artifacts !== void 0) {
                                        let data20 = data.reused_artifacts;
                                        const _errs54 = errors;
                                        if (errors === _errs54) {
                                          if (Array.isArray(data20)) {
                                            var valid9 = true;
                                            const len6 = data20.length;
                                            for (let i6 = 0; i6 < len6; i6++) {
                                              const _errs56 = errors;
                                              if (typeof data20[i6] !== "string") {
                                                validate266.errors = [{ instancePath: instancePath + "/reused_artifacts/" + i6, schemaPath: "#/properties/reused_artifacts/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                return false;
                                              }
                                              var valid9 = _errs56 === errors;
                                              if (!valid9) {
                                                break;
                                              }
                                            }
                                          } else {
                                            validate266.errors = [{ instancePath: instancePath + "/reused_artifacts", schemaPath: "#/properties/reused_artifacts/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                            return false;
                                          }
                                        }
                                        var valid0 = _errs54 === errors;
                                      } else {
                                        var valid0 = true;
                                      }
                                      if (valid0) {
                                        if (data.missing_inputs !== void 0) {
                                          let data22 = data.missing_inputs;
                                          const _errs58 = errors;
                                          if (errors === _errs58) {
                                            if (Array.isArray(data22)) {
                                              var valid10 = true;
                                              const len7 = data22.length;
                                              for (let i7 = 0; i7 < len7; i7++) {
                                                const _errs60 = errors;
                                                if (typeof data22[i7] !== "string") {
                                                  validate266.errors = [{ instancePath: instancePath + "/missing_inputs/" + i7, schemaPath: "#/properties/missing_inputs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                  return false;
                                                }
                                                var valid10 = _errs60 === errors;
                                                if (!valid10) {
                                                  break;
                                                }
                                              }
                                            } else {
                                              validate266.errors = [{ instancePath: instancePath + "/missing_inputs", schemaPath: "#/properties/missing_inputs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                              return false;
                                            }
                                          }
                                          var valid0 = _errs58 === errors;
                                        } else {
                                          var valid0 = true;
                                        }
                                        if (valid0) {
                                          if (data.limitations !== void 0) {
                                            let data24 = data.limitations;
                                            const _errs62 = errors;
                                            if (errors === _errs62) {
                                              if (Array.isArray(data24)) {
                                                var valid11 = true;
                                                const len8 = data24.length;
                                                for (let i8 = 0; i8 < len8; i8++) {
                                                  const _errs64 = errors;
                                                  if (typeof data24[i8] !== "string") {
                                                    validate266.errors = [{ instancePath: instancePath + "/limitations/" + i8, schemaPath: "#/properties/limitations/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                    return false;
                                                  }
                                                  var valid11 = _errs64 === errors;
                                                  if (!valid11) {
                                                    break;
                                                  }
                                                }
                                              } else {
                                                validate266.errors = [{ instancePath: instancePath + "/limitations", schemaPath: "#/properties/limitations/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                                return false;
                                              }
                                            }
                                            var valid0 = _errs62 === errors;
                                          } else {
                                            var valid0 = true;
                                          }
                                          if (valid0) {
                                            if (data.workflow !== void 0) {
                                              let data26 = data.workflow;
                                              const _errs66 = errors;
                                              const _errs67 = errors;
                                              let valid12 = false;
                                              const _errs68 = errors;
                                              if (!validate297(data26, { instancePath: instancePath + "/workflow", parentData: data, parentDataProperty: "workflow", rootData, dynamicAnchors })) {
                                                vErrors = vErrors === null ? validate297.errors : vErrors.concat(validate297.errors);
                                                errors = vErrors.length;
                                              }
                                              var _valid2 = _errs68 === errors;
                                              valid12 = valid12 || _valid2;
                                              const _errs69 = errors;
                                              if (data26 !== null) {
                                                const err3 = { instancePath: instancePath + "/workflow", schemaPath: "#/properties/workflow/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                                if (vErrors === null) {
                                                  vErrors = [err3];
                                                } else {
                                                  vErrors.push(err3);
                                                }
                                                errors++;
                                              }
                                              var _valid2 = _errs69 === errors;
                                              valid12 = valid12 || _valid2;
                                              if (!valid12) {
                                                const err4 = { instancePath: instancePath + "/workflow", schemaPath: "#/properties/workflow/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                                if (vErrors === null) {
                                                  vErrors = [err4];
                                                } else {
                                                  vErrors.push(err4);
                                                }
                                                errors++;
                                                validate266.errors = vErrors;
                                                return false;
                                              } else {
                                                errors = _errs67;
                                                if (vErrors !== null) {
                                                  if (_errs67) {
                                                    vErrors.length = _errs67;
                                                  } else {
                                                    vErrors = null;
                                                  }
                                                }
                                              }
                                              var valid0 = _errs66 === errors;
                                            } else {
                                              var valid0 = true;
                                            }
                                            if (valid0) {
                                              if (data.confirmation !== void 0) {
                                                let data27 = data.confirmation;
                                                const _errs71 = errors;
                                                const _errs72 = errors;
                                                let valid13 = false;
                                                const _errs73 = errors;
                                                if (!validate308(data27, { instancePath: instancePath + "/confirmation", parentData: data, parentDataProperty: "confirmation", rootData, dynamicAnchors })) {
                                                  vErrors = vErrors === null ? validate308.errors : vErrors.concat(validate308.errors);
                                                  errors = vErrors.length;
                                                }
                                                var _valid3 = _errs73 === errors;
                                                valid13 = valid13 || _valid3;
                                                const _errs74 = errors;
                                                if (data27 !== null) {
                                                  const err5 = { instancePath: instancePath + "/confirmation", schemaPath: "#/properties/confirmation/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                                  if (vErrors === null) {
                                                    vErrors = [err5];
                                                  } else {
                                                    vErrors.push(err5);
                                                  }
                                                  errors++;
                                                }
                                                var _valid3 = _errs74 === errors;
                                                valid13 = valid13 || _valid3;
                                                if (!valid13) {
                                                  const err6 = { instancePath: instancePath + "/confirmation", schemaPath: "#/properties/confirmation/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                                  if (vErrors === null) {
                                                    vErrors = [err6];
                                                  } else {
                                                    vErrors.push(err6);
                                                  }
                                                  errors++;
                                                  validate266.errors = vErrors;
                                                  return false;
                                                } else {
                                                  errors = _errs72;
                                                  if (vErrors !== null) {
                                                    if (_errs72) {
                                                      vErrors.length = _errs72;
                                                    } else {
                                                      vErrors = null;
                                                    }
                                                  }
                                                }
                                                var valid0 = _errs71 === errors;
                                              } else {
                                                var valid0 = true;
                                              }
                                              if (valid0) {
                                                if (data.created_at !== void 0) {
                                                  const _errs76 = errors;
                                                  if (typeof data.created_at !== "string") {
                                                    validate266.errors = [{ instancePath: instancePath + "/created_at", schemaPath: "#/properties/created_at/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                    return false;
                                                  }
                                                  var valid0 = _errs76 === errors;
                                                } else {
                                                  var valid0 = true;
                                                }
                                                if (valid0) {
                                                  if (data.review_identity !== void 0) {
                                                    let data29 = data.review_identity;
                                                    const _errs78 = errors;
                                                    const _errs79 = errors;
                                                    let valid14 = false;
                                                    const _errs80 = errors;
                                                    if (errors === _errs80) {
                                                      if (data29 && typeof data29 == "object" && !Array.isArray(data29)) {
                                                      } else {
                                                        const err7 = { instancePath: instancePath + "/review_identity", schemaPath: "#/properties/review_identity/anyOf/0/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                                        if (vErrors === null) {
                                                          vErrors = [err7];
                                                        } else {
                                                          vErrors.push(err7);
                                                        }
                                                        errors++;
                                                      }
                                                    }
                                                    var _valid4 = _errs80 === errors;
                                                    valid14 = valid14 || _valid4;
                                                    const _errs83 = errors;
                                                    if (data29 !== null) {
                                                      const err8 = { instancePath: instancePath + "/review_identity", schemaPath: "#/properties/review_identity/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                                      if (vErrors === null) {
                                                        vErrors = [err8];
                                                      } else {
                                                        vErrors.push(err8);
                                                      }
                                                      errors++;
                                                    }
                                                    var _valid4 = _errs83 === errors;
                                                    valid14 = valid14 || _valid4;
                                                    if (!valid14) {
                                                      const err9 = { instancePath: instancePath + "/review_identity", schemaPath: "#/properties/review_identity/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                                      if (vErrors === null) {
                                                        vErrors = [err9];
                                                      } else {
                                                        vErrors.push(err9);
                                                      }
                                                      errors++;
                                                      validate266.errors = vErrors;
                                                      return false;
                                                    } else {
                                                      errors = _errs79;
                                                      if (vErrors !== null) {
                                                        if (_errs79) {
                                                          vErrors.length = _errs79;
                                                        } else {
                                                          vErrors = null;
                                                        }
                                                      }
                                                    }
                                                    var valid0 = _errs78 === errors;
                                                  } else {
                                                    var valid0 = true;
                                                  }
                                                  if (valid0) {
                                                    if (data.previous_review_identity !== void 0) {
                                                      let data30 = data.previous_review_identity;
                                                      const _errs85 = errors;
                                                      const _errs86 = errors;
                                                      let valid15 = false;
                                                      const _errs87 = errors;
                                                      if (errors === _errs87) {
                                                        if (data30 && typeof data30 == "object" && !Array.isArray(data30)) {
                                                        } else {
                                                          const err10 = { instancePath: instancePath + "/previous_review_identity", schemaPath: "#/properties/previous_review_identity/anyOf/0/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                                          if (vErrors === null) {
                                                            vErrors = [err10];
                                                          } else {
                                                            vErrors.push(err10);
                                                          }
                                                          errors++;
                                                        }
                                                      }
                                                      var _valid5 = _errs87 === errors;
                                                      valid15 = valid15 || _valid5;
                                                      const _errs90 = errors;
                                                      if (data30 !== null) {
                                                        const err11 = { instancePath: instancePath + "/previous_review_identity", schemaPath: "#/properties/previous_review_identity/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                                        if (vErrors === null) {
                                                          vErrors = [err11];
                                                        } else {
                                                          vErrors.push(err11);
                                                        }
                                                        errors++;
                                                      }
                                                      var _valid5 = _errs90 === errors;
                                                      valid15 = valid15 || _valid5;
                                                      if (!valid15) {
                                                        const err12 = { instancePath: instancePath + "/previous_review_identity", schemaPath: "#/properties/previous_review_identity/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                                        if (vErrors === null) {
                                                          vErrors = [err12];
                                                        } else {
                                                          vErrors.push(err12);
                                                        }
                                                        errors++;
                                                        validate266.errors = vErrors;
                                                        return false;
                                                      } else {
                                                        errors = _errs86;
                                                        if (vErrors !== null) {
                                                          if (_errs86) {
                                                            vErrors.length = _errs86;
                                                          } else {
                                                            vErrors = null;
                                                          }
                                                        }
                                                      }
                                                      var valid0 = _errs85 === errors;
                                                    } else {
                                                      var valid0 = true;
                                                    }
                                                  }
                                                }
                                              }
                                            }
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate266.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate266.errors = vErrors;
  return errors === 0;
}
validate266.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var AssistantPage = validate310;
var schema134 = { "additionalProperties": false, "properties": { "seq": { "title": "Seq", "type": "integer" }, "role": { "enum": ["user", "assistant"], "title": "Role", "type": "string" }, "text": { "title": "Text", "type": "string" }, "proposal_id": { "title": "Proposal Id", "type": "string" }, "project_revision": { "title": "Project Revision", "type": "integer" }, "timestamp": { "title": "Timestamp", "type": "string" } }, "required": ["seq", "role", "text", "proposal_id", "project_revision", "timestamp"], "title": "AssistantMessage", "type": "object" };
function validate311(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate311.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.seq === void 0 && (missing0 = "seq") || data.role === void 0 && (missing0 = "role") || data.text === void 0 && (missing0 = "text") || data.proposal_id === void 0 && (missing0 = "proposal_id") || data.project_revision === void 0 && (missing0 = "project_revision") || data.timestamp === void 0 && (missing0 = "timestamp")) {
        validate311.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "seq" || key0 === "role" || key0 === "text" || key0 === "proposal_id" || key0 === "project_revision" || key0 === "timestamp")) {
            validate311.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.seq !== void 0) {
            let data0 = data.seq;
            const _errs2 = errors;
            if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)))) {
              validate311.errors = [{ instancePath: instancePath + "/seq", schemaPath: "#/properties/seq/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.role !== void 0) {
              let data1 = data.role;
              const _errs4 = errors;
              if (typeof data1 !== "string") {
                validate311.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              if (!(data1 === "user" || data1 === "assistant")) {
                validate311.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/enum", keyword: "enum", params: { allowedValues: schema134.properties.role.enum }, message: "must be equal to one of the allowed values" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.text !== void 0) {
                const _errs6 = errors;
                if (typeof data.text !== "string") {
                  validate311.errors = [{ instancePath: instancePath + "/text", schemaPath: "#/properties/text/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.proposal_id !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.proposal_id !== "string") {
                    validate311.errors = [{ instancePath: instancePath + "/proposal_id", schemaPath: "#/properties/proposal_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.project_revision !== void 0) {
                    let data4 = data.project_revision;
                    const _errs10 = errors;
                    if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)))) {
                      validate311.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.timestamp !== void 0) {
                      const _errs12 = errors;
                      if (typeof data.timestamp !== "string") {
                        validate311.errors = [{ instancePath: instancePath + "/timestamp", schemaPath: "#/properties/timestamp/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate311.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate311.errors = vErrors;
  return errors === 0;
}
validate311.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate310(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate310.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.messages === void 0 && (missing0 = "messages") || data.has_more === void 0 && (missing0 = "has_more")) {
        validate310.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "project_id" || key0 === "messages" || key0 === "has_more")) {
            validate310.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate310.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.messages !== void 0) {
              let data1 = data.messages;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (Array.isArray(data1)) {
                  var valid1 = true;
                  const len0 = data1.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs6 = errors;
                    if (!validate311(data1[i0], { instancePath: instancePath + "/messages/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate311.errors : vErrors.concat(validate311.errors);
                      errors = vErrors.length;
                    }
                    var valid1 = _errs6 === errors;
                    if (!valid1) {
                      break;
                    }
                  }
                } else {
                  validate310.errors = [{ instancePath: instancePath + "/messages", schemaPath: "#/properties/messages/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.has_more !== void 0) {
                const _errs7 = errors;
                if (typeof data.has_more !== "boolean") {
                  validate310.errors = [{ instancePath: instancePath + "/has_more", schemaPath: "#/properties/has_more/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                  return false;
                }
                var valid0 = _errs7 === errors;
              } else {
                var valid0 = true;
              }
            }
          }
        }
      }
    } else {
      validate310.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate310.errors = vErrors;
  return errors === 0;
}
validate310.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var ProposalDiff = validate313;
var schema136 = { "additionalProperties": false, "properties": { "kind": { "enum": ["node", "tool", "binding", "dependency", "permission"], "title": "Kind", "type": "string" }, "target": { "title": "Target", "type": "string" }, "before": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Before" }, "after": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "After" } }, "required": ["kind", "target", "before", "after"], "title": "ProposalChange", "type": "object" };
function validate314(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate314.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.kind === void 0 && (missing0 = "kind") || data.target === void 0 && (missing0 = "target") || data.before === void 0 && (missing0 = "before") || data.after === void 0 && (missing0 = "after")) {
        validate314.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "kind" || key0 === "target" || key0 === "before" || key0 === "after")) {
            validate314.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.kind !== void 0) {
            let data0 = data.kind;
            const _errs2 = errors;
            if (typeof data0 !== "string") {
              validate314.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            if (!(data0 === "node" || data0 === "tool" || data0 === "binding" || data0 === "dependency" || data0 === "permission")) {
              validate314.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/enum", keyword: "enum", params: { allowedValues: schema136.properties.kind.enum }, message: "must be equal to one of the allowed values" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.target !== void 0) {
              const _errs4 = errors;
              if (typeof data.target !== "string") {
                validate314.errors = [{ instancePath: instancePath + "/target", schemaPath: "#/properties/target/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.before !== void 0) {
                let data2 = data.before;
                const _errs6 = errors;
                const _errs7 = errors;
                let valid1 = false;
                const _errs8 = errors;
                if (typeof data2 !== "string") {
                  const err0 = { instancePath: instancePath + "/before", schemaPath: "#/properties/before/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                }
                var _valid0 = _errs8 === errors;
                valid1 = valid1 || _valid0;
                const _errs10 = errors;
                if (data2 !== null) {
                  const err1 = { instancePath: instancePath + "/before", schemaPath: "#/properties/before/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                }
                var _valid0 = _errs10 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err2 = { instancePath: instancePath + "/before", schemaPath: "#/properties/before/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err2];
                  } else {
                    vErrors.push(err2);
                  }
                  errors++;
                  validate314.errors = vErrors;
                  return false;
                } else {
                  errors = _errs7;
                  if (vErrors !== null) {
                    if (_errs7) {
                      vErrors.length = _errs7;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.after !== void 0) {
                  let data3 = data.after;
                  const _errs12 = errors;
                  const _errs13 = errors;
                  let valid2 = false;
                  const _errs14 = errors;
                  if (typeof data3 !== "string") {
                    const err3 = { instancePath: instancePath + "/after", schemaPath: "#/properties/after/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                  }
                  var _valid1 = _errs14 === errors;
                  valid2 = valid2 || _valid1;
                  const _errs16 = errors;
                  if (data3 !== null) {
                    const err4 = { instancePath: instancePath + "/after", schemaPath: "#/properties/after/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err4];
                    } else {
                      vErrors.push(err4);
                    }
                    errors++;
                  }
                  var _valid1 = _errs16 === errors;
                  valid2 = valid2 || _valid1;
                  if (!valid2) {
                    const err5 = { instancePath: instancePath + "/after", schemaPath: "#/properties/after/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err5];
                    } else {
                      vErrors.push(err5);
                    }
                    errors++;
                    validate314.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs13;
                    if (vErrors !== null) {
                      if (_errs13) {
                        vErrors.length = _errs13;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs12 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        }
      }
    } else {
      validate314.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate314.errors = vErrors;
  return errors === 0;
}
validate314.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate313(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate313.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.proposal_id === void 0 && (missing0 = "proposal_id") || data.previous_proposal_id === void 0 && (missing0 = "previous_proposal_id") || data.changes === void 0 && (missing0 = "changes") || data.missing_inputs === void 0 && (missing0 = "missing_inputs") || data.evidence === void 0 && (missing0 = "evidence") || data.limitations === void 0 && (missing0 = "limitations")) {
        validate313.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "proposal_id" || key0 === "previous_proposal_id" || key0 === "changes" || key0 === "missing_inputs" || key0 === "evidence" || key0 === "limitations")) {
            validate313.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.proposal_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.proposal_id !== "string") {
              validate313.errors = [{ instancePath: instancePath + "/proposal_id", schemaPath: "#/properties/proposal_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.previous_proposal_id !== void 0) {
              let data1 = data.previous_proposal_id;
              const _errs4 = errors;
              const _errs5 = errors;
              let valid1 = false;
              const _errs6 = errors;
              if (typeof data1 !== "string") {
                const err0 = { instancePath: instancePath + "/previous_proposal_id", schemaPath: "#/properties/previous_proposal_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                if (vErrors === null) {
                  vErrors = [err0];
                } else {
                  vErrors.push(err0);
                }
                errors++;
              }
              var _valid0 = _errs6 === errors;
              valid1 = valid1 || _valid0;
              const _errs8 = errors;
              if (data1 !== null) {
                const err1 = { instancePath: instancePath + "/previous_proposal_id", schemaPath: "#/properties/previous_proposal_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                if (vErrors === null) {
                  vErrors = [err1];
                } else {
                  vErrors.push(err1);
                }
                errors++;
              }
              var _valid0 = _errs8 === errors;
              valid1 = valid1 || _valid0;
              if (!valid1) {
                const err2 = { instancePath: instancePath + "/previous_proposal_id", schemaPath: "#/properties/previous_proposal_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                if (vErrors === null) {
                  vErrors = [err2];
                } else {
                  vErrors.push(err2);
                }
                errors++;
                validate313.errors = vErrors;
                return false;
              } else {
                errors = _errs5;
                if (vErrors !== null) {
                  if (_errs5) {
                    vErrors.length = _errs5;
                  } else {
                    vErrors = null;
                  }
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.changes !== void 0) {
                let data2 = data.changes;
                const _errs10 = errors;
                if (errors === _errs10) {
                  if (Array.isArray(data2)) {
                    var valid2 = true;
                    const len0 = data2.length;
                    for (let i0 = 0; i0 < len0; i0++) {
                      const _errs12 = errors;
                      if (!validate314(data2[i0], { instancePath: instancePath + "/changes/" + i0, parentData: data2, parentDataProperty: i0, rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate314.errors : vErrors.concat(validate314.errors);
                        errors = vErrors.length;
                      }
                      var valid2 = _errs12 === errors;
                      if (!valid2) {
                        break;
                      }
                    }
                  } else {
                    validate313.errors = [{ instancePath: instancePath + "/changes", schemaPath: "#/properties/changes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs10 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.missing_inputs !== void 0) {
                  let data4 = data.missing_inputs;
                  const _errs13 = errors;
                  if (errors === _errs13) {
                    if (Array.isArray(data4)) {
                      var valid3 = true;
                      const len1 = data4.length;
                      for (let i1 = 0; i1 < len1; i1++) {
                        const _errs15 = errors;
                        if (typeof data4[i1] !== "string") {
                          validate313.errors = [{ instancePath: instancePath + "/missing_inputs/" + i1, schemaPath: "#/properties/missing_inputs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid3 = _errs15 === errors;
                        if (!valid3) {
                          break;
                        }
                      }
                    } else {
                      validate313.errors = [{ instancePath: instancePath + "/missing_inputs", schemaPath: "#/properties/missing_inputs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs13 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.evidence !== void 0) {
                    let data6 = data.evidence;
                    const _errs17 = errors;
                    if (errors === _errs17) {
                      if (Array.isArray(data6)) {
                        var valid4 = true;
                        const len2 = data6.length;
                        for (let i2 = 0; i2 < len2; i2++) {
                          const _errs19 = errors;
                          if (typeof data6[i2] !== "string") {
                            validate313.errors = [{ instancePath: instancePath + "/evidence/" + i2, schemaPath: "#/properties/evidence/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid4 = _errs19 === errors;
                          if (!valid4) {
                            break;
                          }
                        }
                      } else {
                        validate313.errors = [{ instancePath: instancePath + "/evidence", schemaPath: "#/properties/evidence/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs17 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.limitations !== void 0) {
                      let data8 = data.limitations;
                      const _errs21 = errors;
                      if (errors === _errs21) {
                        if (Array.isArray(data8)) {
                          var valid5 = true;
                          const len3 = data8.length;
                          for (let i3 = 0; i3 < len3; i3++) {
                            const _errs23 = errors;
                            if (typeof data8[i3] !== "string") {
                              validate313.errors = [{ instancePath: instancePath + "/limitations/" + i3, schemaPath: "#/properties/limitations/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid5 = _errs23 === errors;
                            if (!valid5) {
                              break;
                            }
                          }
                        } else {
                          validate313.errors = [{ instancePath: instancePath + "/limitations", schemaPath: "#/properties/limitations/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs21 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate313.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate313.errors = vErrors;
  return errors === 0;
}
validate313.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var PlanView = validate316;
function validate317(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate317.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.name === void 0 && (missing0 = "name") || data.description === void 0 && (missing0 = "description") || data.version === void 0 && (missing0 = "version") || data.nodes === void 0 && (missing0 = "nodes") || data.execution_policy === void 0 && (missing0 = "execution_policy")) {
        validate317.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "name" || key0 === "description" || key0 === "version" || key0 === "nodes" || key0 === "execution_policy")) {
            validate317.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate317.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.name !== void 0) {
              const _errs4 = errors;
              if (typeof data.name !== "string") {
                validate317.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.description !== void 0) {
                const _errs6 = errors;
                if (typeof data.description !== "string") {
                  validate317.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.version !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.version !== "string") {
                    validate317.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.nodes !== void 0) {
                    let data4 = data.nodes;
                    const _errs10 = errors;
                    if (errors === _errs10) {
                      if (Array.isArray(data4)) {
                        if (data4.length < 1) {
                          validate317.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                          return false;
                        } else {
                          var valid1 = true;
                          const len0 = data4.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs12 = errors;
                            if (!validate298(data4[i0], { instancePath: instancePath + "/nodes/" + i0, parentData: data4, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate298.errors : vErrors.concat(validate298.errors);
                              errors = vErrors.length;
                            }
                            var valid1 = _errs12 === errors;
                            if (!valid1) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate317.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.execution_policy !== void 0) {
                      const _errs13 = errors;
                      if (!validate305(data.execution_policy, { instancePath: instancePath + "/execution_policy", parentData: data, parentDataProperty: "execution_policy", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate305.errors : vErrors.concat(validate305.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs13 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate317.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate317.errors = vErrors;
  return errors === 0;
}
validate317.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate321(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate321.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.project_revision === void 0 && (missing0 = "project_revision") || data.project_input_sha256 === void 0 && (missing0 = "project_input_sha256") || data.workflow_sha256 === void 0 && (missing0 = "workflow_sha256")) {
        validate321.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "project_id" || key0 === "project_revision" || key0 === "project_input_sha256" || key0 === "workflow_sha256")) {
            validate321.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate321.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.project_revision !== void 0) {
              let data1 = data.project_revision;
              const _errs4 = errors;
              if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)))) {
                validate321.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                return false;
              }
              if (errors === _errs4) {
                if (typeof data1 == "number") {
                  if (data1 < 1 || isNaN(data1)) {
                    validate321.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                    return false;
                  }
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.project_input_sha256 !== void 0) {
                let data2 = data.project_input_sha256;
                const _errs6 = errors;
                if (errors === _errs6) {
                  if (typeof data2 === "string") {
                    if (!pattern4.test(data2)) {
                      validate321.errors = [{ instancePath: instancePath + "/project_input_sha256", schemaPath: "#/properties/project_input_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                      return false;
                    }
                  } else {
                    validate321.errors = [{ instancePath: instancePath + "/project_input_sha256", schemaPath: "#/properties/project_input_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.workflow_sha256 !== void 0) {
                  let data3 = data.workflow_sha256;
                  const _errs8 = errors;
                  if (errors === _errs8) {
                    if (typeof data3 === "string") {
                      if (!pattern4.test(data3)) {
                        validate321.errors = [{ instancePath: instancePath + "/workflow_sha256", schemaPath: "#/properties/workflow_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate321.errors = [{ instancePath: instancePath + "/workflow_sha256", schemaPath: "#/properties/workflow_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        }
      }
    } else {
      validate321.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate321.errors = vErrors;
  return errors === 0;
}
validate321.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate316(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate316.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.workflow === void 0 && (missing0 = "workflow") || data.confirmation === void 0 && (missing0 = "confirmation") || data.source === void 0 && (missing0 = "source") || data.requires_confirmation === void 0 && (missing0 = "requires_confirmation") || data.review_id === void 0 && (missing0 = "review_id")) {
        validate316.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "workflow" || key0 === "confirmation" || key0 === "source" || key0 === "requires_confirmation" || key0 === "review_id")) {
            validate316.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.workflow !== void 0) {
            const _errs2 = errors;
            if (!validate317(data.workflow, { instancePath: instancePath + "/workflow", parentData: data, parentDataProperty: "workflow", rootData, dynamicAnchors })) {
              vErrors = vErrors === null ? validate317.errors : vErrors.concat(validate317.errors);
              errors = vErrors.length;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.confirmation !== void 0) {
              const _errs3 = errors;
              if (!validate321(data.confirmation, { instancePath: instancePath + "/confirmation", parentData: data, parentDataProperty: "confirmation", rootData, dynamicAnchors })) {
                vErrors = vErrors === null ? validate321.errors : vErrors.concat(validate321.errors);
                errors = vErrors.length;
              }
              var valid0 = _errs3 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.source !== void 0) {
                const _errs4 = errors;
                if (typeof data.source !== "string") {
                  validate316.errors = [{ instancePath: instancePath + "/source", schemaPath: "#/properties/source/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs4 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.requires_confirmation !== void 0) {
                  const _errs6 = errors;
                  if (typeof data.requires_confirmation !== "boolean") {
                    validate316.errors = [{ instancePath: instancePath + "/requires_confirmation", schemaPath: "#/properties/requires_confirmation/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                    return false;
                  }
                  var valid0 = _errs6 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.review_id !== void 0) {
                    const _errs8 = errors;
                    if (typeof data.review_id !== "string") {
                      validate316.errors = [{ instancePath: instancePath + "/review_id", schemaPath: "#/properties/review_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs8 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate316.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate316.errors = vErrors;
  return errors === 0;
}
validate316.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var WorkflowDocument = validate323;
var schema140 = { "additionalProperties": false, "properties": { "id": { "type": "string" }, "project_id": { "type": "string" }, "project_revision": { "type": "integer" }, "revision": { "type": "integer" }, "semantic_revision": { "type": "integer" }, "layout_revision": { "type": "integer" }, "workflow": { "$ref": "urn:fusionlab:shared#/$defs/Workflow" }, "layout": { "additionalProperties": { "$ref": "urn:fusionlab:shared#/$defs/NodePosition" }, "type": "object" }, "selected_node_id": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "view": { "enum": ["graph", "list"], "type": "string" } }, "required": ["id", "project_id", "project_revision", "revision", "semantic_revision", "layout_revision", "workflow", "layout", "selected_node_id", "view"], "type": "object" };
function validate324(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate324.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.name === void 0 && (missing0 = "name") || data.description === void 0 && (missing0 = "description") || data.version === void 0 && (missing0 = "version") || data.nodes === void 0 && (missing0 = "nodes") || data.execution_policy === void 0 && (missing0 = "execution_policy")) {
        validate324.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "name" || key0 === "description" || key0 === "version" || key0 === "nodes" || key0 === "execution_policy")) {
            validate324.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate324.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.name !== void 0) {
              const _errs4 = errors;
              if (typeof data.name !== "string") {
                validate324.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.description !== void 0) {
                const _errs6 = errors;
                if (typeof data.description !== "string") {
                  validate324.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.version !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.version !== "string") {
                    validate324.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.nodes !== void 0) {
                    let data4 = data.nodes;
                    const _errs10 = errors;
                    if (errors === _errs10) {
                      if (Array.isArray(data4)) {
                        if (data4.length < 1) {
                          validate324.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                          return false;
                        } else {
                          var valid1 = true;
                          const len0 = data4.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs12 = errors;
                            if (!validate298(data4[i0], { instancePath: instancePath + "/nodes/" + i0, parentData: data4, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate298.errors : vErrors.concat(validate298.errors);
                              errors = vErrors.length;
                            }
                            var valid1 = _errs12 === errors;
                            if (!valid1) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate324.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.execution_policy !== void 0) {
                      const _errs13 = errors;
                      if (!validate305(data.execution_policy, { instancePath: instancePath + "/execution_policy", parentData: data, parentDataProperty: "execution_policy", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate305.errors : vErrors.concat(validate305.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs13 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate324.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate324.errors = vErrors;
  return errors === 0;
}
validate324.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate328(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate328.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.x === void 0 && (missing0 = "x") || data.y === void 0 && (missing0 = "y")) {
        validate328.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "x" || key0 === "y")) {
            validate328.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.x !== void 0) {
            let data0 = data.x;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (typeof data0 == "number") {
                if (data0 > 1e5 || isNaN(data0)) {
                  validate328.errors = [{ instancePath: instancePath + "/x", schemaPath: "#/properties/x/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e5 }, message: "must be <= 100000" }];
                  return false;
                } else {
                  if (data0 < 0 || isNaN(data0)) {
                    validate328.errors = [{ instancePath: instancePath + "/x", schemaPath: "#/properties/x/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                    return false;
                  }
                }
              } else {
                validate328.errors = [{ instancePath: instancePath + "/x", schemaPath: "#/properties/x/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.y !== void 0) {
              let data1 = data.y;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (typeof data1 == "number") {
                  if (data1 > 1e5 || isNaN(data1)) {
                    validate328.errors = [{ instancePath: instancePath + "/y", schemaPath: "#/properties/y/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e5 }, message: "must be <= 100000" }];
                    return false;
                  } else {
                    if (data1 < 0 || isNaN(data1)) {
                      validate328.errors = [{ instancePath: instancePath + "/y", schemaPath: "#/properties/y/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                      return false;
                    }
                  }
                } else {
                  validate328.errors = [{ instancePath: instancePath + "/y", schemaPath: "#/properties/y/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
          }
        }
      }
    } else {
      validate328.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate328.errors = vErrors;
  return errors === 0;
}
validate328.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate323(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate323.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.project_id === void 0 && (missing0 = "project_id") || data.project_revision === void 0 && (missing0 = "project_revision") || data.revision === void 0 && (missing0 = "revision") || data.semantic_revision === void 0 && (missing0 = "semantic_revision") || data.layout_revision === void 0 && (missing0 = "layout_revision") || data.workflow === void 0 && (missing0 = "workflow") || data.layout === void 0 && (missing0 = "layout") || data.selected_node_id === void 0 && (missing0 = "selected_node_id") || data.view === void 0 && (missing0 = "view")) {
        validate323.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema140.properties, key0)) {
            validate323.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate323.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.project_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.project_id !== "string") {
                validate323.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.project_revision !== void 0) {
                let data2 = data.project_revision;
                const _errs6 = errors;
                if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                  validate323.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.revision !== void 0) {
                  let data3 = data.revision;
                  const _errs8 = errors;
                  if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)))) {
                    validate323.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.semantic_revision !== void 0) {
                    let data4 = data.semantic_revision;
                    const _errs10 = errors;
                    if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)))) {
                      validate323.errors = [{ instancePath: instancePath + "/semantic_revision", schemaPath: "#/properties/semantic_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.layout_revision !== void 0) {
                      let data5 = data.layout_revision;
                      const _errs12 = errors;
                      if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)))) {
                        validate323.errors = [{ instancePath: instancePath + "/layout_revision", schemaPath: "#/properties/layout_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.workflow !== void 0) {
                        const _errs14 = errors;
                        if (!validate324(data.workflow, { instancePath: instancePath + "/workflow", parentData: data, parentDataProperty: "workflow", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate324.errors : vErrors.concat(validate324.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.layout !== void 0) {
                          let data7 = data.layout;
                          const _errs15 = errors;
                          if (errors === _errs15) {
                            if (data7 && typeof data7 == "object" && !Array.isArray(data7)) {
                              for (const key1 in data7) {
                                const _errs18 = errors;
                                if (!validate328(data7[key1], { instancePath: instancePath + "/layout/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), parentData: data7, parentDataProperty: key1, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate328.errors : vErrors.concat(validate328.errors);
                                  errors = vErrors.length;
                                }
                                var valid1 = _errs18 === errors;
                                if (!valid1) {
                                  break;
                                }
                              }
                            } else {
                              validate323.errors = [{ instancePath: instancePath + "/layout", schemaPath: "#/properties/layout/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                              return false;
                            }
                          }
                          var valid0 = _errs15 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.selected_node_id !== void 0) {
                            let data9 = data.selected_node_id;
                            const _errs19 = errors;
                            const _errs20 = errors;
                            let valid2 = false;
                            const _errs21 = errors;
                            if (typeof data9 !== "string") {
                              const err0 = { instancePath: instancePath + "/selected_node_id", schemaPath: "#/properties/selected_node_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err0];
                              } else {
                                vErrors.push(err0);
                              }
                              errors++;
                            }
                            var _valid0 = _errs21 === errors;
                            valid2 = valid2 || _valid0;
                            const _errs23 = errors;
                            if (data9 !== null) {
                              const err1 = { instancePath: instancePath + "/selected_node_id", schemaPath: "#/properties/selected_node_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err1];
                              } else {
                                vErrors.push(err1);
                              }
                              errors++;
                            }
                            var _valid0 = _errs23 === errors;
                            valid2 = valid2 || _valid0;
                            if (!valid2) {
                              const err2 = { instancePath: instancePath + "/selected_node_id", schemaPath: "#/properties/selected_node_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err2];
                              } else {
                                vErrors.push(err2);
                              }
                              errors++;
                              validate323.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs20;
                              if (vErrors !== null) {
                                if (_errs20) {
                                  vErrors.length = _errs20;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs19 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.view !== void 0) {
                              let data10 = data.view;
                              const _errs25 = errors;
                              if (typeof data10 !== "string") {
                                validate323.errors = [{ instancePath: instancePath + "/view", schemaPath: "#/properties/view/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if (!(data10 === "graph" || data10 === "list")) {
                                validate323.errors = [{ instancePath: instancePath + "/view", schemaPath: "#/properties/view/enum", keyword: "enum", params: { allowedValues: schema140.properties.view.enum }, message: "must be equal to one of the allowed values" }];
                                return false;
                              }
                              var valid0 = _errs25 === errors;
                            } else {
                              var valid0 = true;
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate323.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate323.errors = vErrors;
  return errors === 0;
}
validate323.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var ScientificObservation = validate330;
var schema143 = { "additionalProperties": false, "properties": { "project_id": { "type": "string" }, "project_revision": { "type": "integer" }, "observation_identity": { "type": "string" }, "scientific_input_identity": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "prepared_through": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "scenarios": { "additionalProperties": { "type": "string" }, "type": "object" }, "available_input_refs": { "items": { "type": "string" }, "type": "array" }, "gaps": { "items": { "$ref": "urn:fusionlab:shared#/$defs/ScientificGap" }, "type": "array" }, "omitted_gap_count": { "type": "integer" }, "parameter_summaries": { "items": { "$ref": "urn:fusionlab:shared#/$defs/ReviewedParameterSummary" }, "type": "array" }, "omitted_parameter_count": { "type": "integer" }, "capabilities": { "items": { "$ref": "urn:fusionlab:shared#/$defs/DomainCapability" }, "type": "array" }, "recorded_results": { "items": { "$ref": "urn:fusionlab:shared#/$defs/RecordedStageResult" }, "type": "array" }, "recorded_jobs": { "items": { "$ref": "urn:fusionlab:shared#/$defs/RecordedJob" }, "type": "array" }, "accepted_proposal_refs": { "items": { "type": "string" }, "type": "array" }, "budget": { "additionalProperties": { "anyOf": [{ "type": "integer" }, { "type": "number" }, { "type": "null" }] }, "type": "object" }, "limitations": { "items": { "type": "string" }, "type": "array" } }, "required": ["project_id", "project_revision", "observation_identity", "scientific_input_identity", "prepared_through", "scenarios", "available_input_refs", "gaps", "omitted_gap_count", "parameter_summaries", "omitted_parameter_count", "capabilities", "recorded_results", "recorded_jobs", "accepted_proposal_refs", "budget", "limitations"], "type": "object" };
function validate331(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate331.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.stage === void 0 && (missing0 = "stage") || data.code === void 0 && (missing0 = "code") || data.construct_id === void 0 && (missing0 = "construct_id") || data.condition_id === void 0 && (missing0 = "condition_id") || data.reasons === void 0 && (missing0 = "reasons")) {
        validate331.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "stage" || key0 === "code" || key0 === "construct_id" || key0 === "condition_id" || key0 === "reasons")) {
            validate331.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.stage !== void 0) {
            const _errs2 = errors;
            if (typeof data.stage !== "string") {
              validate331.errors = [{ instancePath: instancePath + "/stage", schemaPath: "#/properties/stage/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.code !== void 0) {
              const _errs4 = errors;
              if (typeof data.code !== "string") {
                validate331.errors = [{ instancePath: instancePath + "/code", schemaPath: "#/properties/code/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.construct_id !== void 0) {
                let data2 = data.construct_id;
                const _errs6 = errors;
                const _errs7 = errors;
                let valid1 = false;
                const _errs8 = errors;
                if (typeof data2 !== "string") {
                  const err0 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                }
                var _valid0 = _errs8 === errors;
                valid1 = valid1 || _valid0;
                const _errs10 = errors;
                if (data2 !== null) {
                  const err1 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                }
                var _valid0 = _errs10 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err2 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err2];
                  } else {
                    vErrors.push(err2);
                  }
                  errors++;
                  validate331.errors = vErrors;
                  return false;
                } else {
                  errors = _errs7;
                  if (vErrors !== null) {
                    if (_errs7) {
                      vErrors.length = _errs7;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.condition_id !== void 0) {
                  let data3 = data.condition_id;
                  const _errs12 = errors;
                  const _errs13 = errors;
                  let valid2 = false;
                  const _errs14 = errors;
                  if (typeof data3 !== "string") {
                    const err3 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                  }
                  var _valid1 = _errs14 === errors;
                  valid2 = valid2 || _valid1;
                  const _errs16 = errors;
                  if (data3 !== null) {
                    const err4 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err4];
                    } else {
                      vErrors.push(err4);
                    }
                    errors++;
                  }
                  var _valid1 = _errs16 === errors;
                  valid2 = valid2 || _valid1;
                  if (!valid2) {
                    const err5 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err5];
                    } else {
                      vErrors.push(err5);
                    }
                    errors++;
                    validate331.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs13;
                    if (vErrors !== null) {
                      if (_errs13) {
                        vErrors.length = _errs13;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs12 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.reasons !== void 0) {
                    let data4 = data.reasons;
                    const _errs18 = errors;
                    if (errors === _errs18) {
                      if (Array.isArray(data4)) {
                        var valid3 = true;
                        const len0 = data4.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          const _errs20 = errors;
                          if (typeof data4[i0] !== "string") {
                            validate331.errors = [{ instancePath: instancePath + "/reasons/" + i0, schemaPath: "#/properties/reasons/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid3 = _errs20 === errors;
                          if (!valid3) {
                            break;
                          }
                        }
                      } else {
                        validate331.errors = [{ instancePath: instancePath + "/reasons", schemaPath: "#/properties/reasons/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs18 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate331.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate331.errors = vErrors;
  return errors === 0;
}
validate331.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate333(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate333.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.parameter_id === void 0 && (missing0 = "parameter_id") || data.parameter_type === void 0 && (missing0 = "parameter_type") || data.construct_id === void 0 && (missing0 = "construct_id") || data.condition_id === void 0 && (missing0 = "condition_id") || data.review_status === void 0 && (missing0 = "review_status") || data.source_type === void 0 && (missing0 = "source_type") || data.unit === void 0 && (missing0 = "unit") || data.entity_basis === void 0 && (missing0 = "entity_basis") || data.model_version === void 0 && (missing0 = "model_version") || data.value === void 0 && (missing0 = "value") || data.parameter_version === void 0 && (missing0 = "parameter_version") || data.conditions === void 0 && (missing0 = "conditions")) {
        validate333.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema116.properties, key0)) {
            validate333.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.parameter_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.parameter_id !== "string") {
              validate333.errors = [{ instancePath: instancePath + "/parameter_id", schemaPath: "#/properties/parameter_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.parameter_type !== void 0) {
              const _errs4 = errors;
              if (typeof data.parameter_type !== "string") {
                validate333.errors = [{ instancePath: instancePath + "/parameter_type", schemaPath: "#/properties/parameter_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.construct_id !== void 0) {
                let data2 = data.construct_id;
                const _errs6 = errors;
                const _errs7 = errors;
                let valid1 = false;
                const _errs8 = errors;
                if (typeof data2 !== "string") {
                  const err0 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                }
                var _valid0 = _errs8 === errors;
                valid1 = valid1 || _valid0;
                const _errs10 = errors;
                if (data2 !== null) {
                  const err1 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                }
                var _valid0 = _errs10 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err2 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err2];
                  } else {
                    vErrors.push(err2);
                  }
                  errors++;
                  validate333.errors = vErrors;
                  return false;
                } else {
                  errors = _errs7;
                  if (vErrors !== null) {
                    if (_errs7) {
                      vErrors.length = _errs7;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.condition_id !== void 0) {
                  let data3 = data.condition_id;
                  const _errs12 = errors;
                  const _errs13 = errors;
                  let valid2 = false;
                  const _errs14 = errors;
                  if (typeof data3 !== "string") {
                    const err3 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                  }
                  var _valid1 = _errs14 === errors;
                  valid2 = valid2 || _valid1;
                  const _errs16 = errors;
                  if (data3 !== null) {
                    const err4 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err4];
                    } else {
                      vErrors.push(err4);
                    }
                    errors++;
                  }
                  var _valid1 = _errs16 === errors;
                  valid2 = valid2 || _valid1;
                  if (!valid2) {
                    const err5 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err5];
                    } else {
                      vErrors.push(err5);
                    }
                    errors++;
                    validate333.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs13;
                    if (vErrors !== null) {
                      if (_errs13) {
                        vErrors.length = _errs13;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs12 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.review_status !== void 0) {
                    const _errs18 = errors;
                    if (typeof data.review_status !== "string") {
                      validate333.errors = [{ instancePath: instancePath + "/review_status", schemaPath: "#/properties/review_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs18 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.source_type !== void 0) {
                      const _errs20 = errors;
                      if (typeof data.source_type !== "string") {
                        validate333.errors = [{ instancePath: instancePath + "/source_type", schemaPath: "#/properties/source_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.unit !== void 0) {
                        let data6 = data.unit;
                        const _errs22 = errors;
                        const _errs23 = errors;
                        let valid3 = false;
                        const _errs24 = errors;
                        if (typeof data6 !== "string") {
                          const err6 = { instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err6];
                          } else {
                            vErrors.push(err6);
                          }
                          errors++;
                        }
                        var _valid2 = _errs24 === errors;
                        valid3 = valid3 || _valid2;
                        const _errs26 = errors;
                        if (data6 !== null) {
                          const err7 = { instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err7];
                          } else {
                            vErrors.push(err7);
                          }
                          errors++;
                        }
                        var _valid2 = _errs26 === errors;
                        valid3 = valid3 || _valid2;
                        if (!valid3) {
                          const err8 = { instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err8];
                          } else {
                            vErrors.push(err8);
                          }
                          errors++;
                          validate333.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs23;
                          if (vErrors !== null) {
                            if (_errs23) {
                              vErrors.length = _errs23;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs22 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.entity_basis !== void 0) {
                          let data7 = data.entity_basis;
                          const _errs28 = errors;
                          const _errs29 = errors;
                          let valid4 = false;
                          const _errs30 = errors;
                          if (typeof data7 !== "string") {
                            const err9 = { instancePath: instancePath + "/entity_basis", schemaPath: "#/properties/entity_basis/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err9];
                            } else {
                              vErrors.push(err9);
                            }
                            errors++;
                          }
                          var _valid3 = _errs30 === errors;
                          valid4 = valid4 || _valid3;
                          const _errs32 = errors;
                          if (data7 !== null) {
                            const err10 = { instancePath: instancePath + "/entity_basis", schemaPath: "#/properties/entity_basis/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err10];
                            } else {
                              vErrors.push(err10);
                            }
                            errors++;
                          }
                          var _valid3 = _errs32 === errors;
                          valid4 = valid4 || _valid3;
                          if (!valid4) {
                            const err11 = { instancePath: instancePath + "/entity_basis", schemaPath: "#/properties/entity_basis/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err11];
                            } else {
                              vErrors.push(err11);
                            }
                            errors++;
                            validate333.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs29;
                            if (vErrors !== null) {
                              if (_errs29) {
                                vErrors.length = _errs29;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs28 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.model_version !== void 0) {
                            let data8 = data.model_version;
                            const _errs34 = errors;
                            const _errs35 = errors;
                            let valid5 = false;
                            const _errs36 = errors;
                            if (typeof data8 !== "string") {
                              const err12 = { instancePath: instancePath + "/model_version", schemaPath: "#/properties/model_version/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err12];
                              } else {
                                vErrors.push(err12);
                              }
                              errors++;
                            }
                            var _valid4 = _errs36 === errors;
                            valid5 = valid5 || _valid4;
                            const _errs38 = errors;
                            if (data8 !== null) {
                              const err13 = { instancePath: instancePath + "/model_version", schemaPath: "#/properties/model_version/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err13];
                              } else {
                                vErrors.push(err13);
                              }
                              errors++;
                            }
                            var _valid4 = _errs38 === errors;
                            valid5 = valid5 || _valid4;
                            if (!valid5) {
                              const err14 = { instancePath: instancePath + "/model_version", schemaPath: "#/properties/model_version/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err14];
                              } else {
                                vErrors.push(err14);
                              }
                              errors++;
                              validate333.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs35;
                              if (vErrors !== null) {
                                if (_errs35) {
                                  vErrors.length = _errs35;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs34 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.value !== void 0) {
                              let data9 = data.value;
                              const _errs40 = errors;
                              const _errs41 = errors;
                              let valid6 = false;
                              const _errs42 = errors;
                              if (!(typeof data9 == "number")) {
                                const err15 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/anyOf/0/type", keyword: "type", params: { type: "number" }, message: "must be number" };
                                if (vErrors === null) {
                                  vErrors = [err15];
                                } else {
                                  vErrors.push(err15);
                                }
                                errors++;
                              }
                              var _valid5 = _errs42 === errors;
                              valid6 = valid6 || _valid5;
                              const _errs44 = errors;
                              if (typeof data9 !== "string") {
                                const err16 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/anyOf/1/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err16];
                                } else {
                                  vErrors.push(err16);
                                }
                                errors++;
                              }
                              var _valid5 = _errs44 === errors;
                              valid6 = valid6 || _valid5;
                              if (!valid6) {
                                const err17 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                if (vErrors === null) {
                                  vErrors = [err17];
                                } else {
                                  vErrors.push(err17);
                                }
                                errors++;
                                validate333.errors = vErrors;
                                return false;
                              } else {
                                errors = _errs41;
                                if (vErrors !== null) {
                                  if (_errs41) {
                                    vErrors.length = _errs41;
                                  } else {
                                    vErrors = null;
                                  }
                                }
                              }
                              var valid0 = _errs40 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.parameter_version !== void 0) {
                                let data10 = data.parameter_version;
                                const _errs46 = errors;
                                if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)))) {
                                  validate333.errors = [{ instancePath: instancePath + "/parameter_version", schemaPath: "#/properties/parameter_version/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                var valid0 = _errs46 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.conditions !== void 0) {
                                  let data11 = data.conditions;
                                  const _errs48 = errors;
                                  if (errors === _errs48) {
                                    if (data11 && typeof data11 == "object" && !Array.isArray(data11)) {
                                      for (const key1 in data11) {
                                        let data12 = data11[key1];
                                        const _errs51 = errors;
                                        const _errs52 = errors;
                                        let valid8 = false;
                                        const _errs53 = errors;
                                        if (typeof data12 !== "string") {
                                          const err18 = { instancePath: instancePath + "/conditions/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/conditions/additionalProperties/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err18];
                                          } else {
                                            vErrors.push(err18);
                                          }
                                          errors++;
                                        }
                                        var _valid6 = _errs53 === errors;
                                        valid8 = valid8 || _valid6;
                                        const _errs55 = errors;
                                        if (!(typeof data12 == "number")) {
                                          const err19 = { instancePath: instancePath + "/conditions/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/conditions/additionalProperties/anyOf/1/type", keyword: "type", params: { type: "number" }, message: "must be number" };
                                          if (vErrors === null) {
                                            vErrors = [err19];
                                          } else {
                                            vErrors.push(err19);
                                          }
                                          errors++;
                                        }
                                        var _valid6 = _errs55 === errors;
                                        valid8 = valid8 || _valid6;
                                        if (!valid8) {
                                          const err20 = { instancePath: instancePath + "/conditions/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/conditions/additionalProperties/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                          if (vErrors === null) {
                                            vErrors = [err20];
                                          } else {
                                            vErrors.push(err20);
                                          }
                                          errors++;
                                          validate333.errors = vErrors;
                                          return false;
                                        } else {
                                          errors = _errs52;
                                          if (vErrors !== null) {
                                            if (_errs52) {
                                              vErrors.length = _errs52;
                                            } else {
                                              vErrors = null;
                                            }
                                          }
                                        }
                                        var valid7 = _errs51 === errors;
                                        if (!valid7) {
                                          break;
                                        }
                                      }
                                    } else {
                                      validate333.errors = [{ instancePath: instancePath + "/conditions", schemaPath: "#/properties/conditions/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                      return false;
                                    }
                                  }
                                  var valid0 = _errs48 === errors;
                                } else {
                                  var valid0 = true;
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate333.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate333.errors = vErrors;
  return errors === 0;
}
validate333.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate335(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate335.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.tool_id === void 0 && (missing0 = "tool_id") || data.version === void 0 && (missing0 = "version") || data.resource === void 0 && (missing0 = "resource") || data.route_state === void 0 && (missing0 = "route_state") || data.execution_allowed_by_policy === void 0 && (missing0 = "execution_allowed_by_policy")) {
        validate335.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "tool_id" || key0 === "version" || key0 === "resource" || key0 === "route_state" || key0 === "execution_allowed_by_policy")) {
            validate335.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.tool_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.tool_id !== "string") {
              validate335.errors = [{ instancePath: instancePath + "/tool_id", schemaPath: "#/properties/tool_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.version !== void 0) {
              const _errs4 = errors;
              if (typeof data.version !== "string") {
                validate335.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.resource !== void 0) {
                const _errs6 = errors;
                if (typeof data.resource !== "string") {
                  validate335.errors = [{ instancePath: instancePath + "/resource", schemaPath: "#/properties/resource/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.route_state !== void 0) {
                  let data3 = data.route_state;
                  const _errs8 = errors;
                  if (typeof data3 !== "string") {
                    validate335.errors = [{ instancePath: instancePath + "/route_state", schemaPath: "#/properties/route_state/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data3 === "local_method" || data3 === "configured_not_verified" || data3 === "unconfigured")) {
                    validate335.errors = [{ instancePath: instancePath + "/route_state", schemaPath: "#/properties/route_state/enum", keyword: "enum", params: { allowedValues: schema117.properties.route_state.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.execution_allowed_by_policy !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.execution_allowed_by_policy !== "boolean") {
                      validate335.errors = [{ instancePath: instancePath + "/execution_allowed_by_policy", schemaPath: "#/properties/execution_allowed_by_policy/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate335.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate335.errors = vErrors;
  return errors === 0;
}
validate335.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate337(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate337.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.run_id === void 0 && (missing0 = "run_id") || data.node_id === void 0 && (missing0 = "node_id") || data.stage === void 0 && (missing0 = "stage") || data.node_status === void 0 && (missing0 = "node_status") || data.attempt === void 0 && (missing0 = "attempt") || data.result_ref === void 0 && (missing0 = "result_ref") || data.current_project_revision === void 0 && (missing0 = "current_project_revision") || data.scientific_status_counts === void 0 && (missing0 = "scientific_status_counts") || data.numerically_solved_count === void 0 && (missing0 = "numerically_solved_count") || data.evidence_ready_count === void 0 && (missing0 = "evidence_ready_count") || data.claim_scopes === void 0 && (missing0 = "claim_scopes")) {
        validate337.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema118.properties, key0)) {
            validate337.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.run_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.run_id !== "string") {
              validate337.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.node_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.node_id !== "string") {
                validate337.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.stage !== void 0) {
                const _errs6 = errors;
                if (typeof data.stage !== "string") {
                  validate337.errors = [{ instancePath: instancePath + "/stage", schemaPath: "#/properties/stage/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.node_status !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.node_status !== "string") {
                    validate337.errors = [{ instancePath: instancePath + "/node_status", schemaPath: "#/properties/node_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.attempt !== void 0) {
                    let data4 = data.attempt;
                    const _errs10 = errors;
                    if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)))) {
                      validate337.errors = [{ instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.result_ref !== void 0) {
                      let data5 = data.result_ref;
                      const _errs12 = errors;
                      const _errs13 = errors;
                      let valid1 = false;
                      const _errs14 = errors;
                      if (typeof data5 !== "string") {
                        const err0 = { instancePath: instancePath + "/result_ref", schemaPath: "#/properties/result_ref/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      }
                      var _valid0 = _errs14 === errors;
                      valid1 = valid1 || _valid0;
                      const _errs16 = errors;
                      if (data5 !== null) {
                        const err1 = { instancePath: instancePath + "/result_ref", schemaPath: "#/properties/result_ref/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      }
                      var _valid0 = _errs16 === errors;
                      valid1 = valid1 || _valid0;
                      if (!valid1) {
                        const err2 = { instancePath: instancePath + "/result_ref", schemaPath: "#/properties/result_ref/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err2];
                        } else {
                          vErrors.push(err2);
                        }
                        errors++;
                        validate337.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs13;
                        if (vErrors !== null) {
                          if (_errs13) {
                            vErrors.length = _errs13;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.current_project_revision !== void 0) {
                        const _errs18 = errors;
                        if (typeof data.current_project_revision !== "boolean") {
                          validate337.errors = [{ instancePath: instancePath + "/current_project_revision", schemaPath: "#/properties/current_project_revision/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                          return false;
                        }
                        var valid0 = _errs18 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.scientific_status_counts !== void 0) {
                          let data7 = data.scientific_status_counts;
                          const _errs20 = errors;
                          if (errors === _errs20) {
                            if (data7 && typeof data7 == "object" && !Array.isArray(data7)) {
                              for (const key1 in data7) {
                                let data8 = data7[key1];
                                const _errs23 = errors;
                                if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)))) {
                                  validate337.errors = [{ instancePath: instancePath + "/scientific_status_counts/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/scientific_status_counts/additionalProperties/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                var valid2 = _errs23 === errors;
                                if (!valid2) {
                                  break;
                                }
                              }
                            } else {
                              validate337.errors = [{ instancePath: instancePath + "/scientific_status_counts", schemaPath: "#/properties/scientific_status_counts/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                              return false;
                            }
                          }
                          var valid0 = _errs20 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.numerically_solved_count !== void 0) {
                            let data9 = data.numerically_solved_count;
                            const _errs25 = errors;
                            const _errs26 = errors;
                            let valid3 = false;
                            const _errs27 = errors;
                            if (!(typeof data9 == "number" && (!(data9 % 1) && !isNaN(data9)))) {
                              const err3 = { instancePath: instancePath + "/numerically_solved_count", schemaPath: "#/properties/numerically_solved_count/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                              if (vErrors === null) {
                                vErrors = [err3];
                              } else {
                                vErrors.push(err3);
                              }
                              errors++;
                            }
                            var _valid1 = _errs27 === errors;
                            valid3 = valid3 || _valid1;
                            const _errs29 = errors;
                            if (data9 !== null) {
                              const err4 = { instancePath: instancePath + "/numerically_solved_count", schemaPath: "#/properties/numerically_solved_count/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err4];
                              } else {
                                vErrors.push(err4);
                              }
                              errors++;
                            }
                            var _valid1 = _errs29 === errors;
                            valid3 = valid3 || _valid1;
                            if (!valid3) {
                              const err5 = { instancePath: instancePath + "/numerically_solved_count", schemaPath: "#/properties/numerically_solved_count/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err5];
                              } else {
                                vErrors.push(err5);
                              }
                              errors++;
                              validate337.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs26;
                              if (vErrors !== null) {
                                if (_errs26) {
                                  vErrors.length = _errs26;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs25 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.evidence_ready_count !== void 0) {
                              let data10 = data.evidence_ready_count;
                              const _errs31 = errors;
                              const _errs32 = errors;
                              let valid4 = false;
                              const _errs33 = errors;
                              if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)))) {
                                const err6 = { instancePath: instancePath + "/evidence_ready_count", schemaPath: "#/properties/evidence_ready_count/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                if (vErrors === null) {
                                  vErrors = [err6];
                                } else {
                                  vErrors.push(err6);
                                }
                                errors++;
                              }
                              var _valid2 = _errs33 === errors;
                              valid4 = valid4 || _valid2;
                              const _errs35 = errors;
                              if (data10 !== null) {
                                const err7 = { instancePath: instancePath + "/evidence_ready_count", schemaPath: "#/properties/evidence_ready_count/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                if (vErrors === null) {
                                  vErrors = [err7];
                                } else {
                                  vErrors.push(err7);
                                }
                                errors++;
                              }
                              var _valid2 = _errs35 === errors;
                              valid4 = valid4 || _valid2;
                              if (!valid4) {
                                const err8 = { instancePath: instancePath + "/evidence_ready_count", schemaPath: "#/properties/evidence_ready_count/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                if (vErrors === null) {
                                  vErrors = [err8];
                                } else {
                                  vErrors.push(err8);
                                }
                                errors++;
                                validate337.errors = vErrors;
                                return false;
                              } else {
                                errors = _errs32;
                                if (vErrors !== null) {
                                  if (_errs32) {
                                    vErrors.length = _errs32;
                                  } else {
                                    vErrors = null;
                                  }
                                }
                              }
                              var valid0 = _errs31 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.claim_scopes !== void 0) {
                                let data11 = data.claim_scopes;
                                const _errs37 = errors;
                                if (errors === _errs37) {
                                  if (Array.isArray(data11)) {
                                    var valid5 = true;
                                    const len0 = data11.length;
                                    for (let i0 = 0; i0 < len0; i0++) {
                                      const _errs39 = errors;
                                      if (typeof data11[i0] !== "string") {
                                        validate337.errors = [{ instancePath: instancePath + "/claim_scopes/" + i0, schemaPath: "#/properties/claim_scopes/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      var valid5 = _errs39 === errors;
                                      if (!valid5) {
                                        break;
                                      }
                                    }
                                  } else {
                                    validate337.errors = [{ instancePath: instancePath + "/claim_scopes", schemaPath: "#/properties/claim_scopes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                    return false;
                                  }
                                }
                                var valid0 = _errs37 === errors;
                              } else {
                                var valid0 = true;
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate337.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate337.errors = vErrors;
  return errors === 0;
}
validate337.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate339(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate339.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.run_id === void 0 && (missing0 = "run_id") || data.node_id === void 0 && (missing0 = "node_id") || data.tool_id === void 0 && (missing0 = "tool_id") || data.node_status === void 0 && (missing0 = "node_status") || data.attempt === void 0 && (missing0 = "attempt") || data.tool_status === void 0 && (missing0 = "tool_status") || data.parse_status === void 0 && (missing0 = "parse_status") || data.remote_status === void 0 && (missing0 = "remote_status") || data.remote_poll_count === void 0 && (missing0 = "remote_poll_count") || data.remote_cancellation_confirmed === void 0 && (missing0 = "remote_cancellation_confirmed")) {
        validate339.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema119.properties, key0)) {
            validate339.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.run_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.run_id !== "string") {
              validate339.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.node_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.node_id !== "string") {
                validate339.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.tool_id !== void 0) {
                const _errs6 = errors;
                if (typeof data.tool_id !== "string") {
                  validate339.errors = [{ instancePath: instancePath + "/tool_id", schemaPath: "#/properties/tool_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.node_status !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.node_status !== "string") {
                    validate339.errors = [{ instancePath: instancePath + "/node_status", schemaPath: "#/properties/node_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.attempt !== void 0) {
                    let data4 = data.attempt;
                    const _errs10 = errors;
                    if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)))) {
                      validate339.errors = [{ instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.tool_status !== void 0) {
                      let data5 = data.tool_status;
                      const _errs12 = errors;
                      const _errs13 = errors;
                      let valid1 = false;
                      const _errs14 = errors;
                      if (typeof data5 !== "string") {
                        const err0 = { instancePath: instancePath + "/tool_status", schemaPath: "#/properties/tool_status/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      }
                      var _valid0 = _errs14 === errors;
                      valid1 = valid1 || _valid0;
                      const _errs16 = errors;
                      if (data5 !== null) {
                        const err1 = { instancePath: instancePath + "/tool_status", schemaPath: "#/properties/tool_status/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      }
                      var _valid0 = _errs16 === errors;
                      valid1 = valid1 || _valid0;
                      if (!valid1) {
                        const err2 = { instancePath: instancePath + "/tool_status", schemaPath: "#/properties/tool_status/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err2];
                        } else {
                          vErrors.push(err2);
                        }
                        errors++;
                        validate339.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs13;
                        if (vErrors !== null) {
                          if (_errs13) {
                            vErrors.length = _errs13;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.parse_status !== void 0) {
                        let data6 = data.parse_status;
                        const _errs18 = errors;
                        const _errs19 = errors;
                        let valid2 = false;
                        const _errs20 = errors;
                        if (typeof data6 !== "string") {
                          const err3 = { instancePath: instancePath + "/parse_status", schemaPath: "#/properties/parse_status/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err3];
                          } else {
                            vErrors.push(err3);
                          }
                          errors++;
                        }
                        var _valid1 = _errs20 === errors;
                        valid2 = valid2 || _valid1;
                        const _errs22 = errors;
                        if (data6 !== null) {
                          const err4 = { instancePath: instancePath + "/parse_status", schemaPath: "#/properties/parse_status/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err4];
                          } else {
                            vErrors.push(err4);
                          }
                          errors++;
                        }
                        var _valid1 = _errs22 === errors;
                        valid2 = valid2 || _valid1;
                        if (!valid2) {
                          const err5 = { instancePath: instancePath + "/parse_status", schemaPath: "#/properties/parse_status/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err5];
                          } else {
                            vErrors.push(err5);
                          }
                          errors++;
                          validate339.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs19;
                          if (vErrors !== null) {
                            if (_errs19) {
                              vErrors.length = _errs19;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs18 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.remote_status !== void 0) {
                          let data7 = data.remote_status;
                          const _errs24 = errors;
                          const _errs25 = errors;
                          let valid3 = false;
                          const _errs26 = errors;
                          if (typeof data7 !== "string") {
                            const err6 = { instancePath: instancePath + "/remote_status", schemaPath: "#/properties/remote_status/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err6];
                            } else {
                              vErrors.push(err6);
                            }
                            errors++;
                          }
                          var _valid2 = _errs26 === errors;
                          valid3 = valid3 || _valid2;
                          const _errs28 = errors;
                          if (data7 !== null) {
                            const err7 = { instancePath: instancePath + "/remote_status", schemaPath: "#/properties/remote_status/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err7];
                            } else {
                              vErrors.push(err7);
                            }
                            errors++;
                          }
                          var _valid2 = _errs28 === errors;
                          valid3 = valid3 || _valid2;
                          if (!valid3) {
                            const err8 = { instancePath: instancePath + "/remote_status", schemaPath: "#/properties/remote_status/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err8];
                            } else {
                              vErrors.push(err8);
                            }
                            errors++;
                            validate339.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs25;
                            if (vErrors !== null) {
                              if (_errs25) {
                                vErrors.length = _errs25;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs24 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.remote_poll_count !== void 0) {
                            let data8 = data.remote_poll_count;
                            const _errs30 = errors;
                            const _errs31 = errors;
                            let valid4 = false;
                            const _errs32 = errors;
                            if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)))) {
                              const err9 = { instancePath: instancePath + "/remote_poll_count", schemaPath: "#/properties/remote_poll_count/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                              if (vErrors === null) {
                                vErrors = [err9];
                              } else {
                                vErrors.push(err9);
                              }
                              errors++;
                            }
                            var _valid3 = _errs32 === errors;
                            valid4 = valid4 || _valid3;
                            const _errs34 = errors;
                            if (data8 !== null) {
                              const err10 = { instancePath: instancePath + "/remote_poll_count", schemaPath: "#/properties/remote_poll_count/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err10];
                              } else {
                                vErrors.push(err10);
                              }
                              errors++;
                            }
                            var _valid3 = _errs34 === errors;
                            valid4 = valid4 || _valid3;
                            if (!valid4) {
                              const err11 = { instancePath: instancePath + "/remote_poll_count", schemaPath: "#/properties/remote_poll_count/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err11];
                              } else {
                                vErrors.push(err11);
                              }
                              errors++;
                              validate339.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs31;
                              if (vErrors !== null) {
                                if (_errs31) {
                                  vErrors.length = _errs31;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs30 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.remote_cancellation_confirmed !== void 0) {
                              let data9 = data.remote_cancellation_confirmed;
                              const _errs36 = errors;
                              if (typeof data9 !== "boolean") {
                                validate339.errors = [{ instancePath: instancePath + "/remote_cancellation_confirmed", schemaPath: "#/properties/remote_cancellation_confirmed/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                return false;
                              }
                              if (false !== data9) {
                                validate339.errors = [{ instancePath: instancePath + "/remote_cancellation_confirmed", schemaPath: "#/properties/remote_cancellation_confirmed/const", keyword: "const", params: { allowedValue: false }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid0 = _errs36 === errors;
                            } else {
                              var valid0 = true;
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate339.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate339.errors = vErrors;
  return errors === 0;
}
validate339.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate330(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate330.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.project_revision === void 0 && (missing0 = "project_revision") || data.observation_identity === void 0 && (missing0 = "observation_identity") || data.scientific_input_identity === void 0 && (missing0 = "scientific_input_identity") || data.prepared_through === void 0 && (missing0 = "prepared_through") || data.scenarios === void 0 && (missing0 = "scenarios") || data.available_input_refs === void 0 && (missing0 = "available_input_refs") || data.gaps === void 0 && (missing0 = "gaps") || data.omitted_gap_count === void 0 && (missing0 = "omitted_gap_count") || data.parameter_summaries === void 0 && (missing0 = "parameter_summaries") || data.omitted_parameter_count === void 0 && (missing0 = "omitted_parameter_count") || data.capabilities === void 0 && (missing0 = "capabilities") || data.recorded_results === void 0 && (missing0 = "recorded_results") || data.recorded_jobs === void 0 && (missing0 = "recorded_jobs") || data.accepted_proposal_refs === void 0 && (missing0 = "accepted_proposal_refs") || data.budget === void 0 && (missing0 = "budget") || data.limitations === void 0 && (missing0 = "limitations")) {
        validate330.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema143.properties, key0)) {
            validate330.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate330.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.project_revision !== void 0) {
              let data1 = data.project_revision;
              const _errs4 = errors;
              if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)))) {
                validate330.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.observation_identity !== void 0) {
                const _errs6 = errors;
                if (typeof data.observation_identity !== "string") {
                  validate330.errors = [{ instancePath: instancePath + "/observation_identity", schemaPath: "#/properties/observation_identity/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scientific_input_identity !== void 0) {
                  let data3 = data.scientific_input_identity;
                  const _errs8 = errors;
                  const _errs9 = errors;
                  let valid1 = false;
                  const _errs10 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/scientific_input_identity", schemaPath: "#/properties/scientific_input_identity/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                  }
                  var _valid0 = _errs10 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs12 = errors;
                  if (data3 !== null) {
                    const err1 = { instancePath: instancePath + "/scientific_input_identity", schemaPath: "#/properties/scientific_input_identity/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                  }
                  var _valid0 = _errs12 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err2 = { instancePath: instancePath + "/scientific_input_identity", schemaPath: "#/properties/scientific_input_identity/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate330.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs9;
                    if (vErrors !== null) {
                      if (_errs9) {
                        vErrors.length = _errs9;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.prepared_through !== void 0) {
                    let data4 = data.prepared_through;
                    const _errs14 = errors;
                    const _errs15 = errors;
                    let valid2 = false;
                    const _errs16 = errors;
                    if (typeof data4 !== "string") {
                      const err3 = { instancePath: instancePath + "/prepared_through", schemaPath: "#/properties/prepared_through/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                      if (vErrors === null) {
                        vErrors = [err3];
                      } else {
                        vErrors.push(err3);
                      }
                      errors++;
                    }
                    var _valid1 = _errs16 === errors;
                    valid2 = valid2 || _valid1;
                    const _errs18 = errors;
                    if (data4 !== null) {
                      const err4 = { instancePath: instancePath + "/prepared_through", schemaPath: "#/properties/prepared_through/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err4];
                      } else {
                        vErrors.push(err4);
                      }
                      errors++;
                    }
                    var _valid1 = _errs18 === errors;
                    valid2 = valid2 || _valid1;
                    if (!valid2) {
                      const err5 = { instancePath: instancePath + "/prepared_through", schemaPath: "#/properties/prepared_through/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err5];
                      } else {
                        vErrors.push(err5);
                      }
                      errors++;
                      validate330.errors = vErrors;
                      return false;
                    } else {
                      errors = _errs15;
                      if (vErrors !== null) {
                        if (_errs15) {
                          vErrors.length = _errs15;
                        } else {
                          vErrors = null;
                        }
                      }
                    }
                    var valid0 = _errs14 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.scenarios !== void 0) {
                      let data5 = data.scenarios;
                      const _errs20 = errors;
                      if (errors === _errs20) {
                        if (data5 && typeof data5 == "object" && !Array.isArray(data5)) {
                          for (const key1 in data5) {
                            const _errs23 = errors;
                            if (typeof data5[key1] !== "string") {
                              validate330.errors = [{ instancePath: instancePath + "/scenarios/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/scenarios/additionalProperties/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid3 = _errs23 === errors;
                            if (!valid3) {
                              break;
                            }
                          }
                        } else {
                          validate330.errors = [{ instancePath: instancePath + "/scenarios", schemaPath: "#/properties/scenarios/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                          return false;
                        }
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.available_input_refs !== void 0) {
                        let data7 = data.available_input_refs;
                        const _errs25 = errors;
                        if (errors === _errs25) {
                          if (Array.isArray(data7)) {
                            var valid4 = true;
                            const len0 = data7.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              const _errs27 = errors;
                              if (typeof data7[i0] !== "string") {
                                validate330.errors = [{ instancePath: instancePath + "/available_input_refs/" + i0, schemaPath: "#/properties/available_input_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid4 = _errs27 === errors;
                              if (!valid4) {
                                break;
                              }
                            }
                          } else {
                            validate330.errors = [{ instancePath: instancePath + "/available_input_refs", schemaPath: "#/properties/available_input_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs25 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.gaps !== void 0) {
                          let data9 = data.gaps;
                          const _errs29 = errors;
                          if (errors === _errs29) {
                            if (Array.isArray(data9)) {
                              var valid5 = true;
                              const len1 = data9.length;
                              for (let i1 = 0; i1 < len1; i1++) {
                                const _errs31 = errors;
                                if (!validate331(data9[i1], { instancePath: instancePath + "/gaps/" + i1, parentData: data9, parentDataProperty: i1, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate331.errors : vErrors.concat(validate331.errors);
                                  errors = vErrors.length;
                                }
                                var valid5 = _errs31 === errors;
                                if (!valid5) {
                                  break;
                                }
                              }
                            } else {
                              validate330.errors = [{ instancePath: instancePath + "/gaps", schemaPath: "#/properties/gaps/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs29 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.omitted_gap_count !== void 0) {
                            let data11 = data.omitted_gap_count;
                            const _errs32 = errors;
                            if (!(typeof data11 == "number" && (!(data11 % 1) && !isNaN(data11)))) {
                              validate330.errors = [{ instancePath: instancePath + "/omitted_gap_count", schemaPath: "#/properties/omitted_gap_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            var valid0 = _errs32 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.parameter_summaries !== void 0) {
                              let data12 = data.parameter_summaries;
                              const _errs34 = errors;
                              if (errors === _errs34) {
                                if (Array.isArray(data12)) {
                                  var valid6 = true;
                                  const len2 = data12.length;
                                  for (let i2 = 0; i2 < len2; i2++) {
                                    const _errs36 = errors;
                                    if (!validate333(data12[i2], { instancePath: instancePath + "/parameter_summaries/" + i2, parentData: data12, parentDataProperty: i2, rootData, dynamicAnchors })) {
                                      vErrors = vErrors === null ? validate333.errors : vErrors.concat(validate333.errors);
                                      errors = vErrors.length;
                                    }
                                    var valid6 = _errs36 === errors;
                                    if (!valid6) {
                                      break;
                                    }
                                  }
                                } else {
                                  validate330.errors = [{ instancePath: instancePath + "/parameter_summaries", schemaPath: "#/properties/parameter_summaries/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs34 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.omitted_parameter_count !== void 0) {
                                let data14 = data.omitted_parameter_count;
                                const _errs37 = errors;
                                if (!(typeof data14 == "number" && (!(data14 % 1) && !isNaN(data14)))) {
                                  validate330.errors = [{ instancePath: instancePath + "/omitted_parameter_count", schemaPath: "#/properties/omitted_parameter_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                var valid0 = _errs37 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.capabilities !== void 0) {
                                  let data15 = data.capabilities;
                                  const _errs39 = errors;
                                  if (errors === _errs39) {
                                    if (Array.isArray(data15)) {
                                      var valid7 = true;
                                      const len3 = data15.length;
                                      for (let i3 = 0; i3 < len3; i3++) {
                                        const _errs41 = errors;
                                        if (!validate335(data15[i3], { instancePath: instancePath + "/capabilities/" + i3, parentData: data15, parentDataProperty: i3, rootData, dynamicAnchors })) {
                                          vErrors = vErrors === null ? validate335.errors : vErrors.concat(validate335.errors);
                                          errors = vErrors.length;
                                        }
                                        var valid7 = _errs41 === errors;
                                        if (!valid7) {
                                          break;
                                        }
                                      }
                                    } else {
                                      validate330.errors = [{ instancePath: instancePath + "/capabilities", schemaPath: "#/properties/capabilities/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                      return false;
                                    }
                                  }
                                  var valid0 = _errs39 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.recorded_results !== void 0) {
                                    let data17 = data.recorded_results;
                                    const _errs42 = errors;
                                    if (errors === _errs42) {
                                      if (Array.isArray(data17)) {
                                        var valid8 = true;
                                        const len4 = data17.length;
                                        for (let i4 = 0; i4 < len4; i4++) {
                                          const _errs44 = errors;
                                          if (!validate337(data17[i4], { instancePath: instancePath + "/recorded_results/" + i4, parentData: data17, parentDataProperty: i4, rootData, dynamicAnchors })) {
                                            vErrors = vErrors === null ? validate337.errors : vErrors.concat(validate337.errors);
                                            errors = vErrors.length;
                                          }
                                          var valid8 = _errs44 === errors;
                                          if (!valid8) {
                                            break;
                                          }
                                        }
                                      } else {
                                        validate330.errors = [{ instancePath: instancePath + "/recorded_results", schemaPath: "#/properties/recorded_results/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                        return false;
                                      }
                                    }
                                    var valid0 = _errs42 === errors;
                                  } else {
                                    var valid0 = true;
                                  }
                                  if (valid0) {
                                    if (data.recorded_jobs !== void 0) {
                                      let data19 = data.recorded_jobs;
                                      const _errs45 = errors;
                                      if (errors === _errs45) {
                                        if (Array.isArray(data19)) {
                                          var valid9 = true;
                                          const len5 = data19.length;
                                          for (let i5 = 0; i5 < len5; i5++) {
                                            const _errs47 = errors;
                                            if (!validate339(data19[i5], { instancePath: instancePath + "/recorded_jobs/" + i5, parentData: data19, parentDataProperty: i5, rootData, dynamicAnchors })) {
                                              vErrors = vErrors === null ? validate339.errors : vErrors.concat(validate339.errors);
                                              errors = vErrors.length;
                                            }
                                            var valid9 = _errs47 === errors;
                                            if (!valid9) {
                                              break;
                                            }
                                          }
                                        } else {
                                          validate330.errors = [{ instancePath: instancePath + "/recorded_jobs", schemaPath: "#/properties/recorded_jobs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                          return false;
                                        }
                                      }
                                      var valid0 = _errs45 === errors;
                                    } else {
                                      var valid0 = true;
                                    }
                                    if (valid0) {
                                      if (data.accepted_proposal_refs !== void 0) {
                                        let data21 = data.accepted_proposal_refs;
                                        const _errs48 = errors;
                                        if (errors === _errs48) {
                                          if (Array.isArray(data21)) {
                                            var valid10 = true;
                                            const len6 = data21.length;
                                            for (let i6 = 0; i6 < len6; i6++) {
                                              const _errs50 = errors;
                                              if (typeof data21[i6] !== "string") {
                                                validate330.errors = [{ instancePath: instancePath + "/accepted_proposal_refs/" + i6, schemaPath: "#/properties/accepted_proposal_refs/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                return false;
                                              }
                                              var valid10 = _errs50 === errors;
                                              if (!valid10) {
                                                break;
                                              }
                                            }
                                          } else {
                                            validate330.errors = [{ instancePath: instancePath + "/accepted_proposal_refs", schemaPath: "#/properties/accepted_proposal_refs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                            return false;
                                          }
                                        }
                                        var valid0 = _errs48 === errors;
                                      } else {
                                        var valid0 = true;
                                      }
                                      if (valid0) {
                                        if (data.budget !== void 0) {
                                          let data23 = data.budget;
                                          const _errs52 = errors;
                                          if (errors === _errs52) {
                                            if (data23 && typeof data23 == "object" && !Array.isArray(data23)) {
                                              for (const key2 in data23) {
                                                let data24 = data23[key2];
                                                const _errs55 = errors;
                                                const _errs56 = errors;
                                                let valid12 = false;
                                                const _errs57 = errors;
                                                if (!(typeof data24 == "number" && (!(data24 % 1) && !isNaN(data24)))) {
                                                  const err6 = { instancePath: instancePath + "/budget/" + key2.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/budget/additionalProperties/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                                  if (vErrors === null) {
                                                    vErrors = [err6];
                                                  } else {
                                                    vErrors.push(err6);
                                                  }
                                                  errors++;
                                                }
                                                var _valid2 = _errs57 === errors;
                                                valid12 = valid12 || _valid2;
                                                const _errs59 = errors;
                                                if (!(typeof data24 == "number")) {
                                                  const err7 = { instancePath: instancePath + "/budget/" + key2.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/budget/additionalProperties/anyOf/1/type", keyword: "type", params: { type: "number" }, message: "must be number" };
                                                  if (vErrors === null) {
                                                    vErrors = [err7];
                                                  } else {
                                                    vErrors.push(err7);
                                                  }
                                                  errors++;
                                                }
                                                var _valid2 = _errs59 === errors;
                                                valid12 = valid12 || _valid2;
                                                const _errs61 = errors;
                                                if (data24 !== null) {
                                                  const err8 = { instancePath: instancePath + "/budget/" + key2.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/budget/additionalProperties/anyOf/2/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                                  if (vErrors === null) {
                                                    vErrors = [err8];
                                                  } else {
                                                    vErrors.push(err8);
                                                  }
                                                  errors++;
                                                }
                                                var _valid2 = _errs61 === errors;
                                                valid12 = valid12 || _valid2;
                                                if (!valid12) {
                                                  const err9 = { instancePath: instancePath + "/budget/" + key2.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/budget/additionalProperties/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                                  if (vErrors === null) {
                                                    vErrors = [err9];
                                                  } else {
                                                    vErrors.push(err9);
                                                  }
                                                  errors++;
                                                  validate330.errors = vErrors;
                                                  return false;
                                                } else {
                                                  errors = _errs56;
                                                  if (vErrors !== null) {
                                                    if (_errs56) {
                                                      vErrors.length = _errs56;
                                                    } else {
                                                      vErrors = null;
                                                    }
                                                  }
                                                }
                                                var valid11 = _errs55 === errors;
                                                if (!valid11) {
                                                  break;
                                                }
                                              }
                                            } else {
                                              validate330.errors = [{ instancePath: instancePath + "/budget", schemaPath: "#/properties/budget/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                              return false;
                                            }
                                          }
                                          var valid0 = _errs52 === errors;
                                        } else {
                                          var valid0 = true;
                                        }
                                        if (valid0) {
                                          if (data.limitations !== void 0) {
                                            let data25 = data.limitations;
                                            const _errs63 = errors;
                                            if (errors === _errs63) {
                                              if (Array.isArray(data25)) {
                                                var valid13 = true;
                                                const len7 = data25.length;
                                                for (let i7 = 0; i7 < len7; i7++) {
                                                  const _errs65 = errors;
                                                  if (typeof data25[i7] !== "string") {
                                                    validate330.errors = [{ instancePath: instancePath + "/limitations/" + i7, schemaPath: "#/properties/limitations/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                    return false;
                                                  }
                                                  var valid13 = _errs65 === errors;
                                                  if (!valid13) {
                                                    break;
                                                  }
                                                }
                                              } else {
                                                validate330.errors = [{ instancePath: instancePath + "/limitations", schemaPath: "#/properties/limitations/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                                return false;
                                              }
                                            }
                                            var valid0 = _errs63 === errors;
                                          } else {
                                            var valid0 = true;
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate330.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate330.errors = vErrors;
  return errors === 0;
}
validate330.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
export {
  AssistantPage,
  PlanView,
  ProposalDiff,
  ProposalView,
  ScientificObservation,
  WorkflowDocument
};
