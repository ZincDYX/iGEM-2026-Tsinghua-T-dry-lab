import os
import re
import time
import json
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
import openai
import pandas as pd
from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, stop_after_attempt, wait_random_exponential, RetryError


ELSEVIER_API_KEY = os.getenv("ELSEVIER_API_KEY")
ELSEVIER_INST_TOKEN = os.getenv("ELSEVIER_INSTTOKEN") # 这个是可选的
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_base = "https://api.deepseek.com/v1/chat/completions"
OUT_DIR_XML = "scidir_xml"
PROMPT_TEMPLATE_FILE = r'C:\Users\zhaol\Desktop\小学期\大作业\25-python-\icl_prompt_comprehensive.txt'
LLM_MODEL = "deepseek-chat"
SEARCH_ENDPOINT = "https://api.elsevier.com/content/search/sciencedirect"

# =========================
# Pydantic Schemas for Comprehensive Validation
# =========================
class ValueUnitPair(BaseModel):
    value: Optional[str | float | int] = None
    unit: Optional[str] = None
class CatalystCharacteristics(BaseModel):
    catalyst_name: Optional[ValueUnitPair] = None
    bet_surface_area: Optional[ValueUnitPair] = None
    pore_volume: Optional[ValueUnitPair] = None
    pore_size: Optional[ValueUnitPair] = None
    cu_crystallite_size: Optional[ValueUnitPair] = None
    cu_surface_area: Optional[ValueUnitPair] = None
    metal_loading: Optional[ValueUnitPair] = None
    elemental_composition_cu_zn_al: Optional[ValueUnitPair] = None
class ReactionConditions(BaseModel):
    temperature: Optional[ValueUnitPair] = None
    pressure: Optional[ValueUnitPair] = None
    space_velocity: Optional[ValueUnitPair] = Field(None, alias='space_velocity_sv_ghsv')
    h2_co2_ratio: Optional[ValueUnitPair] = None
class PerformanceData(BaseModel):
    co2_conversion: Optional[ValueUnitPair] = None
    methanol_selectivity: Optional[ValueUnitPair] = None
    methanol_yield: Optional[ValueUnitPair] = None
class ExtractionItem(BaseModel):
    catalyst_characteristics: Optional[CatalystCharacteristics] = None
    reaction_conditions: Optional[ReactionConditions] = None
    performance_data: Optional[PerformanceData] = None
class ExtractionResult(BaseModel):
    extractions: List[ExtractionItem]

# =========================
# Part 1: Elsevier文献检索与句子提取
# =========================
def get_headers():
    if not ELSEVIER_API_KEY: raise ValueError("Elsevier API Key not found.")
    headers = {"X-ELS-APIKey": ELSEVIER_API_KEY, "Accept": "application/xml"}
    if ELSEVIER_INST_TOKEN: headers["X-ELS-Insttoken"] = ELSEVIER_INST_TOKEN
    return headers

def strip_namespaces(root: ET.Element):
    for el in root.iter():
        if isinstance(el.tag, str) and '}' in el.tag: el.tag = el.tag.split('}', 1)[1]

def extract_pii_doi_from_entry(entry: dict) -> Tuple[Optional[str], Optional[str]]:
    pii, doi = entry.get("pii"), entry.get("prism:doi")
    if not (pii or doi):
        for link in entry.get("link", []):
            if link.get("@ref") == "self" and "/pii/" in link.get("@href", ""):
                pii = link["@href"].split("/pii/")[1]; break
    return pii, doi

#@retry(wait=wait_random_exponential(min=1, max=30), stop=stop_after_attempt(5))
def scidir_search(keyword: str, count: int = 25) -> List[dict]:
    headers = get_headers(); headers['Accept'] = 'application/json'
    # 使用新的API端点，并暂时移除了可能已过时的 'view' 参数
    params = {"query": keyword, "count": count}
    print(f"[DEBUG] Sending request to: {SEARCH_ENDPOINT} with params: {params}") # 添加一行调试信息
    resp = requests.get(SEARCH_ENDPOINT, headers=headers, params=params, timeout=30)
    resp.raise_for_status() # 这行会触发HTTPError

    # 新API的返回结构可能不同，需要检查
    response_json = resp.json()
    print(f"[DEBUG] API Response: {json.dumps(response_json, indent=2)}") # 如果需要，取消注释以查看完整响应

    # 根据新API的响应结构提取条目
    # 假设新的结构是 {'resultsFound': ..., 'results': [...]}
    # 将原来的 return 语句替换为下面这句
    search_results = response_json.get('search-results', {})
    if not search_results:
        return [] # 如果连 'search-results' 都没有，直接返回空
    return search_results.get('entry', [])

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def fetch_fulltext_xml(pii: str, doi: str) -> Optional[bytes]:
    identifier, id_type = (pii, "pii") if pii else (doi, "doi")
    url = f"https://api.elsevier.com/content/article/{id_type}/{identifier}?view=FULL"
    try:
        resp = requests.get(url, headers=get_headers(), timeout=60)
        resp.raise_for_status(); return resp.content
    except requests.exceptions.HTTPError as e:
        if e.response.status_code in [401, 403, 404]:
            print(f"[WARN] Access denied or not found for {id_type.upper()}: {identifier}. Status: {e.response.status_code}. Skipping.")
            return None
        raise e

