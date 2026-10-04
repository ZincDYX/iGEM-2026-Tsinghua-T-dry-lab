"""Run outside the checkout after a wheel install; exercise bundled rules/MCP."""
import json
from igem_drylab.constructs import M1FeatureDefinitions, M1V3Rules, compute_sequence_features
from igem_drylab.mcp import create_default_registry
from igem_drylab.resources import default_config_path
import yaml


definitions, digest = M1FeatureDefinitions.from_yaml(default_config_path("m1_feature_definitions.yaml"))
rules = M1V3Rules.model_validate(yaml.safe_load(default_config_path("m1_rules_v3.yaml").read_text(encoding="utf-8")))
features = compute_sequence_features("GGGGSGGGGS", definitions=definitions, definitions_sha256=digest)
assert features.length == 10
result = create_default_registry().call("igem.m1.compute_features", {"sequence": "GGGGSGGGGS"})
assert not result.is_error, result.as_protocol_dict()
print(json.dumps({"package_smoke": "passed", "rule_version": rules.rule_version, "rules_path": str(default_config_path("m1_rules_v3.yaml"))}))
