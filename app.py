"""
RNBW Staking Sensitivity Analysis — Interactive Streamlit App
Run: streamlit run app.py
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="RNBW Staking Model", page_icon="🌈", layout="wide")

# ── Sidebar: Key Assumptions ────────────────────────────────────────────────────
with st.sidebar:
    st.header("Key Assumptions")
    stake = st.number_input("RNBW Required to Stake", min_value=1_000, max_value=500_000, value=20_000, step=1_000)
    penalty_pct = st.number_input("Exit Penalty (%)", min_value=0.0, max_value=50.0, value=10.0, step=0.5)
    n_users = st.number_input("Total Eligible Users (N)", min_value=100, max_value=100_000, value=6_205, step=100)
    base_vol = st.number_input("Annual Swap Volume ($)", min_value=1_000_000, max_value=2_000_000_000, value=186_851_427, step=1_000_000, format="%d")
    fee_rate_bps = st.number_input("Fee Rate (bps)", min_value=1, max_value=500, value=85)

# ── Constants ────────────────────────────────────────────────────────────────────
STAKE    = stake
PENALTY  = penalty_pct / 100
N        = n_users
FEE_RATE = fee_rate_bps / 10_000
BASE_VOL = base_vol

STAKING_RATES   = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
UNSTAKING_RATES = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
VOL_GROWTHS     = [-0.5, -0.25, 0.0, 0.25, 0.50, 0.75, 1.0]
PRICES          = [0.03, 0.05, 0.07, 0.10, 0.15, 0.20, 0.25, 0.30]

def users_staked(s):        return round(N * s)
def users_unstaked(s, u):   return round(users_staked(s) * u)
def remaining(s, u):        return users_staked(s) - users_unstaked(s, u)
def avg_stakers(s, u):      return users_staked(s) - users_unstaked(s, u) / 2
def adj_vol(g):             return BASE_VOL * (1 + g)
def staked_vol(s, u, g):    return adj_vol(g) / N * avg_stakers(s, u)

def exit_fee_apy(s, u):
    rem = remaining(s, u)
    return users_unstaked(s, u) * PENALTY / rem if rem > 0 else 0

def cashback_apy(g, price):
    return adj_vol(g) / N * FEE_RATE / (STAKE * price)

def price_appreciation_apy(s, u, g, start, end):
    return (1 + exit_fee_apy(s, u)) * (end / start) + cashback_apy(g, start) - 1

# ── Title ────────────────────────────────────────────────────────────────────────
st.title("RNBW Staking Sensitivity Analysis")
st.caption(
    f"Stake: **{STAKE:,} RNBW** · Exit Penalty: **{penalty_pct:.1f}%** · "
    f"Users: **{N:,}** · Avg Vol/User: **${BASE_VOL/N:,.0f}** · Fee: **{fee_rate_bps} bps**"
)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Executive Summary",
    "Revenue Impact",
    "Buy Pressure",
    "APY by Unstaking Rate",
    "Full APY Sensitivity",
    "Price Appreciation",
])


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 1 — Executive Summary
# ══════════════════════════════════════════════════════════════════════════════════
with tab1:
    EXEC_SCENARIOS = [
        ("Conservative Low",    0.10, 0.10, -0.50, 0.03),
        ("Conservative Mid",    0.20, 0.20,  0.00, 0.05),
        ("Conservative High",   0.30, 0.20,  0.00, 0.07),
        ("Base Case Low",       0.30, 0.30,  0.25, 0.10),
        ("Base Case Mid",       0.50, 0.30,  0.25, 0.10),
        ("Base Case High",      0.50, 0.30,  0.50, 0.10),
        ("Moderate Bull Low",   0.50, 0.20,  0.50, 0.15),
        ("Moderate Bull Mid",   0.60, 0.30,  0.50, 0.15),
        ("Moderate Bull High",  0.70, 0.20,  0.75, 0.20),
        ("Bull Case Low",       0.70, 0.30,  0.75, 0.20),
        ("Bull Case Mid",       0.80, 0.30,  1.00, 0.20),
        ("Bull Case High",      0.80, 0.20,  1.00, 0.25),
        ("Max Bull",            1.00, 0.10,  1.00, 0.30),
        ("High Churn Stress",   0.50, 0.70, -0.25, 0.05),
        ("Mass Exodus Stress",  0.80, 0.90, -0.50, 0.03),
    ]

    rows = []
    for (name, s, u, g, price) in EXEC_SCENARIOS:
        us  = users_staked(s)
        uu  = users_unstaked(s, u)
        rem = remaining(s, u)
        sv  = staked_vol(s, u, g)
        nsv = adj_vol(g) - sv
        efa = exit_fee_apy(s, u)
        ca  = cashback_apy(g, price)
        rows.append({
            "Scenario":             name,
            "Staking %":            f"{s:.0%}",
            "Unstaking %":          f"{u:.0%}",
            "Vol Growth":           f"{g:+.0%}",
            "Price ($)":            f"${price:.2f}",
            "Users Staked":         us,
            "Users Unstaked":       uu,
            "Remaining":            rem,
            "Staked Vol ($M)":      sv / 1e6,
            "Non-Staked Vol ($M)":  nsv / 1e6,
            "RNBW Staked (M)":      us * STAKE / 1e6,
            "Stake Value ($M)":     us * STAKE / 1e6 * price,
            "Buy Pressure ($)":     sv * FEE_RATE,
            "Buy Pressure (RNBW)":  sv * FEE_RATE / price,
            "Exit Penalty (RNBW)":  uu * STAKE * PENALTY,
            "Exit Penalty ($)":     uu * STAKE * PENALTY * price,
            "Exit Fee APY":         efa,
            "Cashback APY":         ca,
            "Total APY":            efa + ca,
        })

    df = pd.DataFrame(rows).set_index("Scenario")

    st.markdown("#### 🎯 To answer")
    st.markdown("""
