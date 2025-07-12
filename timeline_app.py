import plotly.express as px
from dash import Dash, dcc, html, Input, Output, callback_context
import dash_bootstrap_components as dbc
import datetime as dt
import pandas as pd
import subprocess, sys, os
import dash_auth
from dotenv import load_dotenv

load_dotenv()

# Palette de couleurs personnalisée
TIMELINE_COLOR_SEQUENCE = [
    "#FFB347", "#AEC6CF", "#77DD77", "#CBAACB", "#FFD1DC",
    "#FDFD96", "#B39EB5", "#FF6961", "#03C03C", "#779ECB"
]

def load_data():
    try:
        df = pd.read_excel("all_clickup_tasks_with_subtasks.xlsx")
        df = df.dropna(subset=["start_date", "due_date"])
        df["start_date"] = pd.to_datetime(df["start_date"])
        df["due_date"] = pd.to_datetime(df["due_date"])
        return df
    except Exception as e:
        print("Erreur chargement données:", e)
        return pd.DataFrame()

def build_timeline_data(df, view_mode):
    status = {
        "to do": "📝", "selected for development": "🚦", "in progress": "⏳",
        "on hold": "⏸️", "review": "🔍", "done": "🆗", "complete": "🎉",
    }
    priority = {
        "urgent": "🔴", "high": "🟠", "normal": "🔵", "low": "⚪",
    }
    rows = []
    for list_name in df["list"].unique():
        group = df[df["list"] == list_name]
        if view_mode == "Project 📁 ":
            rows.append({
                "y_label": f"📦 {list_name}",
                "start": group["start_date"].min(),
                "end": group["due_date"].max(),
                "Project 📁 ": list_name,
                "assignee": "", "priority": "", "status": "",
                "label": f"📁 <b>{list_name}</b>", "textposition": "inside"
            })
        tasks = group[group["type"] == "task"].sort_values("start_date")
        for _, task_row in tasks.iterrows():
            assignees = task_row.get("assignee", "")
            initials = ", ".join(["".join([p[0].upper() for p in a.strip().split()[:2]]) for a in assignees.split(",") if a.strip()]) if assignees else "NA"
            label = task_row["task_name"]
            textposition = "inside" if len(label) <= 25 else "outside"
            if view_mode in ["task", "detailed"]:
                # Affiche task_id en transparent dans y_label
                y_label = f"{initials} | {status.get(task_row.get('status', '').lower(), '')} | {priority.get(task_row.get('priority', '').lower(), '')}"
                if task_row.get("task_id"):
                    y_label += f" | <span style='color:rgba(0,0,0,0.15)'>{task_row['task_id']}</span>"
                rows.append({
                    "y_label": y_label,
                    "start": task_row["start_date"],
                    "end": task_row["due_date"],
                    "Project 📁 ": task_row["list"],
                    "assignee": assignees,
                    "priority": task_row.get("priority", "Non précisée"),
                    "status": task_row.get("status", "Non défini"),
                    "label": label,
                    "textposition": textposition
                })
            if view_mode == "detailed":
                subtasks = group[(group["type"] == "subtask") & (group["parent_id"] == task_row["task_id"])]
                for _, sub_row in subtasks.sort_values("start_date").iterrows():
                    assignees = sub_row.get("assignee", "")
                    initials = ", ".join(["".join([p[0].upper() for p in a.strip().split()[:2]]) for a in assignees.split(",") if a.strip()]) if assignees else "NA"
                    sub_label_text = sub_row["task_name"]
                    textposition = "inside" if len(sub_label_text) <= 25 else "outside"
                    rows.append({
                        "y_label": f"{initials} | {status.get(sub_row.get('status', '').lower(), '')} | {priority.get(sub_row.get('priority', '').lower(), '')} | {sub_row['task_id']}",
                        "start": sub_row["start_date"],
                        "end": sub_row["due_date"],
                        "Project 📁 ": sub_row["list"],
                        "assignee": assignees,
                        "priority": sub_row.get("priority", "Non précisée"),
                        "status": sub_row.get("status", "Non défini"),
                        "label": sub_label_text,
                        "textposition": textposition
                    })
    return pd.DataFrame(rows)

