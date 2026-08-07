# central configuration and constants
KEY_VALUE_COLUMNS = [
    'final_reaction_temp',
    'final_pressure',
    'final_co2_conversion',
    'final_methanol_selectivity',
    'final_methanol_yield'
]

REQUIRED_COLUMNS_FOR_VALID_RECORD = [
    'final_catalyst_name',
    'final_reaction_temp',
    'final_co2_conversion'
]

GROUPING_KEYS = ['doi', 'final_catalyst_name']

DEFAULT_COLUMNS = {
    'T': 'final_reaction_temp',
    'P': 'final_pressure',
    'conv': 'final_co2_conversion',
    'sel': 'final_methanol_selectivity',
    'yld': 'final_methanol_yield',
    'catalyst': 'final_catalyst_name',
    'doi': 'doi',
    'main_sentence': 'main_sentence',
}

DEFAULT_INPUT_CSV = 'main_database.csv'
DEFAULT_OUTPUT_DIR = 'outputs'

# Extraction defaults
ELSEVIER_SEARCH_ENDPOINT = 'https://api.elsevier.com/content/search/sciencedirect'
ELSEVIER_ARTICLE_ENDPOINT = 'https://api.elsevier.com/content/article/{id_type}/{identifier}?view=FULL'
DEFAULT_LLM_BASE = 'https://api.deepseek.com/v1/chat/completions'
DEFAULT_LLM_MODEL = 'deepseek-chat'
DEFAULT_ICL_JSON = 'CatalystOptimizationSystem/docs/icl_examples.default.json'
DEFAULT_SCHEMA_JSON = 'CatalystOptimizationSystem/docs/schemas/glabridin_enzyme_catalysis.schema.json'
DEFAULT_ICL_BANK = 'CatalystOptimizationSystem/docs/icl_bank.default.jsonl'
