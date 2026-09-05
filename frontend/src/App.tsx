import {
  AlertTriangle,
  ArrowRight,
  BarChart3,
  Bell,
  Check,
  ChevronDown,
  CircleDollarSign,
  ClipboardCheck,
  Clock3,
  FileText,
  Flag,
  History,
  LayoutDashboard,
  LockKeyhole,
  LogOut,
  Menu,
  MoreHorizontal,
  Search,
  ShieldCheck,
  ShieldAlert,
  SlidersHorizontal,
  Sparkles,
  Timer,
  UserCog,
  UserRoundCheck,
  Users,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { api } from "./api";
import type {
  FeatureFlag,
  KycCase,
  Permission,
  RefundResponse,
  Role,
  User,
} from "./types";

type ModuleId = "overview" | "kyc" | "flags" | "refunds" | "people";

interface DemoPersona {
  id: string;
  initials: string;
  name: string;
  jobTitle: string;
  department: string;
  access: string;
  color: string;
}

const PERSONAS: DemoPersona[] = [
  {
    id: "morgan",
    initials: "ML",
    name: "Morgan Lee",
    jobTitle: "Platform Operations Director",
    department: "Technology",
    access: "Super admin",
    color: "#3157d5",
  },
  {
    id: "amina",
    initials: "AY",
    name: "Amina Yusuf",
    jobTitle: "Senior Compliance Analyst",
    department: "Compliance",
    access: "KYC reviews",
    color: "#0c7c6d",
  },
  {
    id: "leo",
    initials: "LM",
    name: "Leo Martins",
    jobTitle: "Product Manager",
    department: "Product",
    access: "Feature flags",
    color: "#9a5b13",
  },
  {
    id: "priya",
    initials: "PS",
    name: "Priya Shah",
    jobTitle: "Customer Support Lead",
    department: "Customer Experience",
    access: "Refunds",
    color: "#813aa6",
  },
];

const ROLE_LABELS: Record<Role, string> = {
  super_admin: "Super admin",
  compliance_analyst: "Compliance analyst",
  product_manager: "Product manager",
  support_lead: "Support lead",
};

const ALL_ROLES = Object.keys(ROLE_LABELS) as Role[];

const NAV_ITEMS: {
  id: ModuleId;
  label: string;
  icon: typeof LayoutDashboard;
  permission?: Permission;
  section: "workspace" | "administration";
}[] = [
  {
    id: "overview",
    label: "Overview",
    icon: LayoutDashboard,
    section: "workspace",
  },
  {
    id: "kyc",
    label: "KYC reviews",
    icon: ClipboardCheck,
    permission: "kyc:read",
    section: "workspace",
  },
  {
    id: "flags",
    label: "Feature flags",
    icon: Flag,
    permission: "feature_flags:read",
    section: "workspace",
  },
  {
    id: "refunds",
    label: "Refunds",
    icon: CircleDollarSign,
    permission: "refunds:read",
    section: "workspace",
  },
  {
    id: "people",
    label: "People & access",
    icon: UserCog,
    permission: "users:read",
    section: "administration",
  },
];

function initials(name: string): string {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("");
}

function hasPermission(user: User, permission?: Permission): boolean {
  return permission === undefined || user.permissions.includes(permission);
}

function SignIn({
  onSignIn,
  loading,
  error,
}: {
  onSignIn: (personaId: string) => void;
  loading: boolean;
  error: string;
}) {
  const [selected, setSelected] = useState("morgan");
  const selectedPersona = PERSONAS.find((persona) => persona.id === selected)!;

  return (
    <main className="signin-shell">
      <section className="signin-story">
        <div className="brand brand--light">
          <div className="brand-mark">
            <BarChart3 size={19} strokeWidth={2.4} />
          </div>
          <span>Northstar</span>
          <span className="brand-product">Admin</span>
        </div>
        <div className="signin-copy">
          <span className="eyebrow eyebrow--light">Internal operations</span>
          <h1>One secure workspace for the teams behind every transaction.</h1>
          <p>
            Review risk, control releases, and resolve customer issues without
            exposing the systems underneath.
          </p>
        </div>
        <div className="signin-assurance">
          <ShieldCheck size={22} />
          <div>
            <strong>Built around least privilege</strong>
            <span>Every view and action is governed by role-based access.</span>
          </div>
        </div>
      </section>

      <section className="signin-panel">
        <div className="prototype-pill">
          <Sparkles size={14} />
          Prototype environment · synthetic data
        </div>
        <div className="signin-card">
          <div className="signin-heading">
            <span className="microsoft-mark" aria-hidden="true">
              <i />
              <i />
              <i />
              <i />
            </span>
            <div>
              <h2>Sign in to Northstar</h2>
              <p>Use your company Microsoft account to continue.</p>
            </div>
          </div>

          <div className="demo-callout">
            <LockKeyhole size={17} />
            <p>
              <strong>Demo identity selector</strong>
              Choose a persona to preview their permitted workspace.
            </p>
          </div>

          <div className="persona-list" role="radiogroup" aria-label="Demo identity">
            {PERSONAS.map((persona) => (
              <button
                className={`persona-option ${selected === persona.id ? "is-selected" : ""}`}
                key={persona.id}
                onClick={() => setSelected(persona.id)}
                role="radio"
                aria-checked={selected === persona.id}
              >
                <span
                  className="avatar avatar--small"
                  style={{ backgroundColor: persona.color }}
                >
                  {persona.initials}
                </span>
                <span className="persona-details">
                  <strong>{persona.name}</strong>
                  <span>{persona.department} · {persona.access}</span>
                </span>
                <span className="radio-indicator">
                  {selected === persona.id && <Check size={13} strokeWidth={3} />}
                </span>
              </button>
            ))}
          </div>

          {error && <div className="form-error">{error}</div>}

          <button
            className="microsoft-button"
            onClick={() => onSignIn(selected)}
            disabled={loading}
          >
            <span className="microsoft-mark microsoft-mark--small" aria-hidden="true">
              <i />
              <i />
              <i />
              <i />
            </span>
            {loading ? "Signing in…" : `Continue as ${selectedPersona.name}`}
            {!loading && <ArrowRight size={17} />}
          </button>
          <p className="signin-footnote">
            In production, this redirects to Microsoft Entra ID. No real
            credentials are collected in this prototype.
          </p>
        </div>
        <p className="legal">Authorised internal use only · Access is monitored</p>
      </section>
    </main>
  );
}

function Sidebar({
  user,
  active,
  pendingRefundCount,
  onNavigate,
  onLogout,
  open,
  onClose,
}: {
  user: User;
  active: ModuleId;
  pendingRefundCount: number | null;
  onNavigate: (module: ModuleId) => void;
  onLogout: () => void;
  open: boolean;
  onClose: () => void;
}) {
  const availableItems = NAV_ITEMS.filter((item) =>
    hasPermission(user, item.permission),
  );

  return (
    <>
      {open && <button className="sidebar-scrim" onClick={onClose} aria-label="Close menu" />}
      <aside className={`sidebar ${open ? "is-open" : ""}`}>
        <div className="sidebar-header">
          <div className="brand brand--light">
            <div className="brand-mark">
              <BarChart3 size={18} strokeWidth={2.4} />
            </div>
            <span>Northstar</span>
          </div>
          <button className="icon-button icon-button--dark mobile-only" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <nav className="navigation">
          <span className="nav-label">Workspace</span>
          {availableItems
            .filter((item) => item.section === "workspace")
            .map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  className={`nav-item ${active === item.id ? "is-active" : ""}`}
                  onClick={() => {
                    onNavigate(item.id);
                    onClose();
                  }}
                >
                  <Icon size={18} />
                  <span>{item.label}</span>
                  {item.id === "kyc" && <span className="nav-count">18</span>}
                  {item.id === "refunds" && pendingRefundCount !== null && (
                    <span className="nav-count">{pendingRefundCount}</span>
                  )}
                </button>
              );
            })}

          {availableItems.some((item) => item.section === "administration") && (
            <>
              <span className="nav-label nav-label--spaced">Administration</span>
              {availableItems
                .filter((item) => item.section === "administration")
                .map((item) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={item.id}
                      className={`nav-item ${active === item.id ? "is-active" : ""}`}
                      onClick={() => {
                        onNavigate(item.id);
                        onClose();
                      }}
                    >
                      <Icon size={18} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
            </>
          )}
        </nav>

        <div className="sidebar-security">
          <ShieldCheck size={18} />
          <div>
            <strong>Secure session</strong>
            <span>Role policy applied</span>
          </div>
        </div>

        <div className="sidebar-user">
          <span className="avatar" style={{ backgroundColor: user.avatar_color }}>
            {initials(user.name)}
          </span>
          <div className="sidebar-user-copy">
            <strong>{user.name}</strong>
            <span>{user.job_title}</span>
          </div>
          <button className="icon-button icon-button--dark" onClick={onLogout} title="Sign out">
            <LogOut size={17} />
          </button>
        </div>
      </aside>
    </>
  );
}