def parse_and_find_relevant_sentences(xml_bytes: bytes) -> List[str]:
    try:
        root = ET.fromstring(xml_bytes); strip_namespaces(root)
    except ET.ParseError: return []
    all_paras = [("".join(p.itertext()).strip()) for p in root.findall(".//para") + root.findall(".//simple-para") if "".join(p.itertext()).strip()]
    if not all_paras:
        original_text_node = root.find(".//originalText")
        if original_text_node is not None:
            all_text = "".join(original_text_node.itertext()).strip()
            all_paras = [p.strip() for p in all_text.split('\n\n') if p.strip()]
    full_text = " ".join(all_paras)
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', full_text)
    keyword_pattern = re.compile(r'\b(catalyst|conversion|selectivity|yield|wt%|loading|calcination|reduction|activity|surface area|pressure|temperature)\b', re.IGNORECASE)
    unit_pattern = re.compile(r'(\d+(\.\d+)?)\s*(%|K|°C|MPa|atm|h|min|nm|g|mol|wt\.?%|m²/g|cm³/g)\b')
    return [s.strip() for s in sentences if s.strip() and (unit_pattern.search(s) or keyword_pattern.search(s))]

def get_contextual_sentences(sentences: List[str]) -> List[Dict[str, str]]:
    contextual_data = []
    for i, sent in enumerate(sentences):
        context_before = sentences[i-1] if i > 0 else ""
        context_after = sentences[i+1] if i < len(sentences) - 1 else ""
        full_context = f"{context_before} {sent} {context_after}".strip()
        if len(full_context.split()) > 500: full_context = sent
        contextual_data.append({"main_sentence": sent, "context": full_context})
    return contextual_data

# =========================
# Part 1.5: 数据标准化与分类
# =========================
def classify_and_normalize_value(raw_value) -> Tuple[Optional[float], str]:
    if raw_value is None: return None, 'missing'
    if isinstance(raw_value, (int, float)): return float(raw_value), 'precise'
    s_val = str(raw_value).strip()
    is_approximate = bool(re.match(r'^[~><≥≤\s]*(approx\.\s*)?', s_val))
    s_val = re.sub(r'^[~><≥≤\s]*(approx\.\s*)?', '', s_val)
    delimiter = next((d for d in ['-', 'to'] if d in s_val), None)
    try:
        if delimiter:
            parts = [float(p.strip()) for p in s_val.split(delimiter)]
            return sum(parts) / len(parts), 'range'
        else:
            return float(s_val), 'approximate' if is_approximate else 'precise'
    except (ValueError, TypeError, IndexError): return None, 'unparsable'

def standardize_temperature_to_celsius(value: Optional[float], unit: Optional[str]) -> Optional[float]:
    if value is None or unit is None: return None
    unit_lower = str(unit).lower().strip()
    if 'k' == unit_lower: return value - 273.15
    elif 'c' in unit_lower or '°c' in unit_lower: return value
    elif 'f' in unit_lower or '°f' in unit_lower: return (value - 32) * 5/9
    else: return None

