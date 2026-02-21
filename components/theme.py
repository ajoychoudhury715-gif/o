# components/theme.py
"""All app CSS injected via st.markdown (medical blue glassmorphism theme)."""

import streamlit as st


def inject_global_css() -> None:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
* { font-family: 'Inter', sans-serif !important; box-sizing: border-box; }
/* Restore Material Symbols font for Streamlit icon elements */
[data-testid="stIconMaterial"],
span[class*="material-symbols"],
span[class*="materialIcon"],
.material-symbols-rounded {
    font-family: 'Material Symbols Rounded' !important;
}

/* ── App background ── */
.stApp {
    background: linear-gradient(135deg, #f8fafc 0%, #e8f0fe 50%, #f1f5f9 100%);
    min-height: 100vh;
}

/* ── Sidebar glassmorphism ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(248,250,252,0.97) 0%, rgba(241,245,249,0.97) 100%) !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-right: 1px solid rgba(37,99,235,0.1);
    box-shadow: 4px 0 24px rgba(37,99,235,0.08);
}
[data-testid="stSidebarContent"] { padding: 20px 16px; }

/* ── Sidebar buttons ── */
[data-testid="stSidebar"] button {
    border-radius: 12px !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    box-shadow: 0 4px 20px rgba(37,99,235,0.3) !important;
    backdrop-filter: blur(10px) !important;
    font-weight: 600; color: white !important;
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
}
[data-testid="stSidebar"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(37,99,235,0.4) !important;
    background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
}
[data-testid="stSidebar"] .stSelectbox,
[data-testid="stSidebar"] .stRadio {
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(37,99,235,0.2);
    border-radius: 12px;
    padding: 8px 12px 6px 12px;
    box-shadow: 0 4px 16px rgba(37,99,235,0.08);
}

/* ── Cards ── */
.tdb-card {
    background: rgba(255,255,255,0.75);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.18);
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 8px 32px rgba(37,99,235,0.10);
    transition: all 0.3s ease;
}
.tdb-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 40px rgba(37,99,235,0.15);
    border-color: rgba(59,130,246,0.3);
}
.tdb-card-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 12px; gap: 8px;
}
.tdb-card-header > div {
    min-width: 0; flex: 1;
}
.tdb-patient-name {
    font-size: 17px; font-weight: 700; color: #1e293b;
}
.tdb-card-meta {
    font-size: 13px; color: #64748b; margin-top: 4px; word-break: break-word;
}

