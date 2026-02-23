/*
File Logic Summary: AI chat page with responsive message stream, typing animation, and simulated voice-record indicator.
*/

import { useState } from "react";
import Sidebar from "../components/Sidebar";
import InteractiveButton from "../components/InteractiveButton";
import { sendChatMessage } from "../api/api";
import "../styles/ai-chat.css";

type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  text: string;
};

export default function AIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      role: "assistant",
      text: "Hi, I can guide you with speech exercises. Ask me about fluency, clarity, pacing, or breath control.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState("");

  const canSend = input.trim().length > 0 && !isTyping;

  const sendMessage = async () => {
    if (!canSend) return;
    setError("");
    const trimmedInput = input.trim();
    const userMsg: ChatMessage = {
      id: Date.now(),
      role: "user",
      text: trimmedInput,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    try {
      const historyPayload = messages.map(({ role, text }) => ({ role, text }));
      const response = await sendChatMessage(trimmedInput, historyPayload);
      setMessages((prev) => [
        ...prev,
        { id: Date.now() + 1, role: "assistant", text: response },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get AI response");
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          text: "I am having trouble connecting to the AI service. Please try again shortly.",
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="chat-layout">
      <Sidebar />
      <main className="chat-content page-enter">
        <header className="chat-header">
          <h1>AI Speech Coach</h1>
          <p>Ask for personalized guidance and daily practice strategies.</p>
        </header>

        <section className="chat-shell">
          <div className="chat-messages">
            {messages.map((message, index) => (
              <article
                key={message.id}
                className={`chat-bubble ${message.role}`}
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                {message.text}
              </article>
            ))}

            {isTyping && (
              <div className="chat-bubble assistant typing">
                <span />
                <span />
                <span />
              </div>
            )}
          </div>

          {error && <p style={{ color: "#c0392b", margin: "0.4rem 0 0" }}>Error: {error}</p>}

          <div className="chat-controls">
            <button
              type="button"
              className={`mic-button ${isRecording ? "recording" : ""}`}
              onClick={() => setIsRecording((v) => !v)}
              aria-label="Toggle recording"
            >
              <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5.3-3c0 3-2.54 5.1-5.3 5.1S6.7 14 6.7 11H5c0 3.41 2.72 6.23 6 6.72V21h2v-3.28c3.28-.48 6-3.3 6-6.72h-1.7z" />
              </svg>
              {isRecording && <i className="recording-dot" />}
            </button>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your question..."
              onKeyDown={(e) => {
                if (e.key === "Enter") sendMessage();
              }}
            />
            <InteractiveButton
              type="button"
              variant="primary"
              onClick={sendMessage}
              disabled={!canSend}
            >
              Send
            </InteractiveButton>
          </div>
        </section>
      </main>
    </div>
  );
}
