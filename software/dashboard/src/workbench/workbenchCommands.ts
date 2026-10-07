import type { ProposalView, RunSummaryView } from "../contracts/generated";
export type PrimaryCommand =
  "check" | "review" | "start" | "resume" | "running";
export function primaryCommand(
  proposal: ProposalView | undefined,
  run: RunSummaryView | undefined,
  runSelected: boolean,
  checked: boolean,
): PrimaryCommand {
  if (runSelected && run && ["running", "queued"].includes(run.status))
    return "running";
  if (runSelected && run && ["paused", "interrupted"].includes(run.status))
    return "resume";
  if (proposal?.status === "accepted") return "start";
  return checked ? "review" : "check";
}
export const commandLabels: Record<PrimaryCommand, string> = {
  check: "Check inputs",
  review: "Review plan",
  start: "Start run",
  resume: "Resume run",
  running: "Run in progress",
};
