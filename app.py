import sqlite3
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from privacy_sentinel import db_setup
from privacy_sentinel.auth import authenticate, create_user, email_exists
from privacy_sentinel.comparator import compare_labels
from privacy_sentinel.scoring import calculate_scores
from privacy_sentinel import data_manager as dm

DB_PATH = "data/privacy_sentinel.db"
CATEGORIES = ["Social media", "Health", "Finance", "Other"]

# runs once when the script starts — builds data/ and the tables if they're not there yet
db_setup.init_db(DB_PATH)


def get_conn():
    # short-lived connection, opened and closed per page action instead of kept open
    return sqlite3.connect(DB_PATH)


def risk_badge(flag):
    return {"High": "🔴 High", "Medium": "🟡 Medium", "Low": "🟢 Low"}.get(flag or "", "— —")


for key, default in [
    ("authenticated", False),
    ("current_user", None),
    ("show_register", False),
    ("page", "Dashboard"),
    ("last_result", None),
    ("high_threshold", 0.5),
    ("medium_threshold", 0.7),
]:
    if key not in st.session_state:
        st.session_state[key] = default


# nobody sees the sidebar or any page below this until they log in —
# st.stop() at the bottom of this block kills the script here, so nothing after it runs
if not st.session_state.authenticated:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            "<h1 style='text-align:center; font-size:2.2rem;'>🔒 Privacy Sentinel</h1>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#888; margin-bottom:1.5rem;'>"
            "Cross-platform privacy label analysis</p>",
            unsafe_allow_html=True,
        )

        if not st.session_state.show_register:
            # login form
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                remember = st.checkbox("Remember me")
                login_btn = st.form_submit_button("Login", use_container_width=True, type="primary")

            st.markdown(
                "<p style='text-align:center; margin-top:0.4rem;'>"
                "<small style='color:#888;'>Forgot password? Contact your administrator.</small></p>",
                unsafe_allow_html=True,
            )
            st.markdown("<div style='text-align:center; margin-top:1rem;'>", unsafe_allow_html=True)
            if st.button("Don't have an account? Create one", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            if login_btn:
                if not email.strip() or not password:
                    st.error("Please enter your email and password.")
                else:
                    conn = get_conn()
                    user = authenticate(conn, email, password)
                    conn.close()
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.current_user = {"id": user[0], "name": user[1], "email": user[2]}
                        st.rerun()
                    else:
                        st.error("Incorrect email or password.")

        else:
            # register form
            st.markdown("#### Create your account")
            with st.form("register_form"):
                reg_name = st.text_input("Full name", placeholder="e.g. Jane Smith")
                reg_email = st.text_input("Email", placeholder="e.g. jane@example.com")
                reg_pass = st.text_input("Password", type="password", placeholder="Choose a password")
                reg_pass2 = st.text_input("Confirm password", type="password", placeholder="Repeat your password")
                reg_btn = st.form_submit_button("Create Account", use_container_width=True, type="primary")

            if st.button("Already have an account? Log in", use_container_width=True):
                st.session_state.show_register = False
                st.rerun()

            if reg_btn:
                errors = []
                if not reg_name.strip():
                    errors.append("Full name is required.")
                if not reg_email.strip():
                    errors.append("Email is required.")
                if len(reg_pass) < 6:
                    errors.append("Password must be at least 6 characters.")
                if reg_pass != reg_pass2:
                    errors.append("Passwords do not match.")

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    conn = get_conn()
                    ok = create_user(conn, reg_name.strip(), reg_email.strip(), reg_pass)
                    conn.close()
                    if ok:
                        st.success("Account created! You can now log in.")
                        st.session_state.show_register = False
                        st.rerun()
                    else:
                        st.error("That email address is already registered.")

    st.stop()


# everything below here only runs once logged in
st.sidebar.title("🔒 Privacy Sentinel")
user_info = st.session_state.current_user
if user_info:
    st.sidebar.caption(f"Logged in as **{user_info['name']}**")
st.sidebar.markdown("---")
for label in ["Dashboard", "Submit", "History", "Settings"]:
    if st.sidebar.button(label, use_container_width=True):
        st.session_state.page = label
        st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("Logout", use_container_width=True):
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.show_register = False
    st.session_state.page = "Dashboard"
    st.rerun()

page = st.session_state.page


if page == "Dashboard":
    st.title("Analyst Dashboard")

    conn = get_conn()
    apps = dm.get_all_apps(conn)
    conn.close()

    scored = [a for a in apps if a["overall"] is not None]
    avg_score = sum(a["overall"] for a in scored) / len(scored) if scored else 0
    high_risk = sum(1 for a in scored if a["risk_flag"] == "High")

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Apps", len(apps))
    c2.metric("Avg Transparency Score", f"{avg_score:.0%}")
    c3.metric("High Risk Apps", high_risk)
    c4.metric("Apps Scored", len(scored))

    st.markdown("---")

    # Bar chart — avg score by category
    if scored:
        df = pd.DataFrame(scored)
        df["score_pct"] = df["overall"] * 100
        cat_df = df.dropna(subset=["category"]).groupby("category")["score_pct"].mean().reset_index()
        cat_df.columns = ["Category", "Avg Score (%)"]
        if not cat_df.empty:
            fig = px.bar(
                cat_df, x="Category", y="Avg Score (%)",
                color="Avg Score (%)",
                color_continuous_scale=["red", "orange", "green"],
                range_color=[0, 100],
                title="Average Transparency Score by Category",
            )
            fig.update_layout(coloraxis_showscale=False, height=300)
            st.plotly_chart(fig, use_container_width=True)

    # Recent submissions table
    st.subheader("Recent Submissions")
    if apps:
        hdr = st.columns([3, 2, 2, 2, 1])
        for col, label in zip(hdr, ["App", "Category", "Score", "Risk", ""]):
            col.markdown(f"**{label}**")
        st.divider()
        for a in apps[:10]:
            score_txt = f"{a['overall']:.0%}" if a["overall"] is not None else "—"
            r1, r2, r3, r4, r5 = st.columns([3, 2, 2, 2, 1])
            r1.write(a["name"])
            r2.write(a["category"] or "—")
            r3.write(score_txt)
            r4.write(risk_badge(a["risk_flag"]))
            if r5.button("View", key=f"dash_view_{a['id']}"):
                st.session_state.page = "History"
                st.rerun()
    else:
        st.info("No apps yet. Go to **Submit** to add your first app.")

    st.markdown("---")
    if st.button("+ Add App", type="primary"):
        st.session_state.page = "Submit"
        st.rerun()



elif page == "Submit":
    st.title("New App Submission")

    with st.form("submit_form"):
        st.subheader("App Details")
        d1, d2, d3 = st.columns(3)
        app_name = d1.text_input("App name *", placeholder="e.g. WhatsApp")
        developer = d2.text_input("Developer", placeholder="e.g. Meta Platforms")
        category = d3.selectbox("Category", CATEGORIES)

        st.divider()

        ios_col, android_col = st.columns(2)

        with ios_col:
            st.markdown("**iOS — App Store label**")
            ios_cats = st.text_input("Data categories (comma separated)", key="ios_cats",
                                     placeholder="e.g. analytics, diagnostics")
            ios_types = st.text_input("Data types collected", key="ios_types",
                                      placeholder="e.g. location, identifiers")
            ios_tracking = st.radio("Tracking disclosed?",
                                    ["Yes", "No", "Not stated"], key="ios_tracking", horizontal=True)
            ios_shares = st.radio("Shares with third parties?",
                                  ["Yes", "No"], key="ios_shares", horizontal=True)
            ios_deletion = st.radio("Data deletion option?",
                                    ["Yes", "No"], key="ios_deletion", horizontal=True)

        with android_col:
            st.markdown("**Android — Play Store label**")
            and_cats = st.text_input("Data categories (comma separated)", key="and_cats",
                                     placeholder="e.g. analytics, diagnostics")
            and_types = st.text_input("Data types collected", key="and_types",
                                      placeholder="e.g. location, identifiers")
            and_tracking = st.radio("Tracking disclosed?",
                                    ["Yes", "No", "Not stated"], key="and_tracking", horizontal=True)
            and_shares = st.radio("Shares with third parties?",
                                  ["Yes", "No"], key="and_shares", horizontal=True)
            and_deletion = st.radio("Data deletion option?",
                                    ["Yes", "No"], key="and_deletion", horizontal=True)

        submitted = st.form_submit_button("Submit and Analyse", use_container_width=True, type="primary")

    if submitted:
        if not app_name.strip():
            st.error("App name is required.")
        else:
            label_ios = {
                "data_categories": ios_cats,
                "data_types": ios_types,
                "tracking_disclosed": ios_tracking,
                "shares_data": ios_shares,
                "data_deletion_option": ios_deletion,
            }
            label_android = {
                "data_categories": and_cats,
                "data_types": and_types,
                "tracking_disclosed": and_tracking,
                "shares_data": and_shares,
                "data_deletion_option": and_deletion,
            }

            # this is the actual analysis step — everything else on this page is just the form
            comp = compare_labels(label_ios, label_android)
            scores = calculate_scores(
                label_ios, label_android, comp,
                high_threshold=st.session_state.high_threshold,
                medium_threshold=st.session_state.medium_threshold,
            )

            conn = get_conn()
            app_id = dm.insert_application(conn, app_name.strip(), developer.strip() or None, category)
            dm.insert_label(conn, app_id, "iOS", ios_cats, ios_types, ios_tracking, ios_shares, ios_deletion)
            dm.insert_label(conn, app_id, "Android", and_cats, and_types, and_tracking, and_shares, and_deletion)
            dm.insert_scores(conn, app_id, scores)
            conn.close()

            st.session_state.last_result = {
                "app_name": app_name.strip(),
                "category": category,
                "label_ios": label_ios,
                "label_android": label_android,
                "comp": comp,
                "scores": scores,
            }
            st.session_state.page = "Results"
            st.rerun()



elif page == "Results":
    if not st.session_state.last_result:
        st.info("No results to show. Submit an app first.")
    else:
        r = st.session_state.last_result
        scores = r["scores"]
        comp = r["comp"]

        st.title(f"Analysis Report — {r['app_name']} · {r['category']}")

        # Score headline
        overall_pct = int(scores["overall"] * 100)
        flag = scores["risk_flag"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Overall Score", f"{overall_pct} / 100")
        c2.metric("Risk Level", risk_badge(flag))
        c3.metric("Completeness", f"{scores['completeness']:.0%}")
        c4.metric("Specificity", f"{scores['specificity']:.0%}")

        st.markdown("---")

        chart_col, bar_col = st.columns(2)

        with chart_col:
            # Radar chart — score breakdown
            cats_r = ["Completeness", "Specificity", "Consistency"]
            vals = [scores["completeness"], scores["specificity"], scores["consistency"]]
            fig = go.Figure(go.Scatterpolar(
                r=vals + [vals[0]],
                theta=cats_r + [cats_r[0]],
                fill="toself",
                line_color="steelblue",
            ))
            fig.update_layout(
                polar=dict(radialaxis=dict(range=[0, 1])),
                title="Score Breakdown",
                height=320,
            )
            st.plotly_chart(fig, use_container_width=True)

        with bar_col:
            # Bar chart — iOS vs Android data types
            ios_set = {t.strip().lower() for t in (r["label_ios"].get("data_types") or "").split(",") if t.strip()}
            and_set = {t.strip().lower() for t in (r["label_android"].get("data_types") or "").split(",") if t.strip()}
            all_types = sorted(ios_set | and_set)
            if all_types:
                type_df = pd.DataFrame({
                    "Data Type": all_types,
                    "iOS": [1 if t in ios_set else 0 for t in all_types],
                    "Android": [1 if t in and_set else 0 for t in all_types],
                })
                fig2 = px.bar(type_df, x="Data Type", y=["iOS", "Android"],
                              barmode="group", title="iOS vs Android — Data Types",
                              height=320)
                st.plotly_chart(fig2, use_container_width=True)

        # Discrepancies
        st.subheader("Discrepancies Identified")
        bool_fields = comp.get("boolean_fields", {})
        any_issue = False
        for field, info in bool_fields.items():
            label_name = field.replace("_", " ").title()
            if info["match"] is False:
                st.error(f"✗ {label_name}: iOS = **{info['a']}** | Android = **{info['b']}**")
                any_issue = True
            elif info["match"] is True:
                st.success(f"✓ {label_name}: Both platforms = **{info['a']}**")

        only_ios = set(comp["categories"]["a"]) - set(comp["categories"]["b"])
        only_and = set(comp["categories"]["b"]) - set(comp["categories"]["a"])
        if only_ios:
            st.warning(f"✗ Categories only on iOS: {', '.join(sorted(only_ios))}")
            any_issue = True
        if only_and:
            st.warning(f"✗ Categories only on Android: {', '.join(sorted(only_and))}")
            any_issue = True
        if not any_issue and not bool_fields:
            st.success("No discrepancies detected.")

        # Recommendation box
        st.markdown("---")
        if flag == "High":
            st.error("**Recommendation:** Significant transparency issues detected. Missing declarations and/or major cross-platform inconsistencies. This label should be reviewed.")
        elif flag == "Medium":
            st.warning("**Recommendation:** Some discrepancies between iOS and Android labels. Review the fields above.")
        else:
            st.success("**Recommendation:** Labels appear complete and consistent across both platforms.")

        # Export
        export_df = pd.DataFrame([{
            "App": r["app_name"], "Category": r["category"],
            "Overall": scores["overall"], "Completeness": scores["completeness"],
            "Specificity": scores["specificity"], "Consistency": scores["consistency"],
            "Risk": scores["risk_flag"],
        }])
        st.download_button(
            "Export CSV", export_df.to_csv(index=False),
            file_name=f"{r['app_name'].replace(' ', '_')}_report.csv",
            mime="text/csv",
        )



elif page == "History":
    st.title("Submission History")

    conn = get_conn()
    apps = dm.get_all_apps(conn)
    conn.close()

    # Filters
    f1, f2, f3 = st.columns([3, 2, 2])
    search = f1.text_input("Search app name", placeholder="Search...")
    cat_filter = f2.selectbox("Category", ["All"] + CATEGORIES)
    risk_filter = f3.selectbox("Risk level", ["All", "High", "Medium", "Low"])

    filtered = apps
    if search:
        filtered = [a for a in filtered if search.lower() in (a["name"] or "").lower()]
    if cat_filter != "All":
        filtered = [a for a in filtered if a.get("category") == cat_filter]
    if risk_filter != "All":
        filtered = [a for a in filtered if a.get("risk_flag") == risk_filter]

    st.caption(f"Showing {len(filtered)} of {len(apps)} records")
    st.divider()

    if not filtered:
        st.info("No apps match your filters.")
    else:
        hdr = st.columns([3, 2, 2, 2, 2, 1])
        for col, lbl in zip(hdr, ["App name", "Category", "Score", "Risk", "Date", ""]):
            col.markdown(f"**{lbl}**")
        st.divider()

        for a in filtered:
            c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 2, 2, 2, 1])
            c1.write(a["name"])
            c2.write(a["category"] or "—")
            c3.write(f"{a['overall']:.0%}" if a["overall"] is not None else "—")
            c4.write(risk_badge(a["risk_flag"]))
            c5.write((a["created_at"] or "")[:10])
            if c6.button("🗑", key=f"del_{a['id']}"):
                conn = get_conn()
                dm.delete_app(conn, a["id"])
                conn.close()
                st.rerun()



elif page == "Settings":
    st.title("System Settings")

    st.subheader("Scoring Thresholds")
    st.caption("Scores range from 0 (worst) to 1 (best). High threshold must be lower than medium.")
    s1, s2 = st.columns(2)
    high = s1.number_input("High risk — score below", min_value=0.0, max_value=1.0,
                            value=float(st.session_state.high_threshold), step=0.05, format="%.2f")
    medium = s2.number_input("Medium risk — score below", min_value=0.0, max_value=1.0,
                              value=float(st.session_state.medium_threshold), step=0.05, format="%.2f")

    st.markdown("---")
    b1, b2 = st.columns(2)
    if b1.button("Save settings", type="primary"):
        if high >= medium:
            st.error("High risk threshold must be lower than medium risk threshold.")
        else:
            st.session_state.high_threshold = high
            st.session_state.medium_threshold = medium
            st.success("Settings saved.")
    if b2.button("Reset to defaults"):
        st.session_state.high_threshold = 0.5
        st.session_state.medium_threshold = 0.7
        st.success("Reset to defaults (High < 0.50, Medium < 0.70).")
