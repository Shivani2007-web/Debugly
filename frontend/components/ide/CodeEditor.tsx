"use client";

// Monaco editor wrapper. Kept thin: it only owns the editor surface and
// surfaces value changes upward. The parent owns the code state so later
// phases (behavior tracking, Smart Reuse) can observe edits in one place.

import Editor, { type OnMount } from "@monaco-editor/react";
import { useRef } from "react";

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  readOnly?: boolean;
}

export function CodeEditor({ value, onChange, readOnly = false }: CodeEditorProps) {
  const editorRef = useRef<Parameters<OnMount>[0] | null>(null);

  const handleMount: OnMount = (editor) => {
    editorRef.current = editor;
  };

  return (
    <div className="h-full w-full overflow-hidden">
      <Editor
        height="100%"
        defaultLanguage="python"
        language="python"
        theme="vs-dark"
        value={value}
        onChange={(v) => onChange(v ?? "")}
        onMount={handleMount}
        options={{
          readOnly,
          fontSize: 14,
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          tabSize: 4,
          insertSpaces: true,
          automaticLayout: true,
          lineNumbers: "on",
          renderLineHighlight: "line",
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
        }}
        loading={
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            Loading editor…
          </div>
        }
      />
    </div>
  );
}