- **Q1.** How many users staked and unstaked over the course of the year in the scenario
- **Q2.** What was the annual swap volume from staked vs. unstaked users
- **Q3.** How much RNBW did we start the year with staked *(initial stakers × stake size)*
- **Q4.** How much buy pressure of RNBW did we create *(staked swap volume × 85 bps)*
- **Q5.** How much RNBW was paid to stakers via exit penalty from users who exited
- **Q6.** What is the APY for stakers from exit fees + cashback + price appreciation
    """)
    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Stake per User", f"{STAKE:,} RNBW")
    c2.metric("Exit Penalty", f"{penalty_pct:.1f}%")
    c3.metric("Avg Vol / User", f"${BASE_VOL/N:,.0f}")
    c4.metric("Cashback APY @ $0.10", f"{cashback_apy(0.0, 0.10):.1%}")

    with st.expander("📖 How to read this tab"):
        st.markdown("""
**What this shows:** 15 pre-built scenarios ranging from conservative market conditions to stress tests,
each with a specific combination of staking adoption, unstaking rate, volume growth, and RNBW price.

**What to look at:**
- **Total APY** (rightmost column, color-coded green→red) — this is the headline number stakers earn.
  A meaningful APY (>5–10%) is what motivates users to stake and stay staked.
- **Buy Pressure ($)** — annual dollars spent buying RNBW. Higher = stronger price support from the program.
- **Exit Penalty ($)** — total value forfeited by unstakers. At high churn this becomes significant.
- **Stress scenarios** (last 2 rows) — show the worst case: high churn + falling volume + low price.
  Check that exit fee APY stays positive even here (remaining stakers are rewarded when others leave).

**How to draw conclusions:**
- If the base case scenarios show Total APY < 2%, the incentive may be too weak to drive adoption.
- If stress scenarios show large Exit Penalty pools, the program punishes panic sellers — which is healthy.
- Adjust the sidebar assumptions (stake size, penalty %) and watch how the entire table shifts.
- Compare "Conservative" vs "Base Case" rows to understand how sensitive results are to volume/price assumptions.
        """)

    st.subheader("Scenario Summary")
    styled = df.style.format({
        "Staked Vol ($M)":     "{:.2f}", "Non-Staked Vol ($M)": "{:.2f}",
        "RNBW Staked (M)":     "{:.2f}", "Stake Value ($M)":    "{:.2f}",
        "Buy Pressure ($)":    "${:,.0f}", "Buy Pressure (RNBW)": "{:,.0f}",
        "Exit Penalty (RNBW)": "{:,.0f}", "Exit Penalty ($)":    "${:,.0f}",
        "Exit Fee APY":        "{:.1%}",  "Cashback APY":        "{:.1%}",
        "Total APY":           "{:.1%}",
    }).background_gradient(subset=["Total APY"], cmap="RdYlGn", vmin=0, vmax=0.5)
    st.dataframe(styled, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 2 — Revenue Impact
# ══════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Impact on Rainbow's Swap Revenue")

    st.markdown("#### 🎯 To answer")
    st.markdown("""
