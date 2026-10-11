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
var RunSummaryView = validate341;
var schema149 = { "additionalProperties": false, "properties": { "id": { "type": "string" }, "name": { "type": "string" }, "project_id": { "type": "string" }, "status": { "type": "string" }, "snapshot_hash": { "type": "string" }, "created_at": { "type": "string" }, "updated_at": { "type": "string" }, "control": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "heartbeat": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "state_version": { "type": "integer" }, "event_cursor": { "type": "integer" }, "project_revision": { "type": "integer" }, "workflow": { "$ref": "urn:fusionlab:shared#/$defs/Workflow" }, "tools": { "additionalProperties": true, "type": "object" }, "nodes": { "items": { "$ref": "urn:fusionlab:shared#/$defs/NodeStateView" }, "type": "array" }, "artifacts": { "items": { "$ref": "urn:fusionlab:shared#/$defs/ArtifactView" }, "type": "array" }, "scientific_assessment": { "additionalProperties": { "type": "string" }, "type": "object" } }, "required": ["id", "name", "project_id", "status", "snapshot_hash", "created_at", "updated_at", "control", "heartbeat", "state_version", "event_cursor", "project_revision", "workflow", "tools", "nodes", "artifacts", "scientific_assessment"], "type": "object" };
var func1 = Object.prototype.hasOwnProperty;
var func2 = require_ucs2length().default;
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
function validate342(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate342.evaluated;
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
        validate342.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "name" || key0 === "description" || key0 === "version" || key0 === "nodes" || key0 === "execution_policy")) {
            validate342.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate342.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate342.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                  validate342.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate342.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate342.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
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
                        validate342.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
      validate342.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate342.errors = vErrors;
  return errors === 0;
}
validate342.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate347(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate347.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.module === void 0 && (missing0 = "module") || data.record_count === void 0 && (missing0 = "record_count") || data.status_counts === void 0 && (missing0 = "status_counts") || data.numerically_solved_count === void 0 && (missing0 = "numerically_solved_count") || data.evidence_ready_count === void 0 && (missing0 = "evidence_ready_count") || data.missing_input_count === void 0 && (missing0 = "missing_input_count") || data.claim_scope === void 0 && (missing0 = "claim_scope")) {
        validate347.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "module" || key0 === "record_count" || key0 === "status_counts" || key0 === "numerically_solved_count" || key0 === "evidence_ready_count" || key0 === "missing_input_count" || key0 === "claim_scope")) {
            validate347.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.module !== void 0) {
            const _errs2 = errors;
            if (typeof data.module !== "string") {
              validate347.errors = [{ instancePath: instancePath + "/module", schemaPath: "#/properties/module/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.record_count !== void 0) {
              let data1 = data.record_count;
              const _errs4 = errors;
              if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)))) {
                validate347.errors = [{ instancePath: instancePath + "/record_count", schemaPath: "#/properties/record_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.status_counts !== void 0) {
                let data2 = data.status_counts;
                const _errs6 = errors;
                if (errors === _errs6) {
                  if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                    for (const key1 in data2) {
                      let data3 = data2[key1];
                      const _errs9 = errors;
                      if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)))) {
                        validate347.errors = [{ instancePath: instancePath + "/status_counts/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/status_counts/additionalProperties/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      var valid1 = _errs9 === errors;
                      if (!valid1) {
                        break;
                      }
                    }
                  } else {
                    validate347.errors = [{ instancePath: instancePath + "/status_counts", schemaPath: "#/properties/status_counts/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                    return false;
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.numerically_solved_count !== void 0) {
                  let data4 = data.numerically_solved_count;
                  const _errs11 = errors;
                  if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)))) {
                    validate347.errors = [{ instancePath: instancePath + "/numerically_solved_count", schemaPath: "#/properties/numerically_solved_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  var valid0 = _errs11 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.evidence_ready_count !== void 0) {
                    let data5 = data.evidence_ready_count;
                    const _errs13 = errors;
                    if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)))) {
                      validate347.errors = [{ instancePath: instancePath + "/evidence_ready_count", schemaPath: "#/properties/evidence_ready_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    var valid0 = _errs13 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.missing_input_count !== void 0) {
                      let data6 = data.missing_input_count;
                      const _errs15 = errors;
                      if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)))) {
                        validate347.errors = [{ instancePath: instancePath + "/missing_input_count", schemaPath: "#/properties/missing_input_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      var valid0 = _errs15 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.claim_scope !== void 0) {
                        let data7 = data.claim_scope;
                        const _errs17 = errors;
                        const _errs18 = errors;
                        let valid2 = false;
                        const _errs19 = errors;
                        if (typeof data7 !== "string") {
                          const err0 = { instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                        }
                        var _valid0 = _errs19 === errors;
                        valid2 = valid2 || _valid0;
                        const _errs21 = errors;
                        if (data7 !== null) {
                          const err1 = { instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err1];
                          } else {
                            vErrors.push(err1);
                          }
                          errors++;
                        }
                        var _valid0 = _errs21 === errors;
                        valid2 = valid2 || _valid0;
                        if (!valid2) {
                          const err2 = { instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err2];
                          } else {
                            vErrors.push(err2);
                          }
                          errors++;
                          validate347.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs18;
                          if (vErrors !== null) {
                            if (_errs18) {
                              vErrors.length = _errs18;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs17 === errors;
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
    } else {
      validate347.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate347.errors = vErrors;
  return errors === 0;
}
validate347.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate346(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate346.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.parent_id === void 0 && (missing0 = "parent_id") || data.status === void 0 && (missing0 = "status") || data.attempts === void 0 && (missing0 = "attempts") || data.tool_id === void 0 && (missing0 = "tool_id") || data.label === void 0 && (missing0 = "label") || data.scientific_summary === void 0 && (missing0 = "scientific_summary")) {
        validate346.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "parent_id" || key0 === "status" || key0 === "attempts" || key0 === "tool_id" || key0 === "label" || key0 === "scientific_summary")) {
            validate346.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate346.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.parent_id !== void 0) {
              let data1 = data.parent_id;
              const _errs4 = errors;
              const _errs5 = errors;
              let valid1 = false;
              const _errs6 = errors;
              if (typeof data1 !== "string") {
                const err0 = { instancePath: instancePath + "/parent_id", schemaPath: "#/properties/parent_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                const err1 = { instancePath: instancePath + "/parent_id", schemaPath: "#/properties/parent_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                const err2 = { instancePath: instancePath + "/parent_id", schemaPath: "#/properties/parent_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                if (vErrors === null) {
                  vErrors = [err2];
                } else {
                  vErrors.push(err2);
                }
                errors++;
                validate346.errors = vErrors;
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
              if (data.status !== void 0) {
                const _errs10 = errors;
                if (typeof data.status !== "string") {
                  validate346.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs10 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.attempts !== void 0) {
                  let data3 = data.attempts;
                  const _errs12 = errors;
                  if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)))) {
                    validate346.errors = [{ instancePath: instancePath + "/attempts", schemaPath: "#/properties/attempts/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  var valid0 = _errs12 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.tool_id !== void 0) {
                    let data4 = data.tool_id;
                    const _errs14 = errors;
                    const _errs15 = errors;
                    let valid2 = false;
                    const _errs16 = errors;
                    if (typeof data4 !== "string") {
                      const err3 = { instancePath: instancePath + "/tool_id", schemaPath: "#/properties/tool_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                      const err4 = { instancePath: instancePath + "/tool_id", schemaPath: "#/properties/tool_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                      const err5 = { instancePath: instancePath + "/tool_id", schemaPath: "#/properties/tool_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err5];
                      } else {
                        vErrors.push(err5);
                      }
                      errors++;
                      validate346.errors = vErrors;
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
                    if (data.label !== void 0) {
                      const _errs20 = errors;
                      if (typeof data.label !== "string") {
                        validate346.errors = [{ instancePath: instancePath + "/label", schemaPath: "#/properties/label/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.scientific_summary !== void 0) {
                        let data6 = data.scientific_summary;
                        const _errs22 = errors;
                        const _errs23 = errors;
                        let valid3 = false;
                        const _errs24 = errors;
                        if (!validate347(data6, { instancePath: instancePath + "/scientific_summary", parentData: data, parentDataProperty: "scientific_summary", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate347.errors : vErrors.concat(validate347.errors);
                          errors = vErrors.length;
                        }
                        var _valid2 = _errs24 === errors;
                        valid3 = valid3 || _valid2;
                        const _errs25 = errors;
                        if (data6 !== null) {
                          const err6 = { instancePath: instancePath + "/scientific_summary", schemaPath: "#/properties/scientific_summary/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err6];
                          } else {
                            vErrors.push(err6);
                          }
                          errors++;
                        }
                        var _valid2 = _errs25 === errors;
                        valid3 = valid3 || _valid2;
                        if (!valid3) {
                          const err7 = { instancePath: instancePath + "/scientific_summary", schemaPath: "#/properties/scientific_summary/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err7];
                          } else {
                            vErrors.push(err7);
                          }
                          errors++;
                          validate346.errors = vErrors;
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
                    }
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate346.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate346.errors = vErrors;
  return errors === 0;
}
validate346.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate350(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate350.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.run_id === void 0 && (missing0 = "run_id") || data.node_id === void 0 && (missing0 = "node_id") || data.hash === void 0 && (missing0 = "hash") || data.name === void 0 && (missing0 = "name") || data.upstream === void 0 && (missing0 = "upstream") || data.metadata === void 0 && (missing0 = "metadata")) {
        validate350.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "run_id" || key0 === "node_id" || key0 === "hash" || key0 === "name" || key0 === "upstream" || key0 === "metadata")) {
            validate350.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate350.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.run_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.run_id !== "string") {
                validate350.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.node_id !== void 0) {
                const _errs6 = errors;
                if (typeof data.node_id !== "string") {
                  validate350.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.hash !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.hash !== "string") {
                    validate350.errors = [{ instancePath: instancePath + "/hash", schemaPath: "#/properties/hash/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.name !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.name !== "string") {
                      validate350.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.upstream !== void 0) {
                      let data5 = data.upstream;
                      const _errs12 = errors;
                      if (errors === _errs12) {
                        if (Array.isArray(data5)) {
                          var valid1 = true;
                          const len0 = data5.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs14 = errors;
                            if (typeof data5[i0] !== "string") {
                              validate350.errors = [{ instancePath: instancePath + "/upstream/" + i0, schemaPath: "#/properties/upstream/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid1 = _errs14 === errors;
                            if (!valid1) {
                              break;
                            }
                          }
                        } else {
                          validate350.errors = [{ instancePath: instancePath + "/upstream", schemaPath: "#/properties/upstream/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.metadata !== void 0) {
                        let data7 = data.metadata;
                        const _errs16 = errors;
                        if (errors === _errs16) {
                          if (data7 && typeof data7 == "object" && !Array.isArray(data7)) {
                          } else {
                            validate350.errors = [{ instancePath: instancePath + "/metadata", schemaPath: "#/properties/metadata/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                            return false;
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
      }
    } else {
      validate350.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate350.errors = vErrors;
  return errors === 0;
}
validate350.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate341(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate341.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.name === void 0 && (missing0 = "name") || data.project_id === void 0 && (missing0 = "project_id") || data.status === void 0 && (missing0 = "status") || data.snapshot_hash === void 0 && (missing0 = "snapshot_hash") || data.created_at === void 0 && (missing0 = "created_at") || data.updated_at === void 0 && (missing0 = "updated_at") || data.control === void 0 && (missing0 = "control") || data.heartbeat === void 0 && (missing0 = "heartbeat") || data.state_version === void 0 && (missing0 = "state_version") || data.event_cursor === void 0 && (missing0 = "event_cursor") || data.project_revision === void 0 && (missing0 = "project_revision") || data.workflow === void 0 && (missing0 = "workflow") || data.tools === void 0 && (missing0 = "tools") || data.nodes === void 0 && (missing0 = "nodes") || data.artifacts === void 0 && (missing0 = "artifacts") || data.scientific_assessment === void 0 && (missing0 = "scientific_assessment")) {
        validate341.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema149.properties, key0)) {
            validate341.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate341.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate341.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.project_id !== void 0) {
                const _errs6 = errors;
                if (typeof data.project_id !== "string") {
                  validate341.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.status !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.status !== "string") {
                    validate341.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.snapshot_hash !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.snapshot_hash !== "string") {
                      validate341.errors = [{ instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.created_at !== void 0) {
                      const _errs12 = errors;
                      if (typeof data.created_at !== "string") {
                        validate341.errors = [{ instancePath: instancePath + "/created_at", schemaPath: "#/properties/created_at/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.updated_at !== void 0) {
                        const _errs14 = errors;
                        if (typeof data.updated_at !== "string") {
                          validate341.errors = [{ instancePath: instancePath + "/updated_at", schemaPath: "#/properties/updated_at/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.control !== void 0) {
                          let data7 = data.control;
                          const _errs16 = errors;
                          const _errs17 = errors;
                          let valid1 = false;
                          const _errs18 = errors;
                          if (typeof data7 !== "string") {
                            const err0 = { instancePath: instancePath + "/control", schemaPath: "#/properties/control/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err0];
                            } else {
                              vErrors.push(err0);
                            }
                            errors++;
                          }
                          var _valid0 = _errs18 === errors;
                          valid1 = valid1 || _valid0;
                          const _errs20 = errors;
                          if (data7 !== null) {
                            const err1 = { instancePath: instancePath + "/control", schemaPath: "#/properties/control/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err1];
                            } else {
                              vErrors.push(err1);
                            }
                            errors++;
                          }
                          var _valid0 = _errs20 === errors;
                          valid1 = valid1 || _valid0;
                          if (!valid1) {
                            const err2 = { instancePath: instancePath + "/control", schemaPath: "#/properties/control/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err2];
                            } else {
                              vErrors.push(err2);
                            }
                            errors++;
                            validate341.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs17;
                            if (vErrors !== null) {
                              if (_errs17) {
                                vErrors.length = _errs17;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.heartbeat !== void 0) {
                            let data8 = data.heartbeat;
                            const _errs22 = errors;
                            const _errs23 = errors;
                            let valid2 = false;
                            const _errs24 = errors;
                            if (typeof data8 !== "string") {
                              const err3 = { instancePath: instancePath + "/heartbeat", schemaPath: "#/properties/heartbeat/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err3];
                              } else {
                                vErrors.push(err3);
                              }
                              errors++;
                            }
                            var _valid1 = _errs24 === errors;
                            valid2 = valid2 || _valid1;
                            const _errs26 = errors;
                            if (data8 !== null) {
                              const err4 = { instancePath: instancePath + "/heartbeat", schemaPath: "#/properties/heartbeat/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err4];
                              } else {
                                vErrors.push(err4);
                              }
                              errors++;
                            }
                            var _valid1 = _errs26 === errors;
                            valid2 = valid2 || _valid1;
                            if (!valid2) {
                              const err5 = { instancePath: instancePath + "/heartbeat", schemaPath: "#/properties/heartbeat/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err5];
                              } else {
                                vErrors.push(err5);
                              }
                              errors++;
                              validate341.errors = vErrors;
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
                            if (data.state_version !== void 0) {
                              let data9 = data.state_version;
                              const _errs28 = errors;
                              if (!(typeof data9 == "number" && (!(data9 % 1) && !isNaN(data9)))) {
                                validate341.errors = [{ instancePath: instancePath + "/state_version", schemaPath: "#/properties/state_version/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              var valid0 = _errs28 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.event_cursor !== void 0) {
                                let data10 = data.event_cursor;
                                const _errs30 = errors;
                                if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)))) {
                                  validate341.errors = [{ instancePath: instancePath + "/event_cursor", schemaPath: "#/properties/event_cursor/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                var valid0 = _errs30 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.project_revision !== void 0) {
                                  let data11 = data.project_revision;
                                  const _errs32 = errors;
                                  if (!(typeof data11 == "number" && (!(data11 % 1) && !isNaN(data11)))) {
                                    validate341.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                    return false;
                                  }
                                  var valid0 = _errs32 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.workflow !== void 0) {
                                    const _errs34 = errors;
                                    if (!validate342(data.workflow, { instancePath: instancePath + "/workflow", parentData: data, parentDataProperty: "workflow", rootData, dynamicAnchors })) {
                                      vErrors = vErrors === null ? validate342.errors : vErrors.concat(validate342.errors);
                                      errors = vErrors.length;
                                    }
                                    var valid0 = _errs34 === errors;
                                  } else {
                                    var valid0 = true;
                                  }
                                  if (valid0) {
                                    if (data.tools !== void 0) {
                                      let data13 = data.tools;
                                      const _errs35 = errors;
                                      if (errors === _errs35) {
                                        if (data13 && typeof data13 == "object" && !Array.isArray(data13)) {
                                        } else {
                                          validate341.errors = [{ instancePath: instancePath + "/tools", schemaPath: "#/properties/tools/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                          return false;
                                        }
                                      }
                                      var valid0 = _errs35 === errors;
                                    } else {
                                      var valid0 = true;
                                    }
                                    if (valid0) {
                                      if (data.nodes !== void 0) {
                                        let data14 = data.nodes;
                                        const _errs38 = errors;
                                        if (errors === _errs38) {
                                          if (Array.isArray(data14)) {
                                            var valid3 = true;
                                            const len0 = data14.length;
                                            for (let i0 = 0; i0 < len0; i0++) {
                                              const _errs40 = errors;
                                              if (!validate346(data14[i0], { instancePath: instancePath + "/nodes/" + i0, parentData: data14, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                                vErrors = vErrors === null ? validate346.errors : vErrors.concat(validate346.errors);
                                                errors = vErrors.length;
                                              }
                                              var valid3 = _errs40 === errors;
                                              if (!valid3) {
                                                break;
                                              }
                                            }
                                          } else {
                                            validate341.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                            return false;
                                          }
                                        }
                                        var valid0 = _errs38 === errors;
                                      } else {
                                        var valid0 = true;
                                      }
                                      if (valid0) {
                                        if (data.artifacts !== void 0) {
                                          let data16 = data.artifacts;
                                          const _errs41 = errors;
                                          if (errors === _errs41) {
                                            if (Array.isArray(data16)) {
                                              var valid4 = true;
                                              const len1 = data16.length;
                                              for (let i1 = 0; i1 < len1; i1++) {
                                                const _errs43 = errors;
                                                if (!validate350(data16[i1], { instancePath: instancePath + "/artifacts/" + i1, parentData: data16, parentDataProperty: i1, rootData, dynamicAnchors })) {
                                                  vErrors = vErrors === null ? validate350.errors : vErrors.concat(validate350.errors);
                                                  errors = vErrors.length;
                                                }
                                                var valid4 = _errs43 === errors;
                                                if (!valid4) {
                                                  break;
                                                }
                                              }
                                            } else {
                                              validate341.errors = [{ instancePath: instancePath + "/artifacts", schemaPath: "#/properties/artifacts/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                              return false;
                                            }
                                          }
                                          var valid0 = _errs41 === errors;
                                        } else {
                                          var valid0 = true;
                                        }
                                        if (valid0) {
                                          if (data.scientific_assessment !== void 0) {
                                            let data18 = data.scientific_assessment;
                                            const _errs44 = errors;
                                            if (errors === _errs44) {
                                              if (data18 && typeof data18 == "object" && !Array.isArray(data18)) {
                                                for (const key1 in data18) {
                                                  const _errs47 = errors;
                                                  if (typeof data18[key1] !== "string") {
                                                    validate341.errors = [{ instancePath: instancePath + "/scientific_assessment/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/scientific_assessment/additionalProperties/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                    return false;
                                                  }
                                                  var valid5 = _errs47 === errors;
                                                  if (!valid5) {
                                                    break;
                                                  }
                                                }
                                              } else {
                                                validate341.errors = [{ instancePath: instancePath + "/scientific_assessment", schemaPath: "#/properties/scientific_assessment/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                                return false;
                                              }
                                            }
                                            var valid0 = _errs44 === errors;
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
      validate341.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate341.errors = vErrors;
  return errors === 0;
}
validate341.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var RunListView = validate352;
function validate352(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate352.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.project_id === void 0 && (missing0 = "project_id") || data.status === void 0 && (missing0 = "status") || data.snapshot_hash === void 0 && (missing0 = "snapshot_hash") || data.created_at === void 0 && (missing0 = "created_at") || data.updated_at === void 0 && (missing0 = "updated_at") || data.name === void 0 && (missing0 = "name") || data.project_revision === void 0 && (missing0 = "project_revision")) {
        validate352.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "project_id" || key0 === "status" || key0 === "snapshot_hash" || key0 === "created_at" || key0 === "updated_at" || key0 === "name" || key0 === "project_revision")) {
            validate352.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate352.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate352.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.status !== void 0) {
                const _errs6 = errors;
                if (typeof data.status !== "string") {
                  validate352.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.snapshot_hash !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.snapshot_hash !== "string") {
                    validate352.errors = [{ instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.created_at !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.created_at !== "string") {
                      validate352.errors = [{ instancePath: instancePath + "/created_at", schemaPath: "#/properties/created_at/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.updated_at !== void 0) {
                      const _errs12 = errors;
                      if (typeof data.updated_at !== "string") {
                        validate352.errors = [{ instancePath: instancePath + "/updated_at", schemaPath: "#/properties/updated_at/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.name !== void 0) {
                        const _errs14 = errors;
                        if (typeof data.name !== "string") {
                          validate352.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.project_revision !== void 0) {
                          let data7 = data.project_revision;
                          const _errs16 = errors;
                          if (!(typeof data7 == "number" && (!(data7 % 1) && !isNaN(data7)))) {
                            validate352.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
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
        }
      }
    } else {
      validate352.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate352.errors = vErrors;
  return errors === 0;
}
validate352.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var EventPage = validate353;
function validate354(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate354.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.seq === void 0 && (missing0 = "seq") || data.node_id === void 0 && (missing0 = "node_id") || data.event === void 0 && (missing0 = "event") || data.timestamp === void 0 && (missing0 = "timestamp") || data.payload === void 0 && (missing0 = "payload")) {
        validate354.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "seq" || key0 === "node_id" || key0 === "event" || key0 === "timestamp" || key0 === "payload")) {
            validate354.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.seq !== void 0) {
            let data0 = data.seq;
            const _errs2 = errors;
            if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)))) {
              validate354.errors = [{ instancePath: instancePath + "/seq", schemaPath: "#/properties/seq/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.node_id !== void 0) {
              let data1 = data.node_id;
              const _errs4 = errors;
              const _errs5 = errors;
              let valid1 = false;
              const _errs6 = errors;
              if (typeof data1 !== "string") {
                const err0 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                const err1 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                const err2 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                if (vErrors === null) {
                  vErrors = [err2];
                } else {
                  vErrors.push(err2);
                }
                errors++;
                validate354.errors = vErrors;
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
              if (data.event !== void 0) {
                const _errs10 = errors;
                if (typeof data.event !== "string") {
                  validate354.errors = [{ instancePath: instancePath + "/event", schemaPath: "#/properties/event/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate354.errors = [{ instancePath: instancePath + "/timestamp", schemaPath: "#/properties/timestamp/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs12 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.payload !== void 0) {
                    let data4 = data.payload;
                    const _errs14 = errors;
                    if (errors === _errs14) {
                      if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                      } else {
                        validate354.errors = [{ instancePath: instancePath + "/payload", schemaPath: "#/properties/payload/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs14 === errors;
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
      validate354.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate354.errors = vErrors;
  return errors === 0;
}
validate354.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate353(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate353.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.items === void 0 && (missing0 = "items") || data.cursor === void 0 && (missing0 = "cursor") || data.has_more === void 0 && (missing0 = "has_more")) {
        validate353.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "items" || key0 === "cursor" || key0 === "has_more")) {
            validate353.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.items !== void 0) {
            let data0 = data.items;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (Array.isArray(data0)) {
                var valid1 = true;
                const len0 = data0.length;
                for (let i0 = 0; i0 < len0; i0++) {
                  const _errs4 = errors;
                  if (!validate354(data0[i0], { instancePath: instancePath + "/items/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate354.errors : vErrors.concat(validate354.errors);
                    errors = vErrors.length;
                  }
                  var valid1 = _errs4 === errors;
                  if (!valid1) {
                    break;
                  }
                }
              } else {
                validate353.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.cursor !== void 0) {
              let data2 = data.cursor;
              const _errs5 = errors;
              if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                validate353.errors = [{ instancePath: instancePath + "/cursor", schemaPath: "#/properties/cursor/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                return false;
              }
              var valid0 = _errs5 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.has_more !== void 0) {
                const _errs7 = errors;
                if (typeof data.has_more !== "boolean") {
                  validate353.errors = [{ instancePath: instancePath + "/has_more", schemaPath: "#/properties/has_more/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
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
      validate353.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate353.errors = vErrors;
  return errors === 0;
}
validate353.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var TablePage = validate356;
var schema158 = { "additionalProperties": false, "properties": { "project_id": { "title": "Project Id", "type": "string" }, "file_id": { "title": "File Id", "type": "string" }, "source_sha256": { "title": "Source Sha256", "type": "string" }, "run_id": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Run Id" }, "snapshot_hash": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Snapshot Hash" }, "node_id": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Node Id" }, "attempt": { "anyOf": [{ "type": "integer" }, { "type": "null" }], "default": null, "title": "Attempt" }, "candidate_id": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Candidate Id" }, "construct_id": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Construct Id" }, "condition_id": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Condition Id" } }, "required": ["project_id", "file_id", "source_sha256", "run_id", "snapshot_hash", "node_id", "attempt", "candidate_id", "construct_id", "condition_id"], "title": "ResourceIdentity", "type": "object" };
function validate357(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate357.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.file_id === void 0 && (missing0 = "file_id") || data.source_sha256 === void 0 && (missing0 = "source_sha256") || data.run_id === void 0 && (missing0 = "run_id") || data.snapshot_hash === void 0 && (missing0 = "snapshot_hash") || data.node_id === void 0 && (missing0 = "node_id") || data.attempt === void 0 && (missing0 = "attempt") || data.candidate_id === void 0 && (missing0 = "candidate_id") || data.construct_id === void 0 && (missing0 = "construct_id") || data.condition_id === void 0 && (missing0 = "condition_id")) {
        validate357.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema158.properties, key0)) {
            validate357.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate357.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.file_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.file_id !== "string") {
                validate357.errors = [{ instancePath: instancePath + "/file_id", schemaPath: "#/properties/file_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.source_sha256 !== void 0) {
                const _errs6 = errors;
                if (typeof data.source_sha256 !== "string") {
                  validate357.errors = [{ instancePath: instancePath + "/source_sha256", schemaPath: "#/properties/source_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  let data3 = data.run_id;
                  const _errs8 = errors;
                  const _errs9 = errors;
                  let valid1 = false;
                  const _errs10 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                    const err1 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err2 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate357.errors = vErrors;
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
                  if (data.snapshot_hash !== void 0) {
                    let data4 = data.snapshot_hash;
                    const _errs14 = errors;
                    const _errs15 = errors;
                    let valid2 = false;
                    const _errs16 = errors;
                    if (typeof data4 !== "string") {
                      const err3 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                      const err4 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                      const err5 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err5];
                      } else {
                        vErrors.push(err5);
                      }
                      errors++;
                      validate357.errors = vErrors;
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
                    if (data.node_id !== void 0) {
                      let data5 = data.node_id;
                      const _errs20 = errors;
                      const _errs21 = errors;
                      let valid3 = false;
                      const _errs22 = errors;
                      if (typeof data5 !== "string") {
                        const err6 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err6];
                        } else {
                          vErrors.push(err6);
                        }
                        errors++;
                      }
                      var _valid2 = _errs22 === errors;
                      valid3 = valid3 || _valid2;
                      const _errs24 = errors;
                      if (data5 !== null) {
                        const err7 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err7];
                        } else {
                          vErrors.push(err7);
                        }
                        errors++;
                      }
                      var _valid2 = _errs24 === errors;
                      valid3 = valid3 || _valid2;
                      if (!valid3) {
                        const err8 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err8];
                        } else {
                          vErrors.push(err8);
                        }
                        errors++;
                        validate357.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs21;
                        if (vErrors !== null) {
                          if (_errs21) {
                            vErrors.length = _errs21;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.attempt !== void 0) {
                        let data6 = data.attempt;
                        const _errs26 = errors;
                        const _errs27 = errors;
                        let valid4 = false;
                        const _errs28 = errors;
                        if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)))) {
                          const err9 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                          if (vErrors === null) {
                            vErrors = [err9];
                          } else {
                            vErrors.push(err9);
                          }
                          errors++;
                        }
                        var _valid3 = _errs28 === errors;
                        valid4 = valid4 || _valid3;
                        const _errs30 = errors;
                        if (data6 !== null) {
                          const err10 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err10];
                          } else {
                            vErrors.push(err10);
                          }
                          errors++;
                        }
                        var _valid3 = _errs30 === errors;
                        valid4 = valid4 || _valid3;
                        if (!valid4) {
                          const err11 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err11];
                          } else {
                            vErrors.push(err11);
                          }
                          errors++;
                          validate357.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs27;
                          if (vErrors !== null) {
                            if (_errs27) {
                              vErrors.length = _errs27;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs26 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.candidate_id !== void 0) {
                          let data7 = data.candidate_id;
                          const _errs32 = errors;
                          const _errs33 = errors;
                          let valid5 = false;
                          const _errs34 = errors;
                          if (typeof data7 !== "string") {
                            const err12 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err12];
                            } else {
                              vErrors.push(err12);
                            }
                            errors++;
                          }
                          var _valid4 = _errs34 === errors;
                          valid5 = valid5 || _valid4;
                          const _errs36 = errors;
                          if (data7 !== null) {
                            const err13 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err13];
                            } else {
                              vErrors.push(err13);
                            }
                            errors++;
                          }
                          var _valid4 = _errs36 === errors;
                          valid5 = valid5 || _valid4;
                          if (!valid5) {
                            const err14 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err14];
                            } else {
                              vErrors.push(err14);
                            }
                            errors++;
                            validate357.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs33;
                            if (vErrors !== null) {
                              if (_errs33) {
                                vErrors.length = _errs33;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs32 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.construct_id !== void 0) {
                            let data8 = data.construct_id;
                            const _errs38 = errors;
                            const _errs39 = errors;
                            let valid6 = false;
                            const _errs40 = errors;
                            if (typeof data8 !== "string") {
                              const err15 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err15];
                              } else {
                                vErrors.push(err15);
                              }
                              errors++;
                            }
                            var _valid5 = _errs40 === errors;
                            valid6 = valid6 || _valid5;
                            const _errs42 = errors;
                            if (data8 !== null) {
                              const err16 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err16];
                              } else {
                                vErrors.push(err16);
                              }
                              errors++;
                            }
                            var _valid5 = _errs42 === errors;
                            valid6 = valid6 || _valid5;
                            if (!valid6) {
                              const err17 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err17];
                              } else {
                                vErrors.push(err17);
                              }
                              errors++;
                              validate357.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs39;
                              if (vErrors !== null) {
                                if (_errs39) {
                                  vErrors.length = _errs39;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs38 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.condition_id !== void 0) {
                              let data9 = data.condition_id;
                              const _errs44 = errors;
                              const _errs45 = errors;
                              let valid7 = false;
                              const _errs46 = errors;
                              if (typeof data9 !== "string") {
                                const err18 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err18];
                                } else {
                                  vErrors.push(err18);
                                }
                                errors++;
                              }
                              var _valid6 = _errs46 === errors;
                              valid7 = valid7 || _valid6;
                              const _errs48 = errors;
                              if (data9 !== null) {
                                const err19 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                if (vErrors === null) {
                                  vErrors = [err19];
                                } else {
                                  vErrors.push(err19);
                                }
                                errors++;
                              }
                              var _valid6 = _errs48 === errors;
                              valid7 = valid7 || _valid6;
                              if (!valid7) {
                                const err20 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                if (vErrors === null) {
                                  vErrors = [err20];
                                } else {
                                  vErrors.push(err20);
                                }
                                errors++;
                                validate357.errors = vErrors;
                                return false;
                              } else {
                                errors = _errs45;
                                if (vErrors !== null) {
                                  if (_errs45) {
                                    vErrors.length = _errs45;
                                  } else {
                                    vErrors = null;
                                  }
                                }
                              }
                              var valid0 = _errs44 === errors;
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
      validate357.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate357.errors = vErrors;
  return errors === 0;
}
validate357.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate356(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate356.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.schema_version === void 0 && (missing0 = "schema_version") || data.identity === void 0 && (missing0 = "identity") || data.offset === void 0 && (missing0 = "offset") || data.total === void 0 && (missing0 = "total") || data.has_more === void 0 && (missing0 = "has_more") || data.columns === void 0 && (missing0 = "columns") || data.rows === void 0 && (missing0 = "rows") || data.text === void 0 && (missing0 = "text")) {
        validate356.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "schema_version" || key0 === "identity" || key0 === "offset" || key0 === "total" || key0 === "has_more" || key0 === "columns" || key0 === "rows" || key0 === "text")) {
            validate356.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.schema_version !== void 0) {
            let data0 = data.schema_version;
            const _errs2 = errors;
            if (typeof data0 !== "string") {
              validate356.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            if ("display-table-v1" !== data0) {
              validate356.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "display-table-v1" }, message: "must be equal to constant" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.identity !== void 0) {
              const _errs4 = errors;
              if (!validate357(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
                vErrors = vErrors === null ? validate357.errors : vErrors.concat(validate357.errors);
                errors = vErrors.length;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.offset !== void 0) {
                let data2 = data.offset;
                const _errs5 = errors;
                if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                  validate356.errors = [{ instancePath: instancePath + "/offset", schemaPath: "#/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs5 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.total !== void 0) {
                  let data3 = data.total;
                  const _errs7 = errors;
                  if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)))) {
                    validate356.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.has_more !== void 0) {
                    const _errs9 = errors;
                    if (typeof data.has_more !== "boolean") {
                      validate356.errors = [{ instancePath: instancePath + "/has_more", schemaPath: "#/properties/has_more/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                      return false;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.columns !== void 0) {
                      let data5 = data.columns;
                      const _errs11 = errors;
                      if (errors === _errs11) {
                        if (Array.isArray(data5)) {
                          var valid1 = true;
                          const len0 = data5.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs13 = errors;
                            if (typeof data5[i0] !== "string") {
                              validate356.errors = [{ instancePath: instancePath + "/columns/" + i0, schemaPath: "#/properties/columns/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid1 = _errs13 === errors;
                            if (!valid1) {
                              break;
                            }
                          }
                        } else {
                          validate356.errors = [{ instancePath: instancePath + "/columns", schemaPath: "#/properties/columns/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs11 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.rows !== void 0) {
                        let data7 = data.rows;
                        const _errs15 = errors;
                        if (errors === _errs15) {
                          if (Array.isArray(data7)) {
                            var valid2 = true;
                            const len1 = data7.length;
                            for (let i1 = 0; i1 < len1; i1++) {
                              let data8 = data7[i1];
                              const _errs17 = errors;
                              if (errors === _errs17) {
                                if (Array.isArray(data8)) {
                                  var valid3 = true;
                                  const len2 = data8.length;
                                  for (let i2 = 0; i2 < len2; i2++) {
                                    let data9 = data8[i2];
                                    const _errs19 = errors;
                                    const _errs20 = errors;
                                    let valid4 = false;
                                    const _errs21 = errors;
                                    if (typeof data9 !== "string") {
                                      const err0 = { instancePath: instancePath + "/rows/" + i1 + "/" + i2, schemaPath: "#/properties/rows/items/items/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err0];
                                      } else {
                                        vErrors.push(err0);
                                      }
                                      errors++;
                                    }
                                    var _valid0 = _errs21 === errors;
                                    valid4 = valid4 || _valid0;
                                    const _errs23 = errors;
                                    if (data9 !== null) {
                                      const err1 = { instancePath: instancePath + "/rows/" + i1 + "/" + i2, schemaPath: "#/properties/rows/items/items/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                      if (vErrors === null) {
                                        vErrors = [err1];
                                      } else {
                                        vErrors.push(err1);
                                      }
                                      errors++;
                                    }
                                    var _valid0 = _errs23 === errors;
                                    valid4 = valid4 || _valid0;
                                    if (!valid4) {
                                      const err2 = { instancePath: instancePath + "/rows/" + i1 + "/" + i2, schemaPath: "#/properties/rows/items/items/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                      if (vErrors === null) {
                                        vErrors = [err2];
                                      } else {
                                        vErrors.push(err2);
                                      }
                                      errors++;
                                      validate356.errors = vErrors;
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
                                    var valid3 = _errs19 === errors;
                                    if (!valid3) {
                                      break;
                                    }
                                  }
                                } else {
                                  validate356.errors = [{ instancePath: instancePath + "/rows/" + i1, schemaPath: "#/properties/rows/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs17 === errors;
                              if (!valid2) {
                                break;
                              }
                            }
                          } else {
                            validate356.errors = [{ instancePath: instancePath + "/rows", schemaPath: "#/properties/rows/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs15 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.text !== void 0) {
                          let data10 = data.text;
                          const _errs25 = errors;
                          const _errs26 = errors;
                          let valid5 = false;
                          const _errs27 = errors;
                          if (typeof data10 !== "string") {
                            const err3 = { instancePath: instancePath + "/text", schemaPath: "#/properties/text/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err3];
                            } else {
                              vErrors.push(err3);
                            }
                            errors++;
                          }
                          var _valid1 = _errs27 === errors;
                          valid5 = valid5 || _valid1;
                          const _errs29 = errors;
                          if (data10 !== null) {
                            const err4 = { instancePath: instancePath + "/text", schemaPath: "#/properties/text/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err4];
                            } else {
                              vErrors.push(err4);
                            }
                            errors++;
                          }
                          var _valid1 = _errs29 === errors;
                          valid5 = valid5 || _valid1;
                          if (!valid5) {
                            const err5 = { instancePath: instancePath + "/text", schemaPath: "#/properties/text/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err5];
                            } else {
                              vErrors.push(err5);
                            }
                            errors++;
                            validate356.errors = vErrors;
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
      validate356.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate356.errors = vErrors;
  return errors === 0;
}
validate356.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var ScanPage = validate359;
var schema159 = { "additionalProperties": false, "properties": { "schema_version": { "const": "display-finite-scan-v1", "type": "string" }, "identity": { "$ref": "urn:fusionlab:shared#/$defs/ResourceIdentity" }, "offset": { "type": "integer" }, "total": { "type": "integer" }, "has_more": { "type": "boolean" }, "decision_id": { "type": "string" }, "decision_scope": { "type": "string" }, "objective": { "type": "string" }, "metric_definition": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "metric_unit": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "comparison_contract": { "anyOf": [{ "additionalProperties": true, "type": "object" }, { "type": "null" }] }, "points": { "items": { "$ref": "urn:fusionlab:shared#/$defs/ScanPoint" }, "type": "array" }, "ranking_performed": { "const": false, "type": "boolean" }, "claim_scope": { "const": "source_reported_scan_not_execution_or_parameter_approval", "type": "string" } }, "required": ["schema_version", "identity", "offset", "total", "has_more", "decision_id", "decision_scope", "objective", "metric_definition", "metric_unit", "comparison_contract", "points", "ranking_performed", "claim_scope"], "type": "object" };
function validate360(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate360.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.file_id === void 0 && (missing0 = "file_id") || data.source_sha256 === void 0 && (missing0 = "source_sha256") || data.run_id === void 0 && (missing0 = "run_id") || data.snapshot_hash === void 0 && (missing0 = "snapshot_hash") || data.node_id === void 0 && (missing0 = "node_id") || data.attempt === void 0 && (missing0 = "attempt") || data.candidate_id === void 0 && (missing0 = "candidate_id") || data.construct_id === void 0 && (missing0 = "construct_id") || data.condition_id === void 0 && (missing0 = "condition_id")) {
        validate360.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema158.properties, key0)) {
            validate360.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate360.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.file_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.file_id !== "string") {
                validate360.errors = [{ instancePath: instancePath + "/file_id", schemaPath: "#/properties/file_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.source_sha256 !== void 0) {
                const _errs6 = errors;
                if (typeof data.source_sha256 !== "string") {
                  validate360.errors = [{ instancePath: instancePath + "/source_sha256", schemaPath: "#/properties/source_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  let data3 = data.run_id;
                  const _errs8 = errors;
                  const _errs9 = errors;
                  let valid1 = false;
                  const _errs10 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                    const err1 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err2 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate360.errors = vErrors;
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
                  if (data.snapshot_hash !== void 0) {
                    let data4 = data.snapshot_hash;
                    const _errs14 = errors;
                    const _errs15 = errors;
                    let valid2 = false;
                    const _errs16 = errors;
                    if (typeof data4 !== "string") {
                      const err3 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                      const err4 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                      const err5 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err5];
                      } else {
                        vErrors.push(err5);
                      }
                      errors++;
                      validate360.errors = vErrors;
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
                    if (data.node_id !== void 0) {
                      let data5 = data.node_id;
                      const _errs20 = errors;
                      const _errs21 = errors;
                      let valid3 = false;
                      const _errs22 = errors;
                      if (typeof data5 !== "string") {
                        const err6 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err6];
                        } else {
                          vErrors.push(err6);
                        }
                        errors++;
                      }
                      var _valid2 = _errs22 === errors;
                      valid3 = valid3 || _valid2;
                      const _errs24 = errors;
                      if (data5 !== null) {
                        const err7 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err7];
                        } else {
                          vErrors.push(err7);
                        }
                        errors++;
                      }
                      var _valid2 = _errs24 === errors;
                      valid3 = valid3 || _valid2;
                      if (!valid3) {
                        const err8 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err8];
                        } else {
                          vErrors.push(err8);
                        }
                        errors++;
                        validate360.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs21;
                        if (vErrors !== null) {
                          if (_errs21) {
                            vErrors.length = _errs21;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.attempt !== void 0) {
                        let data6 = data.attempt;
                        const _errs26 = errors;
                        const _errs27 = errors;
                        let valid4 = false;
                        const _errs28 = errors;
                        if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)))) {
                          const err9 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                          if (vErrors === null) {
                            vErrors = [err9];
                          } else {
                            vErrors.push(err9);
                          }
                          errors++;
                        }
                        var _valid3 = _errs28 === errors;
                        valid4 = valid4 || _valid3;
                        const _errs30 = errors;
                        if (data6 !== null) {
                          const err10 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err10];
                          } else {
                            vErrors.push(err10);
                          }
                          errors++;
                        }
                        var _valid3 = _errs30 === errors;
                        valid4 = valid4 || _valid3;
                        if (!valid4) {
                          const err11 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err11];
                          } else {
                            vErrors.push(err11);
                          }
                          errors++;
                          validate360.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs27;
                          if (vErrors !== null) {
                            if (_errs27) {
                              vErrors.length = _errs27;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs26 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.candidate_id !== void 0) {
                          let data7 = data.candidate_id;
                          const _errs32 = errors;
                          const _errs33 = errors;
                          let valid5 = false;
                          const _errs34 = errors;
                          if (typeof data7 !== "string") {
                            const err12 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err12];
                            } else {
                              vErrors.push(err12);
                            }
                            errors++;
                          }
                          var _valid4 = _errs34 === errors;
                          valid5 = valid5 || _valid4;
                          const _errs36 = errors;
                          if (data7 !== null) {
                            const err13 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err13];
                            } else {
                              vErrors.push(err13);
                            }
                            errors++;
                          }
                          var _valid4 = _errs36 === errors;
                          valid5 = valid5 || _valid4;
                          if (!valid5) {
                            const err14 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err14];
                            } else {
                              vErrors.push(err14);
                            }
                            errors++;
                            validate360.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs33;
                            if (vErrors !== null) {
                              if (_errs33) {
                                vErrors.length = _errs33;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs32 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.construct_id !== void 0) {
                            let data8 = data.construct_id;
                            const _errs38 = errors;
                            const _errs39 = errors;
                            let valid6 = false;
                            const _errs40 = errors;
                            if (typeof data8 !== "string") {
                              const err15 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err15];
                              } else {
                                vErrors.push(err15);
                              }
                              errors++;
                            }
                            var _valid5 = _errs40 === errors;
                            valid6 = valid6 || _valid5;
                            const _errs42 = errors;
                            if (data8 !== null) {
                              const err16 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err16];
                              } else {
                                vErrors.push(err16);
                              }
                              errors++;
                            }
                            var _valid5 = _errs42 === errors;
                            valid6 = valid6 || _valid5;
                            if (!valid6) {
                              const err17 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err17];
                              } else {
                                vErrors.push(err17);
                              }
                              errors++;
                              validate360.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs39;
                              if (vErrors !== null) {
                                if (_errs39) {
                                  vErrors.length = _errs39;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs38 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.condition_id !== void 0) {
                              let data9 = data.condition_id;
                              const _errs44 = errors;
                              const _errs45 = errors;
                              let valid7 = false;
                              const _errs46 = errors;
                              if (typeof data9 !== "string") {
                                const err18 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err18];
                                } else {
                                  vErrors.push(err18);
                                }
                                errors++;
                              }
                              var _valid6 = _errs46 === errors;
                              valid7 = valid7 || _valid6;
                              const _errs48 = errors;
                              if (data9 !== null) {
                                const err19 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                if (vErrors === null) {
                                  vErrors = [err19];
                                } else {
                                  vErrors.push(err19);
                                }
                                errors++;
                              }
                              var _valid6 = _errs48 === errors;
                              valid7 = valid7 || _valid6;
                              if (!valid7) {
                                const err20 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                if (vErrors === null) {
                                  vErrors = [err20];
                                } else {
                                  vErrors.push(err20);
                                }
                                errors++;
                                validate360.errors = vErrors;
                                return false;
                              } else {
                                errors = _errs45;
                                if (vErrors !== null) {
                                  if (_errs45) {
                                    vErrors.length = _errs45;
                                  } else {
                                    vErrors = null;
                                  }
                                }
                              }
                              var valid0 = _errs44 === errors;
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
      validate360.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate360.errors = vErrors;
  return errors === 0;
}
validate360.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate362(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate362.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.ordinal === void 0 && (missing0 = "ordinal") || data.candidate_id === void 0 && (missing0 = "candidate_id") || data.site_ratio === void 0 && (missing0 = "site_ratio") || data.dense_oc_dmt_ratio === void 0 && (missing0 = "dense_oc_dmt_ratio") || data.status === void 0 && (missing0 = "status") || data.feasible === void 0 && (missing0 = "feasible") || data.metric_value === void 0 && (missing0 = "metric_value") || data.reason_codes === void 0 && (missing0 = "reason_codes")) {
        validate362.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "ordinal" || key0 === "candidate_id" || key0 === "site_ratio" || key0 === "dense_oc_dmt_ratio" || key0 === "status" || key0 === "feasible" || key0 === "metric_value" || key0 === "reason_codes")) {
            validate362.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.ordinal !== void 0) {
            let data0 = data.ordinal;
            const _errs2 = errors;
            if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)))) {
              validate362.errors = [{ instancePath: instancePath + "/ordinal", schemaPath: "#/properties/ordinal/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.candidate_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.candidate_id !== "string") {
                validate362.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.site_ratio !== void 0) {
                let data2 = data.site_ratio;
                const _errs6 = errors;
                const _errs7 = errors;
                let valid1 = false;
                const _errs8 = errors;
                if (!(typeof data2 == "number")) {
                  const err0 = { instancePath: instancePath + "/site_ratio", schemaPath: "#/properties/site_ratio/anyOf/0/type", keyword: "type", params: { type: "number" }, message: "must be number" };
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
                  const err1 = { instancePath: instancePath + "/site_ratio", schemaPath: "#/properties/site_ratio/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err2 = { instancePath: instancePath + "/site_ratio", schemaPath: "#/properties/site_ratio/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err2];
                  } else {
                    vErrors.push(err2);
                  }
                  errors++;
                  validate362.errors = vErrors;
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
                if (data.dense_oc_dmt_ratio !== void 0) {
                  let data3 = data.dense_oc_dmt_ratio;
                  const _errs12 = errors;
                  const _errs13 = errors;
                  let valid2 = false;
                  const _errs14 = errors;
                  if (!(typeof data3 == "number")) {
                    const err3 = { instancePath: instancePath + "/dense_oc_dmt_ratio", schemaPath: "#/properties/dense_oc_dmt_ratio/anyOf/0/type", keyword: "type", params: { type: "number" }, message: "must be number" };
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
                    const err4 = { instancePath: instancePath + "/dense_oc_dmt_ratio", schemaPath: "#/properties/dense_oc_dmt_ratio/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err5 = { instancePath: instancePath + "/dense_oc_dmt_ratio", schemaPath: "#/properties/dense_oc_dmt_ratio/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err5];
                    } else {
                      vErrors.push(err5);
                    }
                    errors++;
                    validate362.errors = vErrors;
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
                  if (data.status !== void 0) {
                    const _errs18 = errors;
                    if (typeof data.status !== "string") {
                      validate362.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs18 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.feasible !== void 0) {
                      let data5 = data.feasible;
                      const _errs20 = errors;
                      const _errs21 = errors;
                      let valid3 = false;
                      const _errs22 = errors;
                      if (typeof data5 !== "boolean") {
                        const err6 = { instancePath: instancePath + "/feasible", schemaPath: "#/properties/feasible/anyOf/0/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" };
                        if (vErrors === null) {
                          vErrors = [err6];
                        } else {
                          vErrors.push(err6);
                        }
                        errors++;
                      }
                      var _valid2 = _errs22 === errors;
                      valid3 = valid3 || _valid2;
                      const _errs24 = errors;
                      if (data5 !== null) {
                        const err7 = { instancePath: instancePath + "/feasible", schemaPath: "#/properties/feasible/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err7];
                        } else {
                          vErrors.push(err7);
                        }
                        errors++;
                      }
                      var _valid2 = _errs24 === errors;
                      valid3 = valid3 || _valid2;
                      if (!valid3) {
                        const err8 = { instancePath: instancePath + "/feasible", schemaPath: "#/properties/feasible/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err8];
                        } else {
                          vErrors.push(err8);
                        }
                        errors++;
                        validate362.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs21;
                        if (vErrors !== null) {
                          if (_errs21) {
                            vErrors.length = _errs21;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.metric_value !== void 0) {
                        let data6 = data.metric_value;
                        const _errs26 = errors;
                        const _errs27 = errors;
                        let valid4 = false;
                        const _errs28 = errors;
                        if (!(typeof data6 == "number")) {
                          const err9 = { instancePath: instancePath + "/metric_value", schemaPath: "#/properties/metric_value/anyOf/0/type", keyword: "type", params: { type: "number" }, message: "must be number" };
                          if (vErrors === null) {
                            vErrors = [err9];
                          } else {
                            vErrors.push(err9);
                          }
                          errors++;
                        }
                        var _valid3 = _errs28 === errors;
                        valid4 = valid4 || _valid3;
                        const _errs30 = errors;
                        if (data6 !== null) {
                          const err10 = { instancePath: instancePath + "/metric_value", schemaPath: "#/properties/metric_value/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err10];
                          } else {
                            vErrors.push(err10);
                          }
                          errors++;
                        }
                        var _valid3 = _errs30 === errors;
                        valid4 = valid4 || _valid3;
                        if (!valid4) {
                          const err11 = { instancePath: instancePath + "/metric_value", schemaPath: "#/properties/metric_value/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err11];
                          } else {
                            vErrors.push(err11);
                          }
                          errors++;
                          validate362.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs27;
                          if (vErrors !== null) {
                            if (_errs27) {
                              vErrors.length = _errs27;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs26 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.reason_codes !== void 0) {
                          let data7 = data.reason_codes;
                          const _errs32 = errors;
                          if (errors === _errs32) {
                            if (Array.isArray(data7)) {
                              var valid5 = true;
                              const len0 = data7.length;
                              for (let i0 = 0; i0 < len0; i0++) {
                                const _errs34 = errors;
                                if (typeof data7[i0] !== "string") {
                                  validate362.errors = [{ instancePath: instancePath + "/reason_codes/" + i0, schemaPath: "#/properties/reason_codes/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                var valid5 = _errs34 === errors;
                                if (!valid5) {
                                  break;
                                }
                              }
                            } else {
                              validate362.errors = [{ instancePath: instancePath + "/reason_codes", schemaPath: "#/properties/reason_codes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs32 === errors;
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
      validate362.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate362.errors = vErrors;
  return errors === 0;
}
validate362.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate359(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate359.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.schema_version === void 0 && (missing0 = "schema_version") || data.identity === void 0 && (missing0 = "identity") || data.offset === void 0 && (missing0 = "offset") || data.total === void 0 && (missing0 = "total") || data.has_more === void 0 && (missing0 = "has_more") || data.decision_id === void 0 && (missing0 = "decision_id") || data.decision_scope === void 0 && (missing0 = "decision_scope") || data.objective === void 0 && (missing0 = "objective") || data.metric_definition === void 0 && (missing0 = "metric_definition") || data.metric_unit === void 0 && (missing0 = "metric_unit") || data.comparison_contract === void 0 && (missing0 = "comparison_contract") || data.points === void 0 && (missing0 = "points") || data.ranking_performed === void 0 && (missing0 = "ranking_performed") || data.claim_scope === void 0 && (missing0 = "claim_scope")) {
        validate359.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema159.properties, key0)) {
            validate359.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.schema_version !== void 0) {
            let data0 = data.schema_version;
            const _errs2 = errors;
            if (typeof data0 !== "string") {
              validate359.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            if ("display-finite-scan-v1" !== data0) {
              validate359.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "display-finite-scan-v1" }, message: "must be equal to constant" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.identity !== void 0) {
              const _errs4 = errors;
              if (!validate360(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
                vErrors = vErrors === null ? validate360.errors : vErrors.concat(validate360.errors);
                errors = vErrors.length;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.offset !== void 0) {
                let data2 = data.offset;
                const _errs5 = errors;
                if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                  validate359.errors = [{ instancePath: instancePath + "/offset", schemaPath: "#/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs5 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.total !== void 0) {
                  let data3 = data.total;
                  const _errs7 = errors;
                  if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)))) {
                    validate359.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.has_more !== void 0) {
                    const _errs9 = errors;
                    if (typeof data.has_more !== "boolean") {
                      validate359.errors = [{ instancePath: instancePath + "/has_more", schemaPath: "#/properties/has_more/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                      return false;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.decision_id !== void 0) {
                      const _errs11 = errors;
                      if (typeof data.decision_id !== "string") {
                        validate359.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs11 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.decision_scope !== void 0) {
                        const _errs13 = errors;
                        if (typeof data.decision_scope !== "string") {
                          validate359.errors = [{ instancePath: instancePath + "/decision_scope", schemaPath: "#/properties/decision_scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs13 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.objective !== void 0) {
                          const _errs15 = errors;
                          if (typeof data.objective !== "string") {
                            validate359.errors = [{ instancePath: instancePath + "/objective", schemaPath: "#/properties/objective/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid0 = _errs15 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.metric_definition !== void 0) {
                            let data8 = data.metric_definition;
                            const _errs17 = errors;
                            const _errs18 = errors;
                            let valid1 = false;
                            const _errs19 = errors;
                            if (typeof data8 !== "string") {
                              const err0 = { instancePath: instancePath + "/metric_definition", schemaPath: "#/properties/metric_definition/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err0];
                              } else {
                                vErrors.push(err0);
                              }
                              errors++;
                            }
                            var _valid0 = _errs19 === errors;
                            valid1 = valid1 || _valid0;
                            const _errs21 = errors;
                            if (data8 !== null) {
                              const err1 = { instancePath: instancePath + "/metric_definition", schemaPath: "#/properties/metric_definition/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err1];
                              } else {
                                vErrors.push(err1);
                              }
                              errors++;
                            }
                            var _valid0 = _errs21 === errors;
                            valid1 = valid1 || _valid0;
                            if (!valid1) {
                              const err2 = { instancePath: instancePath + "/metric_definition", schemaPath: "#/properties/metric_definition/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err2];
                              } else {
                                vErrors.push(err2);
                              }
                              errors++;
                              validate359.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs18;
                              if (vErrors !== null) {
                                if (_errs18) {
                                  vErrors.length = _errs18;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs17 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.metric_unit !== void 0) {
                              let data9 = data.metric_unit;
                              const _errs23 = errors;
                              const _errs24 = errors;
                              let valid2 = false;
                              const _errs25 = errors;
                              if (typeof data9 !== "string") {
                                const err3 = { instancePath: instancePath + "/metric_unit", schemaPath: "#/properties/metric_unit/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err3];
                                } else {
                                  vErrors.push(err3);
                                }
                                errors++;
                              }
                              var _valid1 = _errs25 === errors;
                              valid2 = valid2 || _valid1;
                              const _errs27 = errors;
                              if (data9 !== null) {
                                const err4 = { instancePath: instancePath + "/metric_unit", schemaPath: "#/properties/metric_unit/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                if (vErrors === null) {
                                  vErrors = [err4];
                                } else {
                                  vErrors.push(err4);
                                }
                                errors++;
                              }
                              var _valid1 = _errs27 === errors;
                              valid2 = valid2 || _valid1;
                              if (!valid2) {
                                const err5 = { instancePath: instancePath + "/metric_unit", schemaPath: "#/properties/metric_unit/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                if (vErrors === null) {
                                  vErrors = [err5];
                                } else {
                                  vErrors.push(err5);
                                }
                                errors++;
                                validate359.errors = vErrors;
                                return false;
                              } else {
                                errors = _errs24;
                                if (vErrors !== null) {
                                  if (_errs24) {
                                    vErrors.length = _errs24;
                                  } else {
                                    vErrors = null;
                                  }
                                }
                              }
                              var valid0 = _errs23 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.comparison_contract !== void 0) {
                                let data10 = data.comparison_contract;
                                const _errs29 = errors;
                                const _errs30 = errors;
                                let valid3 = false;
                                const _errs31 = errors;
                                if (errors === _errs31) {
                                  if (data10 && typeof data10 == "object" && !Array.isArray(data10)) {
                                  } else {
                                    const err6 = { instancePath: instancePath + "/comparison_contract", schemaPath: "#/properties/comparison_contract/anyOf/0/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                    if (vErrors === null) {
                                      vErrors = [err6];
                                    } else {
                                      vErrors.push(err6);
                                    }
                                    errors++;
                                  }
                                }
                                var _valid2 = _errs31 === errors;
                                valid3 = valid3 || _valid2;
                                const _errs34 = errors;
                                if (data10 !== null) {
                                  const err7 = { instancePath: instancePath + "/comparison_contract", schemaPath: "#/properties/comparison_contract/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                  if (vErrors === null) {
                                    vErrors = [err7];
                                  } else {
                                    vErrors.push(err7);
                                  }
                                  errors++;
                                }
                                var _valid2 = _errs34 === errors;
                                valid3 = valid3 || _valid2;
                                if (!valid3) {
                                  const err8 = { instancePath: instancePath + "/comparison_contract", schemaPath: "#/properties/comparison_contract/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                  if (vErrors === null) {
                                    vErrors = [err8];
                                  } else {
                                    vErrors.push(err8);
                                  }
                                  errors++;
                                  validate359.errors = vErrors;
                                  return false;
                                } else {
                                  errors = _errs30;
                                  if (vErrors !== null) {
                                    if (_errs30) {
                                      vErrors.length = _errs30;
                                    } else {
                                      vErrors = null;
                                    }
                                  }
                                }
                                var valid0 = _errs29 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.points !== void 0) {
                                  let data11 = data.points;
                                  const _errs36 = errors;
                                  if (errors === _errs36) {
                                    if (Array.isArray(data11)) {
                                      var valid4 = true;
                                      const len0 = data11.length;
                                      for (let i0 = 0; i0 < len0; i0++) {
                                        const _errs38 = errors;
                                        if (!validate362(data11[i0], { instancePath: instancePath + "/points/" + i0, parentData: data11, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                          vErrors = vErrors === null ? validate362.errors : vErrors.concat(validate362.errors);
                                          errors = vErrors.length;
                                        }
                                        var valid4 = _errs38 === errors;
                                        if (!valid4) {
                                          break;
                                        }
                                      }
                                    } else {
                                      validate359.errors = [{ instancePath: instancePath + "/points", schemaPath: "#/properties/points/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                      return false;
                                    }
                                  }
                                  var valid0 = _errs36 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.ranking_performed !== void 0) {
                                    let data13 = data.ranking_performed;
                                    const _errs39 = errors;
                                    if (typeof data13 !== "boolean") {
                                      validate359.errors = [{ instancePath: instancePath + "/ranking_performed", schemaPath: "#/properties/ranking_performed/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                      return false;
                                    }
                                    if (false !== data13) {
                                      validate359.errors = [{ instancePath: instancePath + "/ranking_performed", schemaPath: "#/properties/ranking_performed/const", keyword: "const", params: { allowedValue: false }, message: "must be equal to constant" }];
                                      return false;
                                    }
                                    var valid0 = _errs39 === errors;
                                  } else {
                                    var valid0 = true;
                                  }
                                  if (valid0) {
                                    if (data.claim_scope !== void 0) {
                                      let data14 = data.claim_scope;
                                      const _errs41 = errors;
                                      if (typeof data14 !== "string") {
                                        validate359.errors = [{ instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      if ("source_reported_scan_not_execution_or_parameter_approval" !== data14) {
                                        validate359.errors = [{ instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/const", keyword: "const", params: { allowedValue: "source_reported_scan_not_execution_or_parameter_approval" }, message: "must be equal to constant" }];
                                        return false;
                                      }
                                      var valid0 = _errs41 === errors;
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
    } else {
      validate359.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate359.errors = vErrors;
  return errors === 0;
}
validate359.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var SeriesPage = validate364;
var schema162 = { "additionalProperties": false, "properties": { "schema_version": { "const": "display-series-v1", "type": "string" }, "identity": { "$ref": "urn:fusionlab:shared#/$defs/ResourceIdentity" }, "result_schema_version": { "type": "string" }, "model_kind": { "type": "string" }, "formula_version": { "type": "string" }, "time_unit": { "type": "string" }, "data_source_sha256": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "source_reference": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "offset": { "type": "integer" }, "total": { "type": "integer" }, "has_more": { "type": "boolean" }, "display_policy": { "const": "exact_contiguous_page_no_decimation", "type": "string" }, "time": { "items": { "type": "number" }, "type": "array" }, "series": { "items": { "$ref": "urn:fusionlab:shared#/$defs/SeriesDescriptor" }, "type": "array" }, "values": { "additionalProperties": { "items": { "anyOf": [{ "type": "number" }, { "type": "null" }] }, "type": "array" }, "type": "object" }, "claim_scope": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "source_type": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "formal_prediction_allowed": { "anyOf": [{ "type": "boolean" }, { "type": "null" }] }, "pool_volumes": { "additionalProperties": { "additionalProperties": true, "type": "object" }, "type": "object" } }, "required": ["schema_version", "identity", "result_schema_version", "model_kind", "formula_version", "time_unit", "data_source_sha256", "source_reference", "offset", "total", "has_more", "display_policy", "time", "series", "values", "claim_scope", "source_type", "formal_prediction_allowed", "pool_volumes"], "type": "object" };
function validate365(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate365.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.file_id === void 0 && (missing0 = "file_id") || data.source_sha256 === void 0 && (missing0 = "source_sha256") || data.run_id === void 0 && (missing0 = "run_id") || data.snapshot_hash === void 0 && (missing0 = "snapshot_hash") || data.node_id === void 0 && (missing0 = "node_id") || data.attempt === void 0 && (missing0 = "attempt") || data.candidate_id === void 0 && (missing0 = "candidate_id") || data.construct_id === void 0 && (missing0 = "construct_id") || data.condition_id === void 0 && (missing0 = "condition_id")) {
        validate365.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema158.properties, key0)) {
            validate365.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate365.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.file_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.file_id !== "string") {
                validate365.errors = [{ instancePath: instancePath + "/file_id", schemaPath: "#/properties/file_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.source_sha256 !== void 0) {
                const _errs6 = errors;
                if (typeof data.source_sha256 !== "string") {
                  validate365.errors = [{ instancePath: instancePath + "/source_sha256", schemaPath: "#/properties/source_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  let data3 = data.run_id;
                  const _errs8 = errors;
                  const _errs9 = errors;
                  let valid1 = false;
                  const _errs10 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                    const err1 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err2 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate365.errors = vErrors;
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
                  if (data.snapshot_hash !== void 0) {
                    let data4 = data.snapshot_hash;
                    const _errs14 = errors;
                    const _errs15 = errors;
                    let valid2 = false;
                    const _errs16 = errors;
                    if (typeof data4 !== "string") {
                      const err3 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                      const err4 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                      const err5 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err5];
                      } else {
                        vErrors.push(err5);
                      }
                      errors++;
                      validate365.errors = vErrors;
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
                    if (data.node_id !== void 0) {
                      let data5 = data.node_id;
                      const _errs20 = errors;
                      const _errs21 = errors;
                      let valid3 = false;
                      const _errs22 = errors;
                      if (typeof data5 !== "string") {
                        const err6 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err6];
                        } else {
                          vErrors.push(err6);
                        }
                        errors++;
                      }
                      var _valid2 = _errs22 === errors;
                      valid3 = valid3 || _valid2;
                      const _errs24 = errors;
                      if (data5 !== null) {
                        const err7 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err7];
                        } else {
                          vErrors.push(err7);
                        }
                        errors++;
                      }
                      var _valid2 = _errs24 === errors;
                      valid3 = valid3 || _valid2;
                      if (!valid3) {
                        const err8 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err8];
                        } else {
                          vErrors.push(err8);
                        }
                        errors++;
                        validate365.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs21;
                        if (vErrors !== null) {
                          if (_errs21) {
                            vErrors.length = _errs21;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.attempt !== void 0) {
                        let data6 = data.attempt;
                        const _errs26 = errors;
                        const _errs27 = errors;
                        let valid4 = false;
                        const _errs28 = errors;
                        if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)))) {
                          const err9 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                          if (vErrors === null) {
                            vErrors = [err9];
                          } else {
                            vErrors.push(err9);
                          }
                          errors++;
                        }
                        var _valid3 = _errs28 === errors;
                        valid4 = valid4 || _valid3;
                        const _errs30 = errors;
                        if (data6 !== null) {
                          const err10 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err10];
                          } else {
                            vErrors.push(err10);
                          }
                          errors++;
                        }
                        var _valid3 = _errs30 === errors;
                        valid4 = valid4 || _valid3;
                        if (!valid4) {
                          const err11 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err11];
                          } else {
                            vErrors.push(err11);
                          }
                          errors++;
                          validate365.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs27;
                          if (vErrors !== null) {
                            if (_errs27) {
                              vErrors.length = _errs27;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs26 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.candidate_id !== void 0) {
                          let data7 = data.candidate_id;
                          const _errs32 = errors;
                          const _errs33 = errors;
                          let valid5 = false;
                          const _errs34 = errors;
                          if (typeof data7 !== "string") {
                            const err12 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err12];
                            } else {
                              vErrors.push(err12);
                            }
                            errors++;
                          }
                          var _valid4 = _errs34 === errors;
                          valid5 = valid5 || _valid4;
                          const _errs36 = errors;
                          if (data7 !== null) {
                            const err13 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err13];
                            } else {
                              vErrors.push(err13);
                            }
                            errors++;
                          }
                          var _valid4 = _errs36 === errors;
                          valid5 = valid5 || _valid4;
                          if (!valid5) {
                            const err14 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err14];
                            } else {
                              vErrors.push(err14);
                            }
                            errors++;
                            validate365.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs33;
                            if (vErrors !== null) {
                              if (_errs33) {
                                vErrors.length = _errs33;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs32 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.construct_id !== void 0) {
                            let data8 = data.construct_id;
                            const _errs38 = errors;
                            const _errs39 = errors;
                            let valid6 = false;
                            const _errs40 = errors;
                            if (typeof data8 !== "string") {
                              const err15 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err15];
                              } else {
                                vErrors.push(err15);
                              }
                              errors++;
                            }
                            var _valid5 = _errs40 === errors;
                            valid6 = valid6 || _valid5;
                            const _errs42 = errors;
                            if (data8 !== null) {
                              const err16 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err16];
                              } else {
                                vErrors.push(err16);
                              }
                              errors++;
                            }
                            var _valid5 = _errs42 === errors;
                            valid6 = valid6 || _valid5;
                            if (!valid6) {
                              const err17 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err17];
                              } else {
                                vErrors.push(err17);
                              }
                              errors++;
                              validate365.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs39;
                              if (vErrors !== null) {
                                if (_errs39) {
                                  vErrors.length = _errs39;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs38 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.condition_id !== void 0) {
                              let data9 = data.condition_id;
                              const _errs44 = errors;
                              const _errs45 = errors;
                              let valid7 = false;
                              const _errs46 = errors;
                              if (typeof data9 !== "string") {
                                const err18 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err18];
                                } else {
                                  vErrors.push(err18);
                                }
                                errors++;
                              }
                              var _valid6 = _errs46 === errors;
                              valid7 = valid7 || _valid6;
                              const _errs48 = errors;
                              if (data9 !== null) {
                                const err19 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                if (vErrors === null) {
                                  vErrors = [err19];
                                } else {
                                  vErrors.push(err19);
                                }
                                errors++;
                              }
                              var _valid6 = _errs48 === errors;
                              valid7 = valid7 || _valid6;
                              if (!valid7) {
                                const err20 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                if (vErrors === null) {
                                  vErrors = [err20];
                                } else {
                                  vErrors.push(err20);
                                }
                                errors++;
                                validate365.errors = vErrors;
                                return false;
                              } else {
                                errors = _errs45;
                                if (vErrors !== null) {
                                  if (_errs45) {
                                    vErrors.length = _errs45;
                                  } else {
                                    vErrors = null;
                                  }
                                }
                              }
                              var valid0 = _errs44 === errors;
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
      validate365.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate365.errors = vErrors;
  return errors === 0;
}
validate365.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate367(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate367.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.compartment === void 0 && (missing0 = "compartment") || data.species === void 0 && (missing0 = "species") || data.unit === void 0 && (missing0 = "unit")) {
        validate367.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "compartment" || key0 === "species" || key0 === "unit")) {
            validate367.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate367.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.compartment !== void 0) {
              const _errs4 = errors;
              if (typeof data.compartment !== "string") {
                validate367.errors = [{ instancePath: instancePath + "/compartment", schemaPath: "#/properties/compartment/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.species !== void 0) {
                const _errs6 = errors;
                if (typeof data.species !== "string") {
                  validate367.errors = [{ instancePath: instancePath + "/species", schemaPath: "#/properties/species/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.unit !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.unit !== "string") {
                    validate367.errors = [{ instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
    } else {
      validate367.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate367.errors = vErrors;
  return errors === 0;
}
validate367.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate364(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate364.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.schema_version === void 0 && (missing0 = "schema_version") || data.identity === void 0 && (missing0 = "identity") || data.result_schema_version === void 0 && (missing0 = "result_schema_version") || data.model_kind === void 0 && (missing0 = "model_kind") || data.formula_version === void 0 && (missing0 = "formula_version") || data.time_unit === void 0 && (missing0 = "time_unit") || data.data_source_sha256 === void 0 && (missing0 = "data_source_sha256") || data.source_reference === void 0 && (missing0 = "source_reference") || data.offset === void 0 && (missing0 = "offset") || data.total === void 0 && (missing0 = "total") || data.has_more === void 0 && (missing0 = "has_more") || data.display_policy === void 0 && (missing0 = "display_policy") || data.time === void 0 && (missing0 = "time") || data.series === void 0 && (missing0 = "series") || data.values === void 0 && (missing0 = "values") || data.claim_scope === void 0 && (missing0 = "claim_scope") || data.source_type === void 0 && (missing0 = "source_type") || data.formal_prediction_allowed === void 0 && (missing0 = "formal_prediction_allowed") || data.pool_volumes === void 0 && (missing0 = "pool_volumes")) {
        validate364.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema162.properties, key0)) {
            validate364.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.schema_version !== void 0) {
            let data0 = data.schema_version;
            const _errs2 = errors;
            if (typeof data0 !== "string") {
              validate364.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            if ("display-series-v1" !== data0) {
              validate364.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "display-series-v1" }, message: "must be equal to constant" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.identity !== void 0) {
              const _errs4 = errors;
              if (!validate365(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
                vErrors = vErrors === null ? validate365.errors : vErrors.concat(validate365.errors);
                errors = vErrors.length;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.result_schema_version !== void 0) {
                const _errs5 = errors;
                if (typeof data.result_schema_version !== "string") {
                  validate364.errors = [{ instancePath: instancePath + "/result_schema_version", schemaPath: "#/properties/result_schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs5 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.model_kind !== void 0) {
                  const _errs7 = errors;
                  if (typeof data.model_kind !== "string") {
                    validate364.errors = [{ instancePath: instancePath + "/model_kind", schemaPath: "#/properties/model_kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.formula_version !== void 0) {
                    const _errs9 = errors;
                    if (typeof data.formula_version !== "string") {
                      validate364.errors = [{ instancePath: instancePath + "/formula_version", schemaPath: "#/properties/formula_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.time_unit !== void 0) {
                      const _errs11 = errors;
                      if (typeof data.time_unit !== "string") {
                        validate364.errors = [{ instancePath: instancePath + "/time_unit", schemaPath: "#/properties/time_unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs11 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.data_source_sha256 !== void 0) {
                        let data6 = data.data_source_sha256;
                        const _errs13 = errors;
                        const _errs14 = errors;
                        let valid1 = false;
                        const _errs15 = errors;
                        if (typeof data6 !== "string") {
                          const err0 = { instancePath: instancePath + "/data_source_sha256", schemaPath: "#/properties/data_source_sha256/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                        }
                        var _valid0 = _errs15 === errors;
                        valid1 = valid1 || _valid0;
                        const _errs17 = errors;
                        if (data6 !== null) {
                          const err1 = { instancePath: instancePath + "/data_source_sha256", schemaPath: "#/properties/data_source_sha256/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err1];
                          } else {
                            vErrors.push(err1);
                          }
                          errors++;
                        }
                        var _valid0 = _errs17 === errors;
                        valid1 = valid1 || _valid0;
                        if (!valid1) {
                          const err2 = { instancePath: instancePath + "/data_source_sha256", schemaPath: "#/properties/data_source_sha256/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err2];
                          } else {
                            vErrors.push(err2);
                          }
                          errors++;
                          validate364.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs14;
                          if (vErrors !== null) {
                            if (_errs14) {
                              vErrors.length = _errs14;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs13 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.source_reference !== void 0) {
                          let data7 = data.source_reference;
                          const _errs19 = errors;
                          const _errs20 = errors;
                          let valid2 = false;
                          const _errs21 = errors;
                          if (typeof data7 !== "string") {
                            const err3 = { instancePath: instancePath + "/source_reference", schemaPath: "#/properties/source_reference/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err3];
                            } else {
                              vErrors.push(err3);
                            }
                            errors++;
                          }
                          var _valid1 = _errs21 === errors;
                          valid2 = valid2 || _valid1;
                          const _errs23 = errors;
                          if (data7 !== null) {
                            const err4 = { instancePath: instancePath + "/source_reference", schemaPath: "#/properties/source_reference/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err4];
                            } else {
                              vErrors.push(err4);
                            }
                            errors++;
                          }
                          var _valid1 = _errs23 === errors;
                          valid2 = valid2 || _valid1;
                          if (!valid2) {
                            const err5 = { instancePath: instancePath + "/source_reference", schemaPath: "#/properties/source_reference/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err5];
                            } else {
                              vErrors.push(err5);
                            }
                            errors++;
                            validate364.errors = vErrors;
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
                          if (data.offset !== void 0) {
                            let data8 = data.offset;
                            const _errs25 = errors;
                            if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)))) {
                              validate364.errors = [{ instancePath: instancePath + "/offset", schemaPath: "#/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            var valid0 = _errs25 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.total !== void 0) {
                              let data9 = data.total;
                              const _errs27 = errors;
                              if (!(typeof data9 == "number" && (!(data9 % 1) && !isNaN(data9)))) {
                                validate364.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              var valid0 = _errs27 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.has_more !== void 0) {
                                const _errs29 = errors;
                                if (typeof data.has_more !== "boolean") {
                                  validate364.errors = [{ instancePath: instancePath + "/has_more", schemaPath: "#/properties/has_more/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                  return false;
                                }
                                var valid0 = _errs29 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.display_policy !== void 0) {
                                  let data11 = data.display_policy;
                                  const _errs31 = errors;
                                  if (typeof data11 !== "string") {
                                    validate364.errors = [{ instancePath: instancePath + "/display_policy", schemaPath: "#/properties/display_policy/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("exact_contiguous_page_no_decimation" !== data11) {
                                    validate364.errors = [{ instancePath: instancePath + "/display_policy", schemaPath: "#/properties/display_policy/const", keyword: "const", params: { allowedValue: "exact_contiguous_page_no_decimation" }, message: "must be equal to constant" }];
                                    return false;
                                  }
                                  var valid0 = _errs31 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.time !== void 0) {
                                    let data12 = data.time;
                                    const _errs33 = errors;
                                    if (errors === _errs33) {
                                      if (Array.isArray(data12)) {
                                        var valid3 = true;
                                        const len0 = data12.length;
                                        for (let i0 = 0; i0 < len0; i0++) {
                                          const _errs35 = errors;
                                          if (!(typeof data12[i0] == "number")) {
                                            validate364.errors = [{ instancePath: instancePath + "/time/" + i0, schemaPath: "#/properties/time/items/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                            return false;
                                          }
                                          var valid3 = _errs35 === errors;
                                          if (!valid3) {
                                            break;
                                          }
                                        }
                                      } else {
                                        validate364.errors = [{ instancePath: instancePath + "/time", schemaPath: "#/properties/time/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                        return false;
                                      }
                                    }
                                    var valid0 = _errs33 === errors;
                                  } else {
                                    var valid0 = true;
                                  }
                                  if (valid0) {
                                    if (data.series !== void 0) {
                                      let data14 = data.series;
                                      const _errs37 = errors;
                                      if (errors === _errs37) {
                                        if (Array.isArray(data14)) {
                                          var valid4 = true;
                                          const len1 = data14.length;
                                          for (let i1 = 0; i1 < len1; i1++) {
                                            const _errs39 = errors;
                                            if (!validate367(data14[i1], { instancePath: instancePath + "/series/" + i1, parentData: data14, parentDataProperty: i1, rootData, dynamicAnchors })) {
                                              vErrors = vErrors === null ? validate367.errors : vErrors.concat(validate367.errors);
                                              errors = vErrors.length;
                                            }
                                            var valid4 = _errs39 === errors;
                                            if (!valid4) {
                                              break;
                                            }
                                          }
                                        } else {
                                          validate364.errors = [{ instancePath: instancePath + "/series", schemaPath: "#/properties/series/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                          return false;
                                        }
                                      }
                                      var valid0 = _errs37 === errors;
                                    } else {
                                      var valid0 = true;
                                    }
                                    if (valid0) {
                                      if (data.values !== void 0) {
                                        let data16 = data.values;
                                        const _errs40 = errors;
                                        if (errors === _errs40) {
                                          if (data16 && typeof data16 == "object" && !Array.isArray(data16)) {
                                            for (const key1 in data16) {
                                              let data17 = data16[key1];
                                              const _errs43 = errors;
                                              if (errors === _errs43) {
                                                if (Array.isArray(data17)) {
                                                  var valid6 = true;
                                                  const len2 = data17.length;
                                                  for (let i2 = 0; i2 < len2; i2++) {
                                                    let data18 = data17[i2];
                                                    const _errs45 = errors;
                                                    const _errs46 = errors;
                                                    let valid7 = false;
                                                    const _errs47 = errors;
                                                    if (!(typeof data18 == "number")) {
                                                      const err6 = { instancePath: instancePath + "/values/" + key1.replace(/~/g, "~0").replace(/\//g, "~1") + "/" + i2, schemaPath: "#/properties/values/additionalProperties/items/anyOf/0/type", keyword: "type", params: { type: "number" }, message: "must be number" };
                                                      if (vErrors === null) {
                                                        vErrors = [err6];
                                                      } else {
                                                        vErrors.push(err6);
                                                      }
                                                      errors++;
                                                    }
                                                    var _valid2 = _errs47 === errors;
                                                    valid7 = valid7 || _valid2;
                                                    const _errs49 = errors;
                                                    if (data18 !== null) {
                                                      const err7 = { instancePath: instancePath + "/values/" + key1.replace(/~/g, "~0").replace(/\//g, "~1") + "/" + i2, schemaPath: "#/properties/values/additionalProperties/items/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                                      if (vErrors === null) {
                                                        vErrors = [err7];
                                                      } else {
                                                        vErrors.push(err7);
                                                      }
                                                      errors++;
                                                    }
                                                    var _valid2 = _errs49 === errors;
                                                    valid7 = valid7 || _valid2;
                                                    if (!valid7) {
                                                      const err8 = { instancePath: instancePath + "/values/" + key1.replace(/~/g, "~0").replace(/\//g, "~1") + "/" + i2, schemaPath: "#/properties/values/additionalProperties/items/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                                      if (vErrors === null) {
                                                        vErrors = [err8];
                                                      } else {
                                                        vErrors.push(err8);
                                                      }
                                                      errors++;
                                                      validate364.errors = vErrors;
                                                      return false;
                                                    } else {
                                                      errors = _errs46;
                                                      if (vErrors !== null) {
                                                        if (_errs46) {
                                                          vErrors.length = _errs46;
                                                        } else {
                                                          vErrors = null;
                                                        }
                                                      }
                                                    }
                                                    var valid6 = _errs45 === errors;
                                                    if (!valid6) {
                                                      break;
                                                    }
                                                  }
                                                } else {
                                                  validate364.errors = [{ instancePath: instancePath + "/values/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/values/additionalProperties/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                                  return false;
                                                }
                                              }
                                              var valid5 = _errs43 === errors;
                                              if (!valid5) {
                                                break;
                                              }
                                            }
                                          } else {
                                            validate364.errors = [{ instancePath: instancePath + "/values", schemaPath: "#/properties/values/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                            return false;
                                          }
                                        }
                                        var valid0 = _errs40 === errors;
                                      } else {
                                        var valid0 = true;
                                      }
                                      if (valid0) {
                                        if (data.claim_scope !== void 0) {
                                          let data19 = data.claim_scope;
                                          const _errs51 = errors;
                                          const _errs52 = errors;
                                          let valid8 = false;
                                          const _errs53 = errors;
                                          if (typeof data19 !== "string") {
                                            const err9 = { instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                            if (vErrors === null) {
                                              vErrors = [err9];
                                            } else {
                                              vErrors.push(err9);
                                            }
                                            errors++;
                                          }
                                          var _valid3 = _errs53 === errors;
                                          valid8 = valid8 || _valid3;
                                          const _errs55 = errors;
                                          if (data19 !== null) {
                                            const err10 = { instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                            if (vErrors === null) {
                                              vErrors = [err10];
                                            } else {
                                              vErrors.push(err10);
                                            }
                                            errors++;
                                          }
                                          var _valid3 = _errs55 === errors;
                                          valid8 = valid8 || _valid3;
                                          if (!valid8) {
                                            const err11 = { instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                            if (vErrors === null) {
                                              vErrors = [err11];
                                            } else {
                                              vErrors.push(err11);
                                            }
                                            errors++;
                                            validate364.errors = vErrors;
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
                                          var valid0 = _errs51 === errors;
                                        } else {
                                          var valid0 = true;
                                        }
                                        if (valid0) {
                                          if (data.source_type !== void 0) {
                                            let data20 = data.source_type;
                                            const _errs57 = errors;
                                            const _errs58 = errors;
                                            let valid9 = false;
                                            const _errs59 = errors;
                                            if (typeof data20 !== "string") {
                                              const err12 = { instancePath: instancePath + "/source_type", schemaPath: "#/properties/source_type/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                              if (vErrors === null) {
                                                vErrors = [err12];
                                              } else {
                                                vErrors.push(err12);
                                              }
                                              errors++;
                                            }
                                            var _valid4 = _errs59 === errors;
                                            valid9 = valid9 || _valid4;
                                            const _errs61 = errors;
                                            if (data20 !== null) {
                                              const err13 = { instancePath: instancePath + "/source_type", schemaPath: "#/properties/source_type/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                              if (vErrors === null) {
                                                vErrors = [err13];
                                              } else {
                                                vErrors.push(err13);
                                              }
                                              errors++;
                                            }
                                            var _valid4 = _errs61 === errors;
                                            valid9 = valid9 || _valid4;
                                            if (!valid9) {
                                              const err14 = { instancePath: instancePath + "/source_type", schemaPath: "#/properties/source_type/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                              if (vErrors === null) {
                                                vErrors = [err14];
                                              } else {
                                                vErrors.push(err14);
                                              }
                                              errors++;
                                              validate364.errors = vErrors;
                                              return false;
                                            } else {
                                              errors = _errs58;
                                              if (vErrors !== null) {
                                                if (_errs58) {
                                                  vErrors.length = _errs58;
                                                } else {
                                                  vErrors = null;
                                                }
                                              }
                                            }
                                            var valid0 = _errs57 === errors;
                                          } else {
                                            var valid0 = true;
                                          }
                                          if (valid0) {
                                            if (data.formal_prediction_allowed !== void 0) {
                                              let data21 = data.formal_prediction_allowed;
                                              const _errs63 = errors;
                                              const _errs64 = errors;
                                              let valid10 = false;
                                              const _errs65 = errors;
                                              if (typeof data21 !== "boolean") {
                                                const err15 = { instancePath: instancePath + "/formal_prediction_allowed", schemaPath: "#/properties/formal_prediction_allowed/anyOf/0/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" };
                                                if (vErrors === null) {
                                                  vErrors = [err15];
                                                } else {
                                                  vErrors.push(err15);
                                                }
                                                errors++;
                                              }
                                              var _valid5 = _errs65 === errors;
                                              valid10 = valid10 || _valid5;
                                              const _errs67 = errors;
                                              if (data21 !== null) {
                                                const err16 = { instancePath: instancePath + "/formal_prediction_allowed", schemaPath: "#/properties/formal_prediction_allowed/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                                if (vErrors === null) {
                                                  vErrors = [err16];
                                                } else {
                                                  vErrors.push(err16);
                                                }
                                                errors++;
                                              }
                                              var _valid5 = _errs67 === errors;
                                              valid10 = valid10 || _valid5;
                                              if (!valid10) {
                                                const err17 = { instancePath: instancePath + "/formal_prediction_allowed", schemaPath: "#/properties/formal_prediction_allowed/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                                if (vErrors === null) {
                                                  vErrors = [err17];
                                                } else {
                                                  vErrors.push(err17);
                                                }
                                                errors++;
                                                validate364.errors = vErrors;
                                                return false;
                                              } else {
                                                errors = _errs64;
                                                if (vErrors !== null) {
                                                  if (_errs64) {
                                                    vErrors.length = _errs64;
                                                  } else {
                                                    vErrors = null;
                                                  }
                                                }
                                              }
                                              var valid0 = _errs63 === errors;
                                            } else {
                                              var valid0 = true;
                                            }
                                            if (valid0) {
                                              if (data.pool_volumes !== void 0) {
                                                let data22 = data.pool_volumes;
                                                const _errs69 = errors;
                                                if (errors === _errs69) {
                                                  if (data22 && typeof data22 == "object" && !Array.isArray(data22)) {
                                                    for (const key2 in data22) {
                                                      let data23 = data22[key2];
                                                      const _errs72 = errors;
                                                      if (errors === _errs72) {
                                                        if (data23 && typeof data23 == "object" && !Array.isArray(data23)) {
                                                        } else {
                                                          validate364.errors = [{ instancePath: instancePath + "/pool_volumes/" + key2.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/pool_volumes/additionalProperties/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                                          return false;
                                                        }
                                                      }
                                                      var valid11 = _errs72 === errors;
                                                      if (!valid11) {
                                                        break;
                                                      }
                                                    }
                                                  } else {
                                                    validate364.errors = [{ instancePath: instancePath + "/pool_volumes", schemaPath: "#/properties/pool_volumes/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                                    return false;
                                                  }
                                                }
                                                var valid0 = _errs69 === errors;
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
    } else {
      validate364.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate364.errors = vErrors;
  return errors === 0;
}
validate364.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var StructurePage = validate369;
var schema165 = { "additionalProperties": false, "properties": { "schema_version": { "const": "display-structure-v1", "type": "string" }, "identity": { "$ref": "urn:fusionlab:shared#/$defs/ResourceIdentity" }, "format": { "type": "string" }, "offset": { "type": "integer" }, "total": { "type": "integer" }, "chains": { "items": { "type": "string" }, "type": "array" }, "models": { "items": { "type": "string" }, "type": "array" }, "residues": { "items": { "$ref": "urn:fusionlab:shared#/$defs/ResidueIdentity" }, "type": "array" }, "confidence_status": { "enum": ["not_registered", "source_registered_not_scientific_approval"], "type": "string" }, "mapping_status": { "enum": ["not_registered", "source_registered_not_scientific_approval"], "type": "string" }, "pocket_status": { "enum": ["not_registered", "source_registered_not_scientific_approval"], "type": "string" }, "annotation_file_id": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "annotation_sha256": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "annotation_source_reference": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "annotation_source_tool": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "annotation_source_tool_version": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "fusion_sequence_file_id": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "fusion_sequence_file_sha256": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "fusion_sequence_id": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "annotations": { "items": { "$ref": "urn:fusionlab:shared#/$defs/DisplayResidueAnnotation" }, "type": "array" }, "annotation_scope": { "enum": ["residue_page", "full_model"], "type": "string" }, "overlays": { "items": { "$ref": "urn:fusionlab:shared#/$defs/DisplayOverlay" }, "type": "array" }, "preview_policy": { "const": "atom_coordinates_only_original_sealed", "type": "string" } }, "required": ["schema_version", "identity", "format", "offset", "total", "chains", "models", "residues", "confidence_status", "mapping_status", "pocket_status", "annotation_file_id", "annotation_sha256", "annotation_source_reference", "annotation_source_tool", "annotation_source_tool_version", "fusion_sequence_file_id", "fusion_sequence_file_sha256", "fusion_sequence_id", "annotations", "annotation_scope", "overlays", "preview_policy"], "type": "object" };
function validate370(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate370.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.file_id === void 0 && (missing0 = "file_id") || data.source_sha256 === void 0 && (missing0 = "source_sha256") || data.run_id === void 0 && (missing0 = "run_id") || data.snapshot_hash === void 0 && (missing0 = "snapshot_hash") || data.node_id === void 0 && (missing0 = "node_id") || data.attempt === void 0 && (missing0 = "attempt") || data.candidate_id === void 0 && (missing0 = "candidate_id") || data.construct_id === void 0 && (missing0 = "construct_id") || data.condition_id === void 0 && (missing0 = "condition_id")) {
        validate370.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema158.properties, key0)) {
            validate370.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate370.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.file_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.file_id !== "string") {
                validate370.errors = [{ instancePath: instancePath + "/file_id", schemaPath: "#/properties/file_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.source_sha256 !== void 0) {
                const _errs6 = errors;
                if (typeof data.source_sha256 !== "string") {
                  validate370.errors = [{ instancePath: instancePath + "/source_sha256", schemaPath: "#/properties/source_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  let data3 = data.run_id;
                  const _errs8 = errors;
                  const _errs9 = errors;
                  let valid1 = false;
                  const _errs10 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                    const err1 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err2 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate370.errors = vErrors;
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
                  if (data.snapshot_hash !== void 0) {
                    let data4 = data.snapshot_hash;
                    const _errs14 = errors;
                    const _errs15 = errors;
                    let valid2 = false;
                    const _errs16 = errors;
                    if (typeof data4 !== "string") {
                      const err3 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                      const err4 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                      const err5 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err5];
                      } else {
                        vErrors.push(err5);
                      }
                      errors++;
                      validate370.errors = vErrors;
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
                    if (data.node_id !== void 0) {
                      let data5 = data.node_id;
                      const _errs20 = errors;
                      const _errs21 = errors;
                      let valid3 = false;
                      const _errs22 = errors;
                      if (typeof data5 !== "string") {
                        const err6 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err6];
                        } else {
                          vErrors.push(err6);
                        }
                        errors++;
                      }
                      var _valid2 = _errs22 === errors;
                      valid3 = valid3 || _valid2;
                      const _errs24 = errors;
                      if (data5 !== null) {
                        const err7 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err7];
                        } else {
                          vErrors.push(err7);
                        }
                        errors++;
                      }
                      var _valid2 = _errs24 === errors;
                      valid3 = valid3 || _valid2;
                      if (!valid3) {
                        const err8 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err8];
                        } else {
                          vErrors.push(err8);
                        }
                        errors++;
                        validate370.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs21;
                        if (vErrors !== null) {
                          if (_errs21) {
                            vErrors.length = _errs21;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.attempt !== void 0) {
                        let data6 = data.attempt;
                        const _errs26 = errors;
                        const _errs27 = errors;
                        let valid4 = false;
                        const _errs28 = errors;
                        if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)))) {
                          const err9 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                          if (vErrors === null) {
                            vErrors = [err9];
                          } else {
                            vErrors.push(err9);
                          }
                          errors++;
                        }
                        var _valid3 = _errs28 === errors;
                        valid4 = valid4 || _valid3;
                        const _errs30 = errors;
                        if (data6 !== null) {
                          const err10 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err10];
                          } else {
                            vErrors.push(err10);
                          }
                          errors++;
                        }
                        var _valid3 = _errs30 === errors;
                        valid4 = valid4 || _valid3;
                        if (!valid4) {
                          const err11 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err11];
                          } else {
                            vErrors.push(err11);
                          }
                          errors++;
                          validate370.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs27;
                          if (vErrors !== null) {
                            if (_errs27) {
                              vErrors.length = _errs27;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs26 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.candidate_id !== void 0) {
                          let data7 = data.candidate_id;
                          const _errs32 = errors;
                          const _errs33 = errors;
                          let valid5 = false;
                          const _errs34 = errors;
                          if (typeof data7 !== "string") {
                            const err12 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err12];
                            } else {
                              vErrors.push(err12);
                            }
                            errors++;
                          }
                          var _valid4 = _errs34 === errors;
                          valid5 = valid5 || _valid4;
                          const _errs36 = errors;
                          if (data7 !== null) {
                            const err13 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err13];
                            } else {
                              vErrors.push(err13);
                            }
                            errors++;
                          }
                          var _valid4 = _errs36 === errors;
                          valid5 = valid5 || _valid4;
                          if (!valid5) {
                            const err14 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err14];
                            } else {
                              vErrors.push(err14);
                            }
                            errors++;
                            validate370.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs33;
                            if (vErrors !== null) {
                              if (_errs33) {
                                vErrors.length = _errs33;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs32 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.construct_id !== void 0) {
                            let data8 = data.construct_id;
                            const _errs38 = errors;
                            const _errs39 = errors;
                            let valid6 = false;
                            const _errs40 = errors;
                            if (typeof data8 !== "string") {
                              const err15 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err15];
                              } else {
                                vErrors.push(err15);
                              }
                              errors++;
                            }
                            var _valid5 = _errs40 === errors;
                            valid6 = valid6 || _valid5;
                            const _errs42 = errors;
                            if (data8 !== null) {
                              const err16 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err16];
                              } else {
                                vErrors.push(err16);
                              }
                              errors++;
                            }
                            var _valid5 = _errs42 === errors;
                            valid6 = valid6 || _valid5;
                            if (!valid6) {
                              const err17 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err17];
                              } else {
                                vErrors.push(err17);
                              }
                              errors++;
                              validate370.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs39;
                              if (vErrors !== null) {
                                if (_errs39) {
                                  vErrors.length = _errs39;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs38 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.condition_id !== void 0) {
                              let data9 = data.condition_id;
                              const _errs44 = errors;
                              const _errs45 = errors;
                              let valid7 = false;
                              const _errs46 = errors;
                              if (typeof data9 !== "string") {
                                const err18 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err18];
                                } else {
                                  vErrors.push(err18);
                                }
                                errors++;
                              }
                              var _valid6 = _errs46 === errors;
                              valid7 = valid7 || _valid6;
                              const _errs48 = errors;
                              if (data9 !== null) {
                                const err19 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                if (vErrors === null) {
                                  vErrors = [err19];
                                } else {
                                  vErrors.push(err19);
                                }
                                errors++;
                              }
                              var _valid6 = _errs48 === errors;
                              valid7 = valid7 || _valid6;
                              if (!valid7) {
                                const err20 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                if (vErrors === null) {
                                  vErrors = [err20];
                                } else {
                                  vErrors.push(err20);
                                }
                                errors++;
                                validate370.errors = vErrors;
                                return false;
                              } else {
                                errors = _errs45;
                                if (vErrors !== null) {
                                  if (_errs45) {
                                    vErrors.length = _errs45;
                                  } else {
                                    vErrors = null;
                                  }
                                }
                              }
                              var valid0 = _errs44 === errors;
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
      validate370.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate370.errors = vErrors;
  return errors === 0;
}
validate370.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate372(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate372.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.model === void 0 && (missing0 = "model") || data.chain === void 0 && (missing0 = "chain") || data.residue_number === void 0 && (missing0 = "residue_number") || data.insertion_code === void 0 && (missing0 = "insertion_code") || data.residue_name === void 0 && (missing0 = "residue_name")) {
        validate372.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "model" || key0 === "chain" || key0 === "residue_number" || key0 === "insertion_code" || key0 === "residue_name")) {
            validate372.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.model !== void 0) {
            const _errs2 = errors;
            if (typeof data.model !== "string") {
              validate372.errors = [{ instancePath: instancePath + "/model", schemaPath: "#/properties/model/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.chain !== void 0) {
              const _errs4 = errors;
              if (typeof data.chain !== "string") {
                validate372.errors = [{ instancePath: instancePath + "/chain", schemaPath: "#/properties/chain/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.residue_number !== void 0) {
                const _errs6 = errors;
                if (typeof data.residue_number !== "string") {
                  validate372.errors = [{ instancePath: instancePath + "/residue_number", schemaPath: "#/properties/residue_number/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.insertion_code !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.insertion_code !== "string") {
                    validate372.errors = [{ instancePath: instancePath + "/insertion_code", schemaPath: "#/properties/insertion_code/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.residue_name !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.residue_name !== "string") {
                      validate372.errors = [{ instancePath: instancePath + "/residue_name", schemaPath: "#/properties/residue_name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
      validate372.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate372.errors = vErrors;
  return errors === 0;
}
validate372.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema168 = { "additionalProperties": false, "properties": { "residue": { "$ref": "#/$defs/ResidueIdentity" }, "full_fusion_position": { "anyOf": [{ "minimum": 1, "type": "integer" }, { "type": "null" }], "default": null, "title": "Full Fusion Position" }, "region": { "anyOf": [{ "enum": ["enzyme", "scaffold", "idr", "linker", "ligand_tail", "tag"], "type": "string" }, { "type": "null" }], "default": null, "title": "Region" }, "reference_residue": { "anyOf": [{ "$ref": "#/$defs/ResidueIdentity" }, { "type": "null" }], "default": null }, "reference_sha256": { "anyOf": [{ "pattern": "^[0-9a-f]{64}$", "type": "string" }, { "type": "null" }], "default": null, "title": "Reference Sha256" }, "pocket": { "default": false, "title": "Pocket", "type": "boolean" }, "clash": { "default": false, "title": "Clash", "type": "boolean" }, "plddt": { "anyOf": [{ "maximum": 100, "minimum": 0, "type": "number" }, { "type": "null" }], "default": null, "title": "Plddt" }, "reference_file_id": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Reference File Id" } }, "required": ["residue", "full_fusion_position", "region", "reference_residue", "reference_sha256", "pocket", "clash", "plddt", "reference_file_id"], "title": "DisplayResidueAnnotation", "type": "object" };
function validate375(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate375.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.model === void 0 && (missing0 = "model") || data.chain === void 0 && (missing0 = "chain") || data.residue_number === void 0 && (missing0 = "residue_number") || data.insertion_code === void 0 && (missing0 = "insertion_code") || data.residue_name === void 0 && (missing0 = "residue_name")) {
        validate375.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "model" || key0 === "chain" || key0 === "residue_number" || key0 === "insertion_code" || key0 === "residue_name")) {
            validate375.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.model !== void 0) {
            const _errs2 = errors;
            if (typeof data.model !== "string") {
              validate375.errors = [{ instancePath: instancePath + "/model", schemaPath: "#/properties/model/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.chain !== void 0) {
              const _errs4 = errors;
              if (typeof data.chain !== "string") {
                validate375.errors = [{ instancePath: instancePath + "/chain", schemaPath: "#/properties/chain/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.residue_number !== void 0) {
                const _errs6 = errors;
                if (typeof data.residue_number !== "string") {
                  validate375.errors = [{ instancePath: instancePath + "/residue_number", schemaPath: "#/properties/residue_number/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.insertion_code !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.insertion_code !== "string") {
                    validate375.errors = [{ instancePath: instancePath + "/insertion_code", schemaPath: "#/properties/insertion_code/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.residue_name !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.residue_name !== "string") {
                      validate375.errors = [{ instancePath: instancePath + "/residue_name", schemaPath: "#/properties/residue_name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
      validate375.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate375.errors = vErrors;
  return errors === 0;
}
validate375.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate374(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate374.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.residue === void 0 && (missing0 = "residue") || data.full_fusion_position === void 0 && (missing0 = "full_fusion_position") || data.region === void 0 && (missing0 = "region") || data.reference_residue === void 0 && (missing0 = "reference_residue") || data.reference_sha256 === void 0 && (missing0 = "reference_sha256") || data.pocket === void 0 && (missing0 = "pocket") || data.clash === void 0 && (missing0 = "clash") || data.plddt === void 0 && (missing0 = "plddt") || data.reference_file_id === void 0 && (missing0 = "reference_file_id")) {
        validate374.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema168.properties, key0)) {
            validate374.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.residue !== void 0) {
            const _errs2 = errors;
            if (!validate375(data.residue, { instancePath: instancePath + "/residue", parentData: data, parentDataProperty: "residue", rootData, dynamicAnchors })) {
              vErrors = vErrors === null ? validate375.errors : vErrors.concat(validate375.errors);
              errors = vErrors.length;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.full_fusion_position !== void 0) {
              let data1 = data.full_fusion_position;
              const _errs3 = errors;
              const _errs4 = errors;
              let valid1 = false;
              const _errs5 = errors;
              if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)))) {
                const err0 = { instancePath: instancePath + "/full_fusion_position", schemaPath: "#/properties/full_fusion_position/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                if (vErrors === null) {
                  vErrors = [err0];
                } else {
                  vErrors.push(err0);
                }
                errors++;
              }
              if (errors === _errs5) {
                if (typeof data1 == "number") {
                  if (data1 < 1 || isNaN(data1)) {
                    const err1 = { instancePath: instancePath + "/full_fusion_position", schemaPath: "#/properties/full_fusion_position/anyOf/0/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                  }
                }
              }
              var _valid0 = _errs5 === errors;
              valid1 = valid1 || _valid0;
              const _errs7 = errors;
              if (data1 !== null) {
                const err2 = { instancePath: instancePath + "/full_fusion_position", schemaPath: "#/properties/full_fusion_position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                if (vErrors === null) {
                  vErrors = [err2];
                } else {
                  vErrors.push(err2);
                }
                errors++;
              }
              var _valid0 = _errs7 === errors;
              valid1 = valid1 || _valid0;
              if (!valid1) {
                const err3 = { instancePath: instancePath + "/full_fusion_position", schemaPath: "#/properties/full_fusion_position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                if (vErrors === null) {
                  vErrors = [err3];
                } else {
                  vErrors.push(err3);
                }
                errors++;
                validate374.errors = vErrors;
                return false;
              } else {
                errors = _errs4;
                if (vErrors !== null) {
                  if (_errs4) {
                    vErrors.length = _errs4;
                  } else {
                    vErrors = null;
                  }
                }
              }
              var valid0 = _errs3 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.region !== void 0) {
                let data2 = data.region;
                const _errs9 = errors;
                const _errs10 = errors;
                let valid2 = false;
                const _errs11 = errors;
                if (typeof data2 !== "string") {
                  const err4 = { instancePath: instancePath + "/region", schemaPath: "#/properties/region/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                  if (vErrors === null) {
                    vErrors = [err4];
                  } else {
                    vErrors.push(err4);
                  }
                  errors++;
                }
                if (!(data2 === "enzyme" || data2 === "scaffold" || data2 === "idr" || data2 === "linker" || data2 === "ligand_tail" || data2 === "tag")) {
                  const err5 = { instancePath: instancePath + "/region", schemaPath: "#/properties/region/anyOf/0/enum", keyword: "enum", params: { allowedValues: schema168.properties.region.anyOf[0].enum }, message: "must be equal to one of the allowed values" };
                  if (vErrors === null) {
                    vErrors = [err5];
                  } else {
                    vErrors.push(err5);
                  }
                  errors++;
                }
                var _valid1 = _errs11 === errors;
                valid2 = valid2 || _valid1;
                const _errs13 = errors;
                if (data2 !== null) {
                  const err6 = { instancePath: instancePath + "/region", schemaPath: "#/properties/region/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err6];
                  } else {
                    vErrors.push(err6);
                  }
                  errors++;
                }
                var _valid1 = _errs13 === errors;
                valid2 = valid2 || _valid1;
                if (!valid2) {
                  const err7 = { instancePath: instancePath + "/region", schemaPath: "#/properties/region/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err7];
                  } else {
                    vErrors.push(err7);
                  }
                  errors++;
                  validate374.errors = vErrors;
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
                var valid0 = _errs9 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.reference_residue !== void 0) {
                  let data3 = data.reference_residue;
                  const _errs15 = errors;
                  const _errs16 = errors;
                  let valid3 = false;
                  const _errs17 = errors;
                  if (!validate375(data3, { instancePath: instancePath + "/reference_residue", parentData: data, parentDataProperty: "reference_residue", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate375.errors : vErrors.concat(validate375.errors);
                    errors = vErrors.length;
                  }
                  var _valid2 = _errs17 === errors;
                  valid3 = valid3 || _valid2;
                  const _errs18 = errors;
                  if (data3 !== null) {
                    const err8 = { instancePath: instancePath + "/reference_residue", schemaPath: "#/properties/reference_residue/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err8];
                    } else {
                      vErrors.push(err8);
                    }
                    errors++;
                  }
                  var _valid2 = _errs18 === errors;
                  valid3 = valid3 || _valid2;
                  if (!valid3) {
                    const err9 = { instancePath: instancePath + "/reference_residue", schemaPath: "#/properties/reference_residue/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err9];
                    } else {
                      vErrors.push(err9);
                    }
                    errors++;
                    validate374.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs16;
                    if (vErrors !== null) {
                      if (_errs16) {
                        vErrors.length = _errs16;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs15 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.reference_sha256 !== void 0) {
                    let data4 = data.reference_sha256;
                    const _errs20 = errors;
                    const _errs21 = errors;
                    let valid4 = false;
                    const _errs22 = errors;
                    if (errors === _errs22) {
                      if (typeof data4 === "string") {
                        if (!pattern4.test(data4)) {
                          const err10 = { instancePath: instancePath + "/reference_sha256", schemaPath: "#/properties/reference_sha256/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                          if (vErrors === null) {
                            vErrors = [err10];
                          } else {
                            vErrors.push(err10);
                          }
                          errors++;
                        }
                      } else {
                        const err11 = { instancePath: instancePath + "/reference_sha256", schemaPath: "#/properties/reference_sha256/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err11];
                        } else {
                          vErrors.push(err11);
                        }
                        errors++;
                      }
                    }
                    var _valid3 = _errs22 === errors;
                    valid4 = valid4 || _valid3;
                    const _errs24 = errors;
                    if (data4 !== null) {
                      const err12 = { instancePath: instancePath + "/reference_sha256", schemaPath: "#/properties/reference_sha256/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err12];
                      } else {
                        vErrors.push(err12);
                      }
                      errors++;
                    }
                    var _valid3 = _errs24 === errors;
                    valid4 = valid4 || _valid3;
                    if (!valid4) {
                      const err13 = { instancePath: instancePath + "/reference_sha256", schemaPath: "#/properties/reference_sha256/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err13];
                      } else {
                        vErrors.push(err13);
                      }
                      errors++;
                      validate374.errors = vErrors;
                      return false;
                    } else {
                      errors = _errs21;
                      if (vErrors !== null) {
                        if (_errs21) {
                          vErrors.length = _errs21;
                        } else {
                          vErrors = null;
                        }
                      }
                    }
                    var valid0 = _errs20 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.pocket !== void 0) {
                      const _errs26 = errors;
                      if (typeof data.pocket !== "boolean") {
                        validate374.errors = [{ instancePath: instancePath + "/pocket", schemaPath: "#/properties/pocket/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                        return false;
                      }
                      var valid0 = _errs26 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.clash !== void 0) {
                        const _errs28 = errors;
                        if (typeof data.clash !== "boolean") {
                          validate374.errors = [{ instancePath: instancePath + "/clash", schemaPath: "#/properties/clash/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                          return false;
                        }
                        var valid0 = _errs28 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.plddt !== void 0) {
                          let data7 = data.plddt;
                          const _errs30 = errors;
                          const _errs31 = errors;
                          let valid5 = false;
                          const _errs32 = errors;
                          if (errors === _errs32) {
                            if (typeof data7 == "number") {
                              if (data7 > 100 || isNaN(data7)) {
                                const err14 = { instancePath: instancePath + "/plddt", schemaPath: "#/properties/plddt/anyOf/0/maximum", keyword: "maximum", params: { comparison: "<=", limit: 100 }, message: "must be <= 100" };
                                if (vErrors === null) {
                                  vErrors = [err14];
                                } else {
                                  vErrors.push(err14);
                                }
                                errors++;
                              } else {
                                if (data7 < 0 || isNaN(data7)) {
                                  const err15 = { instancePath: instancePath + "/plddt", schemaPath: "#/properties/plddt/anyOf/0/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                  if (vErrors === null) {
                                    vErrors = [err15];
                                  } else {
                                    vErrors.push(err15);
                                  }
                                  errors++;
                                }
                              }
                            } else {
                              const err16 = { instancePath: instancePath + "/plddt", schemaPath: "#/properties/plddt/anyOf/0/type", keyword: "type", params: { type: "number" }, message: "must be number" };
                              if (vErrors === null) {
                                vErrors = [err16];
                              } else {
                                vErrors.push(err16);
                              }
                              errors++;
                            }
                          }
                          var _valid4 = _errs32 === errors;
                          valid5 = valid5 || _valid4;
                          const _errs34 = errors;
                          if (data7 !== null) {
                            const err17 = { instancePath: instancePath + "/plddt", schemaPath: "#/properties/plddt/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err17];
                            } else {
                              vErrors.push(err17);
                            }
                            errors++;
                          }
                          var _valid4 = _errs34 === errors;
                          valid5 = valid5 || _valid4;
                          if (!valid5) {
                            const err18 = { instancePath: instancePath + "/plddt", schemaPath: "#/properties/plddt/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err18];
                            } else {
                              vErrors.push(err18);
                            }
                            errors++;
                            validate374.errors = vErrors;
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
                          if (data.reference_file_id !== void 0) {
                            let data8 = data.reference_file_id;
                            const _errs36 = errors;
                            const _errs37 = errors;
                            let valid6 = false;
                            const _errs38 = errors;
                            if (typeof data8 !== "string") {
                              const err19 = { instancePath: instancePath + "/reference_file_id", schemaPath: "#/properties/reference_file_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err19];
                              } else {
                                vErrors.push(err19);
                              }
                              errors++;
                            }
                            var _valid5 = _errs38 === errors;
                            valid6 = valid6 || _valid5;
                            const _errs40 = errors;
                            if (data8 !== null) {
                              const err20 = { instancePath: instancePath + "/reference_file_id", schemaPath: "#/properties/reference_file_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err20];
                              } else {
                                vErrors.push(err20);
                              }
                              errors++;
                            }
                            var _valid5 = _errs40 === errors;
                            valid6 = valid6 || _valid5;
                            if (!valid6) {
                              const err21 = { instancePath: instancePath + "/reference_file_id", schemaPath: "#/properties/reference_file_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err21];
                              } else {
                                vErrors.push(err21);
                              }
                              errors++;
                              validate374.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs37;
                              if (vErrors !== null) {
                                if (_errs37) {
                                  vErrors.length = _errs37;
                                } else {
                                  vErrors = null;
                                }
                              }
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
    } else {
      validate374.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate374.errors = vErrors;
  return errors === 0;
}
validate374.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema170 = { "additionalProperties": false, "properties": { "reference_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Reference Sha256", "type": "string" }, "source_reference": { "minLength": 1, "title": "Source Reference", "type": "string" }, "source_tool": { "minLength": 1, "title": "Source Tool", "type": "string" }, "source_tool_version": { "minLength": 1, "title": "Source Tool Version", "type": "string" }, "direction": { "const": "reference_to_target", "title": "Direction", "type": "string" }, "coordinate_unit": { "const": "angstrom", "title": "Coordinate Unit", "type": "string" }, "convention": { "const": "row_major_column_vector_xyz1", "title": "Convention", "type": "string" }, "matrix": { "items": { "items": { "type": "number" }, "type": "array" }, "title": "Matrix", "type": "array" }, "reference_file_id": { "title": "Reference File Id", "type": "string" }, "target_sha256": { "title": "Target Sha256", "type": "string" } }, "required": ["reference_sha256", "source_reference", "source_tool", "source_tool_version", "direction", "coordinate_unit", "convention", "matrix", "reference_file_id", "target_sha256"], "title": "DisplayOverlay", "type": "object" };
function validate379(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate379.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.reference_sha256 === void 0 && (missing0 = "reference_sha256") || data.source_reference === void 0 && (missing0 = "source_reference") || data.source_tool === void 0 && (missing0 = "source_tool") || data.source_tool_version === void 0 && (missing0 = "source_tool_version") || data.direction === void 0 && (missing0 = "direction") || data.coordinate_unit === void 0 && (missing0 = "coordinate_unit") || data.convention === void 0 && (missing0 = "convention") || data.matrix === void 0 && (missing0 = "matrix") || data.reference_file_id === void 0 && (missing0 = "reference_file_id") || data.target_sha256 === void 0 && (missing0 = "target_sha256")) {
        validate379.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema170.properties, key0)) {
            validate379.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.reference_sha256 !== void 0) {
            let data0 = data.reference_sha256;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (typeof data0 === "string") {
                if (!pattern4.test(data0)) {
                  validate379.errors = [{ instancePath: instancePath + "/reference_sha256", schemaPath: "#/properties/reference_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                  return false;
                }
              } else {
                validate379.errors = [{ instancePath: instancePath + "/reference_sha256", schemaPath: "#/properties/reference_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.source_reference !== void 0) {
              let data1 = data.source_reference;
              const _errs4 = errors;
              if (errors === _errs4) {
                if (typeof data1 === "string") {
                  if (func2(data1) < 1) {
                    validate379.errors = [{ instancePath: instancePath + "/source_reference", schemaPath: "#/properties/source_reference/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                    return false;
                  }
                } else {
                  validate379.errors = [{ instancePath: instancePath + "/source_reference", schemaPath: "#/properties/source_reference/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.source_tool !== void 0) {
                let data2 = data.source_tool;
                const _errs6 = errors;
                if (errors === _errs6) {
                  if (typeof data2 === "string") {
                    if (func2(data2) < 1) {
                      validate379.errors = [{ instancePath: instancePath + "/source_tool", schemaPath: "#/properties/source_tool/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                      return false;
                    }
                  } else {
                    validate379.errors = [{ instancePath: instancePath + "/source_tool", schemaPath: "#/properties/source_tool/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.source_tool_version !== void 0) {
                  let data3 = data.source_tool_version;
                  const _errs8 = errors;
                  if (errors === _errs8) {
                    if (typeof data3 === "string") {
                      if (func2(data3) < 1) {
                        validate379.errors = [{ instancePath: instancePath + "/source_tool_version", schemaPath: "#/properties/source_tool_version/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      }
                    } else {
                      validate379.errors = [{ instancePath: instancePath + "/source_tool_version", schemaPath: "#/properties/source_tool_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.direction !== void 0) {
                    let data4 = data.direction;
                    const _errs10 = errors;
                    if (typeof data4 !== "string") {
                      validate379.errors = [{ instancePath: instancePath + "/direction", schemaPath: "#/properties/direction/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("reference_to_target" !== data4) {
                      validate379.errors = [{ instancePath: instancePath + "/direction", schemaPath: "#/properties/direction/const", keyword: "const", params: { allowedValue: "reference_to_target" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.coordinate_unit !== void 0) {
                      let data5 = data.coordinate_unit;
                      const _errs12 = errors;
                      if (typeof data5 !== "string") {
                        validate379.errors = [{ instancePath: instancePath + "/coordinate_unit", schemaPath: "#/properties/coordinate_unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("angstrom" !== data5) {
                        validate379.errors = [{ instancePath: instancePath + "/coordinate_unit", schemaPath: "#/properties/coordinate_unit/const", keyword: "const", params: { allowedValue: "angstrom" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.convention !== void 0) {
                        let data6 = data.convention;
                        const _errs14 = errors;
                        if (typeof data6 !== "string") {
                          validate379.errors = [{ instancePath: instancePath + "/convention", schemaPath: "#/properties/convention/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("row_major_column_vector_xyz1" !== data6) {
                          validate379.errors = [{ instancePath: instancePath + "/convention", schemaPath: "#/properties/convention/const", keyword: "const", params: { allowedValue: "row_major_column_vector_xyz1" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.matrix !== void 0) {
                          let data7 = data.matrix;
                          const _errs16 = errors;
                          if (errors === _errs16) {
                            if (Array.isArray(data7)) {
                              var valid1 = true;
                              const len0 = data7.length;
                              for (let i0 = 0; i0 < len0; i0++) {
                                let data8 = data7[i0];
                                const _errs18 = errors;
                                if (errors === _errs18) {
                                  if (Array.isArray(data8)) {
                                    var valid2 = true;
                                    const len1 = data8.length;
                                    for (let i1 = 0; i1 < len1; i1++) {
                                      const _errs20 = errors;
                                      if (!(typeof data8[i1] == "number")) {
                                        validate379.errors = [{ instancePath: instancePath + "/matrix/" + i0 + "/" + i1, schemaPath: "#/properties/matrix/items/items/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                        return false;
                                      }
                                      var valid2 = _errs20 === errors;
                                      if (!valid2) {
                                        break;
                                      }
                                    }
                                  } else {
                                    validate379.errors = [{ instancePath: instancePath + "/matrix/" + i0, schemaPath: "#/properties/matrix/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                    return false;
                                  }
                                }
                                var valid1 = _errs18 === errors;
                                if (!valid1) {
                                  break;
                                }
                              }
                            } else {
                              validate379.errors = [{ instancePath: instancePath + "/matrix", schemaPath: "#/properties/matrix/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.reference_file_id !== void 0) {
                            const _errs22 = errors;
                            if (typeof data.reference_file_id !== "string") {
                              validate379.errors = [{ instancePath: instancePath + "/reference_file_id", schemaPath: "#/properties/reference_file_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid0 = _errs22 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.target_sha256 !== void 0) {
                              const _errs24 = errors;
                              if (typeof data.target_sha256 !== "string") {
                                validate379.errors = [{ instancePath: instancePath + "/target_sha256", schemaPath: "#/properties/target_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid0 = _errs24 === errors;
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
      validate379.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate379.errors = vErrors;
  return errors === 0;
}
validate379.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate369(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate369.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.schema_version === void 0 && (missing0 = "schema_version") || data.identity === void 0 && (missing0 = "identity") || data.format === void 0 && (missing0 = "format") || data.offset === void 0 && (missing0 = "offset") || data.total === void 0 && (missing0 = "total") || data.chains === void 0 && (missing0 = "chains") || data.models === void 0 && (missing0 = "models") || data.residues === void 0 && (missing0 = "residues") || data.confidence_status === void 0 && (missing0 = "confidence_status") || data.mapping_status === void 0 && (missing0 = "mapping_status") || data.pocket_status === void 0 && (missing0 = "pocket_status") || data.annotation_file_id === void 0 && (missing0 = "annotation_file_id") || data.annotation_sha256 === void 0 && (missing0 = "annotation_sha256") || data.annotation_source_reference === void 0 && (missing0 = "annotation_source_reference") || data.annotation_source_tool === void 0 && (missing0 = "annotation_source_tool") || data.annotation_source_tool_version === void 0 && (missing0 = "annotation_source_tool_version") || data.fusion_sequence_file_id === void 0 && (missing0 = "fusion_sequence_file_id") || data.fusion_sequence_file_sha256 === void 0 && (missing0 = "fusion_sequence_file_sha256") || data.fusion_sequence_id === void 0 && (missing0 = "fusion_sequence_id") || data.annotations === void 0 && (missing0 = "annotations") || data.annotation_scope === void 0 && (missing0 = "annotation_scope") || data.overlays === void 0 && (missing0 = "overlays") || data.preview_policy === void 0 && (missing0 = "preview_policy")) {
        validate369.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema165.properties, key0)) {
            validate369.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.schema_version !== void 0) {
            let data0 = data.schema_version;
            const _errs2 = errors;
            if (typeof data0 !== "string") {
              validate369.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            if ("display-structure-v1" !== data0) {
              validate369.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "display-structure-v1" }, message: "must be equal to constant" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.identity !== void 0) {
              const _errs4 = errors;
              if (!validate370(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
                vErrors = vErrors === null ? validate370.errors : vErrors.concat(validate370.errors);
                errors = vErrors.length;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.format !== void 0) {
                const _errs5 = errors;
                if (typeof data.format !== "string") {
                  validate369.errors = [{ instancePath: instancePath + "/format", schemaPath: "#/properties/format/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs5 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.offset !== void 0) {
                  let data3 = data.offset;
                  const _errs7 = errors;
                  if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)))) {
                    validate369.errors = [{ instancePath: instancePath + "/offset", schemaPath: "#/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.total !== void 0) {
                    let data4 = data.total;
                    const _errs9 = errors;
                    if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)))) {
                      validate369.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.chains !== void 0) {
                      let data5 = data.chains;
                      const _errs11 = errors;
                      if (errors === _errs11) {
                        if (Array.isArray(data5)) {
                          var valid1 = true;
                          const len0 = data5.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs13 = errors;
                            if (typeof data5[i0] !== "string") {
                              validate369.errors = [{ instancePath: instancePath + "/chains/" + i0, schemaPath: "#/properties/chains/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid1 = _errs13 === errors;
                            if (!valid1) {
                              break;
                            }
                          }
                        } else {
                          validate369.errors = [{ instancePath: instancePath + "/chains", schemaPath: "#/properties/chains/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs11 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.models !== void 0) {
                        let data7 = data.models;
                        const _errs15 = errors;
                        if (errors === _errs15) {
                          if (Array.isArray(data7)) {
                            var valid2 = true;
                            const len1 = data7.length;
                            for (let i1 = 0; i1 < len1; i1++) {
                              const _errs17 = errors;
                              if (typeof data7[i1] !== "string") {
                                validate369.errors = [{ instancePath: instancePath + "/models/" + i1, schemaPath: "#/properties/models/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid2 = _errs17 === errors;
                              if (!valid2) {
                                break;
                              }
                            }
                          } else {
                            validate369.errors = [{ instancePath: instancePath + "/models", schemaPath: "#/properties/models/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs15 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.residues !== void 0) {
                          let data9 = data.residues;
                          const _errs19 = errors;
                          if (errors === _errs19) {
                            if (Array.isArray(data9)) {
                              var valid3 = true;
                              const len2 = data9.length;
                              for (let i2 = 0; i2 < len2; i2++) {
                                const _errs21 = errors;
                                if (!validate372(data9[i2], { instancePath: instancePath + "/residues/" + i2, parentData: data9, parentDataProperty: i2, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate372.errors : vErrors.concat(validate372.errors);
                                  errors = vErrors.length;
                                }
                                var valid3 = _errs21 === errors;
                                if (!valid3) {
                                  break;
                                }
                              }
                            } else {
                              validate369.errors = [{ instancePath: instancePath + "/residues", schemaPath: "#/properties/residues/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs19 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.confidence_status !== void 0) {
                            let data11 = data.confidence_status;
                            const _errs22 = errors;
                            if (typeof data11 !== "string") {
                              validate369.errors = [{ instancePath: instancePath + "/confidence_status", schemaPath: "#/properties/confidence_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if (!(data11 === "not_registered" || data11 === "source_registered_not_scientific_approval")) {
                              validate369.errors = [{ instancePath: instancePath + "/confidence_status", schemaPath: "#/properties/confidence_status/enum", keyword: "enum", params: { allowedValues: schema165.properties.confidence_status.enum }, message: "must be equal to one of the allowed values" }];
                              return false;
                            }
                            var valid0 = _errs22 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.mapping_status !== void 0) {
                              let data12 = data.mapping_status;
                              const _errs24 = errors;
                              if (typeof data12 !== "string") {
                                validate369.errors = [{ instancePath: instancePath + "/mapping_status", schemaPath: "#/properties/mapping_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if (!(data12 === "not_registered" || data12 === "source_registered_not_scientific_approval")) {
                                validate369.errors = [{ instancePath: instancePath + "/mapping_status", schemaPath: "#/properties/mapping_status/enum", keyword: "enum", params: { allowedValues: schema165.properties.mapping_status.enum }, message: "must be equal to one of the allowed values" }];
                                return false;
                              }
                              var valid0 = _errs24 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.pocket_status !== void 0) {
                                let data13 = data.pocket_status;
                                const _errs26 = errors;
                                if (typeof data13 !== "string") {
                                  validate369.errors = [{ instancePath: instancePath + "/pocket_status", schemaPath: "#/properties/pocket_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if (!(data13 === "not_registered" || data13 === "source_registered_not_scientific_approval")) {
                                  validate369.errors = [{ instancePath: instancePath + "/pocket_status", schemaPath: "#/properties/pocket_status/enum", keyword: "enum", params: { allowedValues: schema165.properties.pocket_status.enum }, message: "must be equal to one of the allowed values" }];
                                  return false;
                                }
                                var valid0 = _errs26 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.annotation_file_id !== void 0) {
                                  let data14 = data.annotation_file_id;
                                  const _errs28 = errors;
                                  const _errs29 = errors;
                                  let valid4 = false;
                                  const _errs30 = errors;
                                  if (typeof data14 !== "string") {
                                    const err0 = { instancePath: instancePath + "/annotation_file_id", schemaPath: "#/properties/annotation_file_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err0];
                                    } else {
                                      vErrors.push(err0);
                                    }
                                    errors++;
                                  }
                                  var _valid0 = _errs30 === errors;
                                  valid4 = valid4 || _valid0;
                                  const _errs32 = errors;
                                  if (data14 !== null) {
                                    const err1 = { instancePath: instancePath + "/annotation_file_id", schemaPath: "#/properties/annotation_file_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                    if (vErrors === null) {
                                      vErrors = [err1];
                                    } else {
                                      vErrors.push(err1);
                                    }
                                    errors++;
                                  }
                                  var _valid0 = _errs32 === errors;
                                  valid4 = valid4 || _valid0;
                                  if (!valid4) {
                                    const err2 = { instancePath: instancePath + "/annotation_file_id", schemaPath: "#/properties/annotation_file_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                    if (vErrors === null) {
                                      vErrors = [err2];
                                    } else {
                                      vErrors.push(err2);
                                    }
                                    errors++;
                                    validate369.errors = vErrors;
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
                                  if (data.annotation_sha256 !== void 0) {
                                    let data15 = data.annotation_sha256;
                                    const _errs34 = errors;
                                    const _errs35 = errors;
                                    let valid5 = false;
                                    const _errs36 = errors;
                                    if (typeof data15 !== "string") {
                                      const err3 = { instancePath: instancePath + "/annotation_sha256", schemaPath: "#/properties/annotation_sha256/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err3];
                                      } else {
                                        vErrors.push(err3);
                                      }
                                      errors++;
                                    }
                                    var _valid1 = _errs36 === errors;
                                    valid5 = valid5 || _valid1;
                                    const _errs38 = errors;
                                    if (data15 !== null) {
                                      const err4 = { instancePath: instancePath + "/annotation_sha256", schemaPath: "#/properties/annotation_sha256/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                      if (vErrors === null) {
                                        vErrors = [err4];
                                      } else {
                                        vErrors.push(err4);
                                      }
                                      errors++;
                                    }
                                    var _valid1 = _errs38 === errors;
                                    valid5 = valid5 || _valid1;
                                    if (!valid5) {
                                      const err5 = { instancePath: instancePath + "/annotation_sha256", schemaPath: "#/properties/annotation_sha256/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                      if (vErrors === null) {
                                        vErrors = [err5];
                                      } else {
                                        vErrors.push(err5);
                                      }
                                      errors++;
                                      validate369.errors = vErrors;
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
                                    if (data.annotation_source_reference !== void 0) {
                                      let data16 = data.annotation_source_reference;
                                      const _errs40 = errors;
                                      const _errs41 = errors;
                                      let valid6 = false;
                                      const _errs42 = errors;
                                      if (typeof data16 !== "string") {
                                        const err6 = { instancePath: instancePath + "/annotation_source_reference", schemaPath: "#/properties/annotation_source_reference/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err6];
                                        } else {
                                          vErrors.push(err6);
                                        }
                                        errors++;
                                      }
                                      var _valid2 = _errs42 === errors;
                                      valid6 = valid6 || _valid2;
                                      const _errs44 = errors;
                                      if (data16 !== null) {
                                        const err7 = { instancePath: instancePath + "/annotation_source_reference", schemaPath: "#/properties/annotation_source_reference/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                        if (vErrors === null) {
                                          vErrors = [err7];
                                        } else {
                                          vErrors.push(err7);
                                        }
                                        errors++;
                                      }
                                      var _valid2 = _errs44 === errors;
                                      valid6 = valid6 || _valid2;
                                      if (!valid6) {
                                        const err8 = { instancePath: instancePath + "/annotation_source_reference", schemaPath: "#/properties/annotation_source_reference/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                        if (vErrors === null) {
                                          vErrors = [err8];
                                        } else {
                                          vErrors.push(err8);
                                        }
                                        errors++;
                                        validate369.errors = vErrors;
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
                                      if (data.annotation_source_tool !== void 0) {
                                        let data17 = data.annotation_source_tool;
                                        const _errs46 = errors;
                                        const _errs47 = errors;
                                        let valid7 = false;
                                        const _errs48 = errors;
                                        if (typeof data17 !== "string") {
                                          const err9 = { instancePath: instancePath + "/annotation_source_tool", schemaPath: "#/properties/annotation_source_tool/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err9];
                                          } else {
                                            vErrors.push(err9);
                                          }
                                          errors++;
                                        }
                                        var _valid3 = _errs48 === errors;
                                        valid7 = valid7 || _valid3;
                                        const _errs50 = errors;
                                        if (data17 !== null) {
                                          const err10 = { instancePath: instancePath + "/annotation_source_tool", schemaPath: "#/properties/annotation_source_tool/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                          if (vErrors === null) {
                                            vErrors = [err10];
                                          } else {
                                            vErrors.push(err10);
                                          }
                                          errors++;
                                        }
                                        var _valid3 = _errs50 === errors;
                                        valid7 = valid7 || _valid3;
                                        if (!valid7) {
                                          const err11 = { instancePath: instancePath + "/annotation_source_tool", schemaPath: "#/properties/annotation_source_tool/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                          if (vErrors === null) {
                                            vErrors = [err11];
                                          } else {
                                            vErrors.push(err11);
                                          }
                                          errors++;
                                          validate369.errors = vErrors;
                                          return false;
                                        } else {
                                          errors = _errs47;
                                          if (vErrors !== null) {
                                            if (_errs47) {
                                              vErrors.length = _errs47;
                                            } else {
                                              vErrors = null;
                                            }
                                          }
                                        }
                                        var valid0 = _errs46 === errors;
                                      } else {
                                        var valid0 = true;
                                      }
                                      if (valid0) {
                                        if (data.annotation_source_tool_version !== void 0) {
                                          let data18 = data.annotation_source_tool_version;
                                          const _errs52 = errors;
                                          const _errs53 = errors;
                                          let valid8 = false;
                                          const _errs54 = errors;
                                          if (typeof data18 !== "string") {
                                            const err12 = { instancePath: instancePath + "/annotation_source_tool_version", schemaPath: "#/properties/annotation_source_tool_version/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                            if (vErrors === null) {
                                              vErrors = [err12];
                                            } else {
                                              vErrors.push(err12);
                                            }
                                            errors++;
                                          }
                                          var _valid4 = _errs54 === errors;
                                          valid8 = valid8 || _valid4;
                                          const _errs56 = errors;
                                          if (data18 !== null) {
                                            const err13 = { instancePath: instancePath + "/annotation_source_tool_version", schemaPath: "#/properties/annotation_source_tool_version/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                            if (vErrors === null) {
                                              vErrors = [err13];
                                            } else {
                                              vErrors.push(err13);
                                            }
                                            errors++;
                                          }
                                          var _valid4 = _errs56 === errors;
                                          valid8 = valid8 || _valid4;
                                          if (!valid8) {
                                            const err14 = { instancePath: instancePath + "/annotation_source_tool_version", schemaPath: "#/properties/annotation_source_tool_version/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                            if (vErrors === null) {
                                              vErrors = [err14];
                                            } else {
                                              vErrors.push(err14);
                                            }
                                            errors++;
                                            validate369.errors = vErrors;
                                            return false;
                                          } else {
                                            errors = _errs53;
                                            if (vErrors !== null) {
                                              if (_errs53) {
                                                vErrors.length = _errs53;
                                              } else {
                                                vErrors = null;
                                              }
                                            }
                                          }
                                          var valid0 = _errs52 === errors;
                                        } else {
                                          var valid0 = true;
                                        }
                                        if (valid0) {
                                          if (data.fusion_sequence_file_id !== void 0) {
                                            let data19 = data.fusion_sequence_file_id;
                                            const _errs58 = errors;
                                            const _errs59 = errors;
                                            let valid9 = false;
                                            const _errs60 = errors;
                                            if (typeof data19 !== "string") {
                                              const err15 = { instancePath: instancePath + "/fusion_sequence_file_id", schemaPath: "#/properties/fusion_sequence_file_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                              if (vErrors === null) {
                                                vErrors = [err15];
                                              } else {
                                                vErrors.push(err15);
                                              }
                                              errors++;
                                            }
                                            var _valid5 = _errs60 === errors;
                                            valid9 = valid9 || _valid5;
                                            const _errs62 = errors;
                                            if (data19 !== null) {
                                              const err16 = { instancePath: instancePath + "/fusion_sequence_file_id", schemaPath: "#/properties/fusion_sequence_file_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                              if (vErrors === null) {
                                                vErrors = [err16];
                                              } else {
                                                vErrors.push(err16);
                                              }
                                              errors++;
                                            }
                                            var _valid5 = _errs62 === errors;
                                            valid9 = valid9 || _valid5;
                                            if (!valid9) {
                                              const err17 = { instancePath: instancePath + "/fusion_sequence_file_id", schemaPath: "#/properties/fusion_sequence_file_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                              if (vErrors === null) {
                                                vErrors = [err17];
                                              } else {
                                                vErrors.push(err17);
                                              }
                                              errors++;
                                              validate369.errors = vErrors;
                                              return false;
                                            } else {
                                              errors = _errs59;
                                              if (vErrors !== null) {
                                                if (_errs59) {
                                                  vErrors.length = _errs59;
                                                } else {
                                                  vErrors = null;
                                                }
                                              }
                                            }
                                            var valid0 = _errs58 === errors;
                                          } else {
                                            var valid0 = true;
                                          }
                                          if (valid0) {
                                            if (data.fusion_sequence_file_sha256 !== void 0) {
                                              let data20 = data.fusion_sequence_file_sha256;
                                              const _errs64 = errors;
                                              const _errs65 = errors;
                                              let valid10 = false;
                                              const _errs66 = errors;
                                              if (typeof data20 !== "string") {
                                                const err18 = { instancePath: instancePath + "/fusion_sequence_file_sha256", schemaPath: "#/properties/fusion_sequence_file_sha256/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                if (vErrors === null) {
                                                  vErrors = [err18];
                                                } else {
                                                  vErrors.push(err18);
                                                }
                                                errors++;
                                              }
                                              var _valid6 = _errs66 === errors;
                                              valid10 = valid10 || _valid6;
                                              const _errs68 = errors;
                                              if (data20 !== null) {
                                                const err19 = { instancePath: instancePath + "/fusion_sequence_file_sha256", schemaPath: "#/properties/fusion_sequence_file_sha256/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                                if (vErrors === null) {
                                                  vErrors = [err19];
                                                } else {
                                                  vErrors.push(err19);
                                                }
                                                errors++;
                                              }
                                              var _valid6 = _errs68 === errors;
                                              valid10 = valid10 || _valid6;
                                              if (!valid10) {
                                                const err20 = { instancePath: instancePath + "/fusion_sequence_file_sha256", schemaPath: "#/properties/fusion_sequence_file_sha256/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                                if (vErrors === null) {
                                                  vErrors = [err20];
                                                } else {
                                                  vErrors.push(err20);
                                                }
                                                errors++;
                                                validate369.errors = vErrors;
                                                return false;
                                              } else {
                                                errors = _errs65;
                                                if (vErrors !== null) {
                                                  if (_errs65) {
                                                    vErrors.length = _errs65;
                                                  } else {
                                                    vErrors = null;
                                                  }
                                                }
                                              }
                                              var valid0 = _errs64 === errors;
                                            } else {
                                              var valid0 = true;
                                            }
                                            if (valid0) {
                                              if (data.fusion_sequence_id !== void 0) {
                                                let data21 = data.fusion_sequence_id;
                                                const _errs70 = errors;
                                                const _errs71 = errors;
                                                let valid11 = false;
                                                const _errs72 = errors;
                                                if (typeof data21 !== "string") {
                                                  const err21 = { instancePath: instancePath + "/fusion_sequence_id", schemaPath: "#/properties/fusion_sequence_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                  if (vErrors === null) {
                                                    vErrors = [err21];
                                                  } else {
                                                    vErrors.push(err21);
                                                  }
                                                  errors++;
                                                }
                                                var _valid7 = _errs72 === errors;
                                                valid11 = valid11 || _valid7;
                                                const _errs74 = errors;
                                                if (data21 !== null) {
                                                  const err22 = { instancePath: instancePath + "/fusion_sequence_id", schemaPath: "#/properties/fusion_sequence_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                                  if (vErrors === null) {
                                                    vErrors = [err22];
                                                  } else {
                                                    vErrors.push(err22);
                                                  }
                                                  errors++;
                                                }
                                                var _valid7 = _errs74 === errors;
                                                valid11 = valid11 || _valid7;
                                                if (!valid11) {
                                                  const err23 = { instancePath: instancePath + "/fusion_sequence_id", schemaPath: "#/properties/fusion_sequence_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                                  if (vErrors === null) {
                                                    vErrors = [err23];
                                                  } else {
                                                    vErrors.push(err23);
                                                  }
                                                  errors++;
                                                  validate369.errors = vErrors;
                                                  return false;
                                                } else {
                                                  errors = _errs71;
                                                  if (vErrors !== null) {
                                                    if (_errs71) {
                                                      vErrors.length = _errs71;
                                                    } else {
                                                      vErrors = null;
                                                    }
                                                  }
                                                }
                                                var valid0 = _errs70 === errors;
                                              } else {
                                                var valid0 = true;
                                              }
                                              if (valid0) {
                                                if (data.annotations !== void 0) {
                                                  let data22 = data.annotations;
                                                  const _errs76 = errors;
                                                  if (errors === _errs76) {
                                                    if (Array.isArray(data22)) {
                                                      var valid12 = true;
                                                      const len3 = data22.length;
                                                      for (let i3 = 0; i3 < len3; i3++) {
                                                        const _errs78 = errors;
                                                        if (!validate374(data22[i3], { instancePath: instancePath + "/annotations/" + i3, parentData: data22, parentDataProperty: i3, rootData, dynamicAnchors })) {
                                                          vErrors = vErrors === null ? validate374.errors : vErrors.concat(validate374.errors);
                                                          errors = vErrors.length;
                                                        }
                                                        var valid12 = _errs78 === errors;
                                                        if (!valid12) {
                                                          break;
                                                        }
                                                      }
                                                    } else {
                                                      validate369.errors = [{ instancePath: instancePath + "/annotations", schemaPath: "#/properties/annotations/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                                      return false;
                                                    }
                                                  }
                                                  var valid0 = _errs76 === errors;
                                                } else {
                                                  var valid0 = true;
                                                }
                                                if (valid0) {
                                                  if (data.annotation_scope !== void 0) {
                                                    let data24 = data.annotation_scope;
                                                    const _errs79 = errors;
                                                    if (typeof data24 !== "string") {
                                                      validate369.errors = [{ instancePath: instancePath + "/annotation_scope", schemaPath: "#/properties/annotation_scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                      return false;
                                                    }
                                                    if (!(data24 === "residue_page" || data24 === "full_model")) {
                                                      validate369.errors = [{ instancePath: instancePath + "/annotation_scope", schemaPath: "#/properties/annotation_scope/enum", keyword: "enum", params: { allowedValues: schema165.properties.annotation_scope.enum }, message: "must be equal to one of the allowed values" }];
                                                      return false;
                                                    }
                                                    var valid0 = _errs79 === errors;
                                                  } else {
                                                    var valid0 = true;
                                                  }
                                                  if (valid0) {
                                                    if (data.overlays !== void 0) {
                                                      let data25 = data.overlays;
                                                      const _errs81 = errors;
                                                      if (errors === _errs81) {
                                                        if (Array.isArray(data25)) {
                                                          var valid13 = true;
                                                          const len4 = data25.length;
                                                          for (let i4 = 0; i4 < len4; i4++) {
                                                            const _errs83 = errors;
                                                            if (!validate379(data25[i4], { instancePath: instancePath + "/overlays/" + i4, parentData: data25, parentDataProperty: i4, rootData, dynamicAnchors })) {
                                                              vErrors = vErrors === null ? validate379.errors : vErrors.concat(validate379.errors);
                                                              errors = vErrors.length;
                                                            }
                                                            var valid13 = _errs83 === errors;
                                                            if (!valid13) {
                                                              break;
                                                            }
                                                          }
                                                        } else {
                                                          validate369.errors = [{ instancePath: instancePath + "/overlays", schemaPath: "#/properties/overlays/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                                          return false;
                                                        }
                                                      }
                                                      var valid0 = _errs81 === errors;
                                                    } else {
                                                      var valid0 = true;
                                                    }
                                                    if (valid0) {
                                                      if (data.preview_policy !== void 0) {
                                                        let data27 = data.preview_policy;
                                                        const _errs84 = errors;
                                                        if (typeof data27 !== "string") {
                                                          validate369.errors = [{ instancePath: instancePath + "/preview_policy", schemaPath: "#/properties/preview_policy/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                          return false;
                                                        }
                                                        if ("atom_coordinates_only_original_sealed" !== data27) {
                                                          validate369.errors = [{ instancePath: instancePath + "/preview_policy", schemaPath: "#/properties/preview_policy/const", keyword: "const", params: { allowedValue: "atom_coordinates_only_original_sealed" }, message: "must be equal to constant" }];
                                                          return false;
                                                        }
                                                        var valid0 = _errs84 === errors;
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
      }
    } else {
      validate369.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate369.errors = vErrors;
  return errors === 0;
}
validate369.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var ResourcePage = validate381;
var schema172 = { "additionalProperties": false, "properties": { "identity": { "$ref": "#/$defs/ResourceIdentity" }, "name": { "title": "Name", "type": "string" }, "byte_count": { "title": "Byte Count", "type": "integer" }, "logical_relative_path": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Logical Relative Path" }, "status": { "default": "available", "enum": ["available", "unavailable", "quarantined"], "title": "Status", "type": "string" }, "error_code": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Error Code" }, "kind": { "const": "image", "default": "image", "title": "Kind", "type": "string" }, "media_type": { "enum": ["image/png", "image/jpeg"], "title": "Media Type", "type": "string" }, "role": { "const": "registered_source", "default": "registered_source", "title": "Role", "type": "string" }, "claim_scope": { "const": "display_only_not_experimental_validation", "default": "display_only_not_experimental_validation", "title": "Claim Scope", "type": "string" } }, "required": ["identity", "name", "byte_count", "logical_relative_path", "status", "error_code", "kind", "media_type", "role", "claim_scope"], "title": "ImageResource", "type": "object" };
function validate383(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate383.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.file_id === void 0 && (missing0 = "file_id") || data.source_sha256 === void 0 && (missing0 = "source_sha256") || data.run_id === void 0 && (missing0 = "run_id") || data.snapshot_hash === void 0 && (missing0 = "snapshot_hash") || data.node_id === void 0 && (missing0 = "node_id") || data.attempt === void 0 && (missing0 = "attempt") || data.candidate_id === void 0 && (missing0 = "candidate_id") || data.construct_id === void 0 && (missing0 = "construct_id") || data.condition_id === void 0 && (missing0 = "condition_id")) {
        validate383.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema158.properties, key0)) {
            validate383.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate383.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.file_id !== void 0) {
              const _errs4 = errors;
              if (typeof data.file_id !== "string") {
                validate383.errors = [{ instancePath: instancePath + "/file_id", schemaPath: "#/properties/file_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.source_sha256 !== void 0) {
                const _errs6 = errors;
                if (typeof data.source_sha256 !== "string") {
                  validate383.errors = [{ instancePath: instancePath + "/source_sha256", schemaPath: "#/properties/source_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  let data3 = data.run_id;
                  const _errs8 = errors;
                  const _errs9 = errors;
                  let valid1 = false;
                  const _errs10 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                    const err1 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err2 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate383.errors = vErrors;
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
                  if (data.snapshot_hash !== void 0) {
                    let data4 = data.snapshot_hash;
                    const _errs14 = errors;
                    const _errs15 = errors;
                    let valid2 = false;
                    const _errs16 = errors;
                    if (typeof data4 !== "string") {
                      const err3 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                      const err4 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                      const err5 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err5];
                      } else {
                        vErrors.push(err5);
                      }
                      errors++;
                      validate383.errors = vErrors;
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
                    if (data.node_id !== void 0) {
                      let data5 = data.node_id;
                      const _errs20 = errors;
                      const _errs21 = errors;
                      let valid3 = false;
                      const _errs22 = errors;
                      if (typeof data5 !== "string") {
                        const err6 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err6];
                        } else {
                          vErrors.push(err6);
                        }
                        errors++;
                      }
                      var _valid2 = _errs22 === errors;
                      valid3 = valid3 || _valid2;
                      const _errs24 = errors;
                      if (data5 !== null) {
                        const err7 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err7];
                        } else {
                          vErrors.push(err7);
                        }
                        errors++;
                      }
                      var _valid2 = _errs24 === errors;
                      valid3 = valid3 || _valid2;
                      if (!valid3) {
                        const err8 = { instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err8];
                        } else {
                          vErrors.push(err8);
                        }
                        errors++;
                        validate383.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs21;
                        if (vErrors !== null) {
                          if (_errs21) {
                            vErrors.length = _errs21;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.attempt !== void 0) {
                        let data6 = data.attempt;
                        const _errs26 = errors;
                        const _errs27 = errors;
                        let valid4 = false;
                        const _errs28 = errors;
                        if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)))) {
                          const err9 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                          if (vErrors === null) {
                            vErrors = [err9];
                          } else {
                            vErrors.push(err9);
                          }
                          errors++;
                        }
                        var _valid3 = _errs28 === errors;
                        valid4 = valid4 || _valid3;
                        const _errs30 = errors;
                        if (data6 !== null) {
                          const err10 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err10];
                          } else {
                            vErrors.push(err10);
                          }
                          errors++;
                        }
                        var _valid3 = _errs30 === errors;
                        valid4 = valid4 || _valid3;
                        if (!valid4) {
                          const err11 = { instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err11];
                          } else {
                            vErrors.push(err11);
                          }
                          errors++;
                          validate383.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs27;
                          if (vErrors !== null) {
                            if (_errs27) {
                              vErrors.length = _errs27;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs26 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.candidate_id !== void 0) {
                          let data7 = data.candidate_id;
                          const _errs32 = errors;
                          const _errs33 = errors;
                          let valid5 = false;
                          const _errs34 = errors;
                          if (typeof data7 !== "string") {
                            const err12 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err12];
                            } else {
                              vErrors.push(err12);
                            }
                            errors++;
                          }
                          var _valid4 = _errs34 === errors;
                          valid5 = valid5 || _valid4;
                          const _errs36 = errors;
                          if (data7 !== null) {
                            const err13 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err13];
                            } else {
                              vErrors.push(err13);
                            }
                            errors++;
                          }
                          var _valid4 = _errs36 === errors;
                          valid5 = valid5 || _valid4;
                          if (!valid5) {
                            const err14 = { instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err14];
                            } else {
                              vErrors.push(err14);
                            }
                            errors++;
                            validate383.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs33;
                            if (vErrors !== null) {
                              if (_errs33) {
                                vErrors.length = _errs33;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs32 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.construct_id !== void 0) {
                            let data8 = data.construct_id;
                            const _errs38 = errors;
                            const _errs39 = errors;
                            let valid6 = false;
                            const _errs40 = errors;
                            if (typeof data8 !== "string") {
                              const err15 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err15];
                              } else {
                                vErrors.push(err15);
                              }
                              errors++;
                            }
                            var _valid5 = _errs40 === errors;
                            valid6 = valid6 || _valid5;
                            const _errs42 = errors;
                            if (data8 !== null) {
                              const err16 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err16];
                              } else {
                                vErrors.push(err16);
                              }
                              errors++;
                            }
                            var _valid5 = _errs42 === errors;
                            valid6 = valid6 || _valid5;
                            if (!valid6) {
                              const err17 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err17];
                              } else {
                                vErrors.push(err17);
                              }
                              errors++;
                              validate383.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs39;
                              if (vErrors !== null) {
                                if (_errs39) {
                                  vErrors.length = _errs39;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs38 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.condition_id !== void 0) {
                              let data9 = data.condition_id;
                              const _errs44 = errors;
                              const _errs45 = errors;
                              let valid7 = false;
                              const _errs46 = errors;
                              if (typeof data9 !== "string") {
                                const err18 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err18];
                                } else {
                                  vErrors.push(err18);
                                }
                                errors++;
                              }
                              var _valid6 = _errs46 === errors;
                              valid7 = valid7 || _valid6;
                              const _errs48 = errors;
                              if (data9 !== null) {
                                const err19 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                if (vErrors === null) {
                                  vErrors = [err19];
                                } else {
                                  vErrors.push(err19);
                                }
                                errors++;
                              }
                              var _valid6 = _errs48 === errors;
                              valid7 = valid7 || _valid6;
                              if (!valid7) {
                                const err20 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                if (vErrors === null) {
                                  vErrors = [err20];
                                } else {
                                  vErrors.push(err20);
                                }
                                errors++;
                                validate383.errors = vErrors;
                                return false;
                              } else {
                                errors = _errs45;
                                if (vErrors !== null) {
                                  if (_errs45) {
                                    vErrors.length = _errs45;
                                  } else {
                                    vErrors = null;
                                  }
                                }
                              }
                              var valid0 = _errs44 === errors;
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
      validate383.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate383.errors = vErrors;
  return errors === 0;
}
validate383.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate382(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate382.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.identity === void 0 && (missing0 = "identity") || data.name === void 0 && (missing0 = "name") || data.byte_count === void 0 && (missing0 = "byte_count") || data.logical_relative_path === void 0 && (missing0 = "logical_relative_path") || data.status === void 0 && (missing0 = "status") || data.error_code === void 0 && (missing0 = "error_code") || data.kind === void 0 && (missing0 = "kind") || data.media_type === void 0 && (missing0 = "media_type") || data.role === void 0 && (missing0 = "role") || data.claim_scope === void 0 && (missing0 = "claim_scope")) {
        validate382.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema172.properties, key0)) {
            validate382.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.identity !== void 0) {
            const _errs2 = errors;
            if (!validate383(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
              vErrors = vErrors === null ? validate383.errors : vErrors.concat(validate383.errors);
              errors = vErrors.length;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.name !== void 0) {
              const _errs3 = errors;
              if (typeof data.name !== "string") {
                validate382.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs3 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.byte_count !== void 0) {
                let data2 = data.byte_count;
                const _errs5 = errors;
                if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                  validate382.errors = [{ instancePath: instancePath + "/byte_count", schemaPath: "#/properties/byte_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs5 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.logical_relative_path !== void 0) {
                  let data3 = data.logical_relative_path;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  let valid1 = false;
                  const _errs9 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                  }
                  var _valid0 = _errs9 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs11 = errors;
                  if (data3 !== null) {
                    const err1 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                  }
                  var _valid0 = _errs11 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err2 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate382.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs8;
                    if (vErrors !== null) {
                      if (_errs8) {
                        vErrors.length = _errs8;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    let data4 = data.status;
                    const _errs13 = errors;
                    if (typeof data4 !== "string") {
                      validate382.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data4 === "available" || data4 === "unavailable" || data4 === "quarantined")) {
                      validate382.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema172.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs13 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.error_code !== void 0) {
                      let data5 = data.error_code;
                      const _errs15 = errors;
                      const _errs16 = errors;
                      let valid2 = false;
                      const _errs17 = errors;
                      if (typeof data5 !== "string") {
                        const err3 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err3];
                        } else {
                          vErrors.push(err3);
                        }
                        errors++;
                      }
                      var _valid1 = _errs17 === errors;
                      valid2 = valid2 || _valid1;
                      const _errs19 = errors;
                      if (data5 !== null) {
                        const err4 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err4];
                        } else {
                          vErrors.push(err4);
                        }
                        errors++;
                      }
                      var _valid1 = _errs19 === errors;
                      valid2 = valid2 || _valid1;
                      if (!valid2) {
                        const err5 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err5];
                        } else {
                          vErrors.push(err5);
                        }
                        errors++;
                        validate382.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs16;
                        if (vErrors !== null) {
                          if (_errs16) {
                            vErrors.length = _errs16;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs15 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.kind !== void 0) {
                        let data6 = data.kind;
                        const _errs21 = errors;
                        if (typeof data6 !== "string") {
                          validate382.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("image" !== data6) {
                          validate382.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "image" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs21 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.media_type !== void 0) {
                          let data7 = data.media_type;
                          const _errs23 = errors;
                          if (typeof data7 !== "string") {
                            validate382.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if (!(data7 === "image/png" || data7 === "image/jpeg")) {
                            validate382.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/enum", keyword: "enum", params: { allowedValues: schema172.properties.media_type.enum }, message: "must be equal to one of the allowed values" }];
                            return false;
                          }
                          var valid0 = _errs23 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.role !== void 0) {
                            let data8 = data.role;
                            const _errs25 = errors;
                            if (typeof data8 !== "string") {
                              validate382.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("registered_source" !== data8) {
                              validate382.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/const", keyword: "const", params: { allowedValue: "registered_source" }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid0 = _errs25 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.claim_scope !== void 0) {
                              let data9 = data.claim_scope;
                              const _errs27 = errors;
                              if (typeof data9 !== "string") {
                                validate382.errors = [{ instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("display_only_not_experimental_validation" !== data9) {
                                validate382.errors = [{ instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/const", keyword: "const", params: { allowedValue: "display_only_not_experimental_validation" }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid0 = _errs27 === errors;
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
      validate382.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate382.errors = vErrors;
  return errors === 0;
}
validate382.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema174 = { "additionalProperties": false, "properties": { "identity": { "$ref": "#/$defs/ResourceIdentity" }, "name": { "title": "Name", "type": "string" }, "byte_count": { "title": "Byte Count", "type": "integer" }, "logical_relative_path": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Logical Relative Path" }, "status": { "default": "available", "enum": ["available", "unavailable", "quarantined"], "title": "Status", "type": "string" }, "error_code": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Error Code" }, "kind": { "const": "structure", "default": "structure", "title": "Kind", "type": "string" }, "format": { "enum": ["pdb", "mmcif"], "title": "Format", "type": "string" }, "role": { "const": "registered_source", "default": "registered_source", "title": "Role", "type": "string" }, "claim_scope": { "const": "geometry_only_no_inferred_activity_or_confidence", "default": "geometry_only_no_inferred_activity_or_confidence", "title": "Claim Scope", "type": "string" } }, "required": ["identity", "name", "byte_count", "logical_relative_path", "status", "error_code", "kind", "format", "role", "claim_scope"], "title": "StructureResource", "type": "object" };
function validate386(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate386.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.identity === void 0 && (missing0 = "identity") || data.name === void 0 && (missing0 = "name") || data.byte_count === void 0 && (missing0 = "byte_count") || data.logical_relative_path === void 0 && (missing0 = "logical_relative_path") || data.status === void 0 && (missing0 = "status") || data.error_code === void 0 && (missing0 = "error_code") || data.kind === void 0 && (missing0 = "kind") || data.format === void 0 && (missing0 = "format") || data.role === void 0 && (missing0 = "role") || data.claim_scope === void 0 && (missing0 = "claim_scope")) {
        validate386.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema174.properties, key0)) {
            validate386.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.identity !== void 0) {
            const _errs2 = errors;
            if (!validate383(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
              vErrors = vErrors === null ? validate383.errors : vErrors.concat(validate383.errors);
              errors = vErrors.length;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.name !== void 0) {
              const _errs3 = errors;
              if (typeof data.name !== "string") {
                validate386.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs3 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.byte_count !== void 0) {
                let data2 = data.byte_count;
                const _errs5 = errors;
                if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                  validate386.errors = [{ instancePath: instancePath + "/byte_count", schemaPath: "#/properties/byte_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs5 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.logical_relative_path !== void 0) {
                  let data3 = data.logical_relative_path;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  let valid1 = false;
                  const _errs9 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                  }
                  var _valid0 = _errs9 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs11 = errors;
                  if (data3 !== null) {
                    const err1 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                  }
                  var _valid0 = _errs11 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err2 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate386.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs8;
                    if (vErrors !== null) {
                      if (_errs8) {
                        vErrors.length = _errs8;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    let data4 = data.status;
                    const _errs13 = errors;
                    if (typeof data4 !== "string") {
                      validate386.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data4 === "available" || data4 === "unavailable" || data4 === "quarantined")) {
                      validate386.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema174.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs13 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.error_code !== void 0) {
                      let data5 = data.error_code;
                      const _errs15 = errors;
                      const _errs16 = errors;
                      let valid2 = false;
                      const _errs17 = errors;
                      if (typeof data5 !== "string") {
                        const err3 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err3];
                        } else {
                          vErrors.push(err3);
                        }
                        errors++;
                      }
                      var _valid1 = _errs17 === errors;
                      valid2 = valid2 || _valid1;
                      const _errs19 = errors;
                      if (data5 !== null) {
                        const err4 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err4];
                        } else {
                          vErrors.push(err4);
                        }
                        errors++;
                      }
                      var _valid1 = _errs19 === errors;
                      valid2 = valid2 || _valid1;
                      if (!valid2) {
                        const err5 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err5];
                        } else {
                          vErrors.push(err5);
                        }
                        errors++;
                        validate386.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs16;
                        if (vErrors !== null) {
                          if (_errs16) {
                            vErrors.length = _errs16;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs15 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.kind !== void 0) {
                        let data6 = data.kind;
                        const _errs21 = errors;
                        if (typeof data6 !== "string") {
                          validate386.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("structure" !== data6) {
                          validate386.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "structure" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs21 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.format !== void 0) {
                          let data7 = data.format;
                          const _errs23 = errors;
                          if (typeof data7 !== "string") {
                            validate386.errors = [{ instancePath: instancePath + "/format", schemaPath: "#/properties/format/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if (!(data7 === "pdb" || data7 === "mmcif")) {
                            validate386.errors = [{ instancePath: instancePath + "/format", schemaPath: "#/properties/format/enum", keyword: "enum", params: { allowedValues: schema174.properties.format.enum }, message: "must be equal to one of the allowed values" }];
                            return false;
                          }
                          var valid0 = _errs23 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.role !== void 0) {
                            let data8 = data.role;
                            const _errs25 = errors;
                            if (typeof data8 !== "string") {
                              validate386.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("registered_source" !== data8) {
                              validate386.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/const", keyword: "const", params: { allowedValue: "registered_source" }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid0 = _errs25 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.claim_scope !== void 0) {
                              let data9 = data.claim_scope;
                              const _errs27 = errors;
                              if (typeof data9 !== "string") {
                                validate386.errors = [{ instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("geometry_only_no_inferred_activity_or_confidence" !== data9) {
                                validate386.errors = [{ instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/const", keyword: "const", params: { allowedValue: "geometry_only_no_inferred_activity_or_confidence" }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid0 = _errs27 === errors;
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
      validate386.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate386.errors = vErrors;
  return errors === 0;
}
validate386.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema175 = { "additionalProperties": false, "properties": { "identity": { "$ref": "#/$defs/ResourceIdentity" }, "name": { "title": "Name", "type": "string" }, "byte_count": { "title": "Byte Count", "type": "integer" }, "logical_relative_path": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Logical Relative Path" }, "status": { "default": "available", "enum": ["available", "unavailable", "quarantined"], "title": "Status", "type": "string" }, "error_code": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Error Code" }, "kind": { "const": "series", "default": "series", "title": "Kind", "type": "string" }, "result_schema_version": { "default": "m4-prediction-v2", "enum": ["m4-prediction-v2", "display-series-source-v1", "m4-compartment-amount-v1"], "title": "Result Schema Version", "type": "string" }, "role": { "default": "prediction_contract", "enum": ["prediction_contract", "declared_source_series"], "title": "Role", "type": "string" } }, "required": ["identity", "name", "byte_count", "logical_relative_path", "status", "error_code", "kind", "result_schema_version", "role"], "title": "SeriesResource", "type": "object" };
function validate389(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate389.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.identity === void 0 && (missing0 = "identity") || data.name === void 0 && (missing0 = "name") || data.byte_count === void 0 && (missing0 = "byte_count") || data.logical_relative_path === void 0 && (missing0 = "logical_relative_path") || data.status === void 0 && (missing0 = "status") || data.error_code === void 0 && (missing0 = "error_code") || data.kind === void 0 && (missing0 = "kind") || data.result_schema_version === void 0 && (missing0 = "result_schema_version") || data.role === void 0 && (missing0 = "role")) {
        validate389.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema175.properties, key0)) {
            validate389.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.identity !== void 0) {
            const _errs2 = errors;
            if (!validate383(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
              vErrors = vErrors === null ? validate383.errors : vErrors.concat(validate383.errors);
              errors = vErrors.length;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.name !== void 0) {
              const _errs3 = errors;
              if (typeof data.name !== "string") {
                validate389.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs3 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.byte_count !== void 0) {
                let data2 = data.byte_count;
                const _errs5 = errors;
                if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                  validate389.errors = [{ instancePath: instancePath + "/byte_count", schemaPath: "#/properties/byte_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs5 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.logical_relative_path !== void 0) {
                  let data3 = data.logical_relative_path;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  let valid1 = false;
                  const _errs9 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                  }
                  var _valid0 = _errs9 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs11 = errors;
                  if (data3 !== null) {
                    const err1 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                  }
                  var _valid0 = _errs11 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err2 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate389.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs8;
                    if (vErrors !== null) {
                      if (_errs8) {
                        vErrors.length = _errs8;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    let data4 = data.status;
                    const _errs13 = errors;
                    if (typeof data4 !== "string") {
                      validate389.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data4 === "available" || data4 === "unavailable" || data4 === "quarantined")) {
                      validate389.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema175.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs13 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.error_code !== void 0) {
                      let data5 = data.error_code;
                      const _errs15 = errors;
                      const _errs16 = errors;
                      let valid2 = false;
                      const _errs17 = errors;
                      if (typeof data5 !== "string") {
                        const err3 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err3];
                        } else {
                          vErrors.push(err3);
                        }
                        errors++;
                      }
                      var _valid1 = _errs17 === errors;
                      valid2 = valid2 || _valid1;
                      const _errs19 = errors;
                      if (data5 !== null) {
                        const err4 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err4];
                        } else {
                          vErrors.push(err4);
                        }
                        errors++;
                      }
                      var _valid1 = _errs19 === errors;
                      valid2 = valid2 || _valid1;
                      if (!valid2) {
                        const err5 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err5];
                        } else {
                          vErrors.push(err5);
                        }
                        errors++;
                        validate389.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs16;
                        if (vErrors !== null) {
                          if (_errs16) {
                            vErrors.length = _errs16;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs15 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.kind !== void 0) {
                        let data6 = data.kind;
                        const _errs21 = errors;
                        if (typeof data6 !== "string") {
                          validate389.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("series" !== data6) {
                          validate389.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "series" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs21 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.result_schema_version !== void 0) {
                          let data7 = data.result_schema_version;
                          const _errs23 = errors;
                          if (typeof data7 !== "string") {
                            validate389.errors = [{ instancePath: instancePath + "/result_schema_version", schemaPath: "#/properties/result_schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if (!(data7 === "m4-prediction-v2" || data7 === "display-series-source-v1" || data7 === "m4-compartment-amount-v1")) {
                            validate389.errors = [{ instancePath: instancePath + "/result_schema_version", schemaPath: "#/properties/result_schema_version/enum", keyword: "enum", params: { allowedValues: schema175.properties.result_schema_version.enum }, message: "must be equal to one of the allowed values" }];
                            return false;
                          }
                          var valid0 = _errs23 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.role !== void 0) {
                            let data8 = data.role;
                            const _errs25 = errors;
                            if (typeof data8 !== "string") {
                              validate389.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if (!(data8 === "prediction_contract" || data8 === "declared_source_series")) {
                              validate389.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/enum", keyword: "enum", params: { allowedValues: schema175.properties.role.enum }, message: "must be equal to one of the allowed values" }];
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
    } else {
      validate389.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate389.errors = vErrors;
  return errors === 0;
}
validate389.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema176 = { "additionalProperties": false, "properties": { "identity": { "$ref": "#/$defs/ResourceIdentity" }, "name": { "title": "Name", "type": "string" }, "byte_count": { "title": "Byte Count", "type": "integer" }, "logical_relative_path": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Logical Relative Path" }, "status": { "default": "available", "enum": ["available", "unavailable", "quarantined"], "title": "Status", "type": "string" }, "error_code": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Error Code" }, "kind": { "const": "scan", "default": "scan", "title": "Kind", "type": "string" }, "result_schema_version": { "const": "finite-scaffold-scan-v2", "default": "finite-scaffold-scan-v2", "title": "Result Schema Version", "type": "string" } }, "required": ["identity", "name", "byte_count", "logical_relative_path", "status", "error_code", "kind", "result_schema_version"], "title": "ScanResource", "type": "object" };
function validate392(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate392.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.identity === void 0 && (missing0 = "identity") || data.name === void 0 && (missing0 = "name") || data.byte_count === void 0 && (missing0 = "byte_count") || data.logical_relative_path === void 0 && (missing0 = "logical_relative_path") || data.status === void 0 && (missing0 = "status") || data.error_code === void 0 && (missing0 = "error_code") || data.kind === void 0 && (missing0 = "kind") || data.result_schema_version === void 0 && (missing0 = "result_schema_version")) {
        validate392.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "identity" || key0 === "name" || key0 === "byte_count" || key0 === "logical_relative_path" || key0 === "status" || key0 === "error_code" || key0 === "kind" || key0 === "result_schema_version")) {
            validate392.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.identity !== void 0) {
            const _errs2 = errors;
            if (!validate383(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
              vErrors = vErrors === null ? validate383.errors : vErrors.concat(validate383.errors);
              errors = vErrors.length;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.name !== void 0) {
              const _errs3 = errors;
              if (typeof data.name !== "string") {
                validate392.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs3 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.byte_count !== void 0) {
                let data2 = data.byte_count;
                const _errs5 = errors;
                if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                  validate392.errors = [{ instancePath: instancePath + "/byte_count", schemaPath: "#/properties/byte_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs5 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.logical_relative_path !== void 0) {
                  let data3 = data.logical_relative_path;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  let valid1 = false;
                  const _errs9 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                  }
                  var _valid0 = _errs9 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs11 = errors;
                  if (data3 !== null) {
                    const err1 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                  }
                  var _valid0 = _errs11 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err2 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate392.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs8;
                    if (vErrors !== null) {
                      if (_errs8) {
                        vErrors.length = _errs8;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    let data4 = data.status;
                    const _errs13 = errors;
                    if (typeof data4 !== "string") {
                      validate392.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data4 === "available" || data4 === "unavailable" || data4 === "quarantined")) {
                      validate392.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema176.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs13 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.error_code !== void 0) {
                      let data5 = data.error_code;
                      const _errs15 = errors;
                      const _errs16 = errors;
                      let valid2 = false;
                      const _errs17 = errors;
                      if (typeof data5 !== "string") {
                        const err3 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err3];
                        } else {
                          vErrors.push(err3);
                        }
                        errors++;
                      }
                      var _valid1 = _errs17 === errors;
                      valid2 = valid2 || _valid1;
                      const _errs19 = errors;
                      if (data5 !== null) {
                        const err4 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err4];
                        } else {
                          vErrors.push(err4);
                        }
                        errors++;
                      }
                      var _valid1 = _errs19 === errors;
                      valid2 = valid2 || _valid1;
                      if (!valid2) {
                        const err5 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err5];
                        } else {
                          vErrors.push(err5);
                        }
                        errors++;
                        validate392.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs16;
                        if (vErrors !== null) {
                          if (_errs16) {
                            vErrors.length = _errs16;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs15 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.kind !== void 0) {
                        let data6 = data.kind;
                        const _errs21 = errors;
                        if (typeof data6 !== "string") {
                          validate392.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("scan" !== data6) {
                          validate392.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "scan" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs21 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.result_schema_version !== void 0) {
                          let data7 = data.result_schema_version;
                          const _errs23 = errors;
                          if (typeof data7 !== "string") {
                            validate392.errors = [{ instancePath: instancePath + "/result_schema_version", schemaPath: "#/properties/result_schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("finite-scaffold-scan-v2" !== data7) {
                            validate392.errors = [{ instancePath: instancePath + "/result_schema_version", schemaPath: "#/properties/result_schema_version/const", keyword: "const", params: { allowedValue: "finite-scaffold-scan-v2" }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid0 = _errs23 === errors;
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
      validate392.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate392.errors = vErrors;
  return errors === 0;
}
validate392.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema177 = { "additionalProperties": false, "properties": { "identity": { "$ref": "#/$defs/ResourceIdentity" }, "name": { "title": "Name", "type": "string" }, "byte_count": { "title": "Byte Count", "type": "integer" }, "logical_relative_path": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Logical Relative Path" }, "status": { "default": "available", "enum": ["available", "unavailable", "quarantined"], "title": "Status", "type": "string" }, "error_code": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Error Code" }, "kind": { "const": "m5", "default": "m5", "title": "Kind", "type": "string" }, "result_schema_version": { "const": "m5-comparison-series-v1", "default": "m5-comparison-series-v1", "title": "Result Schema Version", "type": "string" }, "claim_scope": { "const": "recorded_alignment_not_parameter_or_experimental_approval", "default": "recorded_alignment_not_parameter_or_experimental_approval", "title": "Claim Scope", "type": "string" } }, "required": ["identity", "name", "byte_count", "logical_relative_path", "status", "error_code", "kind", "result_schema_version", "claim_scope"], "title": "M5Resource", "type": "object" };
function validate395(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate395.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.identity === void 0 && (missing0 = "identity") || data.name === void 0 && (missing0 = "name") || data.byte_count === void 0 && (missing0 = "byte_count") || data.logical_relative_path === void 0 && (missing0 = "logical_relative_path") || data.status === void 0 && (missing0 = "status") || data.error_code === void 0 && (missing0 = "error_code") || data.kind === void 0 && (missing0 = "kind") || data.result_schema_version === void 0 && (missing0 = "result_schema_version") || data.claim_scope === void 0 && (missing0 = "claim_scope")) {
        validate395.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema177.properties, key0)) {
            validate395.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.identity !== void 0) {
            const _errs2 = errors;
            if (!validate383(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
              vErrors = vErrors === null ? validate383.errors : vErrors.concat(validate383.errors);
              errors = vErrors.length;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.name !== void 0) {
              const _errs3 = errors;
              if (typeof data.name !== "string") {
                validate395.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs3 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.byte_count !== void 0) {
                let data2 = data.byte_count;
                const _errs5 = errors;
                if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                  validate395.errors = [{ instancePath: instancePath + "/byte_count", schemaPath: "#/properties/byte_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs5 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.logical_relative_path !== void 0) {
                  let data3 = data.logical_relative_path;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  let valid1 = false;
                  const _errs9 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                  }
                  var _valid0 = _errs9 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs11 = errors;
                  if (data3 !== null) {
                    const err1 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                  }
                  var _valid0 = _errs11 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err2 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate395.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs8;
                    if (vErrors !== null) {
                      if (_errs8) {
                        vErrors.length = _errs8;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    let data4 = data.status;
                    const _errs13 = errors;
                    if (typeof data4 !== "string") {
                      validate395.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data4 === "available" || data4 === "unavailable" || data4 === "quarantined")) {
                      validate395.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema177.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs13 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.error_code !== void 0) {
                      let data5 = data.error_code;
                      const _errs15 = errors;
                      const _errs16 = errors;
                      let valid2 = false;
                      const _errs17 = errors;
                      if (typeof data5 !== "string") {
                        const err3 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err3];
                        } else {
                          vErrors.push(err3);
                        }
                        errors++;
                      }
                      var _valid1 = _errs17 === errors;
                      valid2 = valid2 || _valid1;
                      const _errs19 = errors;
                      if (data5 !== null) {
                        const err4 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err4];
                        } else {
                          vErrors.push(err4);
                        }
                        errors++;
                      }
                      var _valid1 = _errs19 === errors;
                      valid2 = valid2 || _valid1;
                      if (!valid2) {
                        const err5 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err5];
                        } else {
                          vErrors.push(err5);
                        }
                        errors++;
                        validate395.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs16;
                        if (vErrors !== null) {
                          if (_errs16) {
                            vErrors.length = _errs16;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs15 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.kind !== void 0) {
                        let data6 = data.kind;
                        const _errs21 = errors;
                        if (typeof data6 !== "string") {
                          validate395.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("m5" !== data6) {
                          validate395.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "m5" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs21 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.result_schema_version !== void 0) {
                          let data7 = data.result_schema_version;
                          const _errs23 = errors;
                          if (typeof data7 !== "string") {
                            validate395.errors = [{ instancePath: instancePath + "/result_schema_version", schemaPath: "#/properties/result_schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("m5-comparison-series-v1" !== data7) {
                            validate395.errors = [{ instancePath: instancePath + "/result_schema_version", schemaPath: "#/properties/result_schema_version/const", keyword: "const", params: { allowedValue: "m5-comparison-series-v1" }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid0 = _errs23 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.claim_scope !== void 0) {
                            let data8 = data.claim_scope;
                            const _errs25 = errors;
                            if (typeof data8 !== "string") {
                              validate395.errors = [{ instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("recorded_alignment_not_parameter_or_experimental_approval" !== data8) {
                              validate395.errors = [{ instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/const", keyword: "const", params: { allowedValue: "recorded_alignment_not_parameter_or_experimental_approval" }, message: "must be equal to constant" }];
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
    } else {
      validate395.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate395.errors = vErrors;
  return errors === 0;
}
validate395.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema178 = { "additionalProperties": false, "properties": { "identity": { "$ref": "#/$defs/ResourceIdentity" }, "name": { "title": "Name", "type": "string" }, "byte_count": { "title": "Byte Count", "type": "integer" }, "logical_relative_path": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Logical Relative Path" }, "status": { "default": "available", "enum": ["available", "unavailable", "quarantined"], "title": "Status", "type": "string" }, "error_code": { "anyOf": [{ "type": "string" }, { "type": "null" }], "default": null, "title": "Error Code" }, "kind": { "const": "table", "default": "table", "title": "Kind", "type": "string" }, "media_type": { "title": "Media Type", "type": "string" }, "role": { "const": "registered_source", "default": "registered_source", "title": "Role", "type": "string" } }, "required": ["identity", "name", "byte_count", "logical_relative_path", "status", "error_code", "kind", "media_type", "role"], "title": "TableResource", "type": "object" };
function validate398(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate398.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.identity === void 0 && (missing0 = "identity") || data.name === void 0 && (missing0 = "name") || data.byte_count === void 0 && (missing0 = "byte_count") || data.logical_relative_path === void 0 && (missing0 = "logical_relative_path") || data.status === void 0 && (missing0 = "status") || data.error_code === void 0 && (missing0 = "error_code") || data.kind === void 0 && (missing0 = "kind") || data.media_type === void 0 && (missing0 = "media_type") || data.role === void 0 && (missing0 = "role")) {
        validate398.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema178.properties, key0)) {
            validate398.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.identity !== void 0) {
            const _errs2 = errors;
            if (!validate383(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
              vErrors = vErrors === null ? validate383.errors : vErrors.concat(validate383.errors);
              errors = vErrors.length;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.name !== void 0) {
              const _errs3 = errors;
              if (typeof data.name !== "string") {
                validate398.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs3 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.byte_count !== void 0) {
                let data2 = data.byte_count;
                const _errs5 = errors;
                if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                  validate398.errors = [{ instancePath: instancePath + "/byte_count", schemaPath: "#/properties/byte_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs5 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.logical_relative_path !== void 0) {
                  let data3 = data.logical_relative_path;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  let valid1 = false;
                  const _errs9 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                  }
                  var _valid0 = _errs9 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs11 = errors;
                  if (data3 !== null) {
                    const err1 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                  }
                  var _valid0 = _errs11 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err2 = { instancePath: instancePath + "/logical_relative_path", schemaPath: "#/properties/logical_relative_path/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate398.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs8;
                    if (vErrors !== null) {
                      if (_errs8) {
                        vErrors.length = _errs8;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    let data4 = data.status;
                    const _errs13 = errors;
                    if (typeof data4 !== "string") {
                      validate398.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data4 === "available" || data4 === "unavailable" || data4 === "quarantined")) {
                      validate398.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema178.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs13 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.error_code !== void 0) {
                      let data5 = data.error_code;
                      const _errs15 = errors;
                      const _errs16 = errors;
                      let valid2 = false;
                      const _errs17 = errors;
                      if (typeof data5 !== "string") {
                        const err3 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err3];
                        } else {
                          vErrors.push(err3);
                        }
                        errors++;
                      }
                      var _valid1 = _errs17 === errors;
                      valid2 = valid2 || _valid1;
                      const _errs19 = errors;
                      if (data5 !== null) {
                        const err4 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err4];
                        } else {
                          vErrors.push(err4);
                        }
                        errors++;
                      }
                      var _valid1 = _errs19 === errors;
                      valid2 = valid2 || _valid1;
                      if (!valid2) {
                        const err5 = { instancePath: instancePath + "/error_code", schemaPath: "#/properties/error_code/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err5];
                        } else {
                          vErrors.push(err5);
                        }
                        errors++;
                        validate398.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs16;
                        if (vErrors !== null) {
                          if (_errs16) {
                            vErrors.length = _errs16;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs15 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.kind !== void 0) {
                        let data6 = data.kind;
                        const _errs21 = errors;
                        if (typeof data6 !== "string") {
                          validate398.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("table" !== data6) {
                          validate398.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "table" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs21 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.media_type !== void 0) {
                          const _errs23 = errors;
                          if (typeof data.media_type !== "string") {
                            validate398.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid0 = _errs23 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.role !== void 0) {
                            let data8 = data.role;
                            const _errs25 = errors;
                            if (typeof data8 !== "string") {
                              validate398.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("registered_source" !== data8) {
                              validate398.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/const", keyword: "const", params: { allowedValue: "registered_source" }, message: "must be equal to constant" }];
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
    } else {
      validate398.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate398.errors = vErrors;
  return errors === 0;
}
validate398.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate381(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate381.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.schema_version === void 0 && (missing0 = "schema_version") || data.project_id === void 0 && (missing0 = "project_id") || data.run_id === void 0 && (missing0 = "run_id") || data.snapshot_hash === void 0 && (missing0 = "snapshot_hash") || data.offset === void 0 && (missing0 = "offset") || data.total === void 0 && (missing0 = "total") || data.has_more === void 0 && (missing0 = "has_more") || data.items === void 0 && (missing0 = "items")) {
        validate381.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "schema_version" || key0 === "project_id" || key0 === "run_id" || key0 === "snapshot_hash" || key0 === "offset" || key0 === "total" || key0 === "has_more" || key0 === "items")) {
            validate381.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.schema_version !== void 0) {
            let data0 = data.schema_version;
            const _errs2 = errors;
            if (typeof data0 !== "string") {
              validate381.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            if ("display-resource-v1" !== data0) {
              validate381.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "display-resource-v1" }, message: "must be equal to constant" }];
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
                validate381.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.run_id !== void 0) {
                let data2 = data.run_id;
                const _errs6 = errors;
                const _errs7 = errors;
                let valid1 = false;
                const _errs8 = errors;
                if (typeof data2 !== "string") {
                  const err0 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                  const err1 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err2 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err2];
                  } else {
                    vErrors.push(err2);
                  }
                  errors++;
                  validate381.errors = vErrors;
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
                if (data.snapshot_hash !== void 0) {
                  let data3 = data.snapshot_hash;
                  const _errs12 = errors;
                  const _errs13 = errors;
                  let valid2 = false;
                  const _errs14 = errors;
                  if (typeof data3 !== "string") {
                    const err3 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                    const err4 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err5 = { instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err5];
                    } else {
                      vErrors.push(err5);
                    }
                    errors++;
                    validate381.errors = vErrors;
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
                  if (data.offset !== void 0) {
                    let data4 = data.offset;
                    const _errs18 = errors;
                    if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)))) {
                      validate381.errors = [{ instancePath: instancePath + "/offset", schemaPath: "#/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    var valid0 = _errs18 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.total !== void 0) {
                      let data5 = data.total;
                      const _errs20 = errors;
                      if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)))) {
                        validate381.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.has_more !== void 0) {
                        const _errs22 = errors;
                        if (typeof data.has_more !== "boolean") {
                          validate381.errors = [{ instancePath: instancePath + "/has_more", schemaPath: "#/properties/has_more/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                          return false;
                        }
                        var valid0 = _errs22 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.items !== void 0) {
                          let data7 = data.items;
                          const _errs24 = errors;
                          if (errors === _errs24) {
                            if (Array.isArray(data7)) {
                              var valid3 = true;
                              const len0 = data7.length;
                              for (let i0 = 0; i0 < len0; i0++) {
                                let data8 = data7[i0];
                                const _errs26 = errors;
                                const _errs27 = errors;
                                let valid4 = false;
                                const _errs28 = errors;
                                if (!validate382(data8, { instancePath: instancePath + "/items/" + i0, parentData: data7, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate382.errors : vErrors.concat(validate382.errors);
                                  errors = vErrors.length;
                                }
                                var _valid2 = _errs28 === errors;
                                valid4 = valid4 || _valid2;
                                if (_valid2) {
                                  var props0 = true;
                                }
                                const _errs29 = errors;
                                if (!validate386(data8, { instancePath: instancePath + "/items/" + i0, parentData: data7, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate386.errors : vErrors.concat(validate386.errors);
                                  errors = vErrors.length;
                                }
                                var _valid2 = _errs29 === errors;
                                valid4 = valid4 || _valid2;
                                if (_valid2) {
                                  if (props0 !== true) {
                                    props0 = true;
                                  }
                                }
                                const _errs30 = errors;
                                if (!validate389(data8, { instancePath: instancePath + "/items/" + i0, parentData: data7, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate389.errors : vErrors.concat(validate389.errors);
                                  errors = vErrors.length;
                                }
                                var _valid2 = _errs30 === errors;
                                valid4 = valid4 || _valid2;
                                if (_valid2) {
                                  if (props0 !== true) {
                                    props0 = true;
                                  }
                                }
                                const _errs31 = errors;
                                if (!validate392(data8, { instancePath: instancePath + "/items/" + i0, parentData: data7, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate392.errors : vErrors.concat(validate392.errors);
                                  errors = vErrors.length;
                                }
                                var _valid2 = _errs31 === errors;
                                valid4 = valid4 || _valid2;
                                if (_valid2) {
                                  if (props0 !== true) {
                                    props0 = true;
                                  }
                                }
                                const _errs32 = errors;
                                if (!validate395(data8, { instancePath: instancePath + "/items/" + i0, parentData: data7, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate395.errors : vErrors.concat(validate395.errors);
                                  errors = vErrors.length;
                                }
                                var _valid2 = _errs32 === errors;
                                valid4 = valid4 || _valid2;
                                if (_valid2) {
                                  if (props0 !== true) {
                                    props0 = true;
                                  }
                                }
                                const _errs33 = errors;
                                if (!validate398(data8, { instancePath: instancePath + "/items/" + i0, parentData: data7, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate398.errors : vErrors.concat(validate398.errors);
                                  errors = vErrors.length;
                                }
                                var _valid2 = _errs33 === errors;
                                valid4 = valid4 || _valid2;
                                if (_valid2) {
                                  if (props0 !== true) {
                                    props0 = true;
                                  }
                                }
                                if (!valid4) {
                                  const err6 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/properties/items/items/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                  if (vErrors === null) {
                                    vErrors = [err6];
                                  } else {
                                    vErrors.push(err6);
                                  }
                                  errors++;
                                  validate381.errors = vErrors;
                                  return false;
                                } else {
                                  errors = _errs27;
                                  if (vErrors !== null) {
                                    if (_errs27) {
                                      vErrors.length = _errs27;
                                    } else {
                                      vErrors = null;
                                    }
                                  }
                                }
                                var valid3 = _errs26 === errors;
                                if (!valid3) {
                                  break;
                                }
                              }
                            } else {
                              validate381.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs24 === errors;
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
      validate381.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate381.errors = vErrors;
  return errors === 0;
}
validate381.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var LineagePage = validate401;
function validate402(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate402.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.name === void 0 && (missing0 = "name") || data.created_at === void 0 && (missing0 = "created_at") || data.run_id === void 0 && (missing0 = "run_id") || data.snapshot_hash === void 0 && (missing0 = "snapshot_hash") || data.revision === void 0 && (missing0 = "revision") || data.status === void 0 && (missing0 = "status")) {
        validate402.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "project_id" || key0 === "name" || key0 === "created_at" || key0 === "run_id" || key0 === "snapshot_hash" || key0 === "revision" || key0 === "status")) {
            validate402.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate402.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate402.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.created_at !== void 0) {
                const _errs6 = errors;
                if (typeof data.created_at !== "string") {
                  validate402.errors = [{ instancePath: instancePath + "/created_at", schemaPath: "#/properties/created_at/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.run_id !== "string") {
                    validate402.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.snapshot_hash !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.snapshot_hash !== "string") {
                      validate402.errors = [{ instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.revision !== void 0) {
                      let data5 = data.revision;
                      const _errs12 = errors;
                      if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)))) {
                        validate402.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.status !== void 0) {
                        const _errs14 = errors;
                        if (typeof data.status !== "string") {
                          validate402.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
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
    } else {
      validate402.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate402.errors = vErrors;
  return errors === 0;
}
validate402.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate401(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate401.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.schema_version === void 0 && (missing0 = "schema_version") || data.project_id === void 0 && (missing0 = "project_id") || data.offset === void 0 && (missing0 = "offset") || data.total === void 0 && (missing0 = "total") || data.has_more === void 0 && (missing0 = "has_more") || data.items === void 0 && (missing0 = "items")) {
        validate401.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "schema_version" || key0 === "project_id" || key0 === "offset" || key0 === "total" || key0 === "has_more" || key0 === "items")) {
            validate401.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.schema_version !== void 0) {
            let data0 = data.schema_version;
            const _errs2 = errors;
            if (typeof data0 !== "string") {
              validate401.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            if ("run-lineage-v1" !== data0) {
              validate401.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "run-lineage-v1" }, message: "must be equal to constant" }];
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
                validate401.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.offset !== void 0) {
                let data2 = data.offset;
                const _errs6 = errors;
                if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                  validate401.errors = [{ instancePath: instancePath + "/offset", schemaPath: "#/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.total !== void 0) {
                  let data3 = data.total;
                  const _errs8 = errors;
                  if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)))) {
                    validate401.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.has_more !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.has_more !== "boolean") {
                      validate401.errors = [{ instancePath: instancePath + "/has_more", schemaPath: "#/properties/has_more/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.items !== void 0) {
                      let data5 = data.items;
                      const _errs12 = errors;
                      if (errors === _errs12) {
                        if (Array.isArray(data5)) {
                          var valid1 = true;
                          const len0 = data5.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs14 = errors;
                            if (!validate402(data5[i0], { instancePath: instancePath + "/items/" + i0, parentData: data5, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate402.errors : vErrors.concat(validate402.errors);
                              errors = vErrors.length;
                            }
                            var valid1 = _errs14 === errors;
                            if (!valid1) {
                              break;
                            }
                          }
                        } else {
                          validate401.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
      }
    } else {
      validate401.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate401.errors = vErrors;
  return errors === 0;
}
validate401.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var ComparePage = validate404;
var schema181 = { "additionalProperties": false, "properties": { "schema_version": { "const": "scientific-comparison-v1", "type": "string" }, "left": { "$ref": "urn:fusionlab:shared#/$defs/LineageRun" }, "right": { "$ref": "urn:fusionlab:shared#/$defs/LineageRun" }, "offset": { "type": "integer" }, "total": { "type": "integer" }, "has_more": { "type": "boolean" }, "input_changed_fields": { "items": { "type": "string" }, "type": "array" }, "input_diff_truncated": { "type": "boolean" }, "rows": { "items": { "$ref": "urn:fusionlab:shared#/$defs/CompareRow" }, "type": "array" }, "ranking_performed": { "const": false, "type": "boolean" }, "claim_scope": { "const": "record_comparison_not_new_prediction_or_validation", "type": "string" } }, "required": ["schema_version", "left", "right", "offset", "total", "has_more", "input_changed_fields", "input_diff_truncated", "rows", "ranking_performed", "claim_scope"], "type": "object" };
function validate405(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate405.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.name === void 0 && (missing0 = "name") || data.created_at === void 0 && (missing0 = "created_at") || data.run_id === void 0 && (missing0 = "run_id") || data.snapshot_hash === void 0 && (missing0 = "snapshot_hash") || data.revision === void 0 && (missing0 = "revision") || data.status === void 0 && (missing0 = "status")) {
        validate405.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "project_id" || key0 === "name" || key0 === "created_at" || key0 === "run_id" || key0 === "snapshot_hash" || key0 === "revision" || key0 === "status")) {
            validate405.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate405.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate405.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.created_at !== void 0) {
                const _errs6 = errors;
                if (typeof data.created_at !== "string") {
                  validate405.errors = [{ instancePath: instancePath + "/created_at", schemaPath: "#/properties/created_at/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.run_id !== "string") {
                    validate405.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.snapshot_hash !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.snapshot_hash !== "string") {
                      validate405.errors = [{ instancePath: instancePath + "/snapshot_hash", schemaPath: "#/properties/snapshot_hash/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.revision !== void 0) {
                      let data5 = data.revision;
                      const _errs12 = errors;
                      if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)))) {
                        validate405.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.status !== void 0) {
                        const _errs14 = errors;
                        if (typeof data.status !== "string") {
                          validate405.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
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
    } else {
      validate405.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate405.errors = vErrors;
  return errors === 0;
}
validate405.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema183 = { "additionalProperties": false, "properties": { "module": { "title": "Module", "type": "string" }, "left": { "anyOf": [{ "$ref": "#/$defs/ComparedValue" }, { "type": "null" }] }, "right": { "anyOf": [{ "$ref": "#/$defs/ComparedValue" }, { "type": "null" }] }, "comparable": { "title": "Comparable", "type": "boolean" }, "reason_codes": { "items": { "type": "string" }, "title": "Reason Codes", "type": "array" }, "metric_definition": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Metric Definition" }, "metric_unit": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Metric Unit" }, "comparison_contract_left": { "anyOf": [{ "additionalProperties": true, "type": "object" }, { "type": "null" }], "title": "Comparison Contract Left" }, "comparison_contract_right": { "anyOf": [{ "additionalProperties": true, "type": "object" }, { "type": "null" }], "title": "Comparison Contract Right" } }, "required": ["module", "left", "right", "comparable", "reason_codes", "metric_definition", "metric_unit", "comparison_contract_left", "comparison_contract_right"], "title": "CompareRow", "type": "object" };
var schema184 = { "additionalProperties": false, "properties": { "record_id": { "title": "Record Id", "type": "string" }, "construct_id": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Construct Id" }, "condition_id": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Condition Id" }, "sequence_identity_sha256": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Sequence Identity Sha256" }, "status": { "title": "Status", "type": "string" }, "claim_scope": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Claim Scope" }, "numerically_solved": { "title": "Numerically Solved", "type": "boolean" }, "evidence_ready": { "title": "Evidence Ready", "type": "boolean" }, "artifact_id": { "title": "Artifact Id", "type": "string" }, "artifact_sha256": { "title": "Artifact Sha256", "type": "string" }, "node_id": { "title": "Node Id", "type": "string" }, "attempt": { "title": "Attempt", "type": "integer" }, "value": { "anyOf": [{ "type": "number" }, { "type": "null" }], "title": "Value" } }, "required": ["record_id", "construct_id", "condition_id", "sequence_identity_sha256", "status", "claim_scope", "numerically_solved", "evidence_ready", "artifact_id", "artifact_sha256", "node_id", "attempt", "value"], "title": "ComparedValue", "type": "object" };
function validate409(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate409.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.record_id === void 0 && (missing0 = "record_id") || data.construct_id === void 0 && (missing0 = "construct_id") || data.condition_id === void 0 && (missing0 = "condition_id") || data.sequence_identity_sha256 === void 0 && (missing0 = "sequence_identity_sha256") || data.status === void 0 && (missing0 = "status") || data.claim_scope === void 0 && (missing0 = "claim_scope") || data.numerically_solved === void 0 && (missing0 = "numerically_solved") || data.evidence_ready === void 0 && (missing0 = "evidence_ready") || data.artifact_id === void 0 && (missing0 = "artifact_id") || data.artifact_sha256 === void 0 && (missing0 = "artifact_sha256") || data.node_id === void 0 && (missing0 = "node_id") || data.attempt === void 0 && (missing0 = "attempt") || data.value === void 0 && (missing0 = "value")) {
        validate409.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema184.properties, key0)) {
            validate409.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.record_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.record_id !== "string") {
              validate409.errors = [{ instancePath: instancePath + "/record_id", schemaPath: "#/properties/record_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.construct_id !== void 0) {
              let data1 = data.construct_id;
              const _errs4 = errors;
              const _errs5 = errors;
              let valid1 = false;
              const _errs6 = errors;
              if (typeof data1 !== "string") {
                const err0 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                const err1 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                const err2 = { instancePath: instancePath + "/construct_id", schemaPath: "#/properties/construct_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                if (vErrors === null) {
                  vErrors = [err2];
                } else {
                  vErrors.push(err2);
                }
                errors++;
                validate409.errors = vErrors;
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
              if (data.condition_id !== void 0) {
                let data2 = data.condition_id;
                const _errs10 = errors;
                const _errs11 = errors;
                let valid2 = false;
                const _errs12 = errors;
                if (typeof data2 !== "string") {
                  const err3 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                  if (vErrors === null) {
                    vErrors = [err3];
                  } else {
                    vErrors.push(err3);
                  }
                  errors++;
                }
                var _valid1 = _errs12 === errors;
                valid2 = valid2 || _valid1;
                const _errs14 = errors;
                if (data2 !== null) {
                  const err4 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err4];
                  } else {
                    vErrors.push(err4);
                  }
                  errors++;
                }
                var _valid1 = _errs14 === errors;
                valid2 = valid2 || _valid1;
                if (!valid2) {
                  const err5 = { instancePath: instancePath + "/condition_id", schemaPath: "#/properties/condition_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err5];
                  } else {
                    vErrors.push(err5);
                  }
                  errors++;
                  validate409.errors = vErrors;
                  return false;
                } else {
                  errors = _errs11;
                  if (vErrors !== null) {
                    if (_errs11) {
                      vErrors.length = _errs11;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs10 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.sequence_identity_sha256 !== void 0) {
                  let data3 = data.sequence_identity_sha256;
                  const _errs16 = errors;
                  const _errs17 = errors;
                  let valid3 = false;
                  const _errs18 = errors;
                  if (typeof data3 !== "string") {
                    const err6 = { instancePath: instancePath + "/sequence_identity_sha256", schemaPath: "#/properties/sequence_identity_sha256/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err6];
                    } else {
                      vErrors.push(err6);
                    }
                    errors++;
                  }
                  var _valid2 = _errs18 === errors;
                  valid3 = valid3 || _valid2;
                  const _errs20 = errors;
                  if (data3 !== null) {
                    const err7 = { instancePath: instancePath + "/sequence_identity_sha256", schemaPath: "#/properties/sequence_identity_sha256/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err7];
                    } else {
                      vErrors.push(err7);
                    }
                    errors++;
                  }
                  var _valid2 = _errs20 === errors;
                  valid3 = valid3 || _valid2;
                  if (!valid3) {
                    const err8 = { instancePath: instancePath + "/sequence_identity_sha256", schemaPath: "#/properties/sequence_identity_sha256/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err8];
                    } else {
                      vErrors.push(err8);
                    }
                    errors++;
                    validate409.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs17;
                    if (vErrors !== null) {
                      if (_errs17) {
                        vErrors.length = _errs17;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs16 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    const _errs22 = errors;
                    if (typeof data.status !== "string") {
                      validate409.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs22 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.claim_scope !== void 0) {
                      let data5 = data.claim_scope;
                      const _errs24 = errors;
                      const _errs25 = errors;
                      let valid4 = false;
                      const _errs26 = errors;
                      if (typeof data5 !== "string") {
                        const err9 = { instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err9];
                        } else {
                          vErrors.push(err9);
                        }
                        errors++;
                      }
                      var _valid3 = _errs26 === errors;
                      valid4 = valid4 || _valid3;
                      const _errs28 = errors;
                      if (data5 !== null) {
                        const err10 = { instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err10];
                        } else {
                          vErrors.push(err10);
                        }
                        errors++;
                      }
                      var _valid3 = _errs28 === errors;
                      valid4 = valid4 || _valid3;
                      if (!valid4) {
                        const err11 = { instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err11];
                        } else {
                          vErrors.push(err11);
                        }
                        errors++;
                        validate409.errors = vErrors;
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
                      if (data.numerically_solved !== void 0) {
                        const _errs30 = errors;
                        if (typeof data.numerically_solved !== "boolean") {
                          validate409.errors = [{ instancePath: instancePath + "/numerically_solved", schemaPath: "#/properties/numerically_solved/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                          return false;
                        }
                        var valid0 = _errs30 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.evidence_ready !== void 0) {
                          const _errs32 = errors;
                          if (typeof data.evidence_ready !== "boolean") {
                            validate409.errors = [{ instancePath: instancePath + "/evidence_ready", schemaPath: "#/properties/evidence_ready/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                            return false;
                          }
                          var valid0 = _errs32 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.artifact_id !== void 0) {
                            const _errs34 = errors;
                            if (typeof data.artifact_id !== "string") {
                              validate409.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid0 = _errs34 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.artifact_sha256 !== void 0) {
                              const _errs36 = errors;
                              if (typeof data.artifact_sha256 !== "string") {
                                validate409.errors = [{ instancePath: instancePath + "/artifact_sha256", schemaPath: "#/properties/artifact_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid0 = _errs36 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.node_id !== void 0) {
                                const _errs38 = errors;
                                if (typeof data.node_id !== "string") {
                                  validate409.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                var valid0 = _errs38 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.attempt !== void 0) {
                                  let data11 = data.attempt;
                                  const _errs40 = errors;
                                  if (!(typeof data11 == "number" && (!(data11 % 1) && !isNaN(data11)))) {
                                    validate409.errors = [{ instancePath: instancePath + "/attempt", schemaPath: "#/properties/attempt/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                    return false;
                                  }
                                  var valid0 = _errs40 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.value !== void 0) {
                                    let data12 = data.value;
                                    const _errs42 = errors;
                                    const _errs43 = errors;
                                    let valid5 = false;
                                    const _errs44 = errors;
                                    if (!(typeof data12 == "number")) {
                                      const err12 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/anyOf/0/type", keyword: "type", params: { type: "number" }, message: "must be number" };
                                      if (vErrors === null) {
                                        vErrors = [err12];
                                      } else {
                                        vErrors.push(err12);
                                      }
                                      errors++;
                                    }
                                    var _valid4 = _errs44 === errors;
                                    valid5 = valid5 || _valid4;
                                    const _errs46 = errors;
                                    if (data12 !== null) {
                                      const err13 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                      if (vErrors === null) {
                                        vErrors = [err13];
                                      } else {
                                        vErrors.push(err13);
                                      }
                                      errors++;
                                    }
                                    var _valid4 = _errs46 === errors;
                                    valid5 = valid5 || _valid4;
                                    if (!valid5) {
                                      const err14 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                      if (vErrors === null) {
                                        vErrors = [err14];
                                      } else {
                                        vErrors.push(err14);
                                      }
                                      errors++;
                                      validate409.errors = vErrors;
                                      return false;
                                    } else {
                                      errors = _errs43;
                                      if (vErrors !== null) {
                                        if (_errs43) {
                                          vErrors.length = _errs43;
                                        } else {
                                          vErrors = null;
                                        }
                                      }
                                    }
                                    var valid0 = _errs42 === errors;
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
    } else {
      validate409.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate409.errors = vErrors;
  return errors === 0;
}
validate409.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate408(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate408.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.module === void 0 && (missing0 = "module") || data.left === void 0 && (missing0 = "left") || data.right === void 0 && (missing0 = "right") || data.comparable === void 0 && (missing0 = "comparable") || data.reason_codes === void 0 && (missing0 = "reason_codes") || data.metric_definition === void 0 && (missing0 = "metric_definition") || data.metric_unit === void 0 && (missing0 = "metric_unit") || data.comparison_contract_left === void 0 && (missing0 = "comparison_contract_left") || data.comparison_contract_right === void 0 && (missing0 = "comparison_contract_right")) {
        validate408.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema183.properties, key0)) {
            validate408.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.module !== void 0) {
            const _errs2 = errors;
            if (typeof data.module !== "string") {
              validate408.errors = [{ instancePath: instancePath + "/module", schemaPath: "#/properties/module/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.left !== void 0) {
              let data1 = data.left;
              const _errs4 = errors;
              const _errs5 = errors;
              let valid1 = false;
              const _errs6 = errors;
              if (!validate409(data1, { instancePath: instancePath + "/left", parentData: data, parentDataProperty: "left", rootData, dynamicAnchors })) {
                vErrors = vErrors === null ? validate409.errors : vErrors.concat(validate409.errors);
                errors = vErrors.length;
              }
              var _valid0 = _errs6 === errors;
              valid1 = valid1 || _valid0;
              const _errs7 = errors;
              if (data1 !== null) {
                const err0 = { instancePath: instancePath + "/left", schemaPath: "#/properties/left/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                if (vErrors === null) {
                  vErrors = [err0];
                } else {
                  vErrors.push(err0);
                }
                errors++;
              }
              var _valid0 = _errs7 === errors;
              valid1 = valid1 || _valid0;
              if (!valid1) {
                const err1 = { instancePath: instancePath + "/left", schemaPath: "#/properties/left/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                if (vErrors === null) {
                  vErrors = [err1];
                } else {
                  vErrors.push(err1);
                }
                errors++;
                validate408.errors = vErrors;
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
              if (data.right !== void 0) {
                let data2 = data.right;
                const _errs9 = errors;
                const _errs10 = errors;
                let valid2 = false;
                const _errs11 = errors;
                if (!validate409(data2, { instancePath: instancePath + "/right", parentData: data, parentDataProperty: "right", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate409.errors : vErrors.concat(validate409.errors);
                  errors = vErrors.length;
                }
                var _valid1 = _errs11 === errors;
                valid2 = valid2 || _valid1;
                const _errs12 = errors;
                if (data2 !== null) {
                  const err2 = { instancePath: instancePath + "/right", schemaPath: "#/properties/right/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err2];
                  } else {
                    vErrors.push(err2);
                  }
                  errors++;
                }
                var _valid1 = _errs12 === errors;
                valid2 = valid2 || _valid1;
                if (!valid2) {
                  const err3 = { instancePath: instancePath + "/right", schemaPath: "#/properties/right/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err3];
                  } else {
                    vErrors.push(err3);
                  }
                  errors++;
                  validate408.errors = vErrors;
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
                var valid0 = _errs9 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.comparable !== void 0) {
                  const _errs14 = errors;
                  if (typeof data.comparable !== "boolean") {
                    validate408.errors = [{ instancePath: instancePath + "/comparable", schemaPath: "#/properties/comparable/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                    return false;
                  }
                  var valid0 = _errs14 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.reason_codes !== void 0) {
                    let data4 = data.reason_codes;
                    const _errs16 = errors;
                    if (errors === _errs16) {
                      if (Array.isArray(data4)) {
                        var valid3 = true;
                        const len0 = data4.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          const _errs18 = errors;
                          if (typeof data4[i0] !== "string") {
                            validate408.errors = [{ instancePath: instancePath + "/reason_codes/" + i0, schemaPath: "#/properties/reason_codes/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid3 = _errs18 === errors;
                          if (!valid3) {
                            break;
                          }
                        }
                      } else {
                        validate408.errors = [{ instancePath: instancePath + "/reason_codes", schemaPath: "#/properties/reason_codes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs16 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.metric_definition !== void 0) {
                      let data6 = data.metric_definition;
                      const _errs20 = errors;
                      const _errs21 = errors;
                      let valid4 = false;
                      const _errs22 = errors;
                      if (typeof data6 !== "string") {
                        const err4 = { instancePath: instancePath + "/metric_definition", schemaPath: "#/properties/metric_definition/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err4];
                        } else {
                          vErrors.push(err4);
                        }
                        errors++;
                      }
                      var _valid2 = _errs22 === errors;
                      valid4 = valid4 || _valid2;
                      const _errs24 = errors;
                      if (data6 !== null) {
                        const err5 = { instancePath: instancePath + "/metric_definition", schemaPath: "#/properties/metric_definition/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err5];
                        } else {
                          vErrors.push(err5);
                        }
                        errors++;
                      }
                      var _valid2 = _errs24 === errors;
                      valid4 = valid4 || _valid2;
                      if (!valid4) {
                        const err6 = { instancePath: instancePath + "/metric_definition", schemaPath: "#/properties/metric_definition/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err6];
                        } else {
                          vErrors.push(err6);
                        }
                        errors++;
                        validate408.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs21;
                        if (vErrors !== null) {
                          if (_errs21) {
                            vErrors.length = _errs21;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.metric_unit !== void 0) {
                        let data7 = data.metric_unit;
                        const _errs26 = errors;
                        const _errs27 = errors;
                        let valid5 = false;
                        const _errs28 = errors;
                        if (typeof data7 !== "string") {
                          const err7 = { instancePath: instancePath + "/metric_unit", schemaPath: "#/properties/metric_unit/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err7];
                          } else {
                            vErrors.push(err7);
                          }
                          errors++;
                        }
                        var _valid3 = _errs28 === errors;
                        valid5 = valid5 || _valid3;
                        const _errs30 = errors;
                        if (data7 !== null) {
                          const err8 = { instancePath: instancePath + "/metric_unit", schemaPath: "#/properties/metric_unit/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err8];
                          } else {
                            vErrors.push(err8);
                          }
                          errors++;
                        }
                        var _valid3 = _errs30 === errors;
                        valid5 = valid5 || _valid3;
                        if (!valid5) {
                          const err9 = { instancePath: instancePath + "/metric_unit", schemaPath: "#/properties/metric_unit/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err9];
                          } else {
                            vErrors.push(err9);
                          }
                          errors++;
                          validate408.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs27;
                          if (vErrors !== null) {
                            if (_errs27) {
                              vErrors.length = _errs27;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs26 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.comparison_contract_left !== void 0) {
                          let data8 = data.comparison_contract_left;
                          const _errs32 = errors;
                          const _errs33 = errors;
                          let valid6 = false;
                          const _errs34 = errors;
                          if (errors === _errs34) {
                            if (data8 && typeof data8 == "object" && !Array.isArray(data8)) {
                            } else {
                              const err10 = { instancePath: instancePath + "/comparison_contract_left", schemaPath: "#/properties/comparison_contract_left/anyOf/0/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                              if (vErrors === null) {
                                vErrors = [err10];
                              } else {
                                vErrors.push(err10);
                              }
                              errors++;
                            }
                          }
                          var _valid4 = _errs34 === errors;
                          valid6 = valid6 || _valid4;
                          const _errs37 = errors;
                          if (data8 !== null) {
                            const err11 = { instancePath: instancePath + "/comparison_contract_left", schemaPath: "#/properties/comparison_contract_left/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err11];
                            } else {
                              vErrors.push(err11);
                            }
                            errors++;
                          }
                          var _valid4 = _errs37 === errors;
                          valid6 = valid6 || _valid4;
                          if (!valid6) {
                            const err12 = { instancePath: instancePath + "/comparison_contract_left", schemaPath: "#/properties/comparison_contract_left/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err12];
                            } else {
                              vErrors.push(err12);
                            }
                            errors++;
                            validate408.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs33;
                            if (vErrors !== null) {
                              if (_errs33) {
                                vErrors.length = _errs33;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs32 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.comparison_contract_right !== void 0) {
                            let data9 = data.comparison_contract_right;
                            const _errs39 = errors;
                            const _errs40 = errors;
                            let valid7 = false;
                            const _errs41 = errors;
                            if (errors === _errs41) {
                              if (data9 && typeof data9 == "object" && !Array.isArray(data9)) {
                              } else {
                                const err13 = { instancePath: instancePath + "/comparison_contract_right", schemaPath: "#/properties/comparison_contract_right/anyOf/0/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                if (vErrors === null) {
                                  vErrors = [err13];
                                } else {
                                  vErrors.push(err13);
                                }
                                errors++;
                              }
                            }
                            var _valid5 = _errs41 === errors;
                            valid7 = valid7 || _valid5;
                            const _errs44 = errors;
                            if (data9 !== null) {
                              const err14 = { instancePath: instancePath + "/comparison_contract_right", schemaPath: "#/properties/comparison_contract_right/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err14];
                              } else {
                                vErrors.push(err14);
                              }
                              errors++;
                            }
                            var _valid5 = _errs44 === errors;
                            valid7 = valid7 || _valid5;
                            if (!valid7) {
                              const err15 = { instancePath: instancePath + "/comparison_contract_right", schemaPath: "#/properties/comparison_contract_right/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err15];
                              } else {
                                vErrors.push(err15);
                              }
                              errors++;
                              validate408.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs40;
                              if (vErrors !== null) {
                                if (_errs40) {
                                  vErrors.length = _errs40;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs39 === errors;
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
    } else {
      validate408.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate408.errors = vErrors;
  return errors === 0;
}
validate408.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate404(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate404.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.schema_version === void 0 && (missing0 = "schema_version") || data.left === void 0 && (missing0 = "left") || data.right === void 0 && (missing0 = "right") || data.offset === void 0 && (missing0 = "offset") || data.total === void 0 && (missing0 = "total") || data.has_more === void 0 && (missing0 = "has_more") || data.input_changed_fields === void 0 && (missing0 = "input_changed_fields") || data.input_diff_truncated === void 0 && (missing0 = "input_diff_truncated") || data.rows === void 0 && (missing0 = "rows") || data.ranking_performed === void 0 && (missing0 = "ranking_performed") || data.claim_scope === void 0 && (missing0 = "claim_scope")) {
        validate404.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema181.properties, key0)) {
            validate404.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.schema_version !== void 0) {
            let data0 = data.schema_version;
            const _errs2 = errors;
            if (typeof data0 !== "string") {
              validate404.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            if ("scientific-comparison-v1" !== data0) {
              validate404.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "scientific-comparison-v1" }, message: "must be equal to constant" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.left !== void 0) {
              const _errs4 = errors;
              if (!validate405(data.left, { instancePath: instancePath + "/left", parentData: data, parentDataProperty: "left", rootData, dynamicAnchors })) {
                vErrors = vErrors === null ? validate405.errors : vErrors.concat(validate405.errors);
                errors = vErrors.length;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.right !== void 0) {
                const _errs5 = errors;
                if (!validate405(data.right, { instancePath: instancePath + "/right", parentData: data, parentDataProperty: "right", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate405.errors : vErrors.concat(validate405.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs5 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.offset !== void 0) {
                  let data3 = data.offset;
                  const _errs6 = errors;
                  if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)))) {
                    validate404.errors = [{ instancePath: instancePath + "/offset", schemaPath: "#/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  var valid0 = _errs6 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.total !== void 0) {
                    let data4 = data.total;
                    const _errs8 = errors;
                    if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)))) {
                      validate404.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    var valid0 = _errs8 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.has_more !== void 0) {
                      const _errs10 = errors;
                      if (typeof data.has_more !== "boolean") {
                        validate404.errors = [{ instancePath: instancePath + "/has_more", schemaPath: "#/properties/has_more/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                        return false;
                      }
                      var valid0 = _errs10 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.input_changed_fields !== void 0) {
                        let data6 = data.input_changed_fields;
                        const _errs12 = errors;
                        if (errors === _errs12) {
                          if (Array.isArray(data6)) {
                            var valid1 = true;
                            const len0 = data6.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              const _errs14 = errors;
                              if (typeof data6[i0] !== "string") {
                                validate404.errors = [{ instancePath: instancePath + "/input_changed_fields/" + i0, schemaPath: "#/properties/input_changed_fields/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid1 = _errs14 === errors;
                              if (!valid1) {
                                break;
                              }
                            }
                          } else {
                            validate404.errors = [{ instancePath: instancePath + "/input_changed_fields", schemaPath: "#/properties/input_changed_fields/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs12 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.input_diff_truncated !== void 0) {
                          const _errs16 = errors;
                          if (typeof data.input_diff_truncated !== "boolean") {
                            validate404.errors = [{ instancePath: instancePath + "/input_diff_truncated", schemaPath: "#/properties/input_diff_truncated/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                            return false;
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.rows !== void 0) {
                            let data9 = data.rows;
                            const _errs18 = errors;
                            if (errors === _errs18) {
                              if (Array.isArray(data9)) {
                                var valid2 = true;
                                const len1 = data9.length;
                                for (let i1 = 0; i1 < len1; i1++) {
                                  const _errs20 = errors;
                                  if (!validate408(data9[i1], { instancePath: instancePath + "/rows/" + i1, parentData: data9, parentDataProperty: i1, rootData, dynamicAnchors })) {
                                    vErrors = vErrors === null ? validate408.errors : vErrors.concat(validate408.errors);
                                    errors = vErrors.length;
                                  }
                                  var valid2 = _errs20 === errors;
                                  if (!valid2) {
                                    break;
                                  }
                                }
                              } else {
                                validate404.errors = [{ instancePath: instancePath + "/rows", schemaPath: "#/properties/rows/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                return false;
                              }
                            }
                            var valid0 = _errs18 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.ranking_performed !== void 0) {
                              let data11 = data.ranking_performed;
                              const _errs21 = errors;
                              if (typeof data11 !== "boolean") {
                                validate404.errors = [{ instancePath: instancePath + "/ranking_performed", schemaPath: "#/properties/ranking_performed/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                return false;
                              }
                              if (false !== data11) {
                                validate404.errors = [{ instancePath: instancePath + "/ranking_performed", schemaPath: "#/properties/ranking_performed/const", keyword: "const", params: { allowedValue: false }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid0 = _errs21 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.claim_scope !== void 0) {
                                let data12 = data.claim_scope;
                                const _errs23 = errors;
                                if (typeof data12 !== "string") {
                                  validate404.errors = [{ instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if ("record_comparison_not_new_prediction_or_validation" !== data12) {
                                  validate404.errors = [{ instancePath: instancePath + "/claim_scope", schemaPath: "#/properties/claim_scope/const", keyword: "const", params: { allowedValue: "record_comparison_not_new_prediction_or_validation" }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid0 = _errs23 === errors;
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
      validate404.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate404.errors = vErrors;
  return errors === 0;
}
validate404.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
export {
  ComparePage,
  EventPage,
  LineagePage,
  ResourcePage,
  RunListView,
  RunSummaryView,
  ScanPage,
  SeriesPage,
  StructurePage,
  TablePage
};
