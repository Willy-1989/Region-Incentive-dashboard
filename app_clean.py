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
    "HEAD RETAIL": [(100, 125000), (90, 100000), (80, 90000), (70, 75000), (60, 60000), (0, 50000)],
    "BUSINESS HEAD L1": [(100, 125000), (90, 100000), (80, 90000), (70, 75000), (60, 60000), (0, 50000)],
    "BUSINESS HEAD L2": [(100, 125000), (90, 100000), (80, 90000), (70, 75000), (60, 60000), (0, 50000)],
    "GENERAL MANAGER (G1)": [(100, 105000), (90, 85000), (80, 75000), (70, 63000), (60, 51000), (0, 42000)],
    "DEPUTY GENERAL MANAGER": [(100, 105000), (90, 85000), (80, 75000), (70, 63000), (60, 51000), (0, 42000)],
    "REGIONAL MANAGER (L1)": [(100, 105000), (90, 85000), (80, 75000), (70, 63000), (60, 51000), (0, 42000)],
    "REGIONAL MANAGER (L2)": [(100, 105000), (90, 85000), (80, 75000), (70, 63000), (60, 51000), (0, 42000)],
    "ASST. REGIONAL MANAGER": [(100, 95000), (90, 75000), (80, 67500), (70, 55000), (60, 45000), (0, 37500)]
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