- **Q7.** Impact to Rainbow's swap revenue under different numbers of users staking — *how much does our revenue go down?*
    """)
    st.divider()

    st.markdown(
        "Fee cashback redirects swap fees from protocol revenue into RNBW buybacks for stakers. "
        "This shows how much revenue is retained vs. redirected at each staking adoption level."
    )

    with st.expander("📖 How to read this tab"):
        st.markdown("""
**What this shows:** How the staking program splits Rainbow's total annual fee revenue between
revenue Rainbow keeps vs. revenue redirected into RNBW buybacks for stakers.

**What to look at:**
- **Blue bar (Revenue Kept)** — what Rainbow retains as protocol income.
- **Orange bar (Revenue Redirected)** — fees that go toward buying RNBW on behalf of stakers.
  This is not "lost" revenue — it's converted into buy pressure that supports RNBW price.
- **Total bar height is fixed** at gross revenue for the selected volume/growth scenario.
  The question is purely how it gets *split*.
- **% Revenue Redirected** in the table — the key trade-off metric. At 50% staking, roughly
  half of fee revenue goes to stakers. At 100% staking, nearly all of it does.

**How to draw conclusions:**
- The acceptable level of revenue redirection depends on Rainbow's business model.
  If protocol revenue funds operations, there's a floor below which redirection becomes a problem.
- Use the Volume Growth selector: with strong growth, gross revenue is larger, so redirecting
  the same % still leaves Rainbow with more absolute dollars.
- The Avg Unstaking Rate selector matters because unstakers stop earning cashback mid-period —
  a higher unstaking rate means slightly less total cashback paid out, so slightly more kept.
- **Key question to answer:** At what staking adoption % does the revenue trade-off feel uncomfortable?
  That's the upper bound on how aggressively to market the staking program.
        """)

    c1, c2 = st.columns(2)
    sel_g_rev   = c1.selectbox("Volume Growth", VOL_GROWTHS, index=2, format_func=lambda x: f"{x:+.0%}", key="rev_g")
    sel_u_rev   = c2.selectbox("Avg Unstaking Rate", UNSTAKING_RATES, index=2, format_func=lambda x: f"{x:.0%}", key="rev_u")

    total_gross = adj_vol(sel_g_rev) * FEE_RATE

    rows_rev = []
    for s in STAKING_RATES:
        sv      = staked_vol(s, sel_u_rev, sel_g_rev)
        nsv     = adj_vol(sel_g_rev) - sv
        rev_redir  = sv * FEE_RATE
        rev_kept   = nsv * FEE_RATE
        rows_rev.append({
            "Staking Adoption": f"{s:.0%}",
            "Revenue Kept ($)":        rev_kept,
            "Revenue Redirected ($)":  rev_redir,
            "Total Gross Revenue ($)": total_gross,
            "% Revenue Redirected":    rev_redir / total_gross,
        })

    df_rev = pd.DataFrame(rows_rev).set_index("Staking Adoption")

    # Stacked bar chart
    fig_rev = go.Figure()
    fig_rev.add_bar(
        x=df_rev.index,
        y=df_rev["Revenue Kept ($)"],
        name="Revenue Kept",
        marker_color="#2196F3",
    )
    fig_rev.add_bar(
        x=df_rev.index,
        y=df_rev["Revenue Redirected ($)"],
        name="Redirected to RNBW Buyback",
        marker_color="#FF9800",
    )
    fig_rev.update_layout(
        barmode="stack",
        title=f"Annual Fee Revenue Split — Vol Growth {sel_g_rev:+.0%}, Unstaking {sel_u_rev:.0%}",
        xaxis_title="Staking Adoption Rate",
        yaxis_title="Annual Revenue ($)",
        yaxis_tickformat="$,.0f",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=420,
    )
    st.plotly_chart(fig_rev, use_container_width=True)

    # Summary metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Gross Revenue", f"${total_gross:,.0f}")
    base_s = 0.5
    base_sv   = staked_vol(base_s, sel_u_rev, sel_g_rev)
    base_redir = base_sv * FEE_RATE
    c2.metric("Redirected @ 50% Staking", f"${base_redir:,.0f}", f"{base_redir/total_gross:.1%} of gross")
    c3.metric("Revenue Kept @ 50% Staking", f"${total_gross - base_redir:,.0f}", f"{1 - base_redir/total_gross:.1%} of gross")

    st.divider()
    st.subheader("Detailed Breakdown Table")
    st.dataframe(
        df_rev.style.format({
            "Revenue Kept ($)":        "${:,.0f}",
            "Revenue Redirected ($)":  "${:,.0f}",
            "Total Gross Revenue ($)": "${:,.0f}",
            "% Revenue Redirected":    "{:.1%}",
        }).background_gradient(subset=["% Revenue Redirected"], cmap="Reds"),
        use_container_width=True,
    )

    st.info(
        f"**Key insight:** At 50% staking adoption, Rainbow redirects **{base_redir/total_gross:.1%}** of fee revenue "
        f"(\\${base_redir:,.0f}/yr) into RNBW buybacks. The remaining **{(total_gross-base_redir)/total_gross:.1%}** "
        f"(\\${total_gross-base_redir:,.0f}/yr) stays as protocol revenue."
    )


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 3 — Buy Pressure from Captured Volume
# ══════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Buy Pressure from Capturing Leaked Swap Volume")

    st.markdown("#### 🎯 To answer")
    st.markdown("""
