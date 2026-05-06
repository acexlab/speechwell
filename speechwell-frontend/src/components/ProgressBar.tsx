/*
File Logic Summary: Compact progress meter used across the guided training
screens for module stats and exercise result summaries.
*/

type ProgressBarProps = {
  label: string;
  value: number;
  tone?: "primary" | "success" | "warning";
};

export default function ProgressBar({
  label,
  value,
  tone = "primary",
}: ProgressBarProps) {
  const safeValue = Math.max(0, Math.min(100, value));

  return (
    <div className="training-progress">
      <div className="training-progress__head">
        <span>{label}</span>
        <strong>{safeValue}%</strong>
      </div>
      <div className="training-progress__track">
        <div
          className={`training-progress__fill training-progress__fill--${tone}`}
          style={{ width: `${safeValue}%` }}
        />
      </div>
    </div>
  );
}
