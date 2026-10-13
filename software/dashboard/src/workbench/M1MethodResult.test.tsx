import { fireEvent, render, screen, cleanup } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { M1MethodResult } from "./M1MethodResult";
import { LocalSettings } from "./LocalSettings";
import { defaultLayout } from "./layout";

afterEach(cleanup);

it("keeps analysis scope in Workflow, not appearance settings", () => {
  const onGoal = vi.fn();
  render(
    <LocalSettings layout={defaultLayout()} onLayout={vi.fn()} onRefresh={vi.fn()}
      goal="fusion_screen" mode="template" onGoal={onGoal} onMode={vi.fn()} section="appearance" onSection={vi.fn()}
    />,
  );
  expect(screen.queryByLabelText("Analysis entry point")).toBeNull();
  expect(onGoal).not.toHaveBeenCalled();
});

it("shows original missing evidence without displaying internal identities", () => {
  render(
    <M1MethodResult
      output={{
        schema_version: "m1-method-check-v1",
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
  expect(screen.getByText(/PSIPRED or JPred output/)).toBeTruthy();
  expect(screen.getByText(/20 aa/)).toBeTruthy();
  expect(screen.queryByText(/PRIVATE_HASH/)).toBeNull();
});
