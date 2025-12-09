import React from "react";
import type { ButtonHTMLAttributes, InputHTMLAttributes, SelectHTMLAttributes } from "react";
import { CheckCircle2, AlertTriangle, XCircle } from "lucide-react";

function cx(...classes: Array<string | undefined | false | null>) {
  return classes.filter(Boolean).join(" ");
}

export const Card: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div className={cx("rounded-2xl border border-border bg-white p-4 shadow-card", className)}>{children}</div>
);

export const PanelHeader: React.FC<{ title: string; eyebrow?: string; action?: React.ReactNode; className?: string }> = ({
  title,
  eyebrow,
  action,
  className,
}) => (
  <div className={cx("flex items-center justify-between gap-3 mb-3", className)}>
    <div>
      {eyebrow && <p className="text-xs text-muted">{eyebrow}</p>}
      <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
    </div>
    {action}
  </div>
);

export const Button: React.FC<ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" | "secondary"; size?: "sm" | "md" }> = ({
  className,
  variant = "primary",
  size = "md",
  children,
  ...props
}) => {
  const base = "inline-flex items-center justify-center rounded-xl font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2";
  const variantStyles =
    variant === "primary"
      ? "bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500"
      : variant === "secondary"
        ? "bg-primary-50 text-primary-700 hover:bg-primary-100 focus:ring-primary-500"
      : "border border-border text-slate-900 hover:bg-surface-50 focus:ring-primary-500";
  const sizeStyles = size === "sm" ? "px-3 py-2 text-sm" : "px-4 py-2.5 text-sm";
  return (
    <button className={cx(base, variantStyles, sizeStyles, className)} {...props}>
      {children}
    </button>
  );
};

export const Badge: React.FC<{ tone?: "muted" | "success" | "warn" | "info"; children: React.ReactNode; className?: string }> = ({
  tone = "muted",
  children,
  className,
}) => {
  const tones: Record<string, string> = {
    muted: "bg-surface-100 text-slate-900",
    success: "bg-green-50 text-green-700",
    warn: "bg-orange-50 text-orange-700",
    info: "bg-primary-50 text-primary-700",
  };
  return <span className={cx("inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold", tones[tone], className)}>{children}</span>;
};

export const Input: React.FC<InputHTMLAttributes<HTMLInputElement>> = ({ className, ...props }) => (
  <input
    className={cx(
      "w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200",
      className
    )}
    {...props}
  />
);

export const TextArea: React.FC<React.TextareaHTMLAttributes<HTMLTextAreaElement>> = ({ className, ...props }) => (
  <textarea
    className={cx(
      "w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200",
      className
    )}
    {...props}
  />
);

export const Select: React.FC<SelectHTMLAttributes<HTMLSelectElement>> = ({ className, children, ...props }) => (
  <select
    className={cx(
      "w-full rounded-lg border border-border bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200",
      className
    )}
    {...props}
  >
    {children}
  </select>
);

export const SectionTitle: React.FC<{ title: string; eyebrow?: string; className?: string; actions?: React.ReactNode }> = ({ title, eyebrow, className, actions }) => (
  <div className={cx("flex items-center justify-between mb-3", className)}>
    <div>
      {eyebrow && <p className="text-xs text-muted">{eyebrow}</p>}
      <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
    </div>
    {actions}
  </div>
);

export const Table: React.FC<{ headers: string[]; children: React.ReactNode; className?: string }> = ({ headers, children, className }) => (
  <div className={cx("overflow-hidden rounded-xl border border-border bg-white", className)} role="table">
    <div className="grid grid-cols-[repeat(auto-fit,minmax(120px,1fr))] gap-2 bg-surface-50 px-4 py-2 text-sm font-semibold text-slate-800" role="rowgroup">
      {headers.map((h) => (
        <div key={h} role="columnheader">
          {h}
        </div>
      ))}
    </div>
    <div className="divide-y divide-border/60" role="rowgroup">
      {children}
    </div>
  </div>
);

export const TableRow: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div className="grid grid-cols-[repeat(auto-fit,minmax(120px,1fr))] gap-2 px-4 py-3 text-sm text-slate-900 hover:bg-surface-50" role="row">
    {children}
  </div>
);

export const PillList: React.FC<{ items: Array<{ label: string; tone?: "muted" | "success" | "warn" | "info" }>; className?: string }> = ({ items, className }) => (
  <div className={cx("flex flex-wrap gap-2", className)}>
    {items.map((item) => (
      <Badge key={item.label} tone={item.tone}>{item.label}</Badge>
    ))}
  </div>
);

export const ValidationIndicator: React.FC<{ status: "PASS" | "WARN" | "BLOCK"; label?: string; className?: string }> = ({
  status,
  label,
  className,
}) => {
  const tone =
    status === "PASS" ? "text-green-700 bg-green-50" : status === "WARN" ? "text-orange-700 bg-orange-50" : "text-red-700 bg-red-50";
  const Icon = status === "PASS" ? CheckCircle2 : status === "WARN" ? AlertTriangle : XCircle;
  return (
    <span className={cx("inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold", tone, className)}>
      <Icon className="h-4 w-4" />
      {label ?? status}
    </span>
  );
};