- **Q8.** What's the buy pressure created if we capture more swap volume that's leaking to other platforms today?
- **Q4.** *(extended)* How does total RNBW buy pressure scale across different staking adoption rates and volume capture scenarios?
    """)
    st.divider()

    st.markdown(
        "Today Rainbow captures **\\${:,.0f}** in annual swap volume across {:,} users "
        "(\\${:,.0f}/user avg). Users are also swapping on other platforms — "
        "if staking incentivizes them to route more volume through Rainbow, "
        "that creates additional RNBW buy pressure.".format(BASE_VOL, N, BASE_VOL / N)
    )

    with st.expander("📖 How to read this tab"):
        st.markdown("""
**What this shows:** The RNBW buy pressure generated by the cashback program, and how that pressure
grows if Rainbow captures more of the swap volume that users are currently doing on other platforms.

**Background:** The current model uses Rainbow's existing swap volume ($186M/year for ~6,200 users).
But those users are also swapping on Uniswap, 1inch, Cowswap, etc. If staking incentivizes them
to route more trades through Rainbow, that captured volume generates *additional* RNBW buy pressure.

**What to look at:**
- **Dark green bar** — buy pressure from current captured volume at each staking adoption level.
- **Light green bar** — *incremental* buy pressure if you capture the additional % of volume
  set by the slider. The combined height = total potential buy pressure.
- **RNBW Bought @ 50% metric** — converts dollar buy pressure into actual RNBW purchased at
  the selected price. This directly represents demand on the open market.
- **The table** — shows buy pressure across every combination of staking rate × volume captured,
  so you can find the cell matching your realistic assumptions.

**How to draw conclusions:**
- Set the slider to a realistic volume capture estimate (e.g., +50% = users route half their
  off-platform volume through Rainbow). Read the combined bar height at your expected staking rate.
- Higher RNBW price → same dollar buy pressure = fewer RNBW tokens purchased. Lower price = more
  tokens bought per dollar, which matters more for price floor support.
- **The multiplier effect:** Each % of staking adoption × each % of volume captured compounds.
  A 50% staking + 50% extra capture scenario is much more valuable than either alone.