function PageHeader({
  title,
  subtitle,
  onOpenMenu,
}: {
  title: string;
  subtitle: string;
  onOpenMenu: () => void;
}) {
  return (
    <header className="topbar">
      <button className="icon-button mobile-only" onClick={onOpenMenu}>
        <Menu size={20} />
      </button>
      <div className="page-title">
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      <div className="topbar-actions">
        <label className="global-search">
          <Search size={16} />
          <input placeholder="Search records…" aria-label="Search records" />
          <kbd>⌘ K</kbd>
        </label>
        <button className="icon-button notification-button" aria-label="Notifications">
          <Bell size={19} />
          <span />
        </button>
      </div>
    </header>
  );
}

function StatCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone: "blue" | "amber" | "green" | "purple";
}) {
  return (
    <article className="stat-card">
      <div className={`stat-icon stat-icon--${tone}`}>
        {tone === "blue" && <ClipboardCheck size={19} />}
        {tone === "amber" && <Clock3 size={19} />}
        {tone === "green" && <CircleDollarSign size={19} />}
        {tone === "purple" && <Flag size={19} />}
      </div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
        <small>{detail}</small>
      </div>
    </article>
  );
}

function Overview({
  user,
  refundSummary,
  activeFlagCount,
  showRefundPriority,
  onNavigate,
}: {
  user: User;
  refundSummary: RefundResponse["summary"] | null;
  activeFlagCount: number | null;
  showRefundPriority: boolean;
  onNavigate: (id: ModuleId) => void;
}) {
  const accessibleModules = NAV_ITEMS.filter(
    (item) => item.id !== "overview" && hasPermission(user, item.permission),
  );

  return (
    <div className="page-content">
      <section className="welcome-banner">
        <div>
          <span className="eyebrow">Saturday, 5 September</span>
          <h2>Good afternoon, {user.name.split(" ")[0]}.</h2>
          <p>Here is what needs attention across your operations workspace.</p>
        </div>
        <div className="access-chip">
          <ShieldCheck size={17} />
          {user.roles.map((role) => ROLE_LABELS[role]).join(", ")}
        </div>
      </section>

      <section className="stat-grid">
        {hasPermission(user, "kyc:read") && (
          <StatCard label="KYC cases" value="18" detail="5 high priority" tone="blue" />
        )}
        {hasPermission(user, "refunds:read") && (
          <StatCard
            label="Pending refunds"
            value={refundSummary ? String(refundSummary.pending_count) : "—"}
            detail={refundSummary ? `${refundSummary.pending_value} total` : "Loading queue"}
            tone="amber"
          />
        )}
        {hasPermission(user, "refunds:read") && (
          <StatCard
            label="Processed today"
            value={refundSummary ? String(refundSummary.processed_today) : "—"}
            detail={refundSummary?.approval_rate ?? "Loading performance"}
            tone="green"
          />
        )}
        {hasPermission(user, "feature_flags:read") && (
          <StatCard
            label="Active flags"
            value={activeFlagCount === null ? "—" : String(activeFlagCount)}
            detail="1 staged rollout"
            tone="purple"
          />
        )}
      </section>

      <section className="content-grid">
        <article className="panel activity-panel">
          <div className="panel-header">
            <div>
              <h3>Priority queue</h3>
              <p>Items requiring action from your teams</p>
            </div>
            <button className="text-button">View all <ArrowRight size={15} /></button>
          </div>
          <div className="activity-list">
            {hasPermission(user, "kyc:read") && (
              <button className="activity-row" onClick={() => onNavigate("kyc")}>
                <span className="activity-icon activity-icon--danger">
                  <AlertTriangle size={17} />
                </span>
                <span className="activity-copy">
                  <strong>High-risk KYC case needs review</strong>
                  <span>KYC-1048 · Document mismatch · 12 min ago</span>
                </span>
                <span className="status status--danger">High risk</span>
                <ArrowRight size={16} className="row-arrow" />
              </button>
            )}
            {hasPermission(user, "refunds:read") && showRefundPriority && (
              <button className="activity-row" onClick={() => onNavigate("refunds")}>
                <span className="activity-icon activity-icon--warning">
                  <CircleDollarSign size={17} />
                </span>
                <span className="activity-copy">
                  <strong>Refund above standard approval limit</strong>
                  <span>RF-8291 · £1,249.00 · 18 min ago</span>
                </span>
                <span className="status status--warning">Approval</span>
                <ArrowRight size={16} className="row-arrow" />
              </button>
            )}
            {hasPermission(user, "feature_flags:read") && (
              <button className="activity-row" onClick={() => onNavigate("flags")}>
                <span className="activity-icon activity-icon--info">
                  <Flag size={17} />
                </span>
                <span className="activity-copy">
                  <strong>Staged rollout ready for evaluation</strong>
                  <span>KYC risk signals v2 · 25% rollout</span>
                </span>
                <span className="status status--info">Staging</span>
                <ArrowRight size={16} className="row-arrow" />
              </button>
            )}
          </div>
        </article>

        <article className="panel workspace-panel">
          <div className="panel-header">
            <div>
              <h3>Your workspace</h3>
              <p>Access based on your assigned roles</p>
            </div>
          </div>
          <div className="workspace-list">
            {accessibleModules.map((item) => {
              const Icon = item.icon;
              return (
                <button key={item.id} onClick={() => onNavigate(item.id)}>
                  <span className="workspace-icon"><Icon size={18} /></span>
                  <span>
                    <strong>{item.label}</strong>
                    <small>Open module</small>
                  </span>
                  <ArrowRight size={15} />
                </button>
              );
            })}
          </div>
        </article>
      </section>
    </div>
  );
}

