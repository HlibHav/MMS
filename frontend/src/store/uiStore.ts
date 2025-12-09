import { create } from "zustand";
import { ChatContext } from "../api";

type TabKey = "discovery" | "scenario" | "optimization" | "creative" | "postmortem";

interface UIState {
  activeTab: TabKey;
  setActiveTab: (tab: TabKey) => void;
  chatContext: ChatContext;
  setChatContext: (context: Partial<ChatContext>) => void;
  selectedOpportunityId?: string;
  setSelectedOpportunity: (id?: string) => void;
  activeScenarioIds: string[];
  toggleActiveScenario: (id: string) => void;
  isChatOpen: boolean;
  setChatOpen: (open: boolean) => void;
  isSidebarCollapsed: boolean;
  toggleSidebar: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  activeTab: "discovery",
  setActiveTab: (activeTab) =>
    set((state) => ({
      activeTab,
      chatContext: { ...state.chatContext, screen: activeTab },
    })),
  chatContext: { screen: "discovery", active_scenarios: [], user_task: undefined, metadata: undefined },
  setChatContext: (context) =>
    set((state) => ({
      chatContext: {
        ...state.chatContext,
        ...context,
        metadata: { ...(state.chatContext.metadata || {}), ...(context.metadata || {}) },
      },
    })),
  selectedOpportunityId: undefined,
  setSelectedOpportunity: (id) => set({ selectedOpportunityId: id }),
  activeScenarioIds: [],
  toggleActiveScenario: (id) =>
    set((state) => {
      const exists = state.activeScenarioIds.includes(id);
      return {
        activeScenarioIds: exists ? state.activeScenarioIds.filter((s) => s !== id) : [...state.activeScenarioIds, id],
        chatContext: {
          ...state.chatContext,
          active_scenarios: exists ? state.chatContext.active_scenarios?.filter((s) => s !== id) : [...(state.chatContext.active_scenarios || []), id],
        },
      };
    }),
  isChatOpen: false,
  setChatOpen: (open) => set({ isChatOpen: open }),
  isSidebarCollapsed: false,
  toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
}));
