import { CheckCircle2, Clock3, Filter, LogOut, Plus, Search, Shield, Upload } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const demoCredentials = {
  email: "admin@taskflow.dev",
  password: "Admin123!",
};

function request(path, options = {}, token) {
  return fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  }).then(async (response) => {
    const data = await response.json().catch(() => null);
    if (!response.ok) throw new Error(data?.detail || "Request failed");
    return data;
  });
}

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("taskflow_token") || "");
  const [user, setUser] = useState(null);
  const [tasks, setTasks] = useState([]);
  const [summary, setSummary] = useState(null);
  const [users, setUsers] = useState([]);
  const [filters, setFilters] = useState({ search: "", status: "", priority: "" });
  const [form, setForm] = useState({ ...demoCredentials });
  const [taskForm, setTaskForm] = useState({ title: "", priority: "medium", assignee_id: "" });
  const [error, setError] = useState("");

  const authHeaders = useMemo(() => token, [token]);

  useEffect(() => {
    if (!token) return;
    loadData();
  }, [token, filters.status, filters.priority]);

  async function loadData() {
    try {
      const query = new URLSearchParams(
        Object.entries(filters).filter(([, value]) => value),
      ).toString();
      const [profile, taskList, dashboard] = await Promise.all([
        request("/users/me", {}, authHeaders),
        request(`/tasks${query ? `?${query}` : ""}`, {}, authHeaders),
        request("/dashboard/summary", {}, authHeaders),
      ]);
      setUser(profile);
      setTasks(taskList);
      setSummary(dashboard);
      if (profile.role === "admin") {
        setUsers(await request("/admin/users", {}, authHeaders));
      }
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  async function login(event) {
    event.preventDefault();
    try {
      const data = await request("/auth/login", {
        method: "POST",
        body: JSON.stringify(form),
      });
      localStorage.setItem("taskflow_token", data.access_token);
      setToken(data.access_token);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  async function createTask(event) {
    event.preventDefault();
    await request(
      "/tasks",
      {
        method: "POST",
        body: JSON.stringify({
          title: taskForm.title,
          priority: taskForm.priority,
          assignee_id: taskForm.assignee_id ? Number(taskForm.assignee_id) : null,
        }),
      },
      authHeaders,
    );
    setTaskForm({ title: "", priority: "medium", assignee_id: "" });
    loadData();
  }

  async function moveTask(task, status) {
    await request(`/tasks/${task.id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }, authHeaders);
    loadData();
  }

  function logout() {
    localStorage.removeItem("taskflow_token");
    setToken("");
    setUser(null);
    setTasks([]);
  }

  if (!token) {
    return (
      <main className="login-shell">
        <section className="login-panel">
          <div>
            <p className="eyebrow">TaskFlow</p>
            <h1>Task management with real full-stack depth.</h1>
            <p className="muted">JWT auth, RBAC, dashboards, assignments, comments, upload metadata, filters, Docker, and CI.</p>
          </div>
          <form onSubmit={login} className="stack">
            <label>
              Email
              <input value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            </label>
            <label>
              Password
              <input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
            </label>
            {error && <p className="error">{error}</p>}
            <button className="primary">Log in</button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <p className="eyebrow">TaskFlow</p>
          <h2>Workspace</h2>
        </div>
        <div className="identity">
          <Shield size={18} />
          <span>{user?.name}</span>
          <small>{user?.role}</small>
        </div>
        <button className="ghost" onClick={logout}><LogOut size={16} /> Log out</button>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <h1>Dashboard</h1>
            <p className="muted">Track assigned work, priority, due dates, and team load.</p>
          </div>
          <button className="ghost" onClick={loadData}><Clock3 size={16} /> Refresh</button>
        </header>

        {summary && (
          <section className="metrics">
            <article><span>Total</span><strong>{summary.total_tasks}</strong></article>
            <article><span>Overdue</span><strong>{summary.overdue_tasks}</strong></article>
            <article><span>Due this week</span><strong>{summary.due_this_week}</strong></article>
            <article><span>Done</span><strong>{summary.by_status.done}</strong></article>
          </section>
        )}

        <section className="toolbar">
          <label className="search">
            <Search size={16} />
            <input
              placeholder="Search tasks"
              value={filters.search}
              onChange={(event) => setFilters({ ...filters, search: event.target.value })}
              onKeyDown={(event) => event.key === "Enter" && loadData()}
            />
          </label>
          <label>
            <Filter size={16} />
            <select value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value })}>
              <option value="">Any status</option>
              <option value="todo">Todo</option>
              <option value="in_progress">In progress</option>
              <option value="review">Review</option>
              <option value="done">Done</option>
            </select>
          </label>
          <label>
            <Filter size={16} />
            <select value={filters.priority} onChange={(event) => setFilters({ ...filters, priority: event.target.value })}>
              <option value="">Any priority</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
          </label>
        </section>

        {user?.role === "admin" && (
          <form className="new-task" onSubmit={createTask}>
            <input placeholder="New task title" value={taskForm.title} onChange={(event) => setTaskForm({ ...taskForm, title: event.target.value })} required />
            <select value={taskForm.priority} onChange={(event) => setTaskForm({ ...taskForm, priority: event.target.value })}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>
            <select value={taskForm.assignee_id} onChange={(event) => setTaskForm({ ...taskForm, assignee_id: event.target.value })}>
              <option value="">Unassigned</option>
              {users.map((member) => <option value={member.id} key={member.id}>{member.name}</option>)}
            </select>
            <button className="primary"><Plus size={16} /> Add</button>
          </form>
        )}

        {error && <p className="error">{error}</p>}

        <section className="task-grid">
          {tasks.map((task) => (
            <article className="task-card" key={task.id}>
              <div>
                <strong>{task.title}</strong>
                <p>{task.description || "No description yet."}</p>
              </div>
              <div className="meta">
                <span>{task.priority}</span>
                <span>{task.status.replace("_", " ")}</span>
                <span>{task.assignee?.name || "Unassigned"}</span>
              </div>
              <div className="actions">
                <button onClick={() => moveTask(task, "in_progress")}><Clock3 size={15} /> Start</button>
                <button onClick={() => moveTask(task, "done")}><CheckCircle2 size={15} /> Done</button>
                <button title="Upload handled by API endpoint"><Upload size={15} /></button>
              </div>
            </article>
          ))}
        </section>
      </section>
    </main>
  );
}
