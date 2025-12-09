import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Badge, Button, Card, PanelHeader, TextArea } from "react-bits";
import { ChatContext, sendChatMessage } from "../api";
import { useUIStore } from "../store/uiStore";

type ChatWidgetProps = {
  onClose?: () => void;
  showHeader?: boolean;
  footerActions?: React.ReactNode;
  "aria-label"?: string;
};

export function ChatWidget({ onClose, showHeader = true, footerActions, "aria-label": ariaLabel }: ChatWidgetProps) {
  const activeTab = useUIStore((s) => s.activeTab);
  const chatContext = useUIStore((s) => s.chatContext);
  const setChatContext = useUIStore((s) => s.setChatContext);
  const selectedOpportunityId = useUIStore((s) => s.selectedOpportunityId);
  const activeScenarioIds = useUIStore((s) => s.activeScenarioIds);
  const setChatOpen = useUIStore((s) => s.setChatOpen);

  const [chatInput, setChatInput] = useState("");
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; content: string; suggestions?: string[] }>>([]);

  const effectiveContext: ChatContext = useMemo(
    () => ({
      ...chatContext,
      screen: activeTab,
      active_scenarios: activeScenarioIds,
      metadata: {
        ...chatContext.metadata,
        selectedOpportunityId,
      },
    }),
    [chatContext, activeTab, activeScenarioIds, selectedOpportunityId]
  );

  useEffect(() => {
    setChatContext({ screen: activeTab });
  }, [activeTab, setChatContext]);

  const chatMutation = useMutation({
    mutationFn: ({ message, context }: { message: string; context?: ChatContext }) => sendChatMessage(message, context),
    onSuccess: (data, variables) => {
      setMessages((prev) => [
        ...prev,
        { role: "user", content: variables.message },
        { role: "assistant", content: data.response, suggestions: data.suggestions },
      ]);
    },
  });

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    const trimmed = chatInput.trim();
    if (!trimmed) return;
    chatMutation.mutate({ message: trimmed, context: effectiveContext });
    setChatInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Card aria-label={ariaLabel ?? "Chat widget"} className="flex h-full flex-col gap-3">
      {showHeader && (
        <PanelHeader
          title="Chat"
          eyebrow="Co-Pilot"
          action={
            onClose ? (
              <Button variant="ghost" size="sm" aria-label="Close chat" onClick={() => { setChatOpen(false); onClose(); }}>
                Close
              </Button>
            ) : null
          }
        />
      )}
      <div className="flex items-center gap-2 text-xs text-gray-600">
        <Badge tone="info">Screen: {activeTab}</Badge>
        {selectedOpportunityId && <Badge tone="warn">Opp: {selectedOpportunityId}</Badge>}
        {activeScenarioIds.length > 0 && <Badge tone="muted">{activeScenarioIds.length} scenarios</Badge>}
      </div>
      <div ref={scrollRef} className="flex min-h-[160px] flex-1 flex-col gap-2 overflow-y-auto rounded-xl bg-gray-50 p-3">
        {messages.length === 0 && <p className="text-sm text-gray-500">Ask anything about the current screen, scenarios, or gaps.</p>}
        {messages.map((m, idx) => (
          <div key={idx} className={`rounded-xl px-3 py-2 text-sm ${m.role === "user" ? "bg-primary-50 text-gray-900" : "bg-white shadow-card"}`}>
            <p className="font-semibold text-xs uppercase tracking-wide text-gray-500">{m.role === "user" ? "You" : "Co-Pilot"}</p>
            <p className="whitespace-pre-wrap text-gray-900">{m.content}</p>
            {m.suggestions && (
              <ul className="mt-2 list-disc space-y-1 pl-4 text-gray-700">
                {m.suggestions.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
      <div className="space-y-2">
        <TextArea
          aria-label="Chat input"
          placeholder="Ask about scenarios or gaps…"
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={4}
        />
        <div className="flex items-center justify-between gap-2">
          <Button onClick={handleSend} disabled={chatMutation.isPending}>
            {chatMutation.isPending ? "Sending…" : "Send"}
          </Button>
          {footerActions}
        </div>
      </div>
    </Card>
  );
}

export function FloatingChatLauncher() {
  const isChatOpen = useUIStore((s) => s.isChatOpen);
  const setChatOpen = useUIStore((s) => s.setChatOpen);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setChatOpen(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [setChatOpen]);

  return (
    <>
      <div className="fixed bottom-4 right-4 z-40 lg:hidden">
        {!isChatOpen && (
          <Button className="shadow-hover" size="md" onClick={() => setChatOpen(true)} aria-expanded={isChatOpen} aria-label="Open chat">
            Open Chat
          </Button>
        )}
      </div>
      {isChatOpen && (
        <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden" role="dialog" aria-modal="true">
          <div className="absolute bottom-0 left-0 right-0 max-h-[72vh] overflow-hidden rounded-t-2xl bg-white p-4 shadow-hover">
            <ChatWidget
              aria-label="Mobile chat widget"
              onClose={() => setChatOpen(false)}
              footerActions={
                <Button variant="ghost" size="sm" onClick={() => setChatOpen(false)} aria-label="Close chat">
                  Dismiss
                </Button>
              }
            />
          </div>
        </div>
      )}
    </>
  );
}
