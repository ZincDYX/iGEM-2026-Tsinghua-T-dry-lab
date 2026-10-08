import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { parsePublic } from "../contracts/validation";
import { StructureAnnotationLinker } from "./StructureAnnotationLinker";
import { linkStructureAnnotations } from "./client";
vi.mock("./client", () => ({ linkStructureAnnotations: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
const asset = (id: string, name: string) => ({
  id,
  file_id: id,
  path: "asset:" + id,
  name,
  sha256: "a".repeat(64),
});
const project = () =>
  parsePublic("ProjectView", {
    id: "SOFTWARE_ONLY",
    name: "SOFTWARE_ONLY",
    revision: 3,
    description: "",
    sequences: [],
    assemblies: [],
    conditions: {},
    pathway: null,
    datasets: [],
    scientific_project: null,
    runtime_profile_ref: null,
    parent_run_id: null,
    parent_snapshot_sha256: null,
    files: [
      asset("source", "source.json"),
      asset("target", "target.pdb"),
      asset("reference", "reference.cif"),
      asset("sequence", "fusion.fasta"),
    ],
  });
it("sends explicit file choices, not user-entered hashes, and requires sequence identity only when selected", async () => {
  const preview = parsePublic("ImportView", {
    kind: "structure_annotations",
    patch: {},
    file: asset("linked", "source.linked.json"),
  });
  vi.mocked(linkStructureAnnotations).mockResolvedValue(preview);
  const onPreview = vi.fn();
  const { container } = render(
    <StructureAnnotationLinker
      project={project()}
      disabled={false}
      action={async (job) => job()}
      onPreview={onPreview}
    />,
  );
  fireEvent.click(screen.getByText("Link structure annotation source"));
  const button = screen.getByRole("button", {
    name: "Check annotation file links",
  }) as HTMLButtonElement;
  expect(button.disabled).toBe(true);
  fireEvent.change(screen.getByLabelText("Annotation JSON source"), {
    target: { value: "source" },
  });
  fireEvent.change(screen.getByLabelText("Annotation target structure"), {
    target: { value: "target" },
  });
  fireEvent.change(screen.getByLabelText("Annotation reference structure"), {
    target: { value: "reference" },
  });
  fireEvent.change(screen.getByLabelText("Annotation fusion FASTA"), {
    target: { value: "sequence" },
  });
  expect(button.disabled).toBe(true);
  fireEvent.change(screen.getByLabelText("Annotation FASTA record name"), {
    target: { value: "FULL_FUSION" },
  });
  fireEvent.click(button);
  await waitFor(() => expect(onPreview).toHaveBeenCalledWith(preview));
  expect(linkStructureAnnotations).toHaveBeenCalledWith({
    project_id: "SOFTWARE_ONLY",
    expected_revision: 3,
    source_file_id: "source",
    target_file_id: "target",
    reference_file_id: "reference",
    sequence_file_id: "sequence",
    sequence_id: "FULL_FUSION",
  });
  expect(container.textContent).not.toContain("a".repeat(64));
  expect(container.textContent).not.toContain("asset:");
});
it("does not enable file binding for unsaved or busy inputs", () => {
  render(
    <StructureAnnotationLinker
      project={project()}
      disabled={true}
      action={async (job) => job()}
      onPreview={() => {
        throw Error("unexpected binding");
      }}
    />,
  );
  expect(
    screen.getByLabelText("Annotation target structure").closest("fieldset")
      ?.disabled,
  ).toBe(true);
});
