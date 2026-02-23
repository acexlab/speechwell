/*
File Logic Summary: Shared animated loading indicator with spinner and shimmer bar for data-fetching states.
*/

import "../styles/loading-state.css";

type LoadingStateProps = {
  label?: string;
};

export default function LoadingState({ label = "Loading..." }: LoadingStateProps) {
  return (
    <div className="loading-state" role="status" aria-live="polite">
      <div className="loading-state__spinner" />
      <p>{label}</p>
      <div className="loading-state__track">
        <span />
      </div>
    </div>
  );
}