def get_time_settings(granularity):
    if granularity == "daily":
        return {"tickformat": "%d/%m", "dtick": "D1", "tickangle": -90}
    elif granularity == "weekly":
        return {"tickformat": "Semaine %W\n%Y", "dtick": 604800000, "tickangle": 0}
    elif granularity == "monthly":
        return {"tickformat": "%b %Y", "dtick": "M1", "tickangle": 0}
    elif granularity == "quarterly":
        return {"tickformat": "%b %Y", "dtick": "M3", "tickangle": 0}
    elif granularity == "yearly":
        return {"tickformat": "%Y", "dtick": "M12", "tickangle": 0}
    return {}

# --- Dash Layout ---
app = Dash(__name__, external_stylesheets=[dbc.themes.LUX])

VALID_USERNAME_PASSWORD_PAIRS = {
    os.getenv("DASH_USERNAME"): os.getenv("DASH_PASSWORD")
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

app.title = "Timeline ClickUp Interactive"

df_loaded = load_data()

def dropdown_options(col):
    unique_names = set()
    for assignees in df_loaded[col].dropna():
        for name in assignees.split(","):
            clean = name.strip()
            if clean:
                unique_names.add(clean)
    return [{"label": name, "value": name} for name in sorted(unique_names)]


sidebar = dbc.Card(
    [
        html.H5("Filters", className="text-center mb-3", style={"fontSize": "0.92rem"}),
        html.Div(style={"height": "8px"}),

        dbc.Label("🗓️ Time View", style={"fontSize": "0.78rem"}),
        html.Div(style={"height": "10px"}),
        dcc.Dropdown(
            id="granularity",
            options=[
                {"label": "Daily", "value": "daily"},
                {"label": "Weekly", "value": "weekly"},
                {"label": "Monthly", "value": "monthly"},
                {"label": "Quarterly", "value": "quarterly"},
                {"label": "Yearly", "value": "yearly"},
            ],
            value="monthly",
            clearable=False,
            className="mb-2",
            style={"fontSize": "0.78rem", "height": "24px"}
        ),
        html.Div(style={"height": "30px"}),

        dbc.Label("➕ Detail Level", style={"fontSize": "0.78rem"}),
        html.Div(style={"height": "4px"}),
        dcc.Dropdown(
            id="view-mode",
            options=[
                {"label": "Detailed (tasks + subtasks)", "value": "detailed"},
                {"label": "By task (no subtasks)", "value": "task"},
                {"label": "By project only", "value": "Project 📁 "},
            ],
            value="detailed",
            clearable=False,
            className="mb-2",
            style={"fontSize": "0.78rem", "height": "24px"}
        ),
        html.Div(style={"height": "30px"}),

        dbc.Label("📶 Status", style={"fontSize": "0.78rem"}),
        html.Div(style={"height": "4px"}),
        dcc.Dropdown(
            id="status-filter",
            options=dropdown_options("status"),
            multi=True,
            className="mb-2",
            style={"fontSize": "0.78rem", "height": "24px"}
        ),
        html.Div(style={"height": "16px"}),


        dbc.Label("🚩 Priority", style={"fontSize": "0.78rem"}),
        html.Div(style={"height": "4px"}),
        dcc.Dropdown(
            id="priority-filter",
            options=dropdown_options("priority"),
            multi=True,
            className="mb-2",
            style={"fontSize": "0.78rem", "height": "24px"}
        ),
        html.Div(style={"height": "30px"}),

        dbc.Label("🙍‍♂️ / 🙍‍♀️ Assigned to", style={"fontSize": "0.78rem"}),
        html.Div(style={"height": "4px"}),
        dcc.Dropdown(
            id="assignee-filter",
            options=dropdown_options("assignee"),
            multi=True,
            className="mb-2",
            style={"fontSize": "0.78rem", "height": "24px"}
        ),
        html.Div(style={"height": "30px"}),

        dbc.Button(
            "🔄 Refresh",
            id="refresh-button",
            color="primary",
            className="w-100 mt-2 refresh-anim",
            style={
                "fontSize": "0.75rem",
                "padding": "7px 0",
                "background": "linear-gradient(90deg, #4f8cff 0%, #38c6ff 100%)",
                "border": "none",
                "borderRadius": "8px",
                "boxShadow": "0 2px 8px rgba(80,140,255,0.12)",
                "fontWeight": "bold",
                "letterSpacing": "0.03em",
                "transition": "background 0.2s, box-shadow 0.2s, transform 0.2s",
                "color": "#fff"
            }
        ),
        # CSS animation for the button (see assets/refresh_anim.css)
    ],
    body=True,
    className="shadow-sm",
    style={
        "minWidth": "210px",
        "height": "100vh",
        "position": "fixed",
        "top": 0,
        "left": 0,
        "zIndex": 1000,
        "background": "#fff",
        "padding": "10px 8px"
    }
)

app.layout = dbc.Container(
    [
        dbc.Row([
            dbc.Col(sidebar, width=2, style={"paddingRight": 0, "maxWidth": "210px"}),
            dbc.Col(
                [
                    html.Div(style={"height": "2px"}),
                    html.H4(
                        "📊 Vue Timeline des projets Dusens Research",
                        className="text-center my-3",
                        style={"fontSize": "1.1rem"}
                    ),
                    dcc.Loading(
                        id="loading-graph",
                        type="circle",
                        fullscreen=True,
                        children=[
                            dcc.Graph(id="timeline-graph"),
                            html.Div(id="error-message", className="text-danger mt-2", style={"fontSize": "0.95rem"})
                        ]
                    ),
                ],
                width=10,
                style={"marginLeft": "210px"}
            ),
        ], className="g-0"),
    ],
    fluid=True,
    style={"background": "#f4f6fa", "minHeight": "100vh", "paddingLeft": "0px"}
)

@app.callback(
    Output("timeline-graph", "figure"),
    Output("error-message", "children"),
    Input("granularity", "value"),
    Input("view-mode", "value"),
    Input("assignee-filter", "value"),
    Input("priority-filter", "value"),
    Input("status-filter", "value"),
    Input("refresh-button", "n_clicks")
)
def update_graph(granularity, view_mode, assignee_val, priority_val, status_val, n_clicks):
    error = ""
    triggered = [t["prop_id"] for t in callback_context.triggered]
    if "refresh-button.n_clicks" in triggered and n_clicks:
        try:
            subprocess.run([
                sys.executable, "tasks/get_all_tasks_with_subtasks.py"
            ], check=True, cwd=os.path.dirname(__file__), env={**os.environ, "PYTHONPATH": os.path.abspath(".")})
        except Exception as e:
            error = f"Erreur lors de l'actualisation : {e}"
    df = load_data()
    if df.empty:
        return {}, "Aucune donnée disponible."
    data = build_timeline_data(df, view_mode)
    if assignee_val:
        def matches_assignee(row_assignee):
            if not isinstance(row_assignee, str):
                return False
            row_names = [name.strip() for name in row_assignee.split(",")]
            return any(val in row_names for val in assignee_val)

        data = data[data["assignee"].apply(matches_assignee)]


    if priority_val:
        data = data[data["priority"].isin(priority_val)]
    if status_val:
        data = data[data["status"].isin(status_val)]
    if data.empty:
        return {}, "Aucune tâche ne correspond aux filtres."
    time_cfg = get_time_settings(granularity)
    # Ajoute des icônes dans les labels pour l'info-bulle (hover)
    status_icons = {
        "to do": "📝", "selected for development": "🚦", "in progress": "⏳",
        "on hold": "⏸️", "review": "🔍", "done": "🆗", "complete": "🎉",
    }
    priority_icons = {
        "urgent": "🔴", "high": "🟠", "normal": "🔵", "low": "⚪",
    }

    def assignee_with_icon(row):
        assignees = row.get("assignee", "")
        if not assignees:
            return "NA"
        return ", ".join(
            ["" + "".join([p[0].upper() for p in a.strip().split()[:2]]) for a in assignees.split(",") if a.strip()]
        )

    def status_with_icon(row):
        val = str(row.get("status", "")).lower()
        return f"{status_icons.get(val, '')} {row.get('status', '')}"

    def priority_with_icon(row):
        val = str(row.get("priority", "")).lower()
        return f"{priority_icons.get(val, '')} {row.get('priority', '')}"

    def start_with_icon(row):
        val = row.get("start", "")
        return f"{val.strftime('%Y-%m-%d') if pd.notnull(val) else ''}"

    def end_with_icon(row):
        val = row.get("end", "")
        return f"{val.strftime('%Y-%m-%d') if pd.notnull(val) else ''}"

    data["status"] = data.apply(status_with_icon, axis=1)
    data["priority"] = data.apply(priority_with_icon, axis=1)
    data["assignee"] = data.apply(assignee_with_icon, axis=1)
    data["start date"] = data.apply(start_with_icon, axis=1)
    data["due date"] = data.apply(end_with_icon, axis=1)

    # Ajoute la colonne task_name pour le hover avec une icône
    data["task_name"] = "📝 " + data["label"]

    fig = px.timeline(
        data,
        x_start="start",
        x_end="end",
        y="y_label",
        color="Project 📁 ",
        hover_data={"start": False, "end": False, "y_label": False},
        custom_data=["task_name", "Project 📁 ", "assignee", "priority", "status", "start date", "due date"],
        color_discrete_sequence=TIMELINE_COLOR_SEQUENCE,
        text="task_name"
    )

    # Réduit la hauteur des frises (barres) en réduisant la largeur des barres
    fig.update_traces(textposition="outside", width=0.2)  # width < 1.0 réduit la hauteur des barres horizontales

    # Renomme les colonnes dans les hover labels
    fig.update_traces(
    hovertemplate=(
        "📌 Task: %{customdata[0]}<br>"
        "📁 Project: %{customdata[1]}<br>"
        "📶 Status: %{customdata[4]}<br>"
        "🚩 Priority: %{customdata[3]}<br>"
        "🙍 Assigned to: %{customdata[2]}<br>"
        "🚀 Start: %{customdata[5]}<br>"
        "🏁 End: %{customdata[6]}<extra></extra>"
    )
)

    fig.update_traces(textposition="outside")
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=10))
    fig.add_vline(
        x=dt.datetime.today(),
        line_width=.3,
        line_dash="dash",
        line_color="red"
    )
    fig.update_layout(
        height=800,
        width=1200,
        bargap=0.2,
        margin=dict(l=260, r=40, t=70, b=40),
        yaxis_title=None,
        plot_bgcolor="#ffffff",
        paper_bgcolor="rgba(248,249,250,0.91)",
        font=dict(family="Segoe UI, Arial, sans-serif", size=13, color="#222"),
        xaxis=dict(
            showgrid=True,
            gridcolor="#e5e7eb",
            tickformat=time_cfg["tickformat"],
            tickangle=time_cfg.get("tickangle", 0),
            tickmode="linear",
            tick0=data["start"].min(),
            dtick=time_cfg["dtick"],
            rangeslider_visible=True,
            range=[data["start"].min() - pd.Timedelta(days=2), data["end"].max() + pd.Timedelta(days=2)],
            linecolor="#adb5bd",
            linewidth=1,
            mirror=True,
            showline=True,
            ticks="outside",
            tickfont=dict(size=12, color="#444"),
        ),
        # yaxis=dict(tickfont=dict(size=10), automargin=True),
        yaxis=dict(
            
            showgrid=False,
            linecolor="#adb5bd",
            linewidth=1,
            mirror=True,
            showline=True,
            ticks="outside",
            tickfont=dict(size=12, color="#444"),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="#dee2e6",
            borderwidth=1,
            font=dict(size=12)
        ),
        title=dict(
            font=dict(size=22, color="#222"),
            x=0.5,
            xanchor="center"
        ),
        hoverlabel=dict(
            bgcolor="#fff",
            font_size=13,
            font_family="Segoe UI, Arial, sans-serif",
            bordercolor="#adb5bd"
        ),
        dragmode=False
    )
    # Ajoute la légende à l'extérieur du graphique via Dash
    legend_html = html.Div([
        html.B("📶 Statut"),
        html.Br(),
        html.Span("  📝 to do"), html.Br(),
        html.Span("  🚦 selected for development"), html.Br(),
        html.Span("  ⏳ in progress"), html.Br(),
        html.Span("  ⏸️ on hold"), html.Br(),
        html.Span("  🔍 review"), html.Br(),
        html.Span("  🆗 done"), html.Br(),
        html.Span("  🎉 complete"), html.Br(),
        html.Br(),
        html.B("🚩 Priorité"),
        html.Br(),
        html.Span("  🔴 urgent"), html.Br(),
        html.Span("  🟠 high"), html.Br(),
        html.Span("  🔵 normal"), html.Br(),
        html.Span("  ⚪ low"),
    ], style={
        "background": "white",
        "border": "1px solid #dee2e6",
        "borderRadius": "8px",
        "padding": "12px 18px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.04)",
        "fontSize": "10px",
        "position": "fixed",
        "bottom": "399px",
        "right": "55px",
        "zIndex": 10,
        "opacity": 0.97,
        "maxWidth": "220px"
    })
    
    # On retourne la figure ET la légende dans le message d'erreur (qui est un composant Dash)
    return fig, legend_html if not error else error

if __name__ == "__main__":
    app.run(debug=True)
