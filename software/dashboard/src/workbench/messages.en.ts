/** Static reviewed English messages. Never translate evidence at runtime. */
export const messages = {
  operationFailed: "Operation incomplete. Check the safe diagnostic.",
  metricsComputed: "Metrics computed",
  numericalSolution: "Numerical solution available",
  evidenceMissing: "Required evidence is missing",
  notAssessed: "Not assessed",
  noTrajectory: "No time-course data available",
  noStructure: "No structure artifact attached",
  templatePlanner: "Template planner",
  originalSource: "Original source text",
  sourcePanel: "Data and provenance",
} as const;

export const jobLabels: Readonly<Record<string, string>> = {
  pending: "Pending",
  queued: "Queued",
  running: "Running",
  succeeded: "Job completed",
  failed: "Failed",
  paused: "Paused",
  cancelled: "Cancelled",
  interrupted: "Interrupted",
  blocked: "Blocked",
};
