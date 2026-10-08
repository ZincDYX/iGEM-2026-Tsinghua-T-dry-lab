import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { WorkflowImporter } from "./WorkflowImporter";

afterEach(cleanup);
function deferredFile() {
  let resolve!: (text: string) => void;
  const promise = new Promise<string>((done) => {
    resolve = done;
  });
  return { file: { text: () => promise }, resolve };
}
it("last selected file wins even when reads complete in reverse order", async () => {
  render(
    <WorkflowImporter busy={false} enabled submit={vi.fn()} onEdit={vi.fn()} />,
  );
  const fileInput = screen.getByLabelText("Read workflow file");
  const first = deferredFile(),
    second = deferredFile();
  fireEvent.change(fileInput, { target: { files: [first.file] } });
  fireEvent.change(fileInput, { target: { files: [second.file] } });
  second.resolve("second");
  await waitFor(() =>
    expect(
      (screen.getByLabelText("Workflow JSON") as HTMLTextAreaElement).value,
    ).toBe("second"),
  );
  first.resolve("first");
  await Promise.resolve();
  expect(
    (screen.getByLabelText("Workflow JSON") as HTMLTextAreaElement).value,
  ).toBe("second");
});
it("manual editing invalidates an outstanding file read", async () => {
  render(
    <WorkflowImporter busy={false} enabled submit={vi.fn()} onEdit={vi.fn()} />,
  );
  const first = deferredFile();
  fireEvent.change(screen.getByLabelText("Read workflow file"), {
    target: { files: [first.file] },
  });
  fireEvent.change(screen.getByLabelText("Workflow JSON"), {
    target: { value: "manual" },
  });
  first.resolve("obsolete");
  await Promise.resolve();
  expect(
    (screen.getByLabelText("Workflow JSON") as HTMLTextAreaElement).value,
  ).toBe("manual");
});
