// <stdin>
var ToolCatalogPage = validate456;
var schema205 = { "additionalProperties": false, "properties": { "id": { "title": "Id", "type": "string" }, "name": { "title": "Name", "type": "string" }, "version": { "title": "Version", "type": "string" }, "description": { "title": "Description", "type": "string" }, "runtime": { "title": "Runtime", "type": "string" }, "status": { "const": "registered_not_tested", "default": "registered_not_tested", "title": "Status", "type": "string" }, "license": { "title": "License", "type": "string" }, "input_names": { "items": { "type": "string" }, "title": "Input Names", "type": "array" }, "output_scope": { "title": "Output Scope", "type": "string" } }, "required": ["id", "name", "version", "description", "runtime", "status", "license", "input_names", "output_scope"], "title": "ModuleTool", "type": "object" };
var func1 = Object.prototype.hasOwnProperty;
function validate457(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate457.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.name === void 0 && (missing0 = "name") || data.version === void 0 && (missing0 = "version") || data.description === void 0 && (missing0 = "description") || data.runtime === void 0 && (missing0 = "runtime") || data.status === void 0 && (missing0 = "status") || data.license === void 0 && (missing0 = "license") || data.input_names === void 0 && (missing0 = "input_names") || data.output_scope === void 0 && (missing0 = "output_scope")) {
        validate457.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema205.properties, key0)) {
            validate457.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate457.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate457.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.version !== void 0) {
                const _errs6 = errors;
                if (typeof data.version !== "string") {
                  validate457.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.description !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.description !== "string") {
                    validate457.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.runtime !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.runtime !== "string") {
                      validate457.errors = [{ instancePath: instancePath + "/runtime", schemaPath: "#/properties/runtime/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.status !== void 0) {
                      let data5 = data.status;
                      const _errs12 = errors;
                      if (typeof data5 !== "string") {
                        validate457.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("registered_not_tested" !== data5) {
                        validate457.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/const", keyword: "const", params: { allowedValue: "registered_not_tested" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.license !== void 0) {
                        const _errs14 = errors;
                        if (typeof data.license !== "string") {
                          validate457.errors = [{ instancePath: instancePath + "/license", schemaPath: "#/properties/license/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.input_names !== void 0) {
                          let data7 = data.input_names;
                          const _errs16 = errors;
                          if (errors === _errs16) {
                            if (Array.isArray(data7)) {
                              var valid1 = true;
                              const len0 = data7.length;
                              for (let i0 = 0; i0 < len0; i0++) {
                                const _errs18 = errors;
                                if (typeof data7[i0] !== "string") {
                                  validate457.errors = [{ instancePath: instancePath + "/input_names/" + i0, schemaPath: "#/properties/input_names/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                var valid1 = _errs18 === errors;
                                if (!valid1) {
                                  break;
                                }
                              }
                            } else {
                              validate457.errors = [{ instancePath: instancePath + "/input_names", schemaPath: "#/properties/input_names/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.output_scope !== void 0) {
                            const _errs20 = errors;
                            if (typeof data.output_scope !== "string") {
                              validate457.errors = [{ instancePath: instancePath + "/output_scope", schemaPath: "#/properties/output_scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
      }
    } else {
      validate457.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate457.errors = vErrors;
  return errors === 0;
}
validate457.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate456(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate456.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.items === void 0 && (missing0 = "items") || data.has_more === void 0 && (missing0 = "has_more")) {
        validate456.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "items" || key0 === "has_more")) {
            validate456.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                  if (!validate457(data0[i0], { instancePath: instancePath + "/items/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate457.errors : vErrors.concat(validate457.errors);
                    errors = vErrors.length;
                  }
                  var valid1 = _errs4 === errors;
                  if (!valid1) {
                    break;
                  }
                }
              } else {
                validate456.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.has_more !== void 0) {
              const _errs5 = errors;
              if (typeof data.has_more !== "boolean") {
                validate456.errors = [{ instancePath: instancePath + "/has_more", schemaPath: "#/properties/has_more/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                return false;
              }
              var valid0 = _errs5 === errors;
            } else {
              var valid0 = true;
            }
          }
        }
      }
    } else {
      validate456.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate456.errors = vErrors;
  return errors === 0;
}
validate456.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var PluginInspectionView = validate459;
function validate460(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate460.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.name === void 0 && (missing0 = "name") || data.description === void 0 && (missing0 = "description") || data.version === void 0 && (missing0 = "version") || data.capability === void 0 && (missing0 = "capability") || data.license === void 0 && (missing0 = "license") || data.runtime === void 0 && (missing0 = "runtime") || data.permissions === void 0 && (missing0 = "permissions")) {
        validate460.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "name" || key0 === "description" || key0 === "version" || key0 === "capability" || key0 === "license" || key0 === "runtime" || key0 === "permissions")) {
            validate460.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate460.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate460.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                  validate460.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate460.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.capability !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.capability !== "string") {
                      validate460.errors = [{ instancePath: instancePath + "/capability", schemaPath: "#/properties/capability/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.license !== void 0) {
                      const _errs12 = errors;
                      if (typeof data.license !== "string") {
                        validate460.errors = [{ instancePath: instancePath + "/license", schemaPath: "#/properties/license/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.runtime !== void 0) {
                        const _errs14 = errors;
                        if (typeof data.runtime !== "string") {
                          validate460.errors = [{ instancePath: instancePath + "/runtime", schemaPath: "#/properties/runtime/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.permissions !== void 0) {
                          let data7 = data.permissions;
                          const _errs16 = errors;
                          if (errors === _errs16) {
                            if (Array.isArray(data7)) {
                              var valid1 = true;
                              const len0 = data7.length;
                              for (let i0 = 0; i0 < len0; i0++) {
                                const _errs18 = errors;
                                if (typeof data7[i0] !== "string") {
                                  validate460.errors = [{ instancePath: instancePath + "/permissions/" + i0, schemaPath: "#/properties/permissions/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                var valid1 = _errs18 === errors;
                                if (!valid1) {
                                  break;
                                }
                              }
                            } else {
                              validate460.errors = [{ instancePath: instancePath + "/permissions", schemaPath: "#/properties/permissions/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
      }
    } else {
      validate460.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate460.errors = vErrors;
  return errors === 0;
}
validate460.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate459(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate459.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.manifest === void 0 && (missing0 = "manifest") || data.hash === void 0 && (missing0 = "hash") || data.sandboxed === void 0 && (missing0 = "sandboxed") || data.trust_required === void 0 && (missing0 = "trust_required") || data.installed === void 0 && (missing0 = "installed") || data.source_path === void 0 && (missing0 = "source_path") || data.capability_requests === void 0 && (missing0 = "capability_requests") || data.enabled === void 0 && (missing0 = "enabled")) {
        validate459.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "manifest" || key0 === "hash" || key0 === "sandboxed" || key0 === "trust_required" || key0 === "installed" || key0 === "source_path" || key0 === "capability_requests" || key0 === "enabled")) {
            validate459.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.manifest !== void 0) {
            const _errs2 = errors;
            if (!validate460(data.manifest, { instancePath: instancePath + "/manifest", parentData: data, parentDataProperty: "manifest", rootData, dynamicAnchors })) {
              vErrors = vErrors === null ? validate460.errors : vErrors.concat(validate460.errors);
              errors = vErrors.length;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.hash !== void 0) {
              const _errs3 = errors;
              if (typeof data.hash !== "string") {
                validate459.errors = [{ instancePath: instancePath + "/hash", schemaPath: "#/properties/hash/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs3 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.sandboxed !== void 0) {
                const _errs5 = errors;
                if (typeof data.sandboxed !== "boolean") {
                  validate459.errors = [{ instancePath: instancePath + "/sandboxed", schemaPath: "#/properties/sandboxed/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                  return false;
                }
                var valid0 = _errs5 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.trust_required !== void 0) {
                  const _errs7 = errors;
                  if (typeof data.trust_required !== "boolean") {
                    validate459.errors = [{ instancePath: instancePath + "/trust_required", schemaPath: "#/properties/trust_required/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                    return false;
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.installed !== void 0) {
                    const _errs9 = errors;
                    if (typeof data.installed !== "boolean") {
                      validate459.errors = [{ instancePath: instancePath + "/installed", schemaPath: "#/properties/installed/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                      return false;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.source_path !== void 0) {
                      let data5 = data.source_path;
                      const _errs11 = errors;
                      const _errs12 = errors;
                      let valid1 = false;
                      const _errs13 = errors;
                      if (typeof data5 !== "string") {
                        const err0 = { instancePath: instancePath + "/source_path", schemaPath: "#/properties/source_path/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      }
                      var _valid0 = _errs13 === errors;
                      valid1 = valid1 || _valid0;
                      const _errs15 = errors;
                      if (data5 !== null) {
                        const err1 = { instancePath: instancePath + "/source_path", schemaPath: "#/properties/source_path/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      }
                      var _valid0 = _errs15 === errors;
                      valid1 = valid1 || _valid0;
                      if (!valid1) {
                        const err2 = { instancePath: instancePath + "/source_path", schemaPath: "#/properties/source_path/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err2];
                        } else {
                          vErrors.push(err2);
                        }
                        errors++;
                        validate459.errors = vErrors;
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
                      var valid0 = _errs11 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.capability_requests !== void 0) {
                        let data6 = data.capability_requests;
                        const _errs17 = errors;
                        if (errors === _errs17) {
                          if (Array.isArray(data6)) {
                            var valid2 = true;
                            const len0 = data6.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              const _errs19 = errors;
                              if (typeof data6[i0] !== "string") {
                                validate459.errors = [{ instancePath: instancePath + "/capability_requests/" + i0, schemaPath: "#/properties/capability_requests/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid2 = _errs19 === errors;
                              if (!valid2) {
                                break;
                              }
                            }
                          } else {
                            validate459.errors = [{ instancePath: instancePath + "/capability_requests", schemaPath: "#/properties/capability_requests/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs17 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.enabled !== void 0) {
                          const _errs21 = errors;
                          if (typeof data.enabled !== "boolean") {
                            validate459.errors = [{ instancePath: instancePath + "/enabled", schemaPath: "#/properties/enabled/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                            return false;
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
        }
      }
    } else {
      validate459.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate459.errors = vErrors;
  return errors === 0;
}
validate459.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var PredictionToolView = validate462;
var schema208 = { "additionalProperties": false, "properties": { "id": { "type": "string" }, "name": { "type": "string" }, "status": { "enum": ["not_configured", "configured_unverified", "available", "failed"], "type": "string" }, "version": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "last_real_check": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "latest_file_id": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "source_reference": { "type": "string" }, "location": { "const": "connected_backend", "type": "string" } }, "required": ["id", "name", "status", "version", "last_real_check", "latest_file_id", "source_reference", "location"], "type": "object" };
function validate462(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate462.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.name === void 0 && (missing0 = "name") || data.status === void 0 && (missing0 = "status") || data.version === void 0 && (missing0 = "version") || data.last_real_check === void 0 && (missing0 = "last_real_check") || data.latest_file_id === void 0 && (missing0 = "latest_file_id") || data.source_reference === void 0 && (missing0 = "source_reference") || data.location === void 0 && (missing0 = "location")) {
        validate462.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "name" || key0 === "status" || key0 === "version" || key0 === "last_real_check" || key0 === "latest_file_id" || key0 === "source_reference" || key0 === "location")) {
            validate462.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate462.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate462.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.status !== void 0) {
                let data2 = data.status;
                const _errs6 = errors;
                if (typeof data2 !== "string") {
                  validate462.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if (!(data2 === "not_configured" || data2 === "configured_unverified" || data2 === "available" || data2 === "failed")) {
                  validate462.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema208.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.version !== void 0) {
                  let data3 = data.version;
                  const _errs8 = errors;
                  const _errs9 = errors;
                  let valid1 = false;
                  const _errs10 = errors;
                  if (typeof data3 !== "string") {
                    const err0 = { instancePath: instancePath + "/version", schemaPath: "#/properties/version/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                    const err1 = { instancePath: instancePath + "/version", schemaPath: "#/properties/version/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err2 = { instancePath: instancePath + "/version", schemaPath: "#/properties/version/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate462.errors = vErrors;
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
                  if (data.last_real_check !== void 0) {
                    let data4 = data.last_real_check;
                    const _errs14 = errors;
                    const _errs15 = errors;
                    let valid2 = false;
                    const _errs16 = errors;
                    if (typeof data4 !== "string") {
                      const err3 = { instancePath: instancePath + "/last_real_check", schemaPath: "#/properties/last_real_check/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                      const err4 = { instancePath: instancePath + "/last_real_check", schemaPath: "#/properties/last_real_check/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                      const err5 = { instancePath: instancePath + "/last_real_check", schemaPath: "#/properties/last_real_check/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err5];
                      } else {
                        vErrors.push(err5);
                      }
                      errors++;
                      validate462.errors = vErrors;
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
                    if (data.latest_file_id !== void 0) {
                      let data5 = data.latest_file_id;
                      const _errs20 = errors;
                      const _errs21 = errors;
                      let valid3 = false;
                      const _errs22 = errors;
                      if (typeof data5 !== "string") {
                        const err6 = { instancePath: instancePath + "/latest_file_id", schemaPath: "#/properties/latest_file_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                        const err7 = { instancePath: instancePath + "/latest_file_id", schemaPath: "#/properties/latest_file_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                        const err8 = { instancePath: instancePath + "/latest_file_id", schemaPath: "#/properties/latest_file_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err8];
                        } else {
                          vErrors.push(err8);
                        }
                        errors++;
                        validate462.errors = vErrors;
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
                      if (data.source_reference !== void 0) {
                        const _errs26 = errors;
                        if (typeof data.source_reference !== "string") {
                          validate462.errors = [{ instancePath: instancePath + "/source_reference", schemaPath: "#/properties/source_reference/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs26 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.location !== void 0) {
                          let data7 = data.location;
                          const _errs28 = errors;
                          if (typeof data7 !== "string") {
                            validate462.errors = [{ instancePath: instancePath + "/location", schemaPath: "#/properties/location/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("connected_backend" !== data7) {
                            validate462.errors = [{ instancePath: instancePath + "/location", schemaPath: "#/properties/location/const", keyword: "const", params: { allowedValue: "connected_backend" }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid0 = _errs28 === errors;
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
      validate462.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate462.errors = vErrors;
  return errors === 0;
}
validate462.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var AssistantSettingsView = validate463;
var schema209 = { "additionalProperties": false, "properties": { "profile_id": { "type": "string" }, "provider": { "enum": ["none", "compatible_api", "local_endpoint"], "type": "string" }, "model": { "type": "string" }, "has_secret": { "type": "boolean" }, "configured": { "type": "boolean" }, "local_workspace": { "type": "boolean" }, "style_instructions": { "type": "string" }, "save_scope": { "const": "private_workspace", "type": "string" }, "capabilities": { "additionalProperties": { "type": "string" }, "type": "object" }, "tested_at": { "anyOf": [{ "type": "string" }, { "type": "null" }] } }, "required": ["profile_id", "provider", "model", "has_secret", "configured", "local_workspace", "style_instructions", "save_scope", "capabilities", "tested_at"], "type": "object" };
function validate463(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate463.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.profile_id === void 0 && (missing0 = "profile_id") || data.provider === void 0 && (missing0 = "provider") || data.model === void 0 && (missing0 = "model") || data.has_secret === void 0 && (missing0 = "has_secret") || data.configured === void 0 && (missing0 = "configured") || data.local_workspace === void 0 && (missing0 = "local_workspace") || data.style_instructions === void 0 && (missing0 = "style_instructions") || data.save_scope === void 0 && (missing0 = "save_scope") || data.capabilities === void 0 && (missing0 = "capabilities") || data.tested_at === void 0 && (missing0 = "tested_at")) {
        validate463.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema209.properties, key0)) {
            validate463.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.profile_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.profile_id !== "string") {
              validate463.errors = [{ instancePath: instancePath + "/profile_id", schemaPath: "#/properties/profile_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.provider !== void 0) {
              let data1 = data.provider;
              const _errs4 = errors;
              if (typeof data1 !== "string") {
                validate463.errors = [{ instancePath: instancePath + "/provider", schemaPath: "#/properties/provider/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              if (!(data1 === "none" || data1 === "compatible_api" || data1 === "local_endpoint")) {
                validate463.errors = [{ instancePath: instancePath + "/provider", schemaPath: "#/properties/provider/enum", keyword: "enum", params: { allowedValues: schema209.properties.provider.enum }, message: "must be equal to one of the allowed values" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.model !== void 0) {
                const _errs6 = errors;
                if (typeof data.model !== "string") {
                  validate463.errors = [{ instancePath: instancePath + "/model", schemaPath: "#/properties/model/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.has_secret !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.has_secret !== "boolean") {
                    validate463.errors = [{ instancePath: instancePath + "/has_secret", schemaPath: "#/properties/has_secret/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.configured !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.configured !== "boolean") {
                      validate463.errors = [{ instancePath: instancePath + "/configured", schemaPath: "#/properties/configured/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.local_workspace !== void 0) {
                      const _errs12 = errors;
                      if (typeof data.local_workspace !== "boolean") {
                        validate463.errors = [{ instancePath: instancePath + "/local_workspace", schemaPath: "#/properties/local_workspace/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.style_instructions !== void 0) {
                        const _errs14 = errors;
                        if (typeof data.style_instructions !== "string") {
                          validate463.errors = [{ instancePath: instancePath + "/style_instructions", schemaPath: "#/properties/style_instructions/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.save_scope !== void 0) {
                          let data7 = data.save_scope;
                          const _errs16 = errors;
                          if (typeof data7 !== "string") {
                            validate463.errors = [{ instancePath: instancePath + "/save_scope", schemaPath: "#/properties/save_scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("private_workspace" !== data7) {
                            validate463.errors = [{ instancePath: instancePath + "/save_scope", schemaPath: "#/properties/save_scope/const", keyword: "const", params: { allowedValue: "private_workspace" }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.capabilities !== void 0) {
                            let data8 = data.capabilities;
                            const _errs18 = errors;
                            if (errors === _errs18) {
                              if (data8 && typeof data8 == "object" && !Array.isArray(data8)) {
                                for (const key1 in data8) {
                                  const _errs21 = errors;
                                  if (typeof data8[key1] !== "string") {
                                    validate463.errors = [{ instancePath: instancePath + "/capabilities/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/capabilities/additionalProperties/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  var valid1 = _errs21 === errors;
                                  if (!valid1) {
                                    break;
                                  }
                                }
                              } else {
                                validate463.errors = [{ instancePath: instancePath + "/capabilities", schemaPath: "#/properties/capabilities/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                return false;
                              }
                            }
                            var valid0 = _errs18 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.tested_at !== void 0) {
                              let data10 = data.tested_at;
                              const _errs23 = errors;
                              const _errs24 = errors;
                              let valid2 = false;
                              const _errs25 = errors;
                              if (typeof data10 !== "string") {
                                const err0 = { instancePath: instancePath + "/tested_at", schemaPath: "#/properties/tested_at/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err0];
                                } else {
                                  vErrors.push(err0);
                                }
                                errors++;
                              }
                              var _valid0 = _errs25 === errors;
                              valid2 = valid2 || _valid0;
                              const _errs27 = errors;
                              if (data10 !== null) {
                                const err1 = { instancePath: instancePath + "/tested_at", schemaPath: "#/properties/tested_at/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                if (vErrors === null) {
                                  vErrors = [err1];
                                } else {
                                  vErrors.push(err1);
                                }
                                errors++;
                              }
                              var _valid0 = _errs27 === errors;
                              valid2 = valid2 || _valid0;
                              if (!valid2) {
                                const err2 = { instancePath: instancePath + "/tested_at", schemaPath: "#/properties/tested_at/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                if (vErrors === null) {
                                  vErrors = [err2];
                                } else {
                                  vErrors.push(err2);
                                }
                                errors++;
                                validate463.errors = vErrors;
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
      validate463.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate463.errors = vErrors;
  return errors === 0;
}
validate463.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var AssistantProbeView = validate464;
function validate464(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate464.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.capabilities === void 0 && (missing0 = "capabilities") || data.models === void 0 && (missing0 = "models") || data.tested_at === void 0 && (missing0 = "tested_at") || data.explanation === void 0 && (missing0 = "explanation")) {
        validate464.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "capabilities" || key0 === "models" || key0 === "tested_at" || key0 === "explanation")) {
            validate464.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.capabilities !== void 0) {
            let data0 = data.capabilities;
            const _errs2 = errors;
            if (errors === _errs2) {
              if (data0 && typeof data0 == "object" && !Array.isArray(data0)) {
                for (const key1 in data0) {
                  const _errs5 = errors;
                  if (typeof data0[key1] !== "string") {
                    validate464.errors = [{ instancePath: instancePath + "/capabilities/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/capabilities/additionalProperties/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid1 = _errs5 === errors;
                  if (!valid1) {
                    break;
                  }
                }
              } else {
                validate464.errors = [{ instancePath: instancePath + "/capabilities", schemaPath: "#/properties/capabilities/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.models !== void 0) {
              let data2 = data.models;
              const _errs7 = errors;
              if (errors === _errs7) {
                if (Array.isArray(data2)) {
                  var valid2 = true;
                  const len0 = data2.length;
                  for (let i0 = 0; i0 < len0; i0++) {
                    const _errs9 = errors;
                    if (typeof data2[i0] !== "string") {
                      validate464.errors = [{ instancePath: instancePath + "/models/" + i0, schemaPath: "#/properties/models/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid2 = _errs9 === errors;
                    if (!valid2) {
                      break;
                    }
                  }
                } else {
                  validate464.errors = [{ instancePath: instancePath + "/models", schemaPath: "#/properties/models/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                  return false;
                }
              }
              var valid0 = _errs7 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.tested_at !== void 0) {
                const _errs11 = errors;
                if (typeof data.tested_at !== "string") {
                  validate464.errors = [{ instancePath: instancePath + "/tested_at", schemaPath: "#/properties/tested_at/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs11 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.explanation !== void 0) {
                  const _errs13 = errors;
                  if (typeof data.explanation !== "string") {
                    validate464.errors = [{ instancePath: instancePath + "/explanation", schemaPath: "#/properties/explanation/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
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
    } else {
      validate464.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate464.errors = vErrors;
  return errors === 0;
}
validate464.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var SkillView = validate465;
var schema211 = { "additionalProperties": false, "properties": { "id": { "type": "string" }, "name": { "type": "string" }, "description": { "type": "string" }, "trigger": { "type": "string" }, "version": { "type": "string" }, "source": { "type": "string" }, "license": { "type": "string" }, "enabled": { "type": "boolean" }, "revision": { "type": "integer" }, "text": { "type": "string" }, "updated_at": { "type": "string" }, "execution": { "const": "instructions_only", "type": "string" } }, "required": ["id", "name", "description", "trigger", "version", "source", "license", "enabled", "revision", "text", "updated_at", "execution"], "type": "object" };
function validate465(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate465.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.name === void 0 && (missing0 = "name") || data.description === void 0 && (missing0 = "description") || data.trigger === void 0 && (missing0 = "trigger") || data.version === void 0 && (missing0 = "version") || data.source === void 0 && (missing0 = "source") || data.license === void 0 && (missing0 = "license") || data.enabled === void 0 && (missing0 = "enabled") || data.revision === void 0 && (missing0 = "revision") || data.text === void 0 && (missing0 = "text") || data.updated_at === void 0 && (missing0 = "updated_at") || data.execution === void 0 && (missing0 = "execution")) {
        validate465.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema211.properties, key0)) {
            validate465.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate465.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate465.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                  validate465.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.trigger !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.trigger !== "string") {
                    validate465.errors = [{ instancePath: instancePath + "/trigger", schemaPath: "#/properties/trigger/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.version !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.version !== "string") {
                      validate465.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.source !== void 0) {
                      const _errs12 = errors;
                      if (typeof data.source !== "string") {
                        validate465.errors = [{ instancePath: instancePath + "/source", schemaPath: "#/properties/source/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.license !== void 0) {
                        const _errs14 = errors;
                        if (typeof data.license !== "string") {
                          validate465.errors = [{ instancePath: instancePath + "/license", schemaPath: "#/properties/license/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.enabled !== void 0) {
                          const _errs16 = errors;
                          if (typeof data.enabled !== "boolean") {
                            validate465.errors = [{ instancePath: instancePath + "/enabled", schemaPath: "#/properties/enabled/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                            return false;
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.revision !== void 0) {
                            let data8 = data.revision;
                            const _errs18 = errors;
                            if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)))) {
                              validate465.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            var valid0 = _errs18 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.text !== void 0) {
                              const _errs20 = errors;
                              if (typeof data.text !== "string") {
                                validate465.errors = [{ instancePath: instancePath + "/text", schemaPath: "#/properties/text/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid0 = _errs20 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.updated_at !== void 0) {
                                const _errs22 = errors;
                                if (typeof data.updated_at !== "string") {
                                  validate465.errors = [{ instancePath: instancePath + "/updated_at", schemaPath: "#/properties/updated_at/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                var valid0 = _errs22 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.execution !== void 0) {
                                  let data11 = data.execution;
                                  const _errs24 = errors;
                                  if (typeof data11 !== "string") {
                                    validate465.errors = [{ instancePath: instancePath + "/execution", schemaPath: "#/properties/execution/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("instructions_only" !== data11) {
                                    validate465.errors = [{ instancePath: instancePath + "/execution", schemaPath: "#/properties/execution/const", keyword: "const", params: { allowedValue: "instructions_only" }, message: "must be equal to constant" }];
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
        }
      }
    } else {
      validate465.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate465.errors = vErrors;
  return errors === 0;
}
validate465.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var SkillPage = validate466;
var schema213 = { "additionalProperties": false, "properties": { "id": { "title": "Id", "type": "string" }, "name": { "title": "Name", "type": "string" }, "description": { "title": "Description", "type": "string" }, "trigger": { "title": "Trigger", "type": "string" }, "version": { "title": "Version", "type": "string" }, "source": { "title": "Source", "type": "string" }, "license": { "title": "License", "type": "string" }, "enabled": { "title": "Enabled", "type": "boolean" }, "revision": { "title": "Revision", "type": "integer" }, "text": { "title": "Text", "type": "string" }, "updated_at": { "title": "Updated At", "type": "string" }, "execution": { "const": "instructions_only", "default": "instructions_only", "title": "Execution", "type": "string" } }, "required": ["id", "name", "description", "trigger", "version", "source", "license", "enabled", "revision", "text", "updated_at", "execution"], "title": "SkillView", "type": "object" };
function validate467(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate467.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.name === void 0 && (missing0 = "name") || data.description === void 0 && (missing0 = "description") || data.trigger === void 0 && (missing0 = "trigger") || data.version === void 0 && (missing0 = "version") || data.source === void 0 && (missing0 = "source") || data.license === void 0 && (missing0 = "license") || data.enabled === void 0 && (missing0 = "enabled") || data.revision === void 0 && (missing0 = "revision") || data.text === void 0 && (missing0 = "text") || data.updated_at === void 0 && (missing0 = "updated_at") || data.execution === void 0 && (missing0 = "execution")) {
        validate467.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema213.properties, key0)) {
            validate467.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate467.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate467.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                  validate467.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.trigger !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.trigger !== "string") {
                    validate467.errors = [{ instancePath: instancePath + "/trigger", schemaPath: "#/properties/trigger/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.version !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.version !== "string") {
                      validate467.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.source !== void 0) {
                      const _errs12 = errors;
                      if (typeof data.source !== "string") {
                        validate467.errors = [{ instancePath: instancePath + "/source", schemaPath: "#/properties/source/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.license !== void 0) {
                        const _errs14 = errors;
                        if (typeof data.license !== "string") {
                          validate467.errors = [{ instancePath: instancePath + "/license", schemaPath: "#/properties/license/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.enabled !== void 0) {
                          const _errs16 = errors;
                          if (typeof data.enabled !== "boolean") {
                            validate467.errors = [{ instancePath: instancePath + "/enabled", schemaPath: "#/properties/enabled/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                            return false;
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.revision !== void 0) {
                            let data8 = data.revision;
                            const _errs18 = errors;
                            if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)))) {
                              validate467.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            var valid0 = _errs18 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.text !== void 0) {
                              const _errs20 = errors;
                              if (typeof data.text !== "string") {
                                validate467.errors = [{ instancePath: instancePath + "/text", schemaPath: "#/properties/text/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid0 = _errs20 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.updated_at !== void 0) {
                                const _errs22 = errors;
                                if (typeof data.updated_at !== "string") {
                                  validate467.errors = [{ instancePath: instancePath + "/updated_at", schemaPath: "#/properties/updated_at/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                var valid0 = _errs22 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.execution !== void 0) {
                                  let data11 = data.execution;
                                  const _errs24 = errors;
                                  if (typeof data11 !== "string") {
                                    validate467.errors = [{ instancePath: instancePath + "/execution", schemaPath: "#/properties/execution/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("instructions_only" !== data11) {
                                    validate467.errors = [{ instancePath: instancePath + "/execution", schemaPath: "#/properties/execution/const", keyword: "const", params: { allowedValue: "instructions_only" }, message: "must be equal to constant" }];
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
        }
      }
    } else {
      validate467.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate467.errors = vErrors;
  return errors === 0;
}
validate467.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate466(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate466.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.items === void 0 && (missing0 = "items") || data.has_more === void 0 && (missing0 = "has_more")) {
        validate466.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "items" || key0 === "has_more")) {
            validate466.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                  if (!validate467(data0[i0], { instancePath: instancePath + "/items/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate467.errors : vErrors.concat(validate467.errors);
                    errors = vErrors.length;
                  }
                  var valid1 = _errs4 === errors;
                  if (!valid1) {
                    break;
                  }
                }
              } else {
                validate466.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.has_more !== void 0) {
              const _errs5 = errors;
              if (typeof data.has_more !== "boolean") {
                validate466.errors = [{ instancePath: instancePath + "/has_more", schemaPath: "#/properties/has_more/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                return false;
              }
              var valid0 = _errs5 === errors;
            } else {
              var valid0 = true;
            }
          }
        }
      }
    } else {
      validate466.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate466.errors = vErrors;
  return errors === 0;
}
validate466.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var MethodDefinition = validate469;
var schema214 = { "additionalProperties": false, "properties": { "id": { "type": "string" }, "version": { "type": "string" }, "title": { "type": "string" }, "scope": { "type": "string" }, "source_reference": { "type": "string" }, "source_version": { "type": "string" }, "steps": { "items": { "$ref": "urn:fusionlab:shared#/$defs/MethodStep" }, "type": "array" }, "formulas": { "items": { "$ref": "urn:fusionlab:shared#/$defs/MethodFormula" }, "type": "array" }, "symbols": { "additionalProperties": { "type": "string" }, "type": "object" }, "tools": { "items": { "type": "string" }, "type": "array" }, "discrepancies": { "items": { "type": "string" }, "type": "array" }, "formal_formula_editable": { "const": false, "type": "boolean" } }, "required": ["id", "version", "title", "scope", "source_reference", "source_version", "steps", "formulas", "symbols", "tools", "discrepancies", "formal_formula_editable"], "type": "object" };
function validate470(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate470.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.title === void 0 && (missing0 = "title") || data.description === void 0 && (missing0 = "description")) {
        validate470.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "title" || key0 === "description")) {
            validate470.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate470.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.title !== void 0) {
              const _errs4 = errors;
              if (typeof data.title !== "string") {
                validate470.errors = [{ instancePath: instancePath + "/title", schemaPath: "#/properties/title/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                  validate470.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
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
      validate470.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate470.errors = vErrors;
  return errors === 0;
}
validate470.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var schema216 = { "additionalProperties": false, "properties": { "id": { "title": "Id", "type": "string" }, "title": { "title": "Title", "type": "string" }, "latex": { "title": "Latex", "type": "string" }, "assumptions": { "items": { "type": "string" }, "title": "Assumptions", "type": "array" }, "implementation": { "items": { "type": "string" }, "title": "Implementation", "type": "array" }, "status": { "default": "implemented", "enum": ["implemented", "conditional", "undefined_in_source", "source_discrepancy"], "title": "Status", "type": "string" } }, "required": ["id", "title", "latex", "assumptions", "implementation", "status"], "title": "MethodFormula", "type": "object" };
function validate472(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate472.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.title === void 0 && (missing0 = "title") || data.latex === void 0 && (missing0 = "latex") || data.assumptions === void 0 && (missing0 = "assumptions") || data.implementation === void 0 && (missing0 = "implementation") || data.status === void 0 && (missing0 = "status")) {
        validate472.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "title" || key0 === "latex" || key0 === "assumptions" || key0 === "implementation" || key0 === "status")) {
            validate472.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate472.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.title !== void 0) {
              const _errs4 = errors;
              if (typeof data.title !== "string") {
                validate472.errors = [{ instancePath: instancePath + "/title", schemaPath: "#/properties/title/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.latex !== void 0) {
                const _errs6 = errors;
                if (typeof data.latex !== "string") {
                  validate472.errors = [{ instancePath: instancePath + "/latex", schemaPath: "#/properties/latex/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.assumptions !== void 0) {
                  let data3 = data.assumptions;
                  const _errs8 = errors;
                  if (errors === _errs8) {
                    if (Array.isArray(data3)) {
                      var valid1 = true;
                      const len0 = data3.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs10 = errors;
                        if (typeof data3[i0] !== "string") {
                          validate472.errors = [{ instancePath: instancePath + "/assumptions/" + i0, schemaPath: "#/properties/assumptions/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid1 = _errs10 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    } else {
                      validate472.errors = [{ instancePath: instancePath + "/assumptions", schemaPath: "#/properties/assumptions/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.implementation !== void 0) {
                    let data5 = data.implementation;
                    const _errs12 = errors;
                    if (errors === _errs12) {
                      if (Array.isArray(data5)) {
                        var valid2 = true;
                        const len1 = data5.length;
                        for (let i1 = 0; i1 < len1; i1++) {
                          const _errs14 = errors;
                          if (typeof data5[i1] !== "string") {
                            validate472.errors = [{ instancePath: instancePath + "/implementation/" + i1, schemaPath: "#/properties/implementation/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid2 = _errs14 === errors;
                          if (!valid2) {
                            break;
                          }
                        }
                      } else {
                        validate472.errors = [{ instancePath: instancePath + "/implementation", schemaPath: "#/properties/implementation/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs12 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.status !== void 0) {
                      let data7 = data.status;
                      const _errs16 = errors;
                      if (typeof data7 !== "string") {
                        validate472.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if (!(data7 === "implemented" || data7 === "conditional" || data7 === "undefined_in_source" || data7 === "source_discrepancy")) {
                        validate472.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema216.properties.status.enum }, message: "must be equal to one of the allowed values" }];
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
    } else {
      validate472.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate472.errors = vErrors;
  return errors === 0;
}
validate472.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate469(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate469.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.version === void 0 && (missing0 = "version") || data.title === void 0 && (missing0 = "title") || data.scope === void 0 && (missing0 = "scope") || data.source_reference === void 0 && (missing0 = "source_reference") || data.source_version === void 0 && (missing0 = "source_version") || data.steps === void 0 && (missing0 = "steps") || data.formulas === void 0 && (missing0 = "formulas") || data.symbols === void 0 && (missing0 = "symbols") || data.tools === void 0 && (missing0 = "tools") || data.discrepancies === void 0 && (missing0 = "discrepancies") || data.formal_formula_editable === void 0 && (missing0 = "formal_formula_editable")) {
        validate469.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema214.properties, key0)) {
            validate469.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate469.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate469.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.title !== void 0) {
                const _errs6 = errors;
                if (typeof data.title !== "string") {
                  validate469.errors = [{ instancePath: instancePath + "/title", schemaPath: "#/properties/title/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scope !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.scope !== "string") {
                    validate469.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/properties/scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.source_reference !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.source_reference !== "string") {
                      validate469.errors = [{ instancePath: instancePath + "/source_reference", schemaPath: "#/properties/source_reference/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.source_version !== void 0) {
                      const _errs12 = errors;
                      if (typeof data.source_version !== "string") {
                        validate469.errors = [{ instancePath: instancePath + "/source_version", schemaPath: "#/properties/source_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.steps !== void 0) {
                        let data6 = data.steps;
                        const _errs14 = errors;
                        if (errors === _errs14) {
                          if (Array.isArray(data6)) {
                            var valid1 = true;
                            const len0 = data6.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              const _errs16 = errors;
                              if (!validate470(data6[i0], { instancePath: instancePath + "/steps/" + i0, parentData: data6, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate470.errors : vErrors.concat(validate470.errors);
                                errors = vErrors.length;
                              }
                              var valid1 = _errs16 === errors;
                              if (!valid1) {
                                break;
                              }
                            }
                          } else {
                            validate469.errors = [{ instancePath: instancePath + "/steps", schemaPath: "#/properties/steps/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.formulas !== void 0) {
                          let data8 = data.formulas;
                          const _errs17 = errors;
                          if (errors === _errs17) {
                            if (Array.isArray(data8)) {
                              var valid2 = true;
                              const len1 = data8.length;
                              for (let i1 = 0; i1 < len1; i1++) {
                                const _errs19 = errors;
                                if (!validate472(data8[i1], { instancePath: instancePath + "/formulas/" + i1, parentData: data8, parentDataProperty: i1, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate472.errors : vErrors.concat(validate472.errors);
                                  errors = vErrors.length;
                                }
                                var valid2 = _errs19 === errors;
                                if (!valid2) {
                                  break;
                                }
                              }
                            } else {
                              validate469.errors = [{ instancePath: instancePath + "/formulas", schemaPath: "#/properties/formulas/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs17 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.symbols !== void 0) {
                            let data10 = data.symbols;
                            const _errs20 = errors;
                            if (errors === _errs20) {
                              if (data10 && typeof data10 == "object" && !Array.isArray(data10)) {
                                for (const key1 in data10) {
                                  const _errs23 = errors;
                                  if (typeof data10[key1] !== "string") {
                                    validate469.errors = [{ instancePath: instancePath + "/symbols/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/symbols/additionalProperties/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  var valid3 = _errs23 === errors;
                                  if (!valid3) {
                                    break;
                                  }
                                }
                              } else {
                                validate469.errors = [{ instancePath: instancePath + "/symbols", schemaPath: "#/properties/symbols/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                return false;
                              }
                            }
                            var valid0 = _errs20 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.tools !== void 0) {
                              let data12 = data.tools;
                              const _errs25 = errors;
                              if (errors === _errs25) {
                                if (Array.isArray(data12)) {
                                  var valid4 = true;
                                  const len2 = data12.length;
                                  for (let i2 = 0; i2 < len2; i2++) {
                                    const _errs27 = errors;
                                    if (typeof data12[i2] !== "string") {
                                      validate469.errors = [{ instancePath: instancePath + "/tools/" + i2, schemaPath: "#/properties/tools/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                    var valid4 = _errs27 === errors;
                                    if (!valid4) {
                                      break;
                                    }
                                  }
                                } else {
                                  validate469.errors = [{ instancePath: instancePath + "/tools", schemaPath: "#/properties/tools/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs25 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.discrepancies !== void 0) {
                                let data14 = data.discrepancies;
                                const _errs29 = errors;
                                if (errors === _errs29) {
                                  if (Array.isArray(data14)) {
                                    var valid5 = true;
                                    const len3 = data14.length;
                                    for (let i3 = 0; i3 < len3; i3++) {
                                      const _errs31 = errors;
                                      if (typeof data14[i3] !== "string") {
                                        validate469.errors = [{ instancePath: instancePath + "/discrepancies/" + i3, schemaPath: "#/properties/discrepancies/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      var valid5 = _errs31 === errors;
                                      if (!valid5) {
                                        break;
                                      }
                                    }
                                  } else {
                                    validate469.errors = [{ instancePath: instancePath + "/discrepancies", schemaPath: "#/properties/discrepancies/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                    return false;
                                  }
                                }
                                var valid0 = _errs29 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.formal_formula_editable !== void 0) {
                                  let data16 = data.formal_formula_editable;
                                  const _errs33 = errors;
                                  if (typeof data16 !== "boolean") {
                                    validate469.errors = [{ instancePath: instancePath + "/formal_formula_editable", schemaPath: "#/properties/formal_formula_editable/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                    return false;
                                  }
                                  if (false !== data16) {
                                    validate469.errors = [{ instancePath: instancePath + "/formal_formula_editable", schemaPath: "#/properties/formal_formula_editable/const", keyword: "const", params: { allowedValue: false }, message: "must be equal to constant" }];
                                    return false;
                                  }
                                  var valid0 = _errs33 === errors;
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
      validate469.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate469.errors = vErrors;
  return errors === 0;
}
validate469.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var ModuleMethodView = validate474;
var schema218 = { "additionalProperties": false, "properties": { "id": { "title": "Id", "type": "string" }, "version": { "title": "Version", "type": "string" }, "title": { "title": "Title", "type": "string" }, "scope": { "title": "Scope", "type": "string" }, "source_reference": { "title": "Source Reference", "type": "string" }, "source_version": { "title": "Source Version", "type": "string" }, "steps": { "items": { "$ref": "#/$defs/MethodStep" }, "title": "Steps", "type": "array" }, "formulas": { "items": { "$ref": "#/$defs/MethodFormula" }, "title": "Formulas", "type": "array" }, "symbols": { "additionalProperties": { "type": "string" }, "title": "Symbols", "type": "object" }, "tools": { "items": { "type": "string" }, "title": "Tools", "type": "array" }, "discrepancies": { "items": { "type": "string" }, "title": "Discrepancies", "type": "array" }, "formal_formula_editable": { "const": false, "default": false, "title": "Formal Formula Editable", "type": "boolean" } }, "required": ["id", "version", "title", "scope", "source_reference", "source_version", "steps", "formulas", "symbols", "tools", "discrepancies", "formal_formula_editable"], "title": "MethodDefinition", "type": "object" };
function validate476(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate476.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.title === void 0 && (missing0 = "title") || data.description === void 0 && (missing0 = "description")) {
        validate476.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "title" || key0 === "description")) {
            validate476.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate476.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.title !== void 0) {
              const _errs4 = errors;
              if (typeof data.title !== "string") {
                validate476.errors = [{ instancePath: instancePath + "/title", schemaPath: "#/properties/title/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                  validate476.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
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
      validate476.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate476.errors = vErrors;
  return errors === 0;
}
validate476.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate478(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate478.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.title === void 0 && (missing0 = "title") || data.latex === void 0 && (missing0 = "latex") || data.assumptions === void 0 && (missing0 = "assumptions") || data.implementation === void 0 && (missing0 = "implementation") || data.status === void 0 && (missing0 = "status")) {
        validate478.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "title" || key0 === "latex" || key0 === "assumptions" || key0 === "implementation" || key0 === "status")) {
            validate478.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate478.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.title !== void 0) {
              const _errs4 = errors;
              if (typeof data.title !== "string") {
                validate478.errors = [{ instancePath: instancePath + "/title", schemaPath: "#/properties/title/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.latex !== void 0) {
                const _errs6 = errors;
                if (typeof data.latex !== "string") {
                  validate478.errors = [{ instancePath: instancePath + "/latex", schemaPath: "#/properties/latex/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.assumptions !== void 0) {
                  let data3 = data.assumptions;
                  const _errs8 = errors;
                  if (errors === _errs8) {
                    if (Array.isArray(data3)) {
                      var valid1 = true;
                      const len0 = data3.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs10 = errors;
                        if (typeof data3[i0] !== "string") {
                          validate478.errors = [{ instancePath: instancePath + "/assumptions/" + i0, schemaPath: "#/properties/assumptions/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid1 = _errs10 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    } else {
                      validate478.errors = [{ instancePath: instancePath + "/assumptions", schemaPath: "#/properties/assumptions/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.implementation !== void 0) {
                    let data5 = data.implementation;
                    const _errs12 = errors;
                    if (errors === _errs12) {
                      if (Array.isArray(data5)) {
                        var valid2 = true;
                        const len1 = data5.length;
                        for (let i1 = 0; i1 < len1; i1++) {
                          const _errs14 = errors;
                          if (typeof data5[i1] !== "string") {
                            validate478.errors = [{ instancePath: instancePath + "/implementation/" + i1, schemaPath: "#/properties/implementation/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid2 = _errs14 === errors;
                          if (!valid2) {
                            break;
                          }
                        }
                      } else {
                        validate478.errors = [{ instancePath: instancePath + "/implementation", schemaPath: "#/properties/implementation/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs12 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.status !== void 0) {
                      let data7 = data.status;
                      const _errs16 = errors;
                      if (typeof data7 !== "string") {
                        validate478.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if (!(data7 === "implemented" || data7 === "conditional" || data7 === "undefined_in_source" || data7 === "source_discrepancy")) {
                        validate478.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema216.properties.status.enum }, message: "must be equal to one of the allowed values" }];
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
    } else {
      validate478.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate478.errors = vErrors;
  return errors === 0;
}
validate478.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate475(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate475.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.version === void 0 && (missing0 = "version") || data.title === void 0 && (missing0 = "title") || data.scope === void 0 && (missing0 = "scope") || data.source_reference === void 0 && (missing0 = "source_reference") || data.source_version === void 0 && (missing0 = "source_version") || data.steps === void 0 && (missing0 = "steps") || data.formulas === void 0 && (missing0 = "formulas") || data.symbols === void 0 && (missing0 = "symbols") || data.tools === void 0 && (missing0 = "tools") || data.discrepancies === void 0 && (missing0 = "discrepancies") || data.formal_formula_editable === void 0 && (missing0 = "formal_formula_editable")) {
        validate475.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema218.properties, key0)) {
            validate475.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate475.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate475.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.title !== void 0) {
                const _errs6 = errors;
                if (typeof data.title !== "string") {
                  validate475.errors = [{ instancePath: instancePath + "/title", schemaPath: "#/properties/title/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scope !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.scope !== "string") {
                    validate475.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/properties/scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.source_reference !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.source_reference !== "string") {
                      validate475.errors = [{ instancePath: instancePath + "/source_reference", schemaPath: "#/properties/source_reference/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.source_version !== void 0) {
                      const _errs12 = errors;
                      if (typeof data.source_version !== "string") {
                        validate475.errors = [{ instancePath: instancePath + "/source_version", schemaPath: "#/properties/source_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.steps !== void 0) {
                        let data6 = data.steps;
                        const _errs14 = errors;
                        if (errors === _errs14) {
                          if (Array.isArray(data6)) {
                            var valid1 = true;
                            const len0 = data6.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              const _errs16 = errors;
                              if (!validate476(data6[i0], { instancePath: instancePath + "/steps/" + i0, parentData: data6, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate476.errors : vErrors.concat(validate476.errors);
                                errors = vErrors.length;
                              }
                              var valid1 = _errs16 === errors;
                              if (!valid1) {
                                break;
                              }
                            }
                          } else {
                            validate475.errors = [{ instancePath: instancePath + "/steps", schemaPath: "#/properties/steps/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.formulas !== void 0) {
                          let data8 = data.formulas;
                          const _errs17 = errors;
                          if (errors === _errs17) {
                            if (Array.isArray(data8)) {
                              var valid2 = true;
                              const len1 = data8.length;
                              for (let i1 = 0; i1 < len1; i1++) {
                                const _errs19 = errors;
                                if (!validate478(data8[i1], { instancePath: instancePath + "/formulas/" + i1, parentData: data8, parentDataProperty: i1, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate478.errors : vErrors.concat(validate478.errors);
                                  errors = vErrors.length;
                                }
                                var valid2 = _errs19 === errors;
                                if (!valid2) {
                                  break;
                                }
                              }
                            } else {
                              validate475.errors = [{ instancePath: instancePath + "/formulas", schemaPath: "#/properties/formulas/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs17 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.symbols !== void 0) {
                            let data10 = data.symbols;
                            const _errs20 = errors;
                            if (errors === _errs20) {
                              if (data10 && typeof data10 == "object" && !Array.isArray(data10)) {
                                for (const key1 in data10) {
                                  const _errs23 = errors;
                                  if (typeof data10[key1] !== "string") {
                                    validate475.errors = [{ instancePath: instancePath + "/symbols/" + key1.replace(/~/g, "~0").replace(/\//g, "~1"), schemaPath: "#/properties/symbols/additionalProperties/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  var valid3 = _errs23 === errors;
                                  if (!valid3) {
                                    break;
                                  }
                                }
                              } else {
                                validate475.errors = [{ instancePath: instancePath + "/symbols", schemaPath: "#/properties/symbols/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                return false;
                              }
                            }
                            var valid0 = _errs20 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.tools !== void 0) {
                              let data12 = data.tools;
                              const _errs25 = errors;
                              if (errors === _errs25) {
                                if (Array.isArray(data12)) {
                                  var valid4 = true;
                                  const len2 = data12.length;
                                  for (let i2 = 0; i2 < len2; i2++) {
                                    const _errs27 = errors;
                                    if (typeof data12[i2] !== "string") {
                                      validate475.errors = [{ instancePath: instancePath + "/tools/" + i2, schemaPath: "#/properties/tools/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                    var valid4 = _errs27 === errors;
                                    if (!valid4) {
                                      break;
                                    }
                                  }
                                } else {
                                  validate475.errors = [{ instancePath: instancePath + "/tools", schemaPath: "#/properties/tools/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs25 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.discrepancies !== void 0) {
                                let data14 = data.discrepancies;
                                const _errs29 = errors;
                                if (errors === _errs29) {
                                  if (Array.isArray(data14)) {
                                    var valid5 = true;
                                    const len3 = data14.length;
                                    for (let i3 = 0; i3 < len3; i3++) {
                                      const _errs31 = errors;
                                      if (typeof data14[i3] !== "string") {
                                        validate475.errors = [{ instancePath: instancePath + "/discrepancies/" + i3, schemaPath: "#/properties/discrepancies/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      var valid5 = _errs31 === errors;
                                      if (!valid5) {
                                        break;
                                      }
                                    }
                                  } else {
                                    validate475.errors = [{ instancePath: instancePath + "/discrepancies", schemaPath: "#/properties/discrepancies/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                    return false;
                                  }
                                }
                                var valid0 = _errs29 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.formal_formula_editable !== void 0) {
                                  let data16 = data.formal_formula_editable;
                                  const _errs33 = errors;
                                  if (typeof data16 !== "boolean") {
                                    validate475.errors = [{ instancePath: instancePath + "/formal_formula_editable", schemaPath: "#/properties/formal_formula_editable/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                    return false;
                                  }
                                  if (false !== data16) {
                                    validate475.errors = [{ instancePath: instancePath + "/formal_formula_editable", schemaPath: "#/properties/formal_formula_editable/const", keyword: "const", params: { allowedValue: false }, message: "must be equal to constant" }];
                                    return false;
                                  }
                                  var valid0 = _errs33 === errors;
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
      validate475.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate475.errors = vErrors;
  return errors === 0;
}
validate475.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate481(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate481.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.name === void 0 && (missing0 = "name") || data.version === void 0 && (missing0 = "version") || data.description === void 0 && (missing0 = "description") || data.runtime === void 0 && (missing0 = "runtime") || data.status === void 0 && (missing0 = "status") || data.license === void 0 && (missing0 = "license") || data.input_names === void 0 && (missing0 = "input_names") || data.output_scope === void 0 && (missing0 = "output_scope")) {
        validate481.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema205.properties, key0)) {
            validate481.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate481.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate481.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.version !== void 0) {
                const _errs6 = errors;
                if (typeof data.version !== "string") {
                  validate481.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.description !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.description !== "string") {
                    validate481.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.runtime !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.runtime !== "string") {
                      validate481.errors = [{ instancePath: instancePath + "/runtime", schemaPath: "#/properties/runtime/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.status !== void 0) {
                      let data5 = data.status;
                      const _errs12 = errors;
                      if (typeof data5 !== "string") {
                        validate481.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("registered_not_tested" !== data5) {
                        validate481.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/const", keyword: "const", params: { allowedValue: "registered_not_tested" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.license !== void 0) {
                        const _errs14 = errors;
                        if (typeof data.license !== "string") {
                          validate481.errors = [{ instancePath: instancePath + "/license", schemaPath: "#/properties/license/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.input_names !== void 0) {
                          let data7 = data.input_names;
                          const _errs16 = errors;
                          if (errors === _errs16) {
                            if (Array.isArray(data7)) {
                              var valid1 = true;
                              const len0 = data7.length;
                              for (let i0 = 0; i0 < len0; i0++) {
                                const _errs18 = errors;
                                if (typeof data7[i0] !== "string") {
                                  validate481.errors = [{ instancePath: instancePath + "/input_names/" + i0, schemaPath: "#/properties/input_names/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                var valid1 = _errs18 === errors;
                                if (!valid1) {
                                  break;
                                }
                              }
                            } else {
                              validate481.errors = [{ instancePath: instancePath + "/input_names", schemaPath: "#/properties/input_names/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.output_scope !== void 0) {
                            const _errs20 = errors;
                            if (typeof data.output_scope !== "string") {
                              validate481.errors = [{ instancePath: instancePath + "/output_scope", schemaPath: "#/properties/output_scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
      }
    } else {
      validate481.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate481.errors = vErrors;
  return errors === 0;
}
validate481.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate474(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate474.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.project_id === void 0 && (missing0 = "project_id") || data.project_revision === void 0 && (missing0 = "project_revision") || data.methods === void 0 && (missing0 = "methods") || data.tool === void 0 && (missing0 = "tool") || data.configured_mode === void 0 && (missing0 = "configured_mode") || data.limitations === void 0 && (missing0 = "limitations") || data.parameter_records === void 0 && (missing0 = "parameter_records")) {
        validate474.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "project_id" || key0 === "project_revision" || key0 === "methods" || key0 === "tool" || key0 === "configured_mode" || key0 === "limitations" || key0 === "parameter_records")) {
            validate474.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.project_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.project_id !== "string") {
              validate474.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate474.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.methods !== void 0) {
                let data2 = data.methods;
                const _errs6 = errors;
                if (errors === _errs6) {
                  if (Array.isArray(data2)) {
                    var valid1 = true;
                    const len0 = data2.length;
                    for (let i0 = 0; i0 < len0; i0++) {
                      const _errs8 = errors;
                      if (!validate475(data2[i0], { instancePath: instancePath + "/methods/" + i0, parentData: data2, parentDataProperty: i0, rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate475.errors : vErrors.concat(validate475.errors);
                        errors = vErrors.length;
                      }
                      var valid1 = _errs8 === errors;
                      if (!valid1) {
                        break;
                      }
                    }
                  } else {
                    validate474.errors = [{ instancePath: instancePath + "/methods", schemaPath: "#/properties/methods/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.tool !== void 0) {
                  const _errs9 = errors;
                  if (!validate481(data.tool, { instancePath: instancePath + "/tool", parentData: data, parentDataProperty: "tool", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate481.errors : vErrors.concat(validate481.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs9 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.configured_mode !== void 0) {
                    let data5 = data.configured_mode;
                    const _errs10 = errors;
                    const _errs11 = errors;
                    let valid2 = false;
                    const _errs12 = errors;
                    if (typeof data5 !== "string") {
                      const err0 = { instancePath: instancePath + "/configured_mode", schemaPath: "#/properties/configured_mode/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    }
                    var _valid0 = _errs12 === errors;
                    valid2 = valid2 || _valid0;
                    const _errs14 = errors;
                    if (data5 !== null) {
                      const err1 = { instancePath: instancePath + "/configured_mode", schemaPath: "#/properties/configured_mode/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err1];
                      } else {
                        vErrors.push(err1);
                      }
                      errors++;
                    }
                    var _valid0 = _errs14 === errors;
                    valid2 = valid2 || _valid0;
                    if (!valid2) {
                      const err2 = { instancePath: instancePath + "/configured_mode", schemaPath: "#/properties/configured_mode/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err2];
                      } else {
                        vErrors.push(err2);
                      }
                      errors++;
                      validate474.errors = vErrors;
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
                    if (data.limitations !== void 0) {
                      let data6 = data.limitations;
                      const _errs16 = errors;
                      if (errors === _errs16) {
                        if (Array.isArray(data6)) {
                          var valid3 = true;
                          const len1 = data6.length;
                          for (let i1 = 0; i1 < len1; i1++) {
                            const _errs18 = errors;
                            if (typeof data6[i1] !== "string") {
                              validate474.errors = [{ instancePath: instancePath + "/limitations/" + i1, schemaPath: "#/properties/limitations/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid3 = _errs18 === errors;
                            if (!valid3) {
                              break;
                            }
                          }
                        } else {
                          validate474.errors = [{ instancePath: instancePath + "/limitations", schemaPath: "#/properties/limitations/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs16 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.parameter_records !== void 0) {
                        let data8 = data.parameter_records;
                        const _errs20 = errors;
                        if (errors === _errs20) {
                          if (Array.isArray(data8)) {
                            var valid4 = true;
                            const len2 = data8.length;
                            for (let i2 = 0; i2 < len2; i2++) {
                              let data9 = data8[i2];
                              const _errs22 = errors;
                              if (errors === _errs22) {
                                if (data9 && typeof data9 == "object" && !Array.isArray(data9)) {
                                } else {
                                  validate474.errors = [{ instancePath: instancePath + "/parameter_records/" + i2, schemaPath: "#/properties/parameter_records/items/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                  return false;
                                }
                              }
                              var valid4 = _errs22 === errors;
                              if (!valid4) {
                                break;
                              }
                            }
                          } else {
                            validate474.errors = [{ instancePath: instancePath + "/parameter_records", schemaPath: "#/properties/parameter_records/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
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
    } else {
      validate474.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate474.errors = vErrors;
  return errors === 0;
}
validate474.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var MethodDraftView = validate483;
var schema222 = { "additionalProperties": false, "properties": { "id": { "type": "string" }, "project_id": { "type": "string" }, "project_revision": { "type": "integer" }, "version": { "type": "integer" }, "base_method_id": { "type": "string" }, "base_version": { "type": "string" }, "title": { "type": "string" }, "formula_id": { "type": "string" }, "original_latex": { "type": "string" }, "latex": { "type": "string" }, "reason": { "type": "string" }, "source_reference": { "type": "string" }, "previous_id": { "anyOf": [{ "type": "string" }, { "type": "null" }] }, "validation_status": { "const": "unvalidated", "type": "string" }, "executable": { "const": false, "type": "boolean" } }, "required": ["id", "project_id", "project_revision", "version", "base_method_id", "base_version", "title", "formula_id", "original_latex", "latex", "reason", "source_reference", "previous_id", "validation_status", "executable"], "type": "object" };
function validate483(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate483.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.project_id === void 0 && (missing0 = "project_id") || data.project_revision === void 0 && (missing0 = "project_revision") || data.version === void 0 && (missing0 = "version") || data.base_method_id === void 0 && (missing0 = "base_method_id") || data.base_version === void 0 && (missing0 = "base_version") || data.title === void 0 && (missing0 = "title") || data.formula_id === void 0 && (missing0 = "formula_id") || data.original_latex === void 0 && (missing0 = "original_latex") || data.latex === void 0 && (missing0 = "latex") || data.reason === void 0 && (missing0 = "reason") || data.source_reference === void 0 && (missing0 = "source_reference") || data.previous_id === void 0 && (missing0 = "previous_id") || data.validation_status === void 0 && (missing0 = "validation_status") || data.executable === void 0 && (missing0 = "executable")) {
        validate483.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema222.properties, key0)) {
            validate483.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate483.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate483.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                  validate483.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.version !== void 0) {
                  let data3 = data.version;
                  const _errs8 = errors;
                  if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)))) {
                    validate483.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.base_method_id !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.base_method_id !== "string") {
                      validate483.errors = [{ instancePath: instancePath + "/base_method_id", schemaPath: "#/properties/base_method_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.base_version !== void 0) {
                      const _errs12 = errors;
                      if (typeof data.base_version !== "string") {
                        validate483.errors = [{ instancePath: instancePath + "/base_version", schemaPath: "#/properties/base_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.title !== void 0) {
                        const _errs14 = errors;
                        if (typeof data.title !== "string") {
                          validate483.errors = [{ instancePath: instancePath + "/title", schemaPath: "#/properties/title/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.formula_id !== void 0) {
                          const _errs16 = errors;
                          if (typeof data.formula_id !== "string") {
                            validate483.errors = [{ instancePath: instancePath + "/formula_id", schemaPath: "#/properties/formula_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.original_latex !== void 0) {
                            const _errs18 = errors;
                            if (typeof data.original_latex !== "string") {
                              validate483.errors = [{ instancePath: instancePath + "/original_latex", schemaPath: "#/properties/original_latex/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid0 = _errs18 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.latex !== void 0) {
                              const _errs20 = errors;
                              if (typeof data.latex !== "string") {
                                validate483.errors = [{ instancePath: instancePath + "/latex", schemaPath: "#/properties/latex/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid0 = _errs20 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.reason !== void 0) {
                                const _errs22 = errors;
                                if (typeof data.reason !== "string") {
                                  validate483.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                var valid0 = _errs22 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.source_reference !== void 0) {
                                  const _errs24 = errors;
                                  if (typeof data.source_reference !== "string") {
                                    validate483.errors = [{ instancePath: instancePath + "/source_reference", schemaPath: "#/properties/source_reference/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  var valid0 = _errs24 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.previous_id !== void 0) {
                                    let data12 = data.previous_id;
                                    const _errs26 = errors;
                                    const _errs27 = errors;
                                    let valid1 = false;
                                    const _errs28 = errors;
                                    if (typeof data12 !== "string") {
                                      const err0 = { instancePath: instancePath + "/previous_id", schemaPath: "#/properties/previous_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err0];
                                      } else {
                                        vErrors.push(err0);
                                      }
                                      errors++;
                                    }
                                    var _valid0 = _errs28 === errors;
                                    valid1 = valid1 || _valid0;
                                    const _errs30 = errors;
                                    if (data12 !== null) {
                                      const err1 = { instancePath: instancePath + "/previous_id", schemaPath: "#/properties/previous_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                      if (vErrors === null) {
                                        vErrors = [err1];
                                      } else {
                                        vErrors.push(err1);
                                      }
                                      errors++;
                                    }
                                    var _valid0 = _errs30 === errors;
                                    valid1 = valid1 || _valid0;
                                    if (!valid1) {
                                      const err2 = { instancePath: instancePath + "/previous_id", schemaPath: "#/properties/previous_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                      if (vErrors === null) {
                                        vErrors = [err2];
                                      } else {
                                        vErrors.push(err2);
                                      }
                                      errors++;
                                      validate483.errors = vErrors;
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
                                    if (data.validation_status !== void 0) {
                                      let data13 = data.validation_status;
                                      const _errs32 = errors;
                                      if (typeof data13 !== "string") {
                                        validate483.errors = [{ instancePath: instancePath + "/validation_status", schemaPath: "#/properties/validation_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      if ("unvalidated" !== data13) {
                                        validate483.errors = [{ instancePath: instancePath + "/validation_status", schemaPath: "#/properties/validation_status/const", keyword: "const", params: { allowedValue: "unvalidated" }, message: "must be equal to constant" }];
                                        return false;
                                      }
                                      var valid0 = _errs32 === errors;
                                    } else {
                                      var valid0 = true;
                                    }
                                    if (valid0) {
                                      if (data.executable !== void 0) {
                                        let data14 = data.executable;
                                        const _errs34 = errors;
                                        if (typeof data14 !== "boolean") {
                                          validate483.errors = [{ instancePath: instancePath + "/executable", schemaPath: "#/properties/executable/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                          return false;
                                        }
                                        if (false !== data14) {
                                          validate483.errors = [{ instancePath: instancePath + "/executable", schemaPath: "#/properties/executable/const", keyword: "const", params: { allowedValue: false }, message: "must be equal to constant" }];
                                          return false;
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
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate483.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate483.errors = vErrors;
  return errors === 0;
}
validate483.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var MethodDraftPage = validate484;
var schema224 = { "additionalProperties": false, "properties": { "id": { "title": "Id", "type": "string" }, "project_id": { "title": "Project Id", "type": "string" }, "project_revision": { "title": "Project Revision", "type": "integer" }, "version": { "title": "Version", "type": "integer" }, "base_method_id": { "title": "Base Method Id", "type": "string" }, "base_version": { "title": "Base Version", "type": "string" }, "title": { "title": "Title", "type": "string" }, "formula_id": { "title": "Formula Id", "type": "string" }, "original_latex": { "title": "Original Latex", "type": "string" }, "latex": { "title": "Latex", "type": "string" }, "reason": { "title": "Reason", "type": "string" }, "source_reference": { "title": "Source Reference", "type": "string" }, "previous_id": { "anyOf": [{ "type": "string" }, { "type": "null" }], "title": "Previous Id" }, "validation_status": { "const": "unvalidated", "default": "unvalidated", "title": "Validation Status", "type": "string" }, "executable": { "const": false, "default": false, "title": "Executable", "type": "boolean" } }, "required": ["id", "project_id", "project_revision", "version", "base_method_id", "base_version", "title", "formula_id", "original_latex", "latex", "reason", "source_reference", "previous_id", "validation_status", "executable"], "title": "MethodDraftView", "type": "object" };
function validate485(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate485.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.project_id === void 0 && (missing0 = "project_id") || data.project_revision === void 0 && (missing0 = "project_revision") || data.version === void 0 && (missing0 = "version") || data.base_method_id === void 0 && (missing0 = "base_method_id") || data.base_version === void 0 && (missing0 = "base_version") || data.title === void 0 && (missing0 = "title") || data.formula_id === void 0 && (missing0 = "formula_id") || data.original_latex === void 0 && (missing0 = "original_latex") || data.latex === void 0 && (missing0 = "latex") || data.reason === void 0 && (missing0 = "reason") || data.source_reference === void 0 && (missing0 = "source_reference") || data.previous_id === void 0 && (missing0 = "previous_id") || data.validation_status === void 0 && (missing0 = "validation_status") || data.executable === void 0 && (missing0 = "executable")) {
        validate485.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema224.properties, key0)) {
            validate485.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate485.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate485.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                  validate485.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.version !== void 0) {
                  let data3 = data.version;
                  const _errs8 = errors;
                  if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)))) {
                    validate485.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.base_method_id !== void 0) {
                    const _errs10 = errors;
                    if (typeof data.base_method_id !== "string") {
                      validate485.errors = [{ instancePath: instancePath + "/base_method_id", schemaPath: "#/properties/base_method_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.base_version !== void 0) {
                      const _errs12 = errors;
                      if (typeof data.base_version !== "string") {
                        validate485.errors = [{ instancePath: instancePath + "/base_version", schemaPath: "#/properties/base_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.title !== void 0) {
                        const _errs14 = errors;
                        if (typeof data.title !== "string") {
                          validate485.errors = [{ instancePath: instancePath + "/title", schemaPath: "#/properties/title/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.formula_id !== void 0) {
                          const _errs16 = errors;
                          if (typeof data.formula_id !== "string") {
                            validate485.errors = [{ instancePath: instancePath + "/formula_id", schemaPath: "#/properties/formula_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.original_latex !== void 0) {
                            const _errs18 = errors;
                            if (typeof data.original_latex !== "string") {
                              validate485.errors = [{ instancePath: instancePath + "/original_latex", schemaPath: "#/properties/original_latex/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            var valid0 = _errs18 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.latex !== void 0) {
                              const _errs20 = errors;
                              if (typeof data.latex !== "string") {
                                validate485.errors = [{ instancePath: instancePath + "/latex", schemaPath: "#/properties/latex/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid0 = _errs20 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.reason !== void 0) {
                                const _errs22 = errors;
                                if (typeof data.reason !== "string") {
                                  validate485.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                var valid0 = _errs22 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.source_reference !== void 0) {
                                  const _errs24 = errors;
                                  if (typeof data.source_reference !== "string") {
                                    validate485.errors = [{ instancePath: instancePath + "/source_reference", schemaPath: "#/properties/source_reference/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  var valid0 = _errs24 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.previous_id !== void 0) {
                                    let data12 = data.previous_id;
                                    const _errs26 = errors;
                                    const _errs27 = errors;
                                    let valid1 = false;
                                    const _errs28 = errors;
                                    if (typeof data12 !== "string") {
                                      const err0 = { instancePath: instancePath + "/previous_id", schemaPath: "#/properties/previous_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err0];
                                      } else {
                                        vErrors.push(err0);
                                      }
                                      errors++;
                                    }
                                    var _valid0 = _errs28 === errors;
                                    valid1 = valid1 || _valid0;
                                    const _errs30 = errors;
                                    if (data12 !== null) {
                                      const err1 = { instancePath: instancePath + "/previous_id", schemaPath: "#/properties/previous_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                      if (vErrors === null) {
                                        vErrors = [err1];
                                      } else {
                                        vErrors.push(err1);
                                      }
                                      errors++;
                                    }
                                    var _valid0 = _errs30 === errors;
                                    valid1 = valid1 || _valid0;
                                    if (!valid1) {
                                      const err2 = { instancePath: instancePath + "/previous_id", schemaPath: "#/properties/previous_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                      if (vErrors === null) {
                                        vErrors = [err2];
                                      } else {
                                        vErrors.push(err2);
                                      }
                                      errors++;
                                      validate485.errors = vErrors;
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
                                    if (data.validation_status !== void 0) {
                                      let data13 = data.validation_status;
                                      const _errs32 = errors;
                                      if (typeof data13 !== "string") {
                                        validate485.errors = [{ instancePath: instancePath + "/validation_status", schemaPath: "#/properties/validation_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      if ("unvalidated" !== data13) {
                                        validate485.errors = [{ instancePath: instancePath + "/validation_status", schemaPath: "#/properties/validation_status/const", keyword: "const", params: { allowedValue: "unvalidated" }, message: "must be equal to constant" }];
                                        return false;
                                      }
                                      var valid0 = _errs32 === errors;
                                    } else {
                                      var valid0 = true;
                                    }
                                    if (valid0) {
                                      if (data.executable !== void 0) {
                                        let data14 = data.executable;
                                        const _errs34 = errors;
                                        if (typeof data14 !== "boolean") {
                                          validate485.errors = [{ instancePath: instancePath + "/executable", schemaPath: "#/properties/executable/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                          return false;
                                        }
                                        if (false !== data14) {
                                          validate485.errors = [{ instancePath: instancePath + "/executable", schemaPath: "#/properties/executable/const", keyword: "const", params: { allowedValue: false }, message: "must be equal to constant" }];
                                          return false;
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
                  }
                }
              }
            }
          }
        }
      }
    } else {
      validate485.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate485.errors = vErrors;
  return errors === 0;
}
validate485.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
function validate484(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate484.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.items === void 0 && (missing0 = "items") || data.has_more === void 0 && (missing0 = "has_more")) {
        validate484.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "items" || key0 === "has_more")) {
            validate484.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                  if (!validate485(data0[i0], { instancePath: instancePath + "/items/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate485.errors : vErrors.concat(validate485.errors);
                    errors = vErrors.length;
                  }
                  var valid1 = _errs4 === errors;
                  if (!valid1) {
                    break;
                  }
                }
              } else {
                validate484.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                return false;
              }
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.has_more !== void 0) {
              const _errs5 = errors;
              if (typeof data.has_more !== "boolean") {
                validate484.errors = [{ instancePath: instancePath + "/has_more", schemaPath: "#/properties/has_more/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                return false;
              }
              var valid0 = _errs5 === errors;
            } else {
              var valid0 = true;
            }
          }
        }
      }
    } else {
      validate484.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate484.errors = vErrors;
  return errors === 0;
}
validate484.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
export {
  AssistantProbeView,
  AssistantSettingsView,
  MethodDefinition,
  MethodDraftPage,
  MethodDraftView,
  ModuleMethodView,
  PluginInspectionView,
  PredictionToolView,
  SkillPage,
  SkillView,
  ToolCatalogPage
};
