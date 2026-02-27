import streamlit as st
import json
import os
import itertools
import pandas as pd # <--- ADD THIS LINE
import matplotlib.pyplot as plt
from streamlit_local_storage import LocalStorage

st.set_page_config(layout="wide")

# Initialize Local Storage FIRST
local_storage = LocalStorage()

# ---------------- LOAD FROM BROWSER (FIXED) ----------------
stored_data = local_storage.getItem("region_data")

if stored_data:
    for key, value in stored_data.items():
        # IMPORTANT: We ignore 'excel_editor' here to prevent the crash
        if key not in st.session_state and key != "excel_editor":
            st.session_state[key] = value

# ---------------- GOLD PREMIUM THEME ----------------
st.markdown("""
<style>
h1 {
    color: #d4af37;
}
h2 {
    color: #b8860b;
}
div[data-testid="stMetric"] {
    border-left: 4px solid #d4af37;
}
</style>
""", unsafe_allow_html=True)



# ---------------- SLABS ----------------
slabs = {
    "HEAD RETAIL": [(100,125000),(90,100000),(80,90000),(70,75000),(60,60000),(0,50000)],
    "Business Head L1": [(100,125000),(90,100000),(80,90000),(70,75000),(60,60000),(0,50000)],
    "Business Head L2": [(100,125000),(90,100000),(80,90000),(70,75000),(60,60000),(0,50000)],
    "GENERAL MANAGER (G1)": [(100,105000),(90,85000),(80,75000),(70,63000),(60,51000),(0,42000)],
    "DEPUTY GENERAL MANAGER": [(100,105000),(90,85000),(80,75000),(70,63000),(60,51000),(0,42000)],
    "REGIONAL MANAGER (L1)": [(100,105000),(90,85000),(80,75000),(70,63000),(60,51000),(0,42000)],
    "REGIONAL MANAGER (L2)": [(100,105000),(90,85000),(80,75000),(70,63000),(60,51000),(0,42000)],
    "ASST. REGIONAL MANAGER": [(100,95000),(90,75000),(80,67500),(70,55000),(60,45000),(0,37500)]
}

# ---------------- MARK LOGIC ----------------
def score(x, full, mid1, mid2, low):
    if x >= 100: return full
    elif x >= 90: return mid1
    elif x >= 80: return mid2
    elif x >= 75: return low
    else: return 0

def calculate_marks(t, s, d, sc, dt):
    turnover = score(t,40,30,25,10)
    studded = score(s,20,12.5,7.5,4)
    dmd = score(d,10,7.5,5,0) if s >= 75 else 0
    scheme = score(sc,20,12.5,7.5,4)
    dtso = score(dt,20,12.5,7.5,4)
    return turnover + studded + dmd + scheme + dtso

# ---------------- UI ----------------
st.title("🏆 Region Intelligence Dashboard")
# ---------------- 👤 SIDEBAR CONFIGURATION ----------------
st.sidebar.title("Region Settings")

# This creates the dropdown menu for your role
designation = st.sidebar.selectbox(
    "Select Your Designation",
    options=[
        "HEAD RETAIL",
        "Business Head L1",
        "Business Head L2",
        "GENERAL MANAGER (G1)",
        "DEPUTY GENERAL MANAGER",
        "REGIONAL MANAGER (L1)",
        "REGIONAL MANAGER (L2)",
        "ASST. REGIONAL MANAGER"
    ]
)

# This sets the starting number of rows for your grid
initial_rows = st.sidebar.slider("Starting Number of Stores", 1, 20, 10)

# ================= 📥 BULK DATA ENTRY (NEW & STABLE) =================
st.markdown("## 📥 Bulk Data Entry")
st.info("💡 Pro-Tip: Copy your data from Excel (Cmd+C) and paste it into the first cell (Cmd+V).")



# 2. Table Column Configuration
column_config = {
    "Store Name": st.column_config.TextColumn("Store Name", default="New Store", required=True),
    "Turnover %": st.column_config.NumberColumn("Turnover %", format="%.2f"),
    "Studded %": st.column_config.NumberColumn("Studded %", format="%.2f"), # Fix here
    "DMD %": st.column_config.NumberColumn("DMD %", format="%.2f"),
    "Scheme %": st.column_config.NumberColumn("Scheme %", format="%.2f"),
    "DTSO %": st.column_config.NumberColumn("DTSO %", format="%.2f"), # Fix here
}

# 3. Load saved data or create fresh rows
if 'saved_df_dict' not in st.session_state:
    initial_data = [{"Store Name": f"Store {i+1}", "Turnover %": 0.0, "Studded %": 0.0, "DMD %": 0.0, "Scheme %": 0.0, "DTSO %": 0.0} 
                    for i in range(initial_rows)]
    st.session_state.saved_df_dict = initial_data