function LoadingPanel() {
  return (
    <div className="loading-panel">
      <span className="spinner" />
      Loading secure workspace…
    </div>
  );
}

function KycPanel({ userId }: { userId: string }) {
  const [cases, setCases] = useState<KycCase[]>([]);
  const [loading, setLoading] = useState(true);
  const [queue, setQueue] = useState<"all" | "mine" | "unassigned" | "escalated">("all");
  const [search, setSearch] = useState("");
  const [selectedCase, setSelectedCase] = useState<KycCase | null>(null);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    api.kycCases(userId).then(setCases).finally(() => setLoading(false));
  }, [userId]);

  const filteredCases = cases.filter((item) => {
    const matchesQueue =
      queue === "all"
      || (queue === "mine" && item.assignee_id === userId)
      || (queue === "unassigned" && item.assignee_id === null)
      || (queue === "escalated" && item.status === "Escalated");
    const query = search.trim().toLowerCase();
    const matchesSearch =
      query.length === 0
      || `${item.id} ${item.customer} ${item.customer_id} ${item.reason}`
        .toLowerCase()
        .includes(query);
    return matchesQueue && matchesSearch;
  });
  const highRiskCount = cases.filter((item) => item.risk === "High").length;
  const breachedCount = cases.filter((item) => item.sla_state === "Breached").length;
  const assignedToMe = cases.filter((item) => item.assignee_id === userId).length;
  const unassignedCount = cases.filter((item) => item.assignee_id === null).length;

  async function assignToMe(item: KycCase) {
    const updated = await api.assignKycCase(userId, item.id);
    setCases((current) =>
      current.map((currentCase) => currentCase.id === updated.id ? updated : currentCase),
    );
    setSelectedCase(updated);
    setNotice(`${updated.id} assigned to you. Audit event recorded.`);
    window.setTimeout(() => setNotice(""), 3200);
  }

  if (loading) return <LoadingPanel />;

  return (
    <div className="page-content">
      {notice && <div className="toast"><Check size={16} /> {notice}</div>}
      <section className="module-toolbar">
        <div className="segmented-control">
          <button
            className={queue === "all" ? "is-active" : ""}
            onClick={() => setQueue("all")}
          >
            All open <span>{cases.length}</span>
          </button>
          <button
            className={queue === "mine" ? "is-active" : ""}
            onClick={() => setQueue("mine")}
          >
            My queue <span>{assignedToMe}</span>
          </button>
          <button
            className={queue === "unassigned" ? "is-active" : ""}
            onClick={() => setQueue("unassigned")}
          >
            Unassigned <span>{unassignedCount}</span>
          </button>
          <button
            className={queue === "escalated" ? "is-active" : ""}
            onClick={() => setQueue("escalated")}
          >
            Escalated <span>{cases.filter((item) => item.status === "Escalated").length}</span>
          </button>
        </div>
        <div className="toolbar-actions">
          <label className="inline-search queue-search">
            <Search size={15} />
            <input
              placeholder="Search case or customer"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
          <button
            className="primary-button"
            onClick={() => setSelectedCase(
              cases.find((item) => item.assignee_id === null && item.risk === "High")
              ?? cases[0],
            )}
          >
            Review next case <ArrowRight size={16} />
          </button>
        </div>
      </section>

      <section className="stat-grid">
        <StatCard label="Open cases" value={String(cases.length)} detail="Across all queues" tone="blue" />
        <StatCard label="High risk" value={String(highRiskCount)} detail="1 unassigned" tone="amber" />
        <StatCard label="SLA breached" value={String(breachedCount)} detail="Manager visibility" tone="purple" />
        <StatCard label="Reviewed today" value="47" detail="Median: 11 minutes" tone="green" />
      </section>

      <section className="panel table-panel">
        <div className="panel-header panel-header--table">
          <div>
            <h3>Verification queue</h3>
            <p>{filteredCases.length} customer and business checks requiring manual review</p>
          </div>
          <div className="control-labels">
            <span className="data-label"><LockKeyhole size={13} /> Sensitive fields masked</span>
            <span className="data-label"><History size={13} /> Actions audited</span>
          </div>
        </div>
        <div className="table-scroll">
          <table className="operations-table">
            <thead>
              <tr>
                <th>Customer / case</th>
                <th>Risk signals</th>
                <th>Submitted / SLA</th>
                <th>Owner</th>
                <th>Status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {filteredCases.map((item) => (
                <tr key={item.id}>
                  <td>
                    <div className="customer-cell">
                      <span className="avatar avatar--table">{initials(item.customer)}</span>
                      <span>
                        <button className="record-link" onClick={() => setSelectedCase(item)}>
                          {item.customer}
                        </button>
                        <small>{item.id} · {item.customer_id} · {item.entity_type} · {item.country}</small>
                      </span>
                    </div>
                  </td>
                  <td>
                    <div className="signal-cell">
                      <span className={`risk risk--${item.risk.toLowerCase()}`}>{item.risk}</span>
                      <strong>{item.reason}</strong>
                      <small>{item.signals.join(" · ")}</small>
                    </div>
                  </td>
                  <td>
                    <div className="sla-cell">
                      <span>{item.submitted}</span>
                      <small className={`sla-state sla-state--${item.sla_state.toLowerCase().replace(" ", "-")}`}>
                        <Timer size={12} /> {item.sla}
                      </small>
                    </div>
                  </td>
                  <td>
                    <span className={`assignee ${item.assignee_id === null ? "is-unassigned" : ""}`}>
                      <UserRoundCheck size={14} /> {item.assignee}
                    </span>
                  </td>
                  <td><span className={`status ${item.status === "Escalated" ? "status--danger" : "status--neutral"}`}>{item.status}</span></td>
                  <td>
                    <button
                      className="icon-button"
                      onClick={() => setSelectedCase(item)}
                      aria-label={`Open ${item.id}`}
                    >
                      <MoreHorizontal size={18} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="table-footer">
          <span>Showing {filteredCases.length} of {cases.length} open cases</span>
          <span>Queue refreshed just now</span>
        </div>
      </section>

      {selectedCase && (
        <div className="drawer-backdrop" role="presentation" onMouseDown={() => setSelectedCase(null)}>
          <aside
            className="detail-drawer"
            role="dialog"
            aria-modal="true"
            aria-label={`KYC case ${selectedCase.id}`}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="drawer-header">
              <div>
                <span className="eyebrow">Manual review · {selectedCase.id}</span>
                <h2>{selectedCase.customer}</h2>
                <p>{selectedCase.customer_id} · {selectedCase.entity_type} · {selectedCase.country}</p>
              </div>
              <button className="icon-button" onClick={() => setSelectedCase(null)}><X size={19} /></button>
            </div>

            <div className="control-banner">
              <ShieldAlert size={18} />
              <div>
                <strong>Controlled review</strong>
                <span>Customer data is masked; every view and decision is recorded.</span>
              </div>
            </div>

            <div className="detail-section">
              <h3>Review context</h3>
              <dl className="detail-grid">
                <div><dt>Risk level</dt><dd><span className={`risk risk--${selectedCase.risk.toLowerCase()}`}>{selectedCase.risk}</span></dd></div>
                <div><dt>Queue status</dt><dd>{selectedCase.status}</dd></div>
                <div><dt>Primary reason</dt><dd>{selectedCase.reason}</dd></div>
                <div><dt>SLA</dt><dd>{selectedCase.sla}</dd></div>
                <div><dt>Owner</dt><dd>{selectedCase.assignee}</dd></div>
                <div><dt>Submitted</dt><dd>{selectedCase.submitted}</dd></div>
              </dl>
            </div>

            <div className="detail-section">
              <h3>Risk signals</h3>
              <div className="signal-list">
                {selectedCase.signals.map((signal) => (
                  <span key={signal}><AlertTriangle size={14} /> {signal}</span>
                ))}
              </div>
            </div>

            <div className="detail-section">
              <div className="section-heading">
                <h3>Audit history</h3>
                <span>Append-only</span>
              </div>
              <div className="audit-timeline">
                {selectedCase.audit.map((event, index) => (
                  <div key={`${event.action}-${index}`}>
                    <span className="audit-dot" />
                    <p><strong>{event.action}</strong><small>{event.actor} · {event.at}</small></p>
                  </div>
                ))}
              </div>
            </div>

            <div className="drawer-actions">
              <button className="secondary-button"><FileText size={16} /> View evidence</button>
              <button
                className="primary-button"
                disabled={selectedCase.assignee_id === userId}
                onClick={() => void assignToMe(selectedCase)}
              >
                <UserRoundCheck size={16} />
                {selectedCase.assignee_id === userId ? "Assigned to you" : "Assign to me"}
              </button>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

function FeatureFlagsPanel({
  user,
  onActiveCountChange,
}: {
  user: User;
  onActiveCountChange: (count: number) => void;
}) {
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");
  const [search, setSearch] = useState("");
  const [selectedFlag, setSelectedFlag] = useState<FeatureFlag | null>(null);
  const canWrite = user.permissions.includes("feature_flags:write");

  useEffect(() => {
    api.featureFlags(user.id)
      .then((items) => {
        setFlags(items);
        onActiveCountChange(items.filter((item) => item.enabled).length);
      })
      .finally(() => setLoading(false));
  }, [onActiveCountChange, user.id]);

  async function toggleFlag(flag: FeatureFlag) {
    if (!canWrite) return;
    const updated = await api.updateFeatureFlag(user.id, flag.id, !flag.enabled);
    const nextFlags = flags.map((item) => (item.id === flag.id ? updated : item));
    setFlags(nextFlags);
    setSelectedFlag((current) => current?.id === updated.id ? updated : current);
    onActiveCountChange(nextFlags.filter((item) => item.enabled).length);
    setNotice(`${flag.name} ${updated.enabled ? "enabled" : "disabled"}. Audit event recorded.`);
    window.setTimeout(() => setNotice(""), 3200);
  }

  if (loading) return <LoadingPanel />;

  const filteredFlags = flags.filter((flag) => {
    const query = search.trim().toLowerCase();
    return query.length === 0
      || `${flag.name} ${flag.id} ${flag.owner} ${flag.owner_contact}`
        .toLowerCase()
        .includes(query);
  });

  return (
    <div className="page-content">
      {notice && <div className="toast"><Check size={16} /> {notice}</div>}
      <section className="module-toolbar">
        <div className="environment-picker">
          <span>Environment</span>
          <button><span className="live-dot" /> Production <ChevronDown size={15} /></button>
        </div>
        <button className="primary-button"><Flag size={16} /> Create flag</button>
      </section>

      <section className="flag-summary">
        <div><strong>{flags.length}</strong><span>Total flags</span></div>
        <div><strong>{flags.filter((flag) => flag.enabled).length}</strong><span>Enabled</span></div>
        <div><strong>{flags.filter((flag) => flag.risk !== "Standard").length}</strong><span>Elevated controls</span></div>
        <div className="flag-summary-note"><ShieldCheck size={18} /><span>All changes require a reason and create an audit event.</span></div>
      </section>

      <section className="panel flags-panel">
        <div className="panel-header">
          <div>
            <h3>Feature flags</h3>
            <p>Control the release of customer-facing capabilities</p>
          </div>
          <label className="inline-search">
            <Search size={15} />
            <input
              placeholder="Search flags"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
        </div>
        <div className="flags-list">
          {filteredFlags.map((flag) => (
            <article className="flag-row" key={flag.id}>
              <div className={`flag-icon ${flag.enabled ? "is-enabled" : ""}`}><Flag size={19} /></div>
              <div className="flag-copy">
                <div className="flag-name">
                  <strong>{flag.name}</strong>
                  <span className={`environment-tag ${flag.environment === "Staging" ? "is-staging" : ""}`}>{flag.environment}</span>
                </div>
                <p>{flag.description}</p>
                <div className="flag-meta">
                  <span>{flag.flag_type}</span>
                  <span>Owner: {flag.owner} · {flag.owner_contact}</span>
                  <span>Rollout: {flag.rollout}</span>
                  <span>Changed: {flag.last_changed}</span>
                  <span className="code-label">{flag.id}</span>
                </div>
              </div>
              <div className="flag-governance">
                <span className={`risk-tag risk-tag--${flag.risk.toLowerCase()}`}>{flag.risk}</span>
                <small>{flag.change_ticket}</small>
                <small>Expires {flag.expires}</small>
              </div>
              <div className="flag-state">
                <span>{flag.enabled ? "Enabled" : "Disabled"}</span>
                <button
                  className={`toggle ${flag.enabled ? "is-on" : ""}`}
                  onClick={() => void toggleFlag(flag)}
                  disabled={!canWrite}
                  aria-label={`${flag.enabled ? "Disable" : "Enable"} ${flag.name}`}
                >
                  <i />
                </button>
              </div>
              <button className="icon-button" onClick={() => setSelectedFlag(flag)}><MoreHorizontal size={18} /></button>
            </article>
          ))}
        </div>
        <div className="table-footer">
          <span>Showing {filteredFlags.length} of {flags.length} flags</span>
          <span>Production changes are audit logged</span>
        </div>
      </section>

      {selectedFlag && (
        <div className="drawer-backdrop" role="presentation" onMouseDown={() => setSelectedFlag(null)}>
          <aside
            className="detail-drawer"
            role="dialog"
            aria-modal="true"
            aria-label={`Feature flag ${selectedFlag.name}`}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="drawer-header">
              <div>
                <span className="eyebrow">{selectedFlag.flag_type} · {selectedFlag.environment}</span>
                <h2>{selectedFlag.name}</h2>
                <p>{selectedFlag.id}</p>
              </div>
              <button className="icon-button" onClick={() => setSelectedFlag(null)}><X size={19} /></button>
            </div>
            <div className="control-banner">
              <ShieldCheck size={18} />
              <div>
                <strong>{selectedFlag.risk} change control</strong>
                <span>Changes require a reason and are attributed to the acting administrator.</span>
              </div>
            </div>
            <div className="detail-section">
              <h3>Configuration</h3>
              <dl className="detail-grid">
                <div><dt>Status</dt><dd>{selectedFlag.enabled ? "Enabled" : "Disabled"}</dd></div>
                <div><dt>Rollout</dt><dd>{selectedFlag.rollout}</dd></div>
                <div><dt>Owning team</dt><dd>{selectedFlag.owner}</dd></div>
                <div><dt>Technical owner</dt><dd>{selectedFlag.owner_contact}</dd></div>
                <div><dt>Expiry</dt><dd>{selectedFlag.expires}</dd></div>
                <div><dt>Change ticket</dt><dd>{selectedFlag.change_ticket}</dd></div>
              </dl>
            </div>
            <div className="detail-section">
              <div className="section-heading"><h3>Audit history</h3><span>Append-only</span></div>
              <div className="audit-timeline">
                {selectedFlag.audit.map((event, index) => (
                  <div key={`${event.action}-${index}`}>
                    <span className="audit-dot" />
                    <p><strong>{event.action}</strong><small>{event.actor} · {event.at}</small></p>
                  </div>
                ))}
              </div>
            </div>
            <div className="drawer-actions">
              <button className="secondary-button"><FileText size={16} /> Open {selectedFlag.change_ticket}</button>
              <button
                className="primary-button"
                disabled={!canWrite}
                onClick={() => void toggleFlag(selectedFlag)}
              >
                <Flag size={16} /> {selectedFlag.enabled ? "Disable flag" : "Enable flag"}
              </button>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

function RefundsPanel({
  user,
  onDataChange,
}: {
  user: User;
  onDataChange: (data: RefundResponse) => void;
}) {
  const [data, setData] = useState<RefundResponse | null>(null);
  const [notice, setNotice] = useState("");
  const [queue, setQueue] = useState<"all" | "mine" | "high-value" | "completed">("all");
  const [search, setSearch] = useState("");
  const [selectedRefund, setSelectedRefund] = useState<RefundResponse["items"][number] | null>(null);

  useEffect(() => {
    api.refunds(user.id).then((response) => {
      setData(response);
      onDataChange(response);
    });
  }, [onDataChange, user.id]);

  async function refreshData(selectedId?: string) {
    const nextData = await api.refunds(user.id);
    setData(nextData);
    onDataChange(nextData);
    if (selectedId) {
      setSelectedRefund(nextData.items.find((item) => item.id === selectedId) ?? null);
    }
  }

  async function approve(refundId: string) {
    const updated = await api.approveRefund(user.id, refundId);
    await refreshData(refundId);
    setNotice(
      updated.status === "Approved"
        ? `${updated.id} approved. Audit event recorded.`
        : `${updated.id} recorded. A distinct second approver is required.`,
    );
    window.setTimeout(() => setNotice(""), 3200);
  }

  async function assignToMe(refundId: string) {
    const updated = await api.assignRefund(user.id, refundId);
    await refreshData(refundId);
    setNotice(`${updated.id} assigned to you. Audit event recorded.`);
    window.setTimeout(() => setNotice(""), 3200);
  }

  if (!data) return <LoadingPanel />;

  const filteredRefunds = data.items.filter((refund) => {
    const isApproved = refund.status === "Approved";
    const matchesQueue =
      queue === "all"
      || (queue === "mine" && refund.assignee_id === user.id && !isApproved)
      || (queue === "high-value" && refund.required_approvals === 2 && !isApproved)
      || (queue === "completed" && isApproved);
    const query = search.trim().toLowerCase();
    const matchesSearch =
      query.length === 0
      || `${refund.id} ${refund.customer} ${refund.customer_id} ${refund.reason}`
        .toLowerCase()
        .includes(query);
    return matchesQueue && matchesSearch;
  });
  const highValueCount = data.items.filter(
    (refund) => refund.required_approvals === 2 && refund.status !== "Approved",
  ).length;
  const breachedCount = data.items.filter(
    (refund) => refund.sla_state === "Breached" && refund.status !== "Approved",
  ).length;

  return (
    <div className="page-content">
      {notice && <div className="toast"><Check size={16} /> {notice}</div>}
      <section className="stat-grid stat-grid--refunds">
        <StatCard label="Pending refunds" value={String(data.summary.pending_count)} detail="Needs review" tone="amber" />
        <StatCard label="Pending value" value={data.summary.pending_value} detail="Across all queues" tone="blue" />
        <StatCard label="Processed today" value={String(data.summary.processed_today)} detail="On track for target" tone="green" />
        <StatCard label="Approval rate" value={data.summary.approval_rate} detail="Last 30 days" tone="purple" />
      </section>

      <section className="module-toolbar">
        <div className="segmented-control">
          <button className={queue === "all" ? "is-active" : ""} onClick={() => setQueue("all")}>
            Open <span>{data.summary.pending_count}</span>
          </button>
          <button className={queue === "mine" ? "is-active" : ""} onClick={() => setQueue("mine")}>
            My queue <span>{data.items.filter((item) => item.assignee_id === user.id && item.status !== "Approved").length}</span>
          </button>
          <button className={queue === "high-value" ? "is-active" : ""} onClick={() => setQueue("high-value")}>
            Dual approval <span>{highValueCount}</span>
          </button>
          <button className={queue === "completed" ? "is-active" : ""} onClick={() => setQueue("completed")}>
            Completed
          </button>
        </div>
        <div className="toolbar-actions">
          <label className="inline-search queue-search">
            <Search size={15} />
            <input
              placeholder="Search refund or customer"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>
          <button className="secondary-button"><SlidersHorizontal size={16} /> Filters</button>
        </div>
      </section>

      <section className="panel table-panel">
        <div className="panel-header panel-header--table">
          <div>
            <h3>Refund operations queue</h3>
            <p>{filteredRefunds.length} requests across card, transfer, and cash-withdrawal journeys</p>
          </div>
          <div className="control-labels">
            <span className="data-label"><ShieldCheck size={13} /> {highValueCount} dual-control</span>
            <span className="data-label"><Timer size={13} /> {breachedCount} SLA breached</span>
          </div>
        </div>
        <div className="table-scroll">
          <table className="operations-table refund-operations-table">
            <thead>
              <tr>
                <th>Customer / request</th>
                <th>Reason / channel</th>
                <th>Value</th>
                <th>Owner / SLA</th>
                <th>Control status</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
            {filteredRefunds.map((refund) => {
              const isApproved = refund.status === "Approved";
              const alreadyApproved = refund.approved_by.includes(user.id);
              const buttonLabel = isApproved
                ? "View"
                : alreadyApproved
                  ? "Awaiting peer"
                  : refund.approval_count > 0
                    ? "Second approval"
                    : "Review";
              return (
                <tr key={refund.id}>
                  <td>
                    <div className="customer-cell">
                      <span className="refund-brand"><CircleDollarSign size={18} /></span>
                      <span>
                        <button className="record-link" onClick={() => setSelectedRefund(refund)}>
                          {refund.customer}
                        </button>
                        <small>{refund.id} · {refund.customer_id} · {refund.age} ago</small>
                      </span>
                    </div>
                  </td>
                  <td>
                    <div className="signal-cell">
                      <strong>{refund.reason}</strong>
                      <small>{refund.channel} · {refund.payment_method}</small>
                    </div>
                  </td>
                  <td>
                    <div className="refund-amount">
                      <strong>{refund.amount}</strong>
                      <span>{refund.required_approvals === 2 ? "Dual approval" : "Standard policy"}</span>
                    </div>
                  </td>
                  <td>
                    <div className="owner-sla-cell">
                      <span className={`assignee ${refund.assignee_id === null ? "is-unassigned" : ""}`}>
                        <UserRoundCheck size={14} /> {refund.assignee}
                      </span>
                      <small className={`sla-state sla-state--${refund.sla_state.toLowerCase().replace(" ", "-")}`}>
                        <Timer size={12} /> {refund.sla}
                      </small>
                    </div>
                  </td>
                  <td>
                    <div className="control-status">
                      <span className={`status ${isApproved ? "status--success" : "status--warning"}`}>
                        {refund.status}
                      </span>
                      <small>{refund.approval_count}/{refund.required_approvals} approvals</small>
                    </div>
                  </td>
                  <td>
                    <button className="small-button" onClick={() => setSelectedRefund(refund)}>
                      {buttonLabel}
                    </button>
                  </td>
                </tr>
              );
            })}
            </tbody>
          </table>
        </div>
        <div className="table-footer">
          <span>Showing {filteredRefunds.length} of {data.items.length} requests</span>
          <span>Payment details are partially masked</span>
        </div>
      </section>

      <section className="governance-grid">
        <aside className="panel policy-card">
          <div className="policy-icon"><ShieldCheck size={22} /></div>
          <h3>Approval policy</h3>
          <p>Refunds above £1,000 require approval from two distinct people before processing.</p>
          <div className="policy-rule">
            <span>Standard limit</span>
            <strong>£1,000</strong>
          </div>
          <div className="policy-rule">
            <span>Daily user limit</span>
            <strong>£10,000</strong>
          </div>
          <button className="text-button">View policy <ArrowRight size={14} /></button>
        </aside>
        <aside className="panel policy-card">
          <div className="policy-icon policy-icon--amber"><History size={22} /></div>
          <h3>Operational controls</h3>
          <p>Assignments, evidence views, approvals, and policy overrides are retained for review.</p>
          <div className="policy-rule"><span>Evidence retention</span><strong>7 years</strong></div>
          <div className="policy-rule"><span>Override access</span><strong>Restricted</strong></div>
          <button className="text-button">Open audit log <ArrowRight size={14} /></button>
        </aside>
      </section>

      {selectedRefund && (
        <div className="drawer-backdrop" role="presentation" onMouseDown={() => setSelectedRefund(null)}>
          <aside
            className="detail-drawer"
            role="dialog"
            aria-modal="true"
            aria-label={`Refund ${selectedRefund.id}`}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="drawer-header">
              <div>
                <span className="eyebrow">Refund review · {selectedRefund.id}</span>
                <h2>{selectedRefund.customer}</h2>
                <p>{selectedRefund.customer_id} · {selectedRefund.channel}</p>
              </div>
              <button className="icon-button" onClick={() => setSelectedRefund(null)}><X size={19} /></button>
            </div>

            <div className="control-banner">
              <ShieldCheck size={18} />
              <div>
                <strong>{selectedRefund.required_approvals === 2 ? "Dual approval required" : "Standard approval policy"}</strong>
                <span>{selectedRefund.approval_count} of {selectedRefund.required_approvals} approvals recorded. The requester cannot approve their own override.</span>
              </div>
            </div>

            <div className="detail-section">
              <h3>Request context</h3>
              <dl className="detail-grid">
                <div><dt>Amount</dt><dd>{selectedRefund.amount}</dd></div>
                <div><dt>Status</dt><dd>{selectedRefund.status}</dd></div>
                <div><dt>Reason</dt><dd>{selectedRefund.reason}</dd></div>
                <div><dt>Payment method</dt><dd>{selectedRefund.payment_method}</dd></div>
                <div><dt>Owner</dt><dd>{selectedRefund.assignee}</dd></div>
                <div><dt>SLA</dt><dd>{selectedRefund.sla}</dd></div>
              </dl>
            </div>

            <div className="detail-section">
              <h3>Risk and control signals</h3>
              <div className="signal-list">
                {selectedRefund.risk_flags.length === 0 ? (
                  <span className="signal-clear"><ShieldCheck size={14} /> No elevated signals</span>
                ) : selectedRefund.risk_flags.map((signal) => (
                  <span key={signal}><AlertTriangle size={14} /> {signal}</span>
                ))}
              </div>
            </div>

            <div className="detail-section">
              <div className="section-heading"><h3>Audit history</h3><span>Append-only</span></div>
              <div className="audit-timeline">
                {selectedRefund.audit.map((event, index) => (
                  <div key={`${event.action}-${index}`}>
                    <span className="audit-dot" />
                    <p><strong>{event.action}</strong><small>{event.actor} · {event.at}</small></p>
                  </div>
                ))}
              </div>
            </div>

            <div className="drawer-actions">
              <button
                className="secondary-button"
                disabled={selectedRefund.assignee_id === user.id || selectedRefund.status === "Approved"}
                onClick={() => void assignToMe(selectedRefund.id)}
              >
                <UserRoundCheck size={16} />
                {selectedRefund.assignee_id === user.id ? "Assigned to you" : "Assign to me"}
              </button>
              <button
                className="primary-button"
                disabled={selectedRefund.status === "Approved" || selectedRefund.approved_by.includes(user.id)}
                onClick={() => void approve(selectedRefund.id)}
              >
                <ShieldCheck size={16} />
                {selectedRefund.status === "Approved"
                  ? "Approved"
                  : selectedRefund.approved_by.includes(user.id)
                    ? "Peer approval required"
                    : selectedRefund.approval_count > 0
                      ? "Give second approval"
                      : "Approve refund"}
              </button>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}

function PeoplePanel({ user }: { user: User }) {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [draftRoles, setDraftRoles] = useState<Role[]>([]);
  const [saving, setSaving] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.users(user.id).then(setUsers);
  }, [user.id]);

  function openUser(target: User) {
    setSelectedUser(target);
    setDraftRoles(target.roles);
  }

  function toggleRole(role: Role) {
    setDraftRoles((current) =>
      current.includes(role)
        ? current.filter((item) => item !== role)
        : [...current, role],
    );
  }

  async function saveRoles() {
    if (!selectedUser || draftRoles.length === 0) return;
    setSaving(true);
    const updated = await api.updateRoles(user.id, selectedUser.id, draftRoles);
    setUsers((current) =>
      current.map((item) => (item.id === updated.id ? updated : item)),
    );
    setSelectedUser(null);
    setSaving(false);
  }

  const filteredUsers = users.filter((person) => {
    const query = search.trim().toLowerCase();
    return query.length === 0
      || `${person.name} ${person.email} ${person.department} ${person.job_title}`
        .toLowerCase()
        .includes(query);
  });
  const privilegedUsers = users.filter((person) => person.roles.includes("super_admin")).length;

  return (
    <div className="page-content">
      <section className="admin-intro">
        <div className="admin-intro-icon"><Users size={22} /></div>
        <div>
          <h2>People and access</h2>
          <p>Manage role assignments for internal team members. Changes are recorded in the audit log.</p>
        </div>
        <button className="primary-button"><Users size={16} /> Invite user</button>
      </section>

      <section className="stat-grid access-stat-grid">
        <StatCard label="Active employees" value="287" detail="Across 9 departments" tone="blue" />
        <StatCard label="Privileged access" value={`${privilegedUsers}`} detail="Super-admin users" tone="purple" />
        <StatCard label="Reviews due" value="12" detail="Within 30 days" tone="amber" />
        <StatCard label="MFA coverage" value="100%" detail="4 security-key users" tone="green" />
      </section>

      <section className="panel table-panel">
        <div className="panel-header panel-header--table">
          <div>
            <h3>Users with operational access</h3>
            <p>Showing {filteredUsers.length} of {users.length} elevated-access users in a 287-person tenant</p>
          </div>
          <div className="toolbar-actions">
            <label className="inline-search">
              <Search size={15} />
              <input
                placeholder="Search people"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </label>
            <button className="secondary-button"><SlidersHorizontal size={16} /> Filters</button>
          </div>
        </div>
        <div className="people-columns">
          <span>User</span><span>Department</span><span>Access</span><span>Last active</span><span>Status</span><span />
        </div>
        <div className="people-list">
          {filteredUsers.map((person) => (
            <button className="person-row" key={person.id} onClick={() => openUser(person)}>
              <span className="avatar" style={{ backgroundColor: person.avatar_color }}>{initials(person.name)}</span>
              <span className="person-main">
                <strong>{person.name}</strong>
                <span>{person.job_title} · {person.location}</span>
              </span>
              <span className="person-department">{person.department}</span>
              <span className="role-tags">
                {person.roles.map((role) => <i key={role}>{ROLE_LABELS[role]}</i>)}
              </span>
              <span className="person-activity">{person.last_active}</span>
              <span className="status status--success">Active</span>
              <ArrowRight size={16} />
            </button>
          ))}
        </div>
      </section>

      {selectedUser && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setSelectedUser(null)}>
          <section className="modal" role="dialog" aria-modal="true" onMouseDown={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <span className="eyebrow">Edit access</span>
                <h2>{selectedUser.name}</h2>
                <p>{selectedUser.job_title} · {selectedUser.department}</p>
              </div>
              <button className="icon-button" onClick={() => setSelectedUser(null)}><X size={19} /></button>
            </div>
            <div className="access-context">
              <div><span>Work email</span><strong>{selectedUser.email}</strong></div>
              <div><span>Last active</span><strong>{selectedUser.last_active}</strong></div>
              <div><span>MFA method</span><strong>{selectedUser.mfa_status}</strong></div>
              <div><span>Access review</span><strong>{selectedUser.access_review}</strong></div>
            </div>
            <div className="section-heading role-heading">
              <h3>Role assignments</h3>
              <span>{selectedUser.permissions.length} effective permissions</span>
            </div>
            <div className="role-options">
              {ALL_ROLES.map((role) => (
                <button
                  className={`role-option ${draftRoles.includes(role) ? "is-selected" : ""}`}
                  key={role}
                  onClick={() => toggleRole(role)}
                >
                  <span className="role-check">{draftRoles.includes(role) && <Check size={14} strokeWidth={3} />}</span>
                  <span>
                    <strong>{ROLE_LABELS[role]}</strong>
                    <small>
                      {role === "super_admin" && "Full access to all modules and administration"}
                      {role === "compliance_analyst" && "Review KYC cases and risk information"}
                      {role === "product_manager" && "View and manage feature flags"}
                      {role === "support_lead" && "Review and approve customer refunds"}
                    </small>
                  </span>
                </button>
              ))}
            </div>
            <div className="modal-warning">
              <AlertTriangle size={17} />
              Role changes take effect immediately, require re-authentication, and are written to the audit log.
            </div>
            <div className="modal-actions">
              <button className="secondary-button" onClick={() => setSelectedUser(null)}>Cancel</button>
              <button className="primary-button" disabled={saving || draftRoles.length === 0} onClick={() => void saveRoles()}>
                {saving ? "Saving…" : "Save access"}
              </button>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

const PAGE_META: Record<ModuleId, { title: string; subtitle: string }> = {
  overview: {
    title: "Operations overview",
    subtitle: "Your role-aware view of today's work",
  },
  kyc: {
    title: "KYC reviews",
    subtitle: "Review identity verification and risk signals",
  },
  flags: {
    title: "Feature flags",
    subtitle: "Safely control capabilities across environments",
  },
  refunds: {
    title: "Refunds",
    subtitle: "Investigate and approve customer refund requests",
  },
  people: {
    title: "People & access",
    subtitle: "Manage internal roles and permissions",
  },
};

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [active, setActive] = useState<ModuleId>("overview");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [refundData, setRefundData] = useState<RefundResponse | null>(null);
  const [activeFlagCount, setActiveFlagCount] = useState<number | null>(null);

  const currentMeta = useMemo(() => PAGE_META[active], [active]);
  const refundSummary = refundData?.summary ?? null;
  const showRefundPriority =
    refundData?.items.some((refund) => refund.id === "RF-8291" && refund.status !== "Approved")
    ?? false;

  useEffect(() => {
    if (!user) return;
    if (hasPermission(user, "refunds:read")) {
      api.refunds(user.id).then(setRefundData);
    } else {
      setRefundData(null);
    }
    if (hasPermission(user, "feature_flags:read")) {
      api.featureFlags(user.id).then((flags) => {
        setActiveFlagCount(flags.filter((flag) => flag.enabled).length);
      });
    } else {
      setActiveFlagCount(null);
    }
  }, [user]);

  async function signIn(personaId: string) {
    setLoading(true);
    setError("");
    try {
      const signedInUser = await api.currentUser(personaId);
      setUser(signedInUser);
      setActive("overview");
    } catch {
      setError("The demo API is unavailable. Start the FastAPI server and try again.");
    } finally {
      setLoading(false);
    }
  }

  function logout() {
    setUser(null);
    setActive("overview");
    setRefundData(null);
    setActiveFlagCount(null);
  }

  if (!user) {
    return <SignIn onSignIn={(id) => void signIn(id)} loading={loading} error={error} />;
  }

  return (
    <div className="app-shell">
      <Sidebar
        user={user}
        active={active}
        pendingRefundCount={refundSummary?.pending_count ?? null}
        onNavigate={setActive}
        onLogout={logout}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      <main className="main-area">
        <PageHeader
          title={currentMeta.title}
          subtitle={currentMeta.subtitle}
          onOpenMenu={() => setSidebarOpen(true)}
        />
        <div className="prototype-strip">
          <LockKeyhole size={14} />
          Prototype environment · fictional people and synthetic operational data
        </div>
        {active === "overview" && (
          <Overview
            user={user}
            refundSummary={refundSummary}
            activeFlagCount={activeFlagCount}
            showRefundPriority={showRefundPriority}
            onNavigate={setActive}
          />
        )}
        {active === "kyc" && <KycPanel userId={user.id} />}
        {active === "flags" && (
          <FeatureFlagsPanel user={user} onActiveCountChange={setActiveFlagCount} />
        )}
        {active === "refunds" && (
          <RefundsPanel user={user} onDataChange={setRefundData} />
        )}
        {active === "people" && <PeoplePanel user={user} />}
      </main>
    </div>
  );
}