- Look for the "knee" in the chart — the point where adding more staking adoption gives diminishing
  returns vs. focusing on volume capture instead.
        """)

    c1, c2 = st.columns(2)
    extra_vol_pct = c1.slider(
        "Additional Volume Captured (% on top of current)",
        min_value=0, max_value=300, value=50, step=25,
        help="How much more swap volume, as a % of current, could be captured through the staking incentive"
    )
    sel_price_bp = c2.selectbox(
        "RNBW Price ($)",
        PRICES, index=3, format_func=lambda x: f"${x:.2f}", key="bp_price"
    )

    effective_base_vol = BASE_VOL * (1 + extra_vol_pct / 100)
    extra_vol_abs = effective_base_vol - BASE_VOL

    # Build buy pressure table across staking rates and capture scenarios
    capture_scenarios = [0, 25, 50, 100, 150, 200, 300]
    rows_bp = []
    for s in STAKING_RATES:
        row = {"Staking Adoption": f"{s:.0%}"}
        for cap in capture_scenarios:
            eff_vol = BASE_VOL * (1 + cap / 100)
            sv = eff_vol / N * users_staked(s)   # steady-state: no unstaking
            row[f"+{cap}% vol"] = sv * FEE_RATE
        rows_bp.append(row)

    df_bp = pd.DataFrame(rows_bp).set_index("Staking Adoption")

    # Chart: current vs selected scenario
    fig_bp = go.Figure()
    for s in STAKING_RATES:
        sv_current  = BASE_VOL / N * users_staked(s)
        sv_captured = effective_base_vol / N * users_staked(s)
        bp_current  = sv_current * FEE_RATE
        bp_captured = sv_captured * FEE_RATE
        # Only show selected extra_vol as the highlighted bar

    x_labels = [f"{s:.0%}" for s in STAKING_RATES]
    bp_current_list  = [BASE_VOL / N * users_staked(s) * FEE_RATE for s in STAKING_RATES]
    bp_captured_list = [effective_base_vol / N * users_staked(s) * FEE_RATE for s in STAKING_RATES]
    bp_extra_list    = [bp_captured_list[i] - bp_current_list[i] for i in range(len(STAKING_RATES))]

    fig_bp.add_bar(x=x_labels, y=bp_current_list, name="Current Buy Pressure", marker_color="#1565C0")
    fig_bp.add_bar(x=x_labels, y=bp_extra_list,   name=f"Additional (+{extra_vol_pct}% vol captured)", marker_color="#7B1FA2", opacity=0.8)
    fig_bp.update_layout(
        barmode="stack",
        title=f"Annual RNBW Buy Pressure — Current vs. +{extra_vol_pct}% Volume Captured",
        xaxis_title="Staking Adoption Rate",
        yaxis_title="Annual Buy Pressure ($)",
        yaxis_tickformat="$,.0f",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=420,
    )
    st.plotly_chart(fig_bp, use_container_width=True)

    # Key metrics for the selected scenario
    c1, c2, c3, c4 = st.columns(4)
    bp_50_current  = BASE_VOL / N * users_staked(0.5) * FEE_RATE
    bp_50_captured = effective_base_vol / N * users_staked(0.5) * FEE_RATE
    bp_50_rnbw_c   = bp_50_captured / sel_price_bp

    c1.metric("Captured Vol / User", f"${effective_base_vol/N:,.0f}", f"+${extra_vol_abs/N:,.0f} vs today")
    c2.metric("Total Captured Vol", f"${effective_base_vol/1e6:.1f}M", f"+${extra_vol_abs/1e6:.1f}M vs today")
    c3.metric("Buy Pressure @ 50% staking", f"${bp_50_captured:,.0f}/yr", f"+${bp_50_captured - bp_50_current:,.0f} incremental")
    c4.metric("RNBW Bought @ 50% (annual)", f"{bp_50_rnbw_c:,.0f} RNBW", f"@ ${sel_price_bp:.2f}")

    st.divider()
    st.subheader(f"Buy Pressure ($) by Staking Rate × Volume Captured")
    st.dataframe(
        df_bp.style.format("${:,.0f}").background_gradient(cmap="Greens"),
        use_container_width=True,
    )


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 4 — APY by Unstaking Rate
# ══════════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("APY by Unstaking Rate")

    st.markdown("#### 🎯 To answer")
    st.markdown("""
- **Q9.** What's the APY based on different scenarios of users unstaking?
- **Q6.** *(exit fee component)* How much of staker APY comes from exit fees paid by users who leave vs. cashback from swap activity?
    """)
    st.divider()

    st.markdown(
        "Shows how staker APY changes as different fractions of stakers choose to unstake. "
        "Higher unstaking → more exit fee yield distributed to remaining stakers."
    )

    with st.expander("📖 How to read this tab"):
        st.markdown("""
**What this shows:** How a staker's total APY is composed — and how that composition shifts
as different fractions of stakers decide to exit.

**The two APY components:**
- **Cashback APY (blue)** — earned by every remaining staker from swap fee rebates.
  This is *flat* across all unstaking rates. It depends only on volume, price, and stake size —
  not on how many people leave.
- **Exit Fee APY (red)** — earned by *remaining* stakers when exiters pay their penalty.
  This grows as more people leave, because the same penalty pool is split among fewer stakers.

**What to look at:**
- The chart shows total bar height = total APY at each unstaking rate.
- At low unstaking (10%), almost all APY is cashback. The program is behaving like a loyalty reward.
- At high unstaking (70–90%), the exit fee APY dominates. Remaining stakers are significantly
  rewarded for their loyalty — this is the "diamond hands" incentive.