# This dropdown now reads directly from the dictionary keys
designation = st.sidebar.selectbox(
    "Select Your Designation",
    options=list(slabs.keys()) # <--- This is the magic fix!
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


# ================= 🚀 PRIORITY GAP CLOSER (REPLACES MULTI-STORE) =================
st.markdown("## 🚀 Priority Gap Closer Strategy")
st.write(f"Targets to bridge the **{round(gap, 2)}** point regional gap, prioritized by weightage.")

if gap > 0:
    # 1. Define Priority Weights (As per your request)
    # Turnover (Highest) -> Scheme -> DTSO -> Studded -> DMD (Lowest)
    priority_order = ["turnover", "scheme", "dtso", "studded", "dmd"]
    priority_labels = {
        "turnover": "Turnover", "scheme": "Scheme %", 
        "dtso": "DTSO %", "studded": "Studded %", "dmd": "DMD %"
    }

    # 2. Gather all possible improvements across all stores
    potential_moves = []
    milestones = [75, 80, 90, 100]

    for store in store_data:
        for metric in priority_order:
            actual = store[metric]
            next_m = next((m for m in milestones if m > actual), None)
            
            if next_m:
                # Calculate mark gain
                sim = {m: store[m] for m in priority_order}
                sim[metric] = next_m
                new_mark = calculate_marks(sim["turnover"], sim["studded"], sim["dmd"], sim["scheme"], sim["dtso"])
                gain = new_mark - store["mark"]
                
                if gain > 0:
                    potential_moves.append({
                        "Store": store["name"],
                        "Metric": priority_labels[metric],
                        "Move": f"{actual}% → {next_m}%",
                        "Mark Gain": round(gain, 1),
                        "Regional Impact": round(gain / current_store_count, 2),
                        "Priority": priority_order.index(metric) # Lower index = Higher priority
                    })

    # 3. Sort by Priority first, then by the highest impact
    sorted_moves = sorted(potential_moves, key=lambda x: (x["Priority"], -x["Regional Impact"]))

    if sorted_moves:
        # Display as a clean, actionable table
        df_strategy = pd.DataFrame(sorted_moves).drop(columns=["Priority"])
        
        # We only show the top 10 moves needed to cover the gap
        st.dataframe(
            df_strategy.head(10), 
            use_container_width=True, 
            hide_index=True
        )
        
        
        st.success(f"💡 Focus on these top **Turnover** and **Scheme** moves first to unlock the next slab efficiently.")
    else:
        st.warning("No immediate single-metric moves found. Stores may need to improve multiple metrics simultaneously.")
else:
    st.balloons()
    st.success("Region has already unlocked the maximum slab!")

# =============# ================= 🎯 INTERACTIVE SLAB SIMULATOR (V2 - FINAL) =================
st.markdown("---")
st.markdown("## 🎯 Strategic Path to Target Slab")

# 1. Identify reachable targets based on current Designation
target_options = [t for t, _ in slabs[designation] if t > region_avg]

if target_options:
    selected_target = st.selectbox("Select Target Slab to Simulate Path:", target_options)
    
    # Calculate the points needed
    points_to_gain = selected_target - region_avg
    total_marks_needed = points_to_gain * current_store_count
    
    st.info(f"📍 **Current Region Average:** {region_avg} | **Goal:** {selected_target}\n\n"
            f"🚀 **Total Marks to Gain:** {round(total_marks_needed, 1)} across the region.")

    # 2. Simulation Logic
    sim_data = [dict(s) for s in store_data] 
    path_steps = []
    current_sim_gain = 0
    
    # Priority Order (STRICT): Turnover > Scheme > DTSO > Studded > DMD
    priority_order = ["turnover", "scheme", "dtso", "studded", "dmd"]
    priority_labels = {
        "turnover": "Turnover", 
        "scheme": "Scheme %", 
        "dtso": "DTSO %", 
        "studded": "Studded %", 
        "dmd": "DMD %"  # <--- Added back in!
    }
    milestones = [75, 80, 90, 100]

    # Simulation Logic: Metric -> Milestone -> Store
    for metric in priority_order:
        if current_sim_gain >= total_marks_needed:
            break
            
        for m_target in milestones:
            if current_sim_gain >= total_marks_needed:
                break
                
            for s in sim_data:
                # If store is currently below the milestone
                if s[metric] < m_target:
                    start_val = s[metric]
                    old_mark = s["mark"]
                    
                    # Create temporary state for calculation
                    temp_metrics = {m: s[m] for m in priority_order}
                    temp_metrics[metric] = m_target
                    
                    # Calculate what the marks would be
                    new_mark = calculate_marks(
                        temp_metrics["turnover"], temp_metrics["studded"], 
                        temp_metrics["dmd"], temp_metrics["scheme"], temp_metrics["dtso"]
                    )
                    
                    gain = new_mark - old_mark
                    
                    if gain > 0:
                        path_steps.append({
                            "Priority": priority_labels[metric],
                            "Store": s["name"],
                            "Journey": f"{start_val}% ➡️ {m_target}%",
                            "Store Mark Gain": f"+{round(gain, 1)}",
                            "Regional Contribution": round(gain / current_store_count, 2)
                        })
                        
                        # Update the simulated state so next loops know where we stand
                        s[metric] = m_target
                        s["mark"] = new_mark
                        current_sim_gain += gain
                        
                        if current_sim_gain >= total_marks_needed:
                            break

    # 3. Output the Simulation Table
    if path_steps:
        df_sim = pd.DataFrame(path_steps) # df_sim is created here
        
        # This function must be indented inside the if-block
        def color_path(row):
            if row["Priority"] == "Turnover":
                return ['background-color: #fff9c4; color: #f57f17; font-weight: bold'] * len(row)
            if row["Priority"] == "Scheme %":
                return ['background-color: #e8f5e9; color: #1b5e20'] * len(row)
            return [''] * len(row)

        # This st.dataframe call must ALSO be indented inside the if-block
        st.dataframe(
            df_sim.style.apply(color_path, axis=1),
            use_container_width=True,
            hide_index=True
        )
        
        # Validation Summary
        final_avg = region_avg + (current_sim_gain / current_store_count)
        st.success(f"✅ Simulation Complete! Region Average reaches **{round(final_avg, 2)}** Marks.")
    else:
        # This handles cases where no path is found
        st.warning("⚠️ No standard moves found to bridge this gap with current store data.")

# ================= 🚀 PROACTIVE STORE MILESTONES (UPDATED) =================
if gap > 0:
    st.markdown("---")
    st.markdown("### 🚀 Strategic Milestone Journey")
    st.info("Each cell shows: **Current % ➡️ Next Target % (+Store Marks Earned)**")
    
    table_rows = []
    # Priority order: Turnover > Scheme > DTSO > Studded > DMD
    metrics = ["turnover", "scheme", "dtso", "studded", "dmd"]
    display_names = ["Turnover", "Scheme %", "DTSO %", "Studded %", "DMD %"]
    milestones = [75, 80, 90, 100]

    for store in store_data:
        row = [store["name"]]
        total_unlocked_value = 0 
        
        for metric in metrics:
            actual = store[metric]
            
            # Find the next milestone target
            next_m = next((m for m in milestones if m > actual), None)
            
            if next_m:
                # Calculate gain if they hit this milestone
                sim = {m: store[m] for m in metrics}
                sim[metric] = next_m
                new_mark = calculate_marks(sim["turnover"], sim["studded"], sim["dmd"], sim["scheme"], sim["dtso"])
                
                metric_gain = new_mark - store["mark"]
                # Display the "Journey": Current -> Next (+Points)
                target_display = f"{actual}% ➡️ {next_m}% (+{round(metric_gain, 1)})"
                total_unlocked_value += (metric_gain / current_store_count)
            else:
                target_display = "MAXED ✅"
            
            row.append(target_display)
        
        # Final column showing potential total contribution to regional average
        row.append(round(total_unlocked_value, 2))
        table_rows.append(row)
        
    # --- TABLE SETUP ---
    columns = ["Location"] + display_names + ["Potential Region Gain"]
    df_milestone = pd.DataFrame(table_rows, columns=columns)

    # Highlighting stores that can move the needle by more than 0.5 points
    def highlight_high_impact(val):
        try:
            if float(val) > 0.5:
                return 'background-color: #2e7d32; color: white; font-weight: bold'
        except:
            pass
        return ''

    st.dataframe(
        df_milestone.style.applymap(highlight_high_impact, subset=["Potential Region Gain"]),
        use_container_width=True, 
        hide_index=True
    )
    

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