# =========================
# Part 2: ICL数据提取
# =========================
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(5))
def extract_comprehensive_with_icl(context: str, prompt_template: str) -> Optional[dict]:
    if not OPENAI_API_KEY:
        raise ValueError("API Key not found.")

    client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.deepseek.com/v1")

    filled_prompt = prompt_template.replace("{{CONTEXT}}", context)

    json_str = "" # 初始化json_str以防API调用失败时引用错误
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role": "user", "content": filled_prompt}],
            temperature=0,
            response_format={"type": "json_object"},
            timeout=60.0 # 添加超时以防止卡死
        )
        json_str = response.choices[0].message.content

        # 1. 主动检查LLM返回的内容是否为空或仅包含空格
        if not json_str or not json_str.strip():
            print("[WARN] LLM returned an empty response. Skipping this context.")
            return None # 如果为空，直接返回None，程序继续

        # 2. 清理可能存在的Markdown代码块标记
        if json_str.strip().startswith("```json"):
            json_str = json_str.strip()[7:-3].strip()
            if not json_str.strip():
                print("[WARN] LLM response was empty after cleaning markdown. Skipping.")
                return None

        # 3. 进行Pydantic验证
        validated_data = ExtractionResult.model_validate_json(json_str)
        return validated_data.model_dump(by_alias=True)

    # 4. 扩展异常捕获，使其更具信息性
    except ValidationError as e:
        # Pydantic验证失败，包括你遇到的 "Invalid JSON: EOF"
        print(f"[WARN] Pydantic validation failed. This often means the LLM returned an empty string or malformed JSON.")
        print(f"       Error details: {e}")
        # 打印出有问题的原始字符串，方便调试
        print(f"       Problematic LLM Response (first 100 chars): '{str(json_str)[:100]}...'")
        return None # 返回None，程序继续

    except json.JSONDecodeError as e:
        # JSON格式本身就有问题
        print(f"[WARN] JSON decoding failed. The LLM response was not valid JSON.")
        print(f"       Error details: {e}")
        print(f"       Problematic LLM Response (first 100 chars): '{str(json_str)[:100]}...'")
        return None # 返回None，程序继续

    except openai.APIError as e:
        # 捕获所有OpenAI/DeepSeek的API错误（如超时、连接错误等）
        print(f"[WARN] API call failed. Error: {e}")
        # 这里我们让tenacity的@retry接管，所以重新抛出异常
        raise e