- The **table** shows the exact penalty pool size and per-staker payout at each unstaking rate.
- The **heatmap at the bottom** lets you compare across all staking × unstaking combinations
  simultaneously for the selected price/volume scenario.

**How to draw conclusions:**
- If cashback APY alone (at 10% unstaking) is too low, stakers won't join — increase volume capture
  or reduce the stake requirement.
- If exit fee APY only becomes meaningful at very high unstaking rates (>50%), the normal-case
  incentive is weak. Adjust the penalty rate or stake size.
- A healthy program shows: cashback APY attractive enough to join, exit fee APY high enough to
  discourage leaving. Find the unstaking rate where total APY starts to meaningfully exceed 10%.
        """)

    c1, c2, c3 = st.columns(3)
    sel_s_apy   = c1.selectbox("Staking Adoption", STAKING_RATES, index=4, format_func=lambda x: f"{x:.0%}", key="apy_s")
    sel_p_apy   = c2.selectbox("RNBW Price ($)", PRICES, index=3, format_func=lambda x: f"${x:.2f}", key="apy_p")
    sel_g_apy   = c3.selectbox("Volume Growth", VOL_GROWTHS, index=2, format_func=lambda x: f"{x:+.0%}", key="apy_g")

    ca = cashback_apy(sel_g_apy, sel_p_apy)
    u_labels = [f"{u:.0%}" for u in UNSTAKING_RATES]
    efa_list  = [exit_fee_apy(sel_s_apy, u) for u in UNSTAKING_RATES]
    total_list = [efa + ca for efa in efa_list]
    remaining_list = [remaining(sel_s_apy, u) for u in UNSTAKING_RATES]

    # Stacked bar: exit fee APY + cashback APY
    fig_apy = go.Figure()
    fig_apy.add_bar(
        x=u_labels, y=[ca] * len(UNSTAKING_RATES),
        name="Cashback APY", marker_color="#2196F3",
    )
    fig_apy.add_bar(
        x=u_labels, y=efa_list,
        name="Exit Fee APY", marker_color="#FF5722",
    )
    fig_apy.update_layout(
        barmode="stack",
        title=f"APY Components by Unstaking Rate — {sel_s_apy:.0%} Staking · ${sel_p_apy:.2f} · {sel_g_apy:+.0%} Vol",
        xaxis_title="Unstaking Rate",
        yaxis_title="APY",
        yaxis_tickformat=".0%",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=420,
    )
    st.plotly_chart(fig_apy, use_container_width=True)

    # Breakdown table
    rows_u = []
    for i, u in enumerate(UNSTAKING_RATES):
        efa = efa_list[i]
        us  = users_staked(sel_s_apy)
        uu  = users_unstaked(sel_s_apy, u)
        rem = remaining_list[i]
        rows_u.append({
            "Unstaking Rate":       f"{u:.0%}",
            "Users Staked":         us,
            "Users Unstaked":       uu,
            "Remaining Stakers":    rem,
            "Exit Fee APY":         efa,
            "Cashback APY":         ca,
            "Total APY":            efa + ca,
            "Exit Penalty Pool (RNBW)": uu * STAKE * PENALTY,
            "Penalty Per Staker (RNBW)": (uu * STAKE * PENALTY / rem) if rem > 0 else 0,
        })

    df_u = pd.DataFrame(rows_u)
    st.dataframe(
        df_u.style.format({
            "Exit Fee APY":              "{:.1%}",
            "Cashback APY":              "{:.1%}",
            "Total APY":                 "{:.1%}",
            "Exit Penalty Pool (RNBW)":  "{:,.0f}",
            "Penalty Per Staker (RNBW)": "{:,.0f}",
        }).background_gradient(subset=["Total APY"], cmap="RdYlGn"),
        use_container_width=True, hide_index=True,
    )

    st.info(
        f"**Cashback APY** is fixed at **{ca:.2%}** regardless of unstaking rate — "
        f"it only depends on volume, price, and stake size.\n\n"
        f"**Exit Fee APY** scales sharply with unstaking: at {UNSTAKING_RATES[-1]:.0%} unstaking "
        f"({remaining(sel_s_apy, UNSTAKING_RATES[-1])} remaining stakers split the penalty pool), "
        f"it reaches **{exit_fee_apy(sel_s_apy, UNSTAKING_RATES[-1]):.1%}**."
    )

    # Cross-scenario: APY across multiple staking rates
    st.divider()
    st.subheader("Total APY Across All Staking × Unstaking Combinations")
    st.caption(f"Price: ${sel_p_apy:.2f} · Volume growth: {sel_g_apy:+.0%}")

    grid = {}
    for u in UNSTAKING_RATES:
        col = []
        for s in STAKING_RATES:
            rem = remaining(s, u)
            col.append(exit_fee_apy(s, u) + ca if rem > 0 else ca)
        grid[f"{u:.0%} unstake"] = col

    df_grid = pd.DataFrame(grid, index=[f"{s:.0%} staked" for s in STAKING_RATES])
    st.dataframe(
        df_grid.style.format("{:.1%}").background_gradient(cmap="RdYlGn", vmin=0, vmax=df_grid.values.max()),
        use_container_width=True,
    )


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 5 — Full APY Sensitivity
# ══════════════════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("APY Components Detail")

    st.markdown("#### 🎯 To answer")
    st.markdown("""
