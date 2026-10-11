// <stdin>
var ProjectSummaryView = validate487;
function validate487(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate487.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.id === void 0 && (missing0 = "id") || data.name === void 0 && (missing0 = "name") || data.revision === void 0 && (missing0 = "revision") || data.scientific === void 0 && (missing0 = "scientific") || data.sequence_count === void 0 && (missing0 = "sequence_count") || data.scientific_sequence_count === void 0 && (missing0 = "scientific_sequence_count") || data.scientific_sequence_index_status === void 0 && (missing0 = "scientific_sequence_index_status")) {
        validate487.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "id" || key0 === "name" || key0 === "revision" || key0 === "scientific" || key0 === "sequence_count" || key0 === "scientific_sequence_count" || key0 === "scientific_sequence_index_status")) {
            validate487.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.id !== void 0) {
            const _errs2 = errors;
            if (typeof data.id !== "string") {
              validate487.errors = [{ instancePath: instancePath + "/id", schemaPath: "#/properties/id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                validate487.errors = [{ instancePath: instancePath + "/name", schemaPath: "#/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                return false;
              }
              var valid0 = _errs4 === errors;
            } else {
              var valid0 = true;
            }
            if (valid0) {
              if (data.revision !== void 0) {
                let data2 = data.revision;
                const _errs6 = errors;
                if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)))) {
                  validate487.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scientific !== void 0) {
                  const _errs8 = errors;
                  if (typeof data.scientific !== "boolean") {
                    validate487.errors = [{ instancePath: instancePath + "/scientific", schemaPath: "#/properties/scientific/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.sequence_count !== void 0) {
                    let data4 = data.sequence_count;
                    const _errs10 = errors;
                    if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)))) {
                      validate487.errors = [{ instancePath: instancePath + "/sequence_count", schemaPath: "#/properties/sequence_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.scientific_sequence_count !== void 0) {
                      let data5 = data.scientific_sequence_count;
                      const _errs12 = errors;
                      const _errs13 = errors;
                      let valid1 = false;
                      const _errs14 = errors;
                      if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)))) {
                        const err0 = { instancePath: instancePath + "/scientific_sequence_count", schemaPath: "#/properties/scientific_sequence_count/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
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
                        const err1 = { instancePath: instancePath + "/scientific_sequence_count", schemaPath: "#/properties/scientific_sequence_count/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                        const err2 = { instancePath: instancePath + "/scientific_sequence_count", schemaPath: "#/properties/scientific_sequence_count/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err2];
                        } else {
                          vErrors.push(err2);
                        }
                        errors++;
                        validate487.errors = vErrors;
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
                      if (data.scientific_sequence_index_status !== void 0) {
                        const _errs18 = errors;
                        if (typeof data.scientific_sequence_index_status !== "string") {
                          validate487.errors = [{ instancePath: instancePath + "/scientific_sequence_index_status", schemaPath: "#/properties/scientific_sequence_index_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
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
        }
      }
    } else {
      validate487.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate487.errors = vErrors;
  return errors === 0;
}
validate487.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var ActionView = validate488;
function validate488(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate488.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.seq === void 0 && (missing0 = "seq") || data.proposal_id === void 0 && (missing0 = "proposal_id") || data.run_id === void 0 && (missing0 = "run_id") || data.action === void 0 && (missing0 = "action") || data.actor === void 0 && (missing0 = "actor") || data.timestamp === void 0 && (missing0 = "timestamp")) {
        validate488.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!(key0 === "seq" || key0 === "proposal_id" || key0 === "run_id" || key0 === "action" || key0 === "actor" || key0 === "timestamp")) {
            validate488.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.seq !== void 0) {
            let data0 = data.seq;
            const _errs2 = errors;
            if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)))) {
              validate488.errors = [{ instancePath: instancePath + "/seq", schemaPath: "#/properties/seq/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.proposal_id !== void 0) {
              let data1 = data.proposal_id;
              const _errs4 = errors;
              const _errs5 = errors;
              let valid1 = false;
              const _errs6 = errors;
              if (typeof data1 !== "string") {
                const err0 = { instancePath: instancePath + "/proposal_id", schemaPath: "#/properties/proposal_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                const err1 = { instancePath: instancePath + "/proposal_id", schemaPath: "#/properties/proposal_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                const err2 = { instancePath: instancePath + "/proposal_id", schemaPath: "#/properties/proposal_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                if (vErrors === null) {
                  vErrors = [err2];
                } else {
                  vErrors.push(err2);
                }
                errors++;
                validate488.errors = vErrors;
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
              if (data.run_id !== void 0) {
                let data2 = data.run_id;
                const _errs10 = errors;
                const _errs11 = errors;
                let valid2 = false;
                const _errs12 = errors;
                if (typeof data2 !== "string") {
                  const err3 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                  const err4 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err5 = { instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err5];
                  } else {
                    vErrors.push(err5);
                  }
                  errors++;
                  validate488.errors = vErrors;
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
                if (data.action !== void 0) {
                  const _errs16 = errors;
                  if (typeof data.action !== "string") {
                    validate488.errors = [{ instancePath: instancePath + "/action", schemaPath: "#/properties/action/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  var valid0 = _errs16 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.actor !== void 0) {
                    const _errs18 = errors;
                    if (typeof data.actor !== "string") {
                      validate488.errors = [{ instancePath: instancePath + "/actor", schemaPath: "#/properties/actor/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    var valid0 = _errs18 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.timestamp !== void 0) {
                      const _errs20 = errors;
                      if (typeof data.timestamp !== "string") {
                        validate488.errors = [{ instancePath: instancePath + "/timestamp", schemaPath: "#/properties/timestamp/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
    } else {
      validate488.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate488.errors = vErrors;
  return errors === 0;
}
validate488.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
var InputDiffView = validate489;
var schema227 = { "additionalProperties": false, "properties": { "baseline_run_id": { "type": "string" }, "baseline_snapshot_sha256": { "type": "string" }, "project_id": { "type": "string" }, "project_revision": { "type": "integer" }, "changed_fields": { "items": { "type": "string" }, "type": "array" }, "total_changed_fields": { "type": "integer" }, "affected_nodes": { "items": { "type": "string" }, "type": "array" }, "reuse_supported": { "type": "boolean" }, "explanation": { "type": "string" } }, "required": ["baseline_run_id", "baseline_snapshot_sha256", "project_id", "project_revision", "changed_fields", "total_changed_fields", "affected_nodes", "reuse_supported", "explanation"], "type": "object" };
var func1 = Object.prototype.hasOwnProperty;
function validate489(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
  let vErrors = null;
  let errors = 0;
  const evaluated0 = validate489.evaluated;
  if (evaluated0.dynamicProps) {
    evaluated0.props = void 0;
  }
  if (evaluated0.dynamicItems) {
    evaluated0.items = void 0;
  }
  if (errors === 0) {
    if (data && typeof data == "object" && !Array.isArray(data)) {
      let missing0;
      if (data.baseline_run_id === void 0 && (missing0 = "baseline_run_id") || data.baseline_snapshot_sha256 === void 0 && (missing0 = "baseline_snapshot_sha256") || data.project_id === void 0 && (missing0 = "project_id") || data.project_revision === void 0 && (missing0 = "project_revision") || data.changed_fields === void 0 && (missing0 = "changed_fields") || data.total_changed_fields === void 0 && (missing0 = "total_changed_fields") || data.affected_nodes === void 0 && (missing0 = "affected_nodes") || data.reuse_supported === void 0 && (missing0 = "reuse_supported") || data.explanation === void 0 && (missing0 = "explanation")) {
        validate489.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
        return false;
      } else {
        const _errs1 = errors;
        for (const key0 in data) {
          if (!func1.call(schema227.properties, key0)) {
            validate489.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
            return false;
            break;
          }
        }
        if (_errs1 === errors) {
          if (data.baseline_run_id !== void 0) {
            const _errs2 = errors;
            if (typeof data.baseline_run_id !== "string") {
              validate489.errors = [{ instancePath: instancePath + "/baseline_run_id", schemaPath: "#/properties/baseline_run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
              return false;
            }
            var valid0 = _errs2 === errors;
          } else {
            var valid0 = true;
          }
          if (valid0) {
            if (data.baseline_snapshot_sha256 !== void 0) {
              const _errs4 = errors;
              if (typeof data.baseline_snapshot_sha256 !== "string") {
                validate489.errors = [{ instancePath: instancePath + "/baseline_snapshot_sha256", schemaPath: "#/properties/baseline_snapshot_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                  validate489.errors = [{ instancePath: instancePath + "/project_id", schemaPath: "#/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs6 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.project_revision !== void 0) {
                  let data3 = data.project_revision;
                  const _errs8 = errors;
                  if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)))) {
                    validate489.errors = [{ instancePath: instancePath + "/project_revision", schemaPath: "#/properties/project_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.changed_fields !== void 0) {
                    let data4 = data.changed_fields;
                    const _errs10 = errors;
                    if (errors === _errs10) {
                      if (Array.isArray(data4)) {
                        var valid1 = true;
                        const len0 = data4.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          const _errs12 = errors;
                          if (typeof data4[i0] !== "string") {
                            validate489.errors = [{ instancePath: instancePath + "/changed_fields/" + i0, schemaPath: "#/properties/changed_fields/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          var valid1 = _errs12 === errors;
                          if (!valid1) {
                            break;
                          }
                        }
                      } else {
                        validate489.errors = [{ instancePath: instancePath + "/changed_fields", schemaPath: "#/properties/changed_fields/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.total_changed_fields !== void 0) {
                      let data6 = data.total_changed_fields;
                      const _errs14 = errors;
                      if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)))) {
                        validate489.errors = [{ instancePath: instancePath + "/total_changed_fields", schemaPath: "#/properties/total_changed_fields/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      var valid0 = _errs14 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.affected_nodes !== void 0) {
                        let data7 = data.affected_nodes;
                        const _errs16 = errors;
                        if (errors === _errs16) {
                          if (Array.isArray(data7)) {
                            var valid2 = true;
                            const len1 = data7.length;
                            for (let i1 = 0; i1 < len1; i1++) {
                              const _errs18 = errors;
                              if (typeof data7[i1] !== "string") {
                                validate489.errors = [{ instancePath: instancePath + "/affected_nodes/" + i1, schemaPath: "#/properties/affected_nodes/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid2 = _errs18 === errors;
                              if (!valid2) {
                                break;
                              }
                            }
                          } else {
                            validate489.errors = [{ instancePath: instancePath + "/affected_nodes", schemaPath: "#/properties/affected_nodes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs16 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.reuse_supported !== void 0) {
                          const _errs20 = errors;
                          if (typeof data.reuse_supported !== "boolean") {
                            validate489.errors = [{ instancePath: instancePath + "/reuse_supported", schemaPath: "#/properties/reuse_supported/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                            return false;
                          }
                          var valid0 = _errs20 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.explanation !== void 0) {
                            const _errs22 = errors;
                            if (typeof data.explanation !== "string") {
                              validate489.errors = [{ instancePath: instancePath + "/explanation", schemaPath: "#/properties/explanation/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
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
        }
      }
    } else {
      validate489.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
      return false;
    }
  }
  validate489.errors = vErrors;
  return errors === 0;
}
validate489.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
export {
  ActionView,
  InputDiffView,
  ProjectSummaryView
};