# =========================
# 主流程
# =========================
def run_pipeline():
    print("=== Comprehensive AI Catalyst Data Extractor ===")
    # --- 添加下面这两行来进行调试 ---
    key_from_env = os.getenv("ELSEVIER_API_KEY")
    print(f"--- [DEBUG] 脚本读取到的Elsevier Key是: '{key_from_env}' ---")
    # --- 调试代码结束 ---
    search_query = input("1. 请输入Elsevier搜索关键词 (例如: 'Cu/ZnO/Al2O3' 'methanol synthesis'): ")
    max_papers_str = input("2. 你希望最多处理多少篇论文? (默认5进行测试): ")
    max_papers = int(max_papers_str) if max_papers_str.isdigit() else 5

    try:
        with open(PROMPT_TEMPLATE_FILE, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
    except FileNotFoundError:
        print(f"[ERROR] Prompt模板文件 '{PROMPT_TEMPLATE_FILE}' 未找到。请确保该文件存在。")
        return # 使用 return 代替 exit() 更优雅

    print(f"\n[INFO] 正在搜索文献，关键词: '{search_query}'...")
    try:
        search_entries = scidir_search(search_query, count=max_papers)
    except RetryError as e:
        # Tenacity的RetryError会包裹最后一次尝试的异常
        # .exception() 是一个方法，需要调用它来获取异常实例
        last_exception = e.last_attempt.exception()

        print("\n" + "="*60)
        print("[FATAL ERROR] 文献搜索失败，所有重试均告失败。")
        print(f"  - 最后一次错误的类型: {type(last_exception)}")
        print(f"  - 最后一次错误的详细信息: {last_exception}")
        print("="*60 + "\n")

        # 如果最后一次错误是HTTPError，打印更详细的信息
        if isinstance(last_exception, requests.exceptions.HTTPError):
            response = last_exception.response
            print("--- [服务器详细响应] ---")
            print(f"  - HTTP状态码: {response.status_code}")
            try:
                # 尝试解析JSON响应以获得结构化错误信息
                error_details = response.json()
                print(f"  - 服务器响应 (JSON): {error_details}")
            except requests.exceptions.JSONDecodeError:
                # 如果响应不是JSON，则打印原始文本
                print(f"  - 服务器响应 (Text): {response.text}")

            print("--- [诊断建议] ---")
            if response.status_code in [401, 403]:
                print("  - 错误码 401/403 (Unauthorized/Forbidden) 强烈表明您的 API Key 无效、已过期或没有访问该资源的权限。")
                print("    请确认：")
                print("    1. 您设置的环境变量 `ELSEVIER_API_KEY` 的值是您新申请的那个，并且复制粘贴时没有多余的字符或空格。")
                print("    2. 在Elsevier开发者网站上，您的新Key是否已经处于'Active'状态。")
            elif response.status_code == 400:
                 print("  - 错误码 400 (Bad Request) 表明您的请求格式有问题。可能是搜索关键词包含API不支持的特殊字符。")
            else:
                print(f"  - 这是一个未预料到的HTTP错误 ({response.status_code})。请检查网络连接或Elsevier API状态页面。")
            print("-" * 25)
        return # 发生严重错误后，终止程序

    print(f"[INFO] 找到 {len(search_entries)} 篇相关文献。开始处理...")
    final_results_raw = []
    for i, entry in enumerate(search_entries):
        title = entry.get("dc:title", "Unknown Title")
        pii, doi = extract_pii_doi_from_entry(entry)
        print(f"\n--- Processing Paper {i+1}/{len(search_entries)}: {title[:80]}... ---")

        if not (pii or doi):
            print("[INFO] 缺少PII和DOI，跳过。")
            continue
        try:
            xml_bytes = fetch_fulltext_xml(pii, doi)
            if not xml_bytes: continue
            relevant_sentences = parse_and_find_relevant_sentences(xml_bytes)
            if not relevant_sentences:
                print("[INFO] 未找到包含关键信息的相关句子。")
                continue

            contextual_data = get_contextual_sentences(relevant_sentences)
            print(f"[INFO] 找到 {len(contextual_data)} 个可能包含数据点的上下文。开始ICL提取...")
            for item in contextual_data:
                extracted_json = extract_comprehensive_with_icl(item['context'], prompt_template)
                if extracted_json and extracted_json.get('extractions'):
                    for experiment in extracted_json['extractions']:
                        base_info = {"doi": doi or pii, "main_sentence": item['main_sentence']}
                        base_info.update(experiment)
                        final_results_raw.append(base_info)
        except Exception as e:
            print(f"[ERROR] 处理论文 '{title[:50]}...' 时发生未知异常: {e}")
            continue
    # --- 数据分流和转换 (保持不变) ---
    if not final_results_raw:
        print("\n[INFO] 流程结束，未提取到任何数据。")
        return

    print("\n[INFO] ICL提取完成，开始数据标准化与分流...")
    df_raw = pd.json_normalize(final_results_raw, sep='_')

    columns_to_process = {
        # === Catalyst Characteristics ===
        'catalyst_name': ('catalyst_characteristics_catalyst_name_value', 'catalyst_characteristics_catalyst_name_unit', None),
        'bet_surface_area': ('catalyst_characteristics_bet_surface_area_value', 'catalyst_characteristics_bet_surface_area_unit', None),
        'pore_volume': ('catalyst_characteristics_pore_volume_value', 'catalyst_characteristics_pore_volume_unit', None),
        'pore_size': ('catalyst_characteristics_pore_size_value', 'catalyst_characteristics_pore_size_unit', None),
        'cu_crystallite_size': ('catalyst_characteristics_cu_crystallite_size_value', 'catalyst_characteristics_cu_crystallite_size_unit', None),
        'cu_surface_area': ('catalyst_characteristics_cu_surface_area_value', 'catalyst_characteristics_cu_surface_area_unit', None),
        'metal_loading': ('catalyst_characteristics_metal_loading_value', 'catalyst_characteristics_metal_loading_unit', None),
        'elemental_composition': ('catalyst_characteristics_elemental_composition_cu_zn_al_value', 'catalyst_characteristics_elemental_composition_cu_zn_al_unit', None),

        # === Reaction Conditions ===
        'reaction_temp': ('reaction_conditions_temperature_value', 'reaction_conditions_temperature_unit', standardize_temperature_to_celsius),
        'pressure': ('reaction_conditions_pressure_value', 'reaction_conditions_pressure_unit', None),
        'space_velocity': ('reaction_conditions_space_velocity_sv_ghsv_value', 'reaction_conditions_space_velocity_sv_ghsv_unit', None),
        'h2_co2_ratio': ('reaction_conditions_h2_co2_ratio_value', 'reaction_conditions_h2_co2_ratio_unit', None),

        # === Performance Data ===
        'co2_conversion': ('performance_data_co2_conversion_value', 'performance_data_co2_conversion_unit', None),
        'methanol_selectivity': ('performance_data_methanol_selectivity_value', 'performance_data_methanol_selectivity_unit', None),
        'methanol_yield': ('performance_data_methanol_yield_value', 'performance_data_methanol_yield_unit', None),
    }
    key_numeric_cols = []
    for new_name, (val_col, unit_col, func) in columns_to_process.items():
        if val_col in df_raw.columns:
            # 对于催化剂名称和元素组成这类可能不是数字的值，特殊处理，直接保留原值
            if new_name in ['catalyst_name', 'elemental_composition']:
                 df_raw[f'final_{new_name}'] = df_raw[val_col]
                 df_raw[f'type_{new_name}'] = 'text' # 标记为文本类型
            else:
                # 原有的数值处理逻辑
                temp_data = df_raw[val_col].apply(classify_and_normalize_value)
                df_raw[f'norm_{new_name}'] = temp_data.apply(lambda x: x[0])
                df_raw[f'type_{new_name}'] = temp_data.apply(lambda x: x[1])
                key_numeric_cols.append(f'type_{new_name}')

                if func:
                    df_raw[f'final_{new_name}'] = df_raw.apply(
                        lambda row: func(row[f'norm_{new_name}'], row.get(unit_col)), axis=1
                    )
                else:
                    df_raw[f'final_{new_name}'] = df_raw[f'norm_{new_name}']

    # 修改筛选逻辑，允许文本类型的数据通过
    is_precise_mask = pd.Series(True, index=df_raw.index)
    for col_type_name in key_numeric_cols: # 只对数值类型的列进行筛选
        if col_type_name in df_raw.columns:
            # 允许 'precise', 'missing' 或 'text' 类型的数据进入主数据库
            is_precise_mask &= (df_raw[col_type_name].isin(['precise', 'missing', 'text']))
    is_precise_mask = pd.Series(True, index=df_raw.index)
    for col_type in key_numeric_cols:
        if col_type in df_raw.columns:
            # 允许缺失值被视为“非精确”，但不会被直接排除
            is_precise_mask &= (df_raw[col_type] == 'precise') | (df_raw[col_type] == 'missing')

    df_main = df_raw[is_precise_mask].copy()
    df_review = df_raw[~is_precise_mask].copy()

    timestamp = time.strftime('%Y%m%d-%H%M%S')
    if not df_main.empty:
        final_cols = ['doi', 'main_sentence'] + [f'final_{name}' for name in columns_to_process.keys() if f'final_{name}' in df_main.columns]
        df_main_final = df_main[final_cols].dropna(how='all', subset=[f for f in final_cols if f.startswith('final_')])
        if not df_main_final.empty:
            output_main = f"main_database_{timestamp}.csv"
            df_main_final.to_csv(output_main, index=False, encoding='utf-8-sig')
            print(f"\n[DONE] 主数据库已保存到 {output_main} (共 {len(df_main_final)} 条精确记录)")

    if not df_review.empty:
        review_cols = ['doi', 'main_sentence']
        for name, (val_col, unit_col, _) in columns_to_process.items():
            if val_col in df_review.columns: review_cols.extend([val_col, unit_col, f'type_{name}'])
        review_cols_exist = [c for c in review_cols if c in df_review.columns]
        df_review_final = df_review[review_cols_exist]
        if not df_review_final.empty:
            output_review = f"review_database_{timestamp}.csv"
            df_review_final.to_csv(output_review, index=False, encoding='utf-8-sig')
            print(f"[DONE] 待审查数据库已保存到 {output_review} (共 {len(df_review_final)} 条范围/近似记录)")


def check_env_vars():
    """检查必要的环境变量是否已设置"""
    missing_vars = []
    if not ELSEVIER_API_KEY:
        missing_vars.append("ELSEVIER_API_KEY")
    if not OPENAI_API_KEY:
        missing_vars.append("OPENAI_API_KEY")

    if missing_vars:
        print("[ERROR] 关键的API密钥缺失！请设置以下环境变量:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\n设置方法示例:")
        print("  - Windows (CMD): set VAR_NAME=your_key")
        print("  - macOS/Linux: export VAR_NAME=your_key")
        return False
    return True

if __name__ == "__main__":
    if check_env_vars():
        os.makedirs(OUT_DIR_XML, exist_ok=True)
        run_pipeline()
    else:
        print("\n程序因缺少配置而退出。")