- **Q6.** What is the full APY for stakers — broken down into exit fee yield, cashback yield, and price appreciation — across key market scenarios?
- **Q2.** *(extended)* How does swap volume from staked users translate into buy pressure across different staking/unstaking combinations?
    """)
    st.divider()

    DETAIL_SCENARIOS = [
        ("Conservative — $0.05 / 0% Growth",   0.05, 0.0),
        ("Base Case — $0.10 / +25% Growth",     0.10, 0.25),
        ("Moderate Bull — $0.10 / +50% Growth", 0.10, 0.50),
        ("Bull — $0.20 / +50% Growth",          0.20, 0.50),
        ("Strong Bull — $0.20 / +100% Growth",  0.20, 1.00),
        ("Max Bull — $0.30 / +100% Growth",     0.30, 1.00),
    ]
    DETAIL_COMBOS = [
        (0.2, 0.1), (0.2, 0.3), (0.2, 0.5), (0.2, 0.7),
        (0.5, 0.1), (0.5, 0.3), (0.5, 0.5), (0.5, 0.7),
        (0.8, 0.1), (0.8, 0.3), (0.8, 0.5), (0.8, 0.7),
    ]

    with st.expander("📖 How to read this tab"):
        st.markdown("""
**What this shows:** A detailed APY breakdown for 12 specific staking/unstaking combinations
under a selected market scenario (price + volume growth).

**How the scenarios are structured:**
- Each dropdown scenario fixes a RNBW price and volume growth rate (e.g., Base Case = $0.10 / +25%).
- The 12 rows cover 3 staking levels (20%, 50%, 80%) × 4 unstaking levels (10%, 30%, 50%, 70%).
  This captures the "2×2 matrix" of optimistic/pessimistic for each dimension.

**What to look at:**
- **Exit Fee APY vs Cashback APY columns** — understand which driver is dominant in this scenario.
  In low-price scenarios, cashback APY is compressed (price is in the denominator), so exit fees matter more.
  In high-price scenarios, cashback APY is lower in absolute % terms but RNBW price is higher.
- **Buy Pressure ($)** — actual dollar value of RNBW purchased annually. Useful for tokenomics planning.
- **Exit Penalty (RNBW)** — total RNBW redistributed to stayers if everyone at that unstaking rate exits.
- **Cashback APY grid at the bottom** — isolates the pure price/volume effect on cashback.
  Use this to find which price × volume scenario first makes cashback APY "meaningful" (e.g., >5%).

**How to draw conclusions:**
- Pick the scenario closest to your expected market conditions, then find the row matching your
  expected staking/unstaking behaviour. That cell's Total APY is your expected staker return.
- If the base case Total APY is below 5% for realistic staking/unstaking combinations, the program
  design (stake size, penalty, fee rate) likely needs adjustment.