else:
    initial_data = st.session_state.saved_df_dict

# 4. The Excel Grid (The Widget)
edited_df = st.data_editor(
    initial_data,
    column_config=column_config,
    num_rows="dynamic",
    use_container_width=True,
    hide_index=True,
    key="excel_editor"
)

# 5. Save the table state so it doesn't disappear
# We check if edited_df is already a list (common in newer Streamlit versions)
# before trying to convert it
st.session_state.saved_df_dict = edited_df if isinstance(edited_df, list) else edited_df.to_dict('records')

# ================= 🧮 SYNC, SCALE & CALCULATE (LIST VERSION) =================
store_data = []
total_marks = 0

# Check if edited_df is a DataFrame or a list, then loop accordingly
data_to_process = edited_df.to_dict('records') if hasattr(edited_df, 'to_dict') else edited_df

for row in data_to_process:
    name = row.get("Store Name", "New Store")
    
    # SMART SCALING: Fixes the issue where 0.92 from Excel becomes 92%
    metrics_keys = ["Turnover %", "Studded %", "DMD %", "Scheme %", "DTSO %"]
    s_val = {}
    
    for k in metrics_keys:
        val = float(row.get(k, 0.0))
        # If the number is a decimal (e.g., 0.92), multiply by 100
        s_val[k] = round(val * 100, 2) if 0 < val <= 2.0 else round(val, 2)
    
    # Run the Mark Calculation Logic
    mark = calculate_marks(s_val["Turnover %"], s_val["Studded %"], s_val["DMD %"], s_val["Scheme %"], s_val["DTSO %"])
    total_marks += mark
    
    store_data.append({
        "name": name,
        "turnover": s_val["Turnover %"],
        "studded": s_val["Studded %"],
        "dmd": s_val["DMD %"],
        "scheme": s_val["Scheme %"],
        "dtso": s_val["DTSO %"],
        "mark": mark
    })

# Define variables for the rest of the dashboard
current_store_count = len(store_data) if len(store_data) > 0 else 1
region_avg = total_marks / current_store_count
# =========================================================================

# ================= 💰 INCENTIVE & SLAB CALCULATION =================
# Calculate the final incentive amount based on the Region Average
incentive = 0
for threshold, amount in slabs[designation]:
    if region_avg >= threshold:
        incentive = amount
        break

# Find the next slab to calculate the 'Gap'
thresholds = sorted([t for t, _ in slabs[designation]])
next_threshold = next((t for t in thresholds if t > region_avg), None)

# Calculate the gap and total marks required to unlock the next level
gap = next_threshold - region_avg if next_threshold else 0
required_total = gap * current_store_count if gap > 0 else 0
# ===================================================================

# ================= TOP SNAPSHOT =================
st.markdown("## 📊 Regional Snapshot")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Region Average", round(region_avg,2))
col2.metric("Current Incentive", f"₹{incentive}")
col3.metric("Gap to Next Slab", round(gap,2))
col4.metric("Marks Required", round(required_total,2))


# ================= STRATEGIC FOCUS =================
st.markdown("## 🎯 Strategic Focus")

col_left, col_right = st.columns([2,1])

with col_left:
    st.markdown("### Multi-Store Unlock Strategy")

    if gap > 0:
        slab_targets = [75, 80, 90, 100]
        priority_metrics = ["turnover", "scheme", "dtso", "studded", "dmd"]

        strategy_found = False

        for r in [2, 3]:
            for combo in itertools.combinations(store_data, r):

                improvement_total = 0
                actions = []

                for store in combo:

                    best_improvement = 0
                    best_action = None

                    for metric in priority_metrics:

                        current = store[metric]

                        for target in slab_targets:

                            if target > current:

                                new_mark = calculate_marks(
                                    target if metric == "turnover" else store["turnover"],
                                    target if metric == "studded" else store["studded"],
                                    target if metric == "dmd" else store["dmd"],
                                    target if metric == "scheme" else store["scheme"],
                                    target if metric == "dtso" else store["dtso"],
                                )

                                improvement = new_mark - store["mark"]

                                if improvement > best_improvement:
                                    best_improvement = improvement
                                    best_action = (
                                        store["name"],
                                        metric.upper(),
                                        current,
                                        target,
                                    )

                    if best_action:
                        improvement_total += best_improvement
                        actions.append(best_action)

                if improvement_total >= required_total:
                    for action in actions:
                        st.info(
                            f"{action[0]} improves {action[1]} "
                            f"{action[2]}% → {action[3]}%"
                        )

                    st.success("👉 Combined improvement unlocks next slab")
                    strategy_found = True
                    break

            if strategy_found:
                break

        if not strategy_found:
            st.warning("No 2–3 store combination sufficient. Structural uplift required.")

    else:
        st.success("Highest slab achieved")


