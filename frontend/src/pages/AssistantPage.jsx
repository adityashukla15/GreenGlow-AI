import { useEffect, useRef, useState } from "react";
import {
  AlertCircle,
  Bot,
  Leaf,
  LoaderCircle,
  MessageCircle,
  RefreshCw,
  Send,
  Trash2,
  UserRound,
} from "lucide-react";
import { ApiError, request } from "../services/api.js";
import { endpoints } from "../services/endpoints.js";

const MAX_MESSAGE_LENGTH = 2000;
const QUICK_PROMPTS = [
  "How can I celebrate an eco-friendly Diwali?",
  "How do I reduce plastic waste?",
  "What are sustainable alternatives to decorations?",
  "How can I save electricity during festivals?",
];

export function AssistantPage() {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [validationError, setValidationError] = useState("");
  const messageEndRef = useRef(null);
  const requestControllerRef = useRef(null);
  const sendLockRef = useRef(false);
  const nextIdRef = useRef(1);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({
      behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches
        ? "auto"
        : "smooth",
      block: "end",
    });
  }, [messages]);

  useEffect(
    () => () => {
      requestControllerRef.current?.abort();
    },
    [],
  );

  async function sendMessage(messageText = draft, retryAssistantId = null) {
    const message = messageText.trim();
    if (sendLockRef.current) {
      return;
    }
    if (!message) {
      setValidationError("Write a message before sending.");
      return;
    }
    if (message.length > MAX_MESSAGE_LENGTH) {
      setValidationError(
        `Messages must be ${MAX_MESSAGE_LENGTH.toLocaleString()} characters or fewer.`,
      );
      return;
    }

    setValidationError("");
    setDraft("");
    sendLockRef.current = true;
    setIsSending(true);

    const assistantMessageId = retryAssistantId ?? nextIdRef.current++;
    if (retryAssistantId === null) {
      const userMessageId = nextIdRef.current++;
      setMessages((current) => [
        ...current,
        { id: userMessageId, role: "user", text: message },
        {
          id: assistantMessageId,
          role: "assistant",
          status: "loading",
        },
      ]);
    } else {
      setMessages((current) =>
        current.map((item) =>
          item.id === assistantMessageId
            ? {
                id: assistantMessageId,
                role: "assistant",
                status: "loading",
              }
            : item,
        ),
      );
    }

    const controller = new AbortController();
    requestControllerRef.current = controller;

    try {
      const response = await request(endpoints.assistant, {
        method: "POST",
        body: { message },
        signal: controller.signal,
      });

      if (typeof response?.reply !== "string" || !response.reply.trim()) {
        throw new Error("The assistant returned an invalid response.");
      }

      setMessages((current) =>
        current.map((item) =>
          item.id === assistantMessageId
            ? {
                id: assistantMessageId,
                role: "assistant",
                text: response.reply,
              }
            : item,
        ),
      );
    } catch (error) {
      if (error.name === "AbortError") {
        return;
      }

      const errorMessage =
        error instanceof ApiError
          ? error.status === 422
            ? "The message could not be accepted. Check its length and try again."
            : error.status === 404
              ? "The assistant endpoint is unavailable right now. Please try again later."
            : error.message
          : "The assistant response could not be read. Please try again.";
      setMessages((current) =>
        current.map((item) =>
          item.id === assistantMessageId
            ? {
                id: assistantMessageId,
                role: "assistant",
                error: errorMessage,
                retryText: message,
              }
            : item,
        ),
      );
    } finally {
      requestControllerRef.current = null;
      sendLockRef.current = false;
      setIsSending(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    sendMessage();
  }

  function handleInputKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      sendMessage();
    }
  }

  function clearConversation() {
    if (messages.length === 0 || isSending) {
      return;
    }
    if (
      window.confirm(
        "Clear this conversation? The messages will be removed from this page.",
      )
    ) {
      setMessages([]);
      setDraft("");
      setValidationError("");
    }
  }

  function retryFailedMessage(assistantMessageId, message) {
    setValidationError("");
    sendMessage(message, assistantMessageId);
  }

  return (
    <main className="assistant-page">
      <header className="assistant-heading">
        <p className="eyebrow">
          <Leaf size={14} aria-hidden="true" />
          GreenGlow AI Assistant
        </p>
        <h1>Thoughtful ideas for a greener Diwali.</h1>
        <p>
          Ask for practical eco-friendly Diwali suggestions. Your conversation
          stays on this page for the current session and is not saved as profile
          data.
        </p>
      </header>

      <section className="assistant-chat" aria-label="Assistant conversation">
        <div className="assistant-chat-toolbar">
          <div className="assistant-identity">
            <span className="assistant-avatar">
              <Bot size={19} aria-hidden="true" />
            </span>
            <div>
              <strong>GreenGlow Assistant</strong>
              <span>Eco-friendly Diwali suggestions</span>
            </div>
          </div>
          <button
            className="assistant-clear-button"
            type="button"
            onClick={clearConversation}
            disabled={messages.length === 0 || isSending}
            aria-label="Clear conversation"
            title="Clear conversation"
          >
            <Trash2 size={16} aria-hidden="true" />
            <span>Clear</span>
          </button>
        </div>

        <div className="assistant-transcript" aria-live="polite">
          <div className="assistant-message assistant-message-bot">
            <span className="assistant-message-icon" aria-hidden="true">
              <Bot size={16} />
            </span>
            <div className="assistant-message-content">
              <span className="assistant-message-label">GreenGlow Assistant</span>
              <p>
                Hello! Ask me for practical ideas to celebrate Diwali more
                thoughtfully, from decorations and gifting to waste reduction.
              </p>
            </div>
          </div>

          {messages.map((message) => (
            <div
              className={`assistant-message${message.role === "user" ? " assistant-message-user" : " assistant-message-bot"}`}
              key={message.id}
            >
              <span className="assistant-message-icon" aria-hidden="true">
                {message.role === "user" ? (
                  <UserRound size={16} />
                ) : (
                  <Bot size={16} />
                )}
              </span>
              <div className="assistant-message-content">
                <span className="assistant-message-label">
                  {message.role === "user" ? "You" : "GreenGlow Assistant"}
                </span>
                {message.status === "loading" ? (
                  <div className="assistant-typing" role="status">
                    <LoaderCircle size={16} aria-hidden="true" />
                    <span>Preparing a response…</span>
                  </div>
                ) : message.error ? (
                  <div className="assistant-error-message" role="alert">
                    <p>
                      <AlertCircle size={15} aria-hidden="true" />
                      {message.error}
                    </p>
                    <button
                      type="button"
                      onClick={() =>
                        retryFailedMessage(message.id, message.retryText)
                      }
                    >
                      <RefreshCw size={13} aria-hidden="true" />
                      Retry this message
                    </button>
                  </div>
                ) : (
                  <p>{message.text}</p>
                )}
              </div>
            </div>
          ))}
          <div ref={messageEndRef} />
        </div>

        {messages.length === 0 && (
          <div className="assistant-prompts" aria-label="Suggested questions">
            <p>
              <MessageCircle size={14} aria-hidden="true" />
              Try asking
            </p>
            <div>
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  type="button"
                  key={prompt}
                  disabled={isSending}
                  onClick={() => sendMessage(prompt)}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        <form className="assistant-composer" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="assistant-message-input">
            Your message
          </label>
          <textarea
            id="assistant-message-input"
            value={draft}
            onChange={(event) => {
              setDraft(event.target.value);
              setValidationError("");
            }}
            onKeyDown={handleInputKeyDown}
            placeholder="Ask about an eco-friendly Diwali…"
            maxLength={MAX_MESSAGE_LENGTH}
            rows={2}
            disabled={isSending}
            aria-describedby="assistant-input-note assistant-validation"
          />
          <div className="assistant-composer-footer">
            <span id="assistant-input-note">
              Enter to send · Shift+Enter for a new line ·{" "}
              {draft.length.toLocaleString()}/{MAX_MESSAGE_LENGTH.toLocaleString()}
            </span>
            <button
              className="button button-primary assistant-send-button"
              type="submit"
              disabled={isSending || !draft.trim()}
            >
              {isSending ? (
                <>
                  <LoaderCircle size={16} aria-hidden="true" />
                  Sending
                </>
              ) : (
                <>
                  Send <Send size={15} aria-hidden="true" />
                </>
              )}
            </button>
          </div>
          <p
            className="assistant-validation-message"
            id="assistant-validation"
            role={validationError ? "alert" : undefined}
          >
            {validationError}
          </p>
        </form>
      </section>
    </main>
  );
}