- The cashback APY grid is the fastest way to see: "at what price does cashback become irrelevant
  as a standalone incentive?" — when it drops below ~1%, exit fees must do all the work.
        """)

    sel_detail = st.selectbox("Scenario", [d[0] for d in DETAIL_SCENARIOS])
    price_d, g_d = next((p, g) for (n, p, g) in DETAIL_SCENARIOS if n == sel_detail)
    ca_d = cashback_apy(g_d, price_d)

    rows_d = []
    for (s, u) in DETAIL_COMBOS:
        efa = exit_fee_apy(s, u)
        bp  = staked_vol(s, u, g_d) * FEE_RATE
        ep  = users_unstaked(s, u) * STAKE * PENALTY
        rows_d.append({
            "Staking %": f"{s:.0%}", "Unstaking %": f"{u:.0%}",
            "Users Staked": users_staked(s), "Users Unstaked": users_unstaked(s, u), "Remaining": remaining(s, u),
            "Exit Fee APY": efa, "Cashback APY": ca_d, "Total APY": efa + ca_d,
            "Buy Pressure ($)": bp, "Exit Penalty (RNBW)": ep,
        })

    df_d = pd.DataFrame(rows_d)
    st.dataframe(
        df_d.style.format({
            "Exit Fee APY": "{:.1%}", "Cashback APY": "{:.1%}", "Total APY": "{:.1%}",
            "Buy Pressure ($)": "${:,.0f}", "Exit Penalty (RNBW)": "{:,.0f}",
        }).background_gradient(subset=["Total APY"], cmap="RdYlGn"),
        use_container_width=True, hide_index=True,
    )

    st.divider()
    st.subheader("Cashback APY by Price & Volume Growth")
    cb_data = {f"{g:+.0%} vol": [cashback_apy(g, p) for p in PRICES] for g in VOL_GROWTHS}
    df_cb = pd.DataFrame(cb_data, index=[f"${p:.2f}" for p in PRICES])
    st.dataframe(df_cb.style.format("{:.1%}").background_gradient(cmap="Blues"), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════════
# TAB 6 — Price Appreciation Scenarios
# ══════════════════════════════════════════════════════════════════════════════════
with tab6:
    st.subheader("Price Appreciation Scenarios")

    st.markdown("#### 🎯 To answer")
    st.markdown("""
- **Q6.** *(price appreciation component)* What is the total staker APY when RNBW price moves from entry to exit — combining cashback yield, exit fee yield, and token price gain/loss?
    """)
    st.divider()

    with st.expander("📖 How to read this tab"):
        st.markdown("""
**What this shows:** The *total* staker return including price appreciation — what a staker would
earn if RNBW price moves from their entry price to a different price by end of year.

**Assumes:** 50% staking adoption, 30% unstaking rate (a moderate base scenario).

**How to read the matrices:**
- **Rows = starting (entry) price** — the price at which a user staked.
- **Columns = ending price** — the price at which they could unstake (or the end-of-year price).
- **Each cell** = total APY including cashback yield + exit fee yield + price gain/loss.
- Three matrices are shown: at 0%, +50%, and +100% volume growth.

**Key patterns to look for:**
- **The diagonal** (same start and end price) = APY with no price change. This is purely
  cashback + exit fee yield. Compare this to the APY analysis tabs.
- **Upper-right triangle** (end price > start price) = price appreciation adds to yield.
  The further top-right, the better — these are the "bought low, RNBW moon" scenarios.
- **Lower-left triangle** (end price < start price) = price depreciation. A cell turning
  red means price fell enough to wipe out the staking yield. Find where this threshold is.
- **Volume growth effect**: Compare the same cell across the three matrices. Higher volume
  growth lifts the entire table — because cashback APY is higher when more fees are generated.

**How to draw conclusions:**
- Find your "realistic" entry price on the row axis. Scan right to see what price RNBW needs
  to reach for staking to be worthwhile vs just holding.
- If even moderate price drops (e.g., $0.10 → $0.07) turn cells deeply red, the cashback/exit
  fee yield isn't enough to buffer downside — consider increasing the penalty or reducing stake size.
- The strongest staking incentive case is when the diagonal (zero price change) cells are already
  meaningfully positive — stakers are rewarded even without any price appreciation.
        """)

    st.caption("Assumes 50% staking / 30% unstaking. Rows = starting price, Cols = ending price.")

    p_labels = [f"${p:.2f}" for p in PRICES]
    for (title, g) in [("0% Volume Growth", 0.0), ("+50% Volume Growth", 0.50), ("+100% Volume Growth", 1.00)]:
        st.markdown(f"**{title}**")
        pa_data = {p_labels[j]: [price_appreciation_apy(0.5, 0.3, g, sp, ep) for sp in PRICES] for j, ep in enumerate(PRICES)}
        df_pa = pd.DataFrame(pa_data, index=p_labels)
        df_pa.index.name = "Start →"
        vmax, vmin = df_pa.values.max(), df_pa.values.min()
        st.dataframe(df_pa.style.format("{:.1%}").background_gradient(cmap="RdYlGn", vmin=vmin, vmax=vmax), use_container_width=True)
        st.divider()
