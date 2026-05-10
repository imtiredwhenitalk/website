import React, { useState, useRef, useEffect } from 'react';

export type AttachedFile = {
  id: string;
  file: File;
  preview?: string;
};

export type ChatMessage = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  attachments?: AttachedFile[];
  isThinking?: boolean;
};

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hi! I\'m your AI assistant. How can I help you today?',
      timestamp: Date.now(),
    },
  ]);

  const [input, setInput] = useState('');
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach((file) => {
      const fileId = Date.now().toString() + Math.random();
      const fileObj: AttachedFile = {
        id: fileId,
        file,
      };

      // Create preview for images
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          setAttachedFiles((prev) =>
            prev.map((f) =>
              f.id === fileId ? { ...f, preview: event.target?.result as string } : f
            )
          );
        };
        reader.readAsDataURL(file);
      }

      setAttachedFiles((prev) => [...prev, fileObj]);
    });

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (fileId: string) => {
    setAttachedFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  const handleSendMessage = async () => {
    if (!input.trim() && attachedFiles.length === 0) return;

    // Add user message with attachments
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: Date.now(),
      attachments: attachedFiles,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setAttachedFiles([]);
    setIsLoading(true);

    // Add thinking indicator
    const thinkingId = (Date.now() + 0.5).toString();
    setMessages((prev) => [
      ...prev,
      {
        id: thinkingId,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        isThinking: true,
      },
    ]);

    try {
      // Build conversation history
      const conversationMessages = messages
        .filter((m) => !m.isThinking)
        .map((m) => ({
          role: m.role,
          content: m.content,
        }))
        .concat([{ role: 'user', content: input }]);

      // Call backend API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: conversationMessages,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.ok) {
        throw new Error(data.error || 'Unknown error from AI');
      }

      // Remove thinking indicator and add actual response
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== thinkingId);
        return [
          ...filtered,
          {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: data.content,
            timestamp: Date.now(),
          },
        ];
      });
    } catch (error) {
      // Remove thinking indicator and add error
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== thinkingId);
        return [
          ...filtered,
          {
            id: (Date.now() + 1).toString(),
            role: 'assistant',
            content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
            timestamp: Date.now(),
          },
        ];
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-message chat-message--${msg.role}`}
          >
            <div className="chat-message__avatar">
              {msg.role === 'user' ? '👤' : '✨'}
            </div>
            <div className="chat-message__content">
              {msg.isThinking ? (
                <div className="chat-message__thinking">
                  <div className="thinking-dot"></div>
                  <div className="thinking-dot"></div>
                  <div className="thinking-dot"></div>
                  <span className="thinking-text">AI is thinking</span>
                </div>
              ) : (
                <>
                  {msg.attachments && msg.attachments.length > 0 && (
                    <div className="chat-message__attachments">
                      {msg.attachments.map((file) => (
                        <div key={file.id} className="file-preview">
                          {file.preview ? (
                            <img src={file.preview} alt={file.file.name} />
                          ) : (
                            <div className="file-icon">📎</div>
                          )}
                          <span className="file-name">{file.file.name}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="chat-message__text">{msg.content}</div>
                </>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-area">
        {attachedFiles.length > 0 && (
          <div className="attached-files">
            {attachedFiles.map((file) => (
              <div key={file.id} className="attached-file-tag">
                <span>{file.file.name}</span>
                <button
                  onClick={() => removeFile(file.id)}
                  className="remove-file"
                  type="button"
                  aria-label="Remove file"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}
        <div className="chat-input-wrapper">
          <textarea
            className="chat-input"
            placeholder="Type your message... (Shift+Enter for new line, Enter to send)"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
          />
          <div className="input-actions">
            <label className="attach-btn" title="Attach files">
              📎
              <input
                ref={fileInputRef}
                type="file"
                multiple
                onChange={handleFileSelect}
                disabled={isLoading}
                style={{ display: 'none' }}
                accept="image/*,.pdf,.txt,.doc,.docx,.json"
              />
            </label>
            <button
              className="chat-send-btn"
              onClick={handleSendMessage}
              disabled={isLoading || (!input.trim() && attachedFiles.length === 0)}
              aria-label="Send message"
            >
              {isLoading ? '⏳' : '→'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