/* ── Status badges ── */
.status-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 20px;
    font-size: 12px; font-weight: 600; letter-spacing: 0.5px;
    text-transform: uppercase;
}
.status-PENDING   { background: rgba(148,163,184,0.2); color: #475569; border: 1px solid rgba(148,163,184,0.4); }
.status-WAITING   { background: rgba(245,158,11,0.15); color: #92400e; border: 1px solid rgba(245,158,11,0.4); }
.status-ARRIVING  { background: rgba(59,130,246,0.15); color: #1d4ed8; border: 1px solid rgba(59,130,246,0.4); }
.status-ARRIVED   { background: rgba(139,92,246,0.15); color: #5b21b6; border: 1px solid rgba(139,92,246,0.4); }
.status-ONGOING   { background: rgba(16,185,129,0.15); color: #065f46; border: 1px solid rgba(16,185,129,0.4); }
.status-DONE      { background: rgba(107,114,128,0.15); color: #374151; border: 1px solid rgba(107,114,128,0.4); }
.status-COMPLETED { background: rgba(107,114,128,0.15); color: #374151; border: 1px solid rgba(107,114,128,0.4); }
.status-CANCELLED { background: rgba(239,68,68,0.15); color: #991b1b; border: 1px solid rgba(239,68,68,0.4); }
.status-SHIFTED   { background: rgba(249,115,22,0.15); color: #7c2d12; border: 1px solid rgba(249,115,22,0.4); }
.status-LATE      { background: rgba(239,68,68,0.15); color: #991b1b; border: 1px solid rgba(239,68,68,0.4); }

/* ── Availability badges ── */
.avail-FREE    { background: rgba(16,185,129,0.15); color: #065f46; border: 1px solid rgba(16,185,129,0.4); }
.avail-BUSY    { background: rgba(245,158,11,0.15); color: #78350f; border: 1px solid rgba(245,158,11,0.4); }
.avail-BLOCKED { background: rgba(239,68,68,0.15); color: #7f1d1d; border: 1px solid rgba(239,68,68,0.4); }

/* ── Section headers ── */
.tdb-section-header {
    font-size: 22px; font-weight: 800;
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 16px;
}
.tdb-sub-header {
    font-size: 13px; font-weight: 600; color: #64748b;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;
}

/* ── Live pulse dot ── */
.live-pill {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 6px 14px; border-radius: 20px;
    font-size: 13px; font-weight: 600;
    background: linear-gradient(135deg,rgba(16,185,129,0.2),rgba(5,150,105,0.2));
    border: 1px solid rgba(16,185,129,0.3);
    color: #059669; margin-bottom: 12px;
}
.live-dot {
    width: 10px; height: 10px; border-radius: 50%;
    background: linear-gradient(135deg, #10b981, #059669);
    box-shadow: 0 0 10px rgba(16,185,129,0.6);
    animation: pulse-dot 2s ease-in-out infinite;
    display: inline-block;
}
@keyframes pulse-dot {
    0%,100% { opacity: 1; box-shadow: 0 0 10px rgba(16,185,129,0.6); }
    50%      { opacity: 0.6; box-shadow: 0 0 20px rgba(16,185,129,0.3); }
}

/* ── Conflict / pending banners ── */
.conflict-banner {
    background: linear-gradient(135deg,rgba(239,68,68,0.1),rgba(220,38,38,0.05));
    border: 2px solid rgba(239,68,68,0.3);
    border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; color: #7f1d1d;
}
.pending-banner {
    background: linear-gradient(135deg,rgba(245,158,11,0.1),rgba(217,119,6,0.05));
    border: 2px solid rgba(245,158,11,0.3);
    border-radius: 12px; padding: 12px 16px; margin-bottom: 12px;
    color: #78350f; font-size: 13px; font-weight: 500;
}

/* ── Metric cards ── */
.metric-card {
    background: rgba(255,255,255,0.75); backdrop-filter: blur(12px);
    border: 1px solid rgba(59,130,246,0.15); border-radius: 14px; padding: 16px;
    text-align: center; box-shadow: 0 4px 16px rgba(37,99,235,0.08);
}
.metric-value {
    font-size: 32px; font-weight: 800;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.metric-label { font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }

/* ── Reminder card ── */
.reminder-card {
    background: linear-gradient(135deg,rgba(239,68,68,0.08),rgba(220,38,38,0.04));
    border: 1px solid rgba(239,68,68,0.25); border-radius: 12px;
    padding: 14px; margin-bottom: 10px;
}

/* ── Duty timer card ── */
.duty-timer-card {
    background: linear-gradient(135deg,rgba(59,130,246,0.08),rgba(37,99,235,0.04));
    border: 2px solid rgba(59,130,246,0.25);
    border-radius: 12px; padding: 16px; text-align: center;
}
.duty-timer-value {
    font-size: 36px; font-weight: 800; font-variant-numeric: tabular-nums;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

/* ── Profile cards ── */
.profile-card {
    background: rgba(255,255,255,0.8); backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.3); border-radius: 14px;
    padding: 18px; margin-bottom: 12px;
    box-shadow: 0 4px 20px rgba(37,99,235,0.08); transition: all 0.25s ease;
}
.profile-card:hover { box-shadow: 0 8px 30px rgba(37,99,235,0.12); }

/* ── Main content ── */
.main .block-container { padding: 1.5rem 2rem 2rem 2rem; }

/* ── Sidebar title ── */
.sidebar-title {
    font-size: 22px; font-weight: 800;
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; margin-bottom: 16px;
}

/* ── Streamlit overrides ── */
.stButton > button {
    border-radius: 10px !important; font-weight: 600 !important;
    transition: all 0.25s ease !important;
}
.stSelectbox > div > div {
    border-radius: 10px !important; border-color: rgba(59,130,246,0.3) !important;
}
div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

/* ── Schedule scroll ── */
.schedule-scroll { max-height: 70vh; overflow-y: auto; padding-right: 8px; }
.schedule-scroll::-webkit-scrollbar { width: 6px; }
.schedule-scroll::-webkit-scrollbar-track { background: rgba(0,0,0,0.05); border-radius: 3px; }
.schedule-scroll::-webkit-scrollbar-thumb { background: rgba(37,99,235,0.3); border-radius: 3px; }

/* ── Glass panel ── */
.glass-panel {
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.25); border-radius: 20px; padding: 24px;
    box-shadow: 0 8px 32px rgba(37,99,235,0.1);
}

/* ── Doctor card ── */
.doctor-card {
    background: linear-gradient(135deg,rgba(255,255,255,0.9),rgba(248,250,252,0.9));
    border: 1px solid rgba(59,130,246,0.15); border-radius: 14px; padding: 20px;
    box-shadow: 0 4px 16px rgba(37,99,235,0.07); margin-bottom: 14px;
}

/* ── Assignment pills ── */
.assign-pill {
    display: inline-block; padding: 3px 10px;
    background: rgba(59,130,246,0.1); border: 1px solid rgba(59,130,246,0.25);
    border-radius: 14px; font-size: 12px; font-weight: 600; color: #1d4ed8;
    margin-right: 4px; margin-bottom: 2px;
}
.assign-pill-empty {
    display: inline-block; padding: 3px 10px;
    background: rgba(148,163,184,0.1); border: 1px dashed rgba(148,163,184,0.4);
    border-radius: 14px; font-size: 12px; color: #94a3b8;
    margin-right: 4px;
}
</style>
""", unsafe_allow_html=True)


def status_badge_html(status: str) -> str:
    s = status.strip().upper()
    css_key = s.replace(" ", "")
    return f'<span class="status-badge status-{css_key}">{s}</span>'


def avail_badge_html(status: str) -> str:
    s = status.strip().upper()
    icons = {"FREE": "🟢", "BUSY": "🟡", "BLOCKED": "🔴"}
    icon = icons.get(s, "⚪")
    return f'<span class="status-badge avail-{s}">{icon} {s}</span>'


def assign_pill_html(name: str) -> str:
    if not name or name.strip() in ("", "nan", "none"):
        return '<span class="assign-pill-empty">—</span>'
    return f'<span class="assign-pill">{name.strip()}</span>'
