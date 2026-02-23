/*
File Logic Summary: Shared refresh action button with rotating icon animation while refresh request is in progress.
*/

import "../styles/loading-state.css";

type RefreshButtonProps = {
  onClick: () => void;
  refreshing?: boolean;
  label?: string;
  className?: string;
};

export default function RefreshButton({
  onClick,
  refreshing = false,
  label = "Refresh",
  className = "",
}: RefreshButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`refresh-button ${className}`.trim()}
      disabled={refreshing}
      aria-busy={refreshing}
    >
      <svg
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
        className={refreshing ? "spinning" : ""}
      >
        <path d="M17.65 6.35A7.95 7.95 0 0012 4V1L7 6l5 5V7a5 5 0 11-5 5H5a7 7 0 107.75-6.95c1.2.13 2.33.57 3.29 1.3l1.61-1z" />
      </svg>
      <span>{refreshing ? "Refreshing..." : label}</span>
    </button>
  );
}

