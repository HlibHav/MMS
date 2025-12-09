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
    <div className="grid min-h-screen grid-cols-1 bg-gray-100 text-gray-900 lg:grid-cols-[260px_1fr]">
      <aside
        className={`${
          isSidebarCollapsed ? "hidden" : "flex"
        } h-full flex-col gap-6 bg-gray-900 px-5 py-6 text-gray-100 lg:flex`}
      >
        <div className="flex items-center justify-between">
          <div className="text-lg font-bold tracking-tight" aria-label="App title">MMS</div>
          <Button variant="ghost" size="sm" className="text-gray-200 lg:hidden" onClick={toggleSidebar} aria-label="Close navigation">
            Close
          </Button>
        </div>
        <nav className="flex flex-col gap-2" aria-label="Primary">
          {tabs.map((t) => (
            <button
              key={t.key}
              className={`flex w-full items-center justify-between rounded-xl px-3 py-2 text-left text-sm transition ${
                activeTab === t.key ? "bg-gray-800 text-white" : "hover:bg-gray-800 hover:text-white"
              }`}
              onClick={() => setActiveTab(t.key as typeof t.key)}
              aria-current={activeTab === t.key}
            >
              <span>{t.label}</span>
              {activeTab === t.key && <Badge tone="info">Active</Badge>}
            </button>
          ))}
        </nav>
        <div className="mt-auto text-xs text-gray-400">v1.0.0</div>
      </aside>

      <div className="relative flex flex-col px-4 py-5 md:px-6">
        <header className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between" aria-label="Page header">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" className="lg:hidden" aria-label="Toggle navigation" onClick={toggleSidebar}>
              Menu
            </Button>
            <div>
              <p className="text-xs uppercase tracking-wide text-gray-500">Promo Co-Pilot</p>
              <h1 className="text-2xl font-semibold">{activeLabel}</h1>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Input className="w-56" placeholder="Search or ask..." aria-label="Search" />
            <Button variant="ghost" size="sm" aria-label="Notifications">Notifications</Button>
            <div className="grid h-10 w-10 place-items-center rounded-full bg-primary-600 text-sm font-bold text-white" aria-label="User avatar">
              PM
            </div>
          </div>
        </header>
        <div className="flex flex-col gap-3 pb-32">{renderTab()}</div>

        <div className="pointer-events-auto fixed bottom-6 right-6 hidden w-[360px] drop-shadow-2xl lg:block">
          <ChatWidget />
        </div>
      </div>

      <FloatingChatLauncher />
    </div>
  );
}
