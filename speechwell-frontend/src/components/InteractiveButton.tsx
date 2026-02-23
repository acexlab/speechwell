/*
File Logic Summary: Reusable UI button with reflection-hover micro-interaction, used across pages for consistent premium button behavior.
*/

import type { ButtonHTMLAttributes, ReactNode } from "react";
import "../styles/interactive-button.css";

type InteractiveButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  fullWidth?: boolean;
};

export default function InteractiveButton({
  children,
  className = "",
  variant = "primary",
  fullWidth = false,
  ...props
}: InteractiveButtonProps) {
  const widthClass = fullWidth ? "interactive-button--full" : "";
  return (
    <button
      {...props}
      className={`interactive-button interactive-button--${variant} ${widthClass} ${className}`.trim()}
    >
      <span className="interactive-button__label">{children}</span>
      <span className="interactive-button__shine" aria-hidden="true" />
    </button>
  );
}

