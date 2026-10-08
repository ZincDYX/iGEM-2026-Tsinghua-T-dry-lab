import { fireEvent, render, screen, cleanup } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { M1MethodResult } from "./M1MethodResult";
import { AgentPanel } from "./AgentPanel";

afterEach(cleanup);

it("selects the M1 workflow rather than silently retaining the old goal", () => {
  const onGoal = vi.fn();
  render(
    <AgentPanel
      goal="fusion_screen"
      objective=""
      mode="template"
      permission={false}
      busy={false}
      canPlan
      onGoal={onGoal}
      onObjective={vi.fn()}
      onMode={vi.fn()}
      onPermission={vi.fn()}
      onPropose={vi.fn()}
      onDecision={vi.fn()}
    />,
  );
  fireEvent.change(screen.getByLabelText("Analysis entry point"), {
    target: { value: "m1_sequence_checks" },
  });
  expect(onGoal).toHaveBeenCalledWith("m1_sequence_checks");
});

it("shows original missing evidence without displaying internal identities", () => {
  render(
    <M1MethodResult
      output={{
        candidate_id: "linker20",
        verdict: "blocked",
        precheck: {
          sequence_kind: "scaffold_linker",
          features: { length: 20, sequence_sha256: "PRIVATE_HASH" },
        },
        screen: {
          missing_required_evidence: ["PSIPRED_or_JPred_output"],
          hard_reject_reasons: [],
        },
        steps: [
          {
            step: "2",
            name: "External fragment predictors",
            status: "partial",
            missing: ["secondary structure"],
          },
        ],
      }}
    />,
  );
  expect(screen.getByText(/PSIPRED_or_JPred_output/)).toBeTruthy();
  expect(screen.getByText(/20 aa/)).toBeTruthy();
  expect(screen.queryByText(/PRIVATE_HASH/)).toBeNull();
});