with col_right:
    st.markdown("### 🔴 Top 3 Risk Stores")

    sorted_stores = sorted(store_data, key=lambda x: x["mark"])

    for s in sorted_stores[:3]:
        st.error(f"{s['name']} | {s['mark']}")


# ================= PROACTIVE MILESTONE MATRIX =================
st.markdown("## 🎯 Proactive Store Milestones")
st.write("This table shows the immediate next performance slab for every store and how much it reduces the regional gap.")

if gap > 0:
    table_rows = []
    metrics = ["turnover", "studded", "dmd", "scheme", "dtso"]
    display_names = ["Turnover", "Studded %", "DMD %", "Scheme %", "DTSO %"]
    milestones = [75, 80, 90, 100]

    for store in store_data:
        row = [store["name"]]
        for metric in metrics:
            actual = store[metric]
            row.append(f"{actual}%")
            
            # Milestone logic
            next_milestone = next((m for m in milestones if m > actual), None)
            
            if next_milestone:
                sim = {m: store[m] for m in metrics}
                sim[metric] = next_milestone
                new_mark = calculate_marks(sim["turnover"], sim["studded"], sim["dmd"], sim["scheme"], sim["dtso"])
                gain = round(new_mark - store["mark"], 1)
                target_display = f"{next_milestone}% (+{gain})"
            else:
                target_display = "Maxed"
            
            row.append(target_display)
        
        # Aligned with 'for metric' to add the row after all metrics are checked
        row.append(round(store["mark"] / current_store_count, 2))
        table_rows.append(row)
        
    # Aligned with 'for store' to build the table after all stores are processed
    top_level = ["Location Name"] + [item for sublist in [[m, m] for m in display_names] for item in sublist] + ["Contribution"]
    sub_level = [" "] + ["Actual", "Next Goal"] * 5 + ["to Region"]
    
    col_tuples = list(zip(top_level, sub_level))
    columns = pd.MultiIndex.from_tuples(col_tuples)
    
    df_milestone = pd.DataFrame(table_rows, columns=columns)
    st.dataframe(df_milestone, use_container_width=True, hide_index=True)

# ================= PERFORMANCE INSIGHT =================
st.markdown("## 📈 Performance Insight")

col_chart, col_gap = st.columns([2,1])

with col_chart:
    st.markdown("### Store Performance Chart")

    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D

    store_names = []
    store_marks = []
    colors = []

    for s in store_data:
        store_names.append(s["name"])
        store_marks.append(s["mark"])

        if s["mark"] >= region_avg:
            colors.append("green")
        elif s["mark"] >= 70:
            colors.append("orange")
        else:
            colors.append("red")

    fig, ax = plt.subplots(figsize=(7,3.5))
    bars = ax.bar(store_names, store_marks, color=colors)
    ax.axhline(region_avg, linestyle='--')

    ax.set_title("Store Marks vs Region Average")
    plt.xticks(rotation=45)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2,
                height,
                f'{round(height,1)}',
                ha='center',
                va='bottom')

    legend_elements = [
        Patch(facecolor='green', label='Above Avg'),
        Patch(facecolor='orange', label='Below Avg (>=70)'),
        Patch(facecolor='red', label='Risk (<70)'),
        Line2D([0], [0], color='black', linestyle='--', label='Region Avg')
    ]

    ax.legend(handles=legend_elements)
    st.pyplot(fig)


with col_gap:
    st.markdown("### Marks to Reach Region Avg")

    for s in store_data:
        needed = round(region_avg - s["mark"],2)
        if needed > 0:
            st.warning(f"{s['name']} needs {needed}")
        else:
            st.success(f"{s['name']} above avg")


# ================= DETAILS =================
with st.expander("📊 Contribution Ranking (Detailed View)"):
    for s in sorted(store_data, key=lambda x: x["mark"], reverse=True):
        contribution = round(s["mark"]/current_store_count,2)
        st.write(f"{s['name']} | Mark: {s['mark']} | Contribution: {contribution}")

# ---------------- AUTO SAVE (STRICT) ----------------
try:
    save_data = {}
    for k, v in st.session_state.items():
        # Exclude technical widgets that cause crashes
        if k == "excel_editor" or k.startswith("_"):
            continue
        if isinstance(v, (str, int, float, bool, list, dict)):
            save_data[k] = v
    
    local_storage.setItem("region_data", save_data)
except:
    pass
