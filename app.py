import streamlit as st, os, py_compile, urllib.request, json

# 1. Ollama Client & Auto-Detection
def run_query(prompt, model=None, system=None):
    try:
        if not model:
            model = "ornith-1.0-9b:latest"
        
        data = json.dumps({"model": model, "prompt": prompt, "system": system, "stream": False, "options": {"think": False, "temperature": 0.1}})
        req = urllib.request.Request("http://localhost:11434/api/generate", data=data.encode(), headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=30) as res:
            text = json.loads(res.read())['response']
            return model, text.split("</think>")[-1].replace("<think>", "").strip(" `\n").replace("```python\n", "").replace("```", "")
    except Exception as e: return None, str(e)

# 2. UI Styling & Layout
st.set_page_config(page_title="Ornith Agent", page_icon="🦤", layout="wide")
st.markdown("<h1 style='color:#FD8E5B;'>🦤 Ornith Coding Agent</h1><hr/>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    prompt = st.text_area("Task Description:", "Write a python function to check if a number is prime.")
    file_path = st.text_input("Output File:", "prime_checker.py")
    run = st.button("🚀 Run Agent Loop", use_container_width=True)

# 3. Self-Correcting Agent Loop
if run and prompt:
    logs, code, success, err = [], "", False, ""
    with col2:
        log_box = st.empty()
        for attempt in range(1, 4):
            logs.append(f"Attempt {attempt}: Querying Ollama...")
            log_box.code("\n".join(logs))
            model, code = run_query(prompt + (f"\n\nPrevious error:\n{err}" if attempt > 1 else ""), system="Output ONLY raw Python code.")
            if not model:
                logs.append(f"Error: {code}"); log_box.code("\n".join(logs)); break
            logs.append(f"Model used: {model}\nWriting code to {file_path}...")
            with open(file_path, "w", encoding="utf-8") as f: f.write(code)
            try:
                py_compile.compile(file_path, doraise=True)
                logs.append("Syntax validation passed! Success."); success = True; break
            except py_compile.PyCompileError as ce:
                err = str(ce)
                logs.append(f"Validation failed:\n{err}\nSelf-correcting...")
        log_box.code("\n".join(logs))
        if success: st.success("Task completed successfully!"); st.code(code, language="python")
