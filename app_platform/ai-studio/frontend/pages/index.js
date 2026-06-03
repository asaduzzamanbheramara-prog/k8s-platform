import { useState } from "react";

export default function Home() {

  const [prompt, setPrompt] = useState("");
  const [output, setOutput] = useState("");

  const generate = async () => {

    const res = await fetch("/api/generate", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ prompt })
    });

    const data = await res.json();
    setOutput(data.result);
  };

  return (
    <div style={{ display: "flex", height: "100vh" }}>

      <textarea
        style={{ width: "50%" }}
        value={output}
        onChange={(e) => setOutput(e.target.value)}
      />

      <div style={{ width: "50%", padding: 20 }}>
        <h2>AI Cursor Studio</h2>

        <textarea
          style={{ width: "100%", height: 120 }}
          placeholder="Ask AI..."
          onChange={(e) => setPrompt(e.target.value)}
        />

        <button onClick={generate}>
          Generate
        </button>
      </div>

    </div>
  );
}
