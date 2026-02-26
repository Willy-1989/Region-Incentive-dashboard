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

# ---------------- LOAD FROM BROWSER ----------------
stored_data = local_storage.getItem("region_data")

if stored_data:
    for key, value in stored_data.items():
        if key not in st.session_state:
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
# ---------------- DESIGNATION SELECTOR ----------------
st.sidebar.markdown("## 👤 Select Designation")

designation = st.sidebar.selectbox(
    "Designation",
    [
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


store_count = st.slider("Number of Stores",1,20,10)

total_marks = 0
store_data = []

for i in range(store_count):

    name = st.text_input(f"Store Name {i+1}", key=f"name_{i}")
    col1,col2,col3,col4,col5 = st.columns(5)

    t = col1.number_input("Turnover %",0.0,200.0,key=f"turn_{i}")
    s = col2.number_input("Studded %",0.0,200.0,key=f"stud_{i}")
    d = col3.number_input("DMD %",0.0,200.0,key=f"dmd_{i}")
    sc = col4.number_input("Scheme %",0.0,200.0,key=f"scheme_{i}")
    dt = col5.number_input("DTSO %",0.0,200.0,key=f"dtso_{i}")

    mark = calculate_marks(t,s,d,sc,dt)
    total_marks += mark

    store_data.append({
    "name": name if name else f"Store {i+1}",
    "turnover": t,
    "studded": s,
    "dmd": d,
    "scheme": sc,
    "dtso": dt,
    "mark": mark
})

    st.metric("Store Mark", mark)
    st.markdown("---")

# ---------------- REGION CALC ----------------
region_avg = total_marks/store_count

incentive = 0
for threshold,amount in slabs[designation]:
    if region_avg >= threshold:
        incentive = amount
        break

thresholds = sorted([t for t,_ in slabs[designation]])
next_threshold = next((t for t in thresholds if t>region_avg),None)

gap = next_threshold-region_avg if next_threshold else 0
required_total = gap*store_count if gap>0 else 0

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
    # These are your system's scoring milestones
    milestones = [75, 80, 90, 100]

    for store in store_data:
        row = [store["name"]]
        
        for metric in metrics:
            actual = store[metric]
            row.append(f"{actual}%") # Show current Actual
            
            # Find the NEXT milestone above the current achievement
            next_milestone = None
            for m in milestones:
                if m > actual:
                    next_milestone = m
                    break
            
            if next_milestone:
                # Simulate the marks gained by hitting this next milestone
                sim = {m: store[m] for m in metrics}
                sim[metric] = next_milestone
                new_mark = calculate_marks(sim["turnover"], sim["studded"], sim["dmd"], sim["scheme"], sim["dtso"])
                gain = round(new_mark - store["mark"], 1)
                
                target_display = f"{next_milestone}% (+{gain} marks)"
            else:
                target_display = "Max Slab Reached"
            
            row.append(target_display)
        
        # Contribution to the current average
        row.append(round(store["mark"] / store_count, 2))
        table_rows.append(row)
        
    # Headers matching your manual design
    top_level = ["Location Name"] + [item for sublist in [[m, m] for m in display_names] for item in sublist] + ["Contribution"]
    sub_level = [" "] + ["Actual", "Next Milestone"] * 5 + ["to Region Avg"]
    
    col_tuples = list(zip(top_level, sub_level))
    columns = pd.MultiIndex.from_tuples(col_tuples)
    
    df = pd.DataFrame(table_rows, columns=columns)
    
    # Display the interactive table
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.info(f"💡 Total regional marks needed to reach next slab: **{round(required_total, 2)}**")

else:
    st.success("🏆 Region is already at the highest slab!")

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
        contribution = round(s["mark"]/store_count,2)
        st.write(f"{s['name']} | Mark: {s['mark']} | Contribution: {contribution}")

# ---------------- AUTO SAVE TO BROWSER (FIXED) ----------------
# We filter the session state to only save data (strings, numbers, lists) 
# and ignore complex system objects that cause the "Circular Reference" error.
save_data = {k: v for k, v in st.session_state.items() if isinstance(v, (str, int, float, bool, list, dict))}
local_storage.setItem("region_data", save_data)
