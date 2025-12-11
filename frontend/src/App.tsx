import { useEffect } from "react";
import { Badge, Button, Input } from "react-bits";
import "./index.css";
import { useUIStore } from "./store/uiStore";
import DiscoveryScreen from "./screens/DiscoveryScreen";
import ScenarioLabScreen from "./screens/ScenarioLabScreen";
import OptimizationScreen from "./screens/OptimizationScreen";
import CreativeScreen from "./screens/CreativeScreen";
import PostMortemScreen from "./screens/PostMortemScreen";
import { ChatWidget, FloatingChatLauncher } from "./components/ChatWidget";

const tabs = [
  { key: "discovery", label: "Discovery" },
  { key: "scenario", label: "Scenario Lab" },
  { key: "optimization", label: "Optimization" },
  { key: "creative", label: "Creative Companion" },
  { key: "postmortem", label: "Post-Mortem" },
];

export default function App() {
  const activeTab = useUIStore((s) => s.activeTab);
  const setActiveTab = useUIStore((s) => s.setActiveTab);
  const isSidebarCollapsed = useUIStore((s) => s.isSidebarCollapsed);
  const toggleSidebar = useUIStore((s) => s.toggleSidebar);
  const isChatOpen = useUIStore((s) => s.isChatOpen);
  const setChatOpen = useUIStore((s) => s.setChatOpen);

  useEffect(() => {
    setChatOpen(false);
  }, [activeTab, setChatOpen]);

  const renderTab = () => {
    switch (activeTab) {
      case "discovery":
        return <DiscoveryScreen />;
      case "scenario":
        return <ScenarioLabScreen />;
      case "optimization":
        return <OptimizationScreen />;
      case "creative":
        return <CreativeScreen />;
      case "postmortem":
        return <PostMortemScreen />;
      default:
        return null;
    }
  };

  const activeLabel = tabs.find((t) => t.key === activeTab)?.label ?? "";

  return (
    <div className="min-h-screen bg-surface-50 text-slate-900 lg:grid lg:grid-cols-[260px_1fr]">
      <aside
        className={`${
          isSidebarCollapsed ? "hidden" : "flex"
        } relative h-full flex-col gap-6 border-r border-slate-800 bg-slate-900 px-5 py-6 text-slate-100 shadow-card lg:flex`}
      >
        <div className="flex items-center justify-between">
          <div className="text-lg font-semibold tracking-tight" aria-label="App title">
            MMS
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-slate-200 lg:hidden"
            onClick={toggleSidebar}
            aria-label="Close navigation"
          >
            Close
          </Button>
        </div>
        <nav className="flex flex-col gap-2" aria-label="Primary">
          {tabs.map((t) => (
            <button
              key={t.key}
              className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm transition ${
                activeTab === t.key
                  ? "bg-white/10 text-white shadow-inner"
                  : "text-slate-200 hover:bg-white/5 hover:text-white"
              }`}
              onClick={() => setActiveTab(t.key as typeof activeTab)}
              aria-current={activeTab === t.key}
            >
              <span>{t.label}</span>
              {activeTab === t.key && <Badge tone="info">Active</Badge>}
            </button>
          ))}
        </nav>
        <div className="mt-auto text-xs text-slate-400">v1.0.0</div>
      </aside>

      <div className="relative flex flex-col px-4 py-6 md:px-8">
        <header
          className="mb-5 flex flex-col gap-4 rounded-xl border border-border bg-white p-4 shadow-card md:flex-row md:items-center md:justify-between"
          aria-label="Page header"
        >
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              className="lg:hidden"
              aria-label="Toggle navigation"
              onClick={toggleSidebar}
            >
              Menu
            </Button>
            <div>
              <p className="text-xs uppercase tracking-wide text-muted">Promo Co-Pilot</p>
              <h1 className="text-2xl font-semibold text-slate-900">{activeLabel}</h1>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Input
              className="w-56 rounded-lg border-border bg-surface-50"
              placeholder="Search or ask..."
              aria-label="Search"
            />
            <Button
              variant="ghost"
              size="sm"
              aria-label="Open chat sidebar"
              onClick={() => setChatOpen(!isChatOpen)}
              title={isChatOpen ? "Hide Co-Pilot" : "Open Co-Pilot"}
              aria-pressed={isChatOpen}
            >
              <span className="text-lg leading-none">💬</span>
            </Button>
            <Button variant="ghost" size="sm" aria-label="Notifications">
              Notifications
            </Button>
            <div
              className="grid h-10 w-10 place-items-center rounded-full bg-primary-600 text-sm font-bold text-white"
              aria-label="User avatar"
            >
              PM
            </div>
          </div>
        </header>
        <div className="flex flex-col gap-4 pb-32">{renderTab()}</div>
      </div>

      {/* Desktop right-side panel toggleable by button */}
      <div className="pointer-events-none fixed inset-y-4 right-4 z-30 hidden w-[380px] transition duration-200 ease-in-out lg:block">
        <div
          className={`pointer-events-auto rounded-2xl bg-white shadow-2xl ring-1 ring-slate-200/80 transform transition duration-200 ${
            isChatOpen ? "translate-x-0 opacity-100" : "translate-x-[420px] opacity-0"
          }`}
        >
          <ChatWidget
            aria-label="Chat widget"
            showHeader
            onClose={() => setChatOpen(false)}
            footerActions={
              <Button variant="ghost" size="sm" onClick={() => setChatOpen(false)}>
                Close
              </Button>
            }
          />
        </div>
      </div>

      <FloatingChatLauncher />
    </div>
  );
}
